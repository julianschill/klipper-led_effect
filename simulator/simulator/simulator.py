from distutils.command.config import config
import sys

from pathlib import Path # if you haven't already done so
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[2]
print(root)
sys.path.append(str(root))
from pathlib import Path

import wx
import simgui
import time
from src.led_effect import ledEffect, ledFrameHandler

USE_BUFFERED_DC = True

class mockLedHelper:
    def __init__(self,config):
        self.led_count = config.getint("ledcount", 1, 1, 1024)
    def get_led_count(self):
        return self.led_count

class mockPrinter:
    NOW = 0
    def __init__(self, config):
        self.config = config
        self.config.set_printer(self)
        self.led_helper = mockLedHelper(config)
        self.objects={}
        self.led_effect=ledEffect(config)
        self.objects["myeffect"] = self.led_effect

    def _handle_ready(self):
        for o in self.objects.values():
            o._handle_ready()
        
    def lookup_object(self, o):
        return self
    def load_object(self, config, o):
        if o in self.objects.keys():
            return self.objects[o] 
        else:
            if o == "led_effect":
                self.objects[o]=ledFrameHandler(config)
                return self.objects[o]
        return None
    def register_event_handler(self, event, callback):
        pass
    def register_mux_command(self, cmd, foo, name, command, desc):
        pass
    def register_command(self, cmd, callback, desc):
        pass
    def get_reactor(self):
        return self
    def register_timer(self, callback, time):
        pass

class mockConfig:
    
    def __init__(self):
        self.config={
            "frame_rate" : "24.0",
            "autostart" : "False",
            "run_on_error" : "False",
            "heater" : None,
            "analog_pin" : None,
            "stepper" : None,
            "layers"  : """gradient       1 1 top  (1, 0.0, 0.0),(0, 1, 0.0),(0.0, 0.0, 1)""",
            "leds" : "leds:leds",
       }
    def set_printer(self, printer):
        self.printer=printer
    def get_printer(self):
        return self.printer
    def get_object(self,o):
        return self
    def getfloat(self,key,default,minval,maxval):
        return float(self.config[key])
    def getboolean(self,key,default):
        return bool(self.config[key])
    def getint(self,key,default,minval,maxval):
        return int(self.config[key])
    def setint(self,key, value):
        self.config[key] = int (value)
    def get_name(self):
        return "led_effect simulator"
    def get(self, key, default=None ):
        return self.config[key]
    def set(self, key, value ):
        self.config[key]=value


class Simulator( simgui.SimFrame ):
    def __init__( self, parent ):
        simgui.SimFrame.__init__( self, parent )
        self.config = mockConfig()
        self.config.setint("ledcount",self.m_spinLED.GetValue())
        self.config.set("layers", "gradient 1 1 top (1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0) ")
        self.init_printer()

        effect_list=list(self.printer.led_effect.availableLayers)
        blend_list=list(self.printer.led_effect.blendingModes)

        self.m_cbEffect.Set(effect_list)
        self.m_cbBlending.Set(blend_list)

        self.led_count = 0
        self.leds = [wx.Colour("black")] * self.led_count

        self.m_ledpanel.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)

        self.m_lcEffectsList.AppendColumn("Active")
        self.m_lcEffectsList.AppendColumn("Effect")
        self.m_lcEffectsList.AppendColumn("Effect Rate")
        self.m_lcEffectsList.AppendColumn("Cut-Off")
        self.m_lcEffectsList.AppendColumn("Blending")
        self.m_lcEffectsList.AppendColumn("Palette")
        

        self.m_txtSettings.SetValue("gradient 1 1 top (1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0)")

        self.parse_layers_from_text()
        self.m_timer.Start(int(1000.0/24.0))

    def init_printer(self):
        self.printer = mockPrinter(self.config)
        self.printer._handle_ready()
        self.printer.led_effect.set_enabled(True)

    def parse_layers_from_text(self):
        self.m_lcEffectsList.DeleteAllItems()
        for i, layer in enumerate([line for line \
            in self.m_txtSettings.GetValue().split('\n') if line.strip()]):
            parms = layer.split()
            self.m_lcEffectsList.InsertItem(self.m_lcEffectsList.GetItemCount(),"")
            for c in range(1,self.m_lcEffectsList.GetColumnCount()):
                self.m_lcEffectsList.SetItem(i,c,parms[c-1])
            self.m_lcEffectsList.SetItem(i,5, "".join(parms[4:]) )
            self.m_lcEffectsList.SetItem(i,0, "1")
            self.m_lcEffectsList.SetColumnWidth(5,wx.LIST_AUTOSIZE )

    def parse_layers_from_list(self):
        layer_str = ""
        for r in range(self.m_lcEffectsList.GetItemCount()):
            if self.m_lcEffectsList.GetItem(r,0).GetText() == "1":
                for c in range(1,self.m_lcEffectsList.GetColumnCount()):
                    layer_str = layer_str + self.m_lcEffectsList.GetItem(r,c).GetText() + " "
                layer_str += "\n"
        self.m_txtSettings.SetValue(layer_str)
        self.config.set("layers",layer_str)
        self.init_printer()

        
    def OnLed_ctrl_changed(self, event):
        self.config.setint("ledcount",self.m_spinLED.GetValue())
        self.init_printer()
    
    def OnApplyClicked(self, event):
        self.parse_layers_from_text()        
        self.config.set("layers", self.m_txtSettings.GetValue())
        self.init_printer()

    def OnBtnLayerClicked(self, event):
        btn = event.GetEventObject()
        if btn == self.btnAddLayerTop:
            self.settingsgrid.InsertRows()
            self._init_row()
        elif btn == self.btnAddLayerBottom:
            self.settingsgrid.InsertRows(self.settingsgrid.GetNumberRows())
            self._init_row(self.settingsgrid.GetNumberRows()-1)
        elif btn == self.btnRemoveLayerTop:
            self.settingsgrid.DeleteRows(0)
        elif btn == self.btnRemoveLayerBottom:
            self.settingsgrid.DeleteRows(self.settingsgrid.GetNumberRows()-1)
        self.configureGrid()
        self.parse_layers_from_grid()
    
    def _insert_in_list(self, list_ctrl, row, item):
        r = list_ctrl.InsertItem(row,"")
        for c,v in enumerate(item):
            list_ctrl.SetItem(r,c,v)
        
    def _remove_from_list(self, list_ctrl, index):
        list_ctrl.DeleteItem(index)
        index=min(index, list_ctrl.GetItemCount()-1)
        list_ctrl.Select(index)

    def OnBtnAddClicked(self, event):
        i = self.m_lcEffectsList.GetFirstSelected()
        self._insert_in_list(self.m_lcEffectsList, i+1,["1","static","0","0","add","(0.0,0.0,0.0)"])
        self.parse_layers_from_list()

    def OnBtnRemoveClicked(self, event):
        self._remove_from_list(self.m_lcEffectsList, self.m_lcEffectsList.GetFirstSelected())
        self.parse_layers_from_list()

    def OnBtnUpClicked(self, event):
        r = self.m_lcEffectsList.GetFirstSelected()
        if r <= 0: return
        item=[]
        for c in range(self.m_lcEffectsList.GetColumnCount()):
            item.append(self.m_lcEffectsList.GetItem(r,c).GetText())
        
        self._remove_from_list(self.m_lcEffectsList,r)
        self._insert_in_list(self.m_lcEffectsList,r-1, item)
        self.m_lcEffectsList.Select(r-1)
        self.parse_layers_from_list()


    def OnBtnDownClicked(self, event):
        r = self.m_lcEffectsList.GetFirstSelected()
        if r >= self.m_lcEffectsList.GetItemCount()-1: return
        item=[]
        for c in range(self.m_lcEffectsList.GetColumnCount()):
            item.append(self.m_lcEffectsList.GetItem(r,c).GetText())
        
        self._remove_from_list(self.m_lcEffectsList,r)
        self._insert_in_list(self.m_lcEffectsList,r+1, item)
        self.m_lcEffectsList.Select(min(r+1,self.m_lcEffectsList.GetItemCount()-1))
        self.parse_layers_from_list()

    def OnEffectsListItemSelected(self, event):

        r = self.m_lcEffectsList.GetFirstSelected()
        if r < 0: 
            self.m_cbActive.Enable(False)
            self.m_cbEffect.Enable(False)
            self.m_spinEffectRate.Enable(False)
            self.m_spinCutOff.Enable(False)
            self.m_cbBlending.Enable(False)
            self.m_lbPalette.Enable(False)
            self.m_lbPalette.Clear()
            self.m_btnAddColour.Enable(False)
            self.m_btnRemoveColour.Enable(False)
            self.m_btnColourUp.Enable(False)
            self.m_btnColourDown.Enable(False)
            self.m_cpColor.Enable(False)
            return
        else:
            self.m_cbActive.Enable(True)
            self.m_cbEffect.Enable(True)
            self.m_spinEffectRate.Enable(True)
            self.m_spinCutOff.Enable(True)
            self.m_cbBlending.Enable(True)
            self.m_lbPalette.Enable(True)
            self.m_btnAddColour.Enable(True)
            self.m_btnRemoveColour.Enable(True)
            self.m_btnColourUp.Enable(True)
            self.m_btnColourDown.Enable(True)
            self.m_cpColor.Enable(True)

        self.m_cbActive.SetValue(self.m_lcEffectsList.GetItem(r,0).GetText() == "1")
        self.m_cbEffect.SetValue(self.m_lcEffectsList.GetItem(r,1).GetText())
        self.m_spinEffectRate.SetValue(float(self.m_lcEffectsList.GetItem(r,2).GetText()))
        self.m_spinCutOff.SetValue(float(self.m_lcEffectsList.GetItem(r,3).GetText()))
        self.m_cbBlending.SetValue(self.m_lcEffectsList.GetItem(r,4).GetText())
        palette = self._parse_palette_from_string(self.m_lcEffectsList.GetItem(r,5).GetText())
        self.m_lbPalette.Clear()
        for c in palette:
            self.m_lbPalette.Append(c)

    def _parse_palette_from_string(self, palette_string):
        palette="".join(palette_string.split())                         # remove whitespaces
        palette=palette.strip(",")
        palette=palette.split("),(")                                    # split colors
        palette=[ c.strip("()") for c in palette]
        return palette

    def OnEffectSettingChanged(self,event):
        r = self.m_lcEffectsList.GetFirstSelected()
        self.m_lcEffectsList.SetItem(r,0,str(int(self.m_cbActive.GetValue())))
        self.m_lcEffectsList.SetItem(r,1,self.m_cbEffect.GetValue())
        self.m_lcEffectsList.SetItem(r,2,self.m_spinEffectRate.GetTextValue())
        self.m_lcEffectsList.SetItem(r,3,self.m_spinCutOff.GetTextValue())
        self.m_lcEffectsList.SetItem(r,4,self.m_cbBlending.GetValue())
        
        sel = self.m_lbPalette.GetSelection()            
        if sel >=0:
            selected_colour=self.m_lbPalette.GetString(self.m_lbPalette.GetSelection())
            selected_colour=selected_colour.split(",")
            selected_colour=[int(255.0 * float(v)) for v in selected_colour]
            self.m_cpColor.SetColour(wx.Colour(selected_colour))
        self.parse_layers_from_list()
        
    
    def OnColourChanged(self, event):
        colour=self.m_cpColor.GetColour()
        colour = [colour.GetRed(),colour.GetGreen(),colour.GetBlue()]
        colour = ["{:.2f}".format(c/255.0) for c in colour]
        colour = ",".join(colour)
        self.m_lbPalette.SetString(self.m_lbPalette.GetSelection(),colour)
        self._update_colors()

    def _update_colors(self):
        palette=self.m_lbPalette.GetStrings()
        palette= ["(" + c + ")" for c in palette]
        self.m_lcEffectsList.SetItem(self.m_lcEffectsList.GetFirstSelected(),5,",".join(palette))
        self.parse_layers_from_list()

    def OnBtnAddColourClick(self, event):
        i = self.m_lbPalette.GetSelection()
        self.m_lbPalette.Insert("0.0,0.0,0.0",i+1)        
        self._update_colors()

    def OnBtnRemoveColourClick(self, event):
        i = self.m_lbPalette.GetSelection()
        self.m_lbPalette.Delete(i)
        self.m_lbPalette.Select(min(i,self.m_lbPalette.GetCount()-1))
        self._update_colors()

    def OnBtnColourUpClick(self, event):
        i = self.m_lbPalette.GetSelection()
        if i <= 0: return
        self.m_lbPalette.Insert(self.m_lbPalette.GetString(i), i-1)
        self.m_lbPalette.Delete(i+1)
        self.m_lbPalette.Select(i-1)
        self._update_colors()

    def OnBtnColourDownClick(self, event):
        i = self.m_lbPalette.GetSelection()
        if i >= self.m_lbPalette.GetCount()-1: return
        self.m_lbPalette.Insert(self.m_lbPalette.GetString(i), i+2)
        self.m_lbPalette.Delete(i)
        self.m_lbPalette.Select(i+1)
        self._update_colors()


    def OnExit(self, event):
        self.Close(True)

    def update(self, event):
        ledframe, update = self.printer.led_effect.getFrame(time.monotonic())
        if update:
            led_count = self.printer.led_helper.get_led_count()
            self.setLedCount( led_count )
            for led_index in range(led_count):
                self.setLeds(led_index, 
                    int(255.0*ledframe[led_index * 4]),
                    int(255.0*ledframe[led_index * 4 + 1]),
                    int(255.0*ledframe[led_index * 4 + 2]))
    

    def setLedCount(self, count):
        self.led_count = count
        self.leds=[wx.Colour("black")] * self.led_count
        
    def setLeds(self,index, r,g,b):
        self.leds[index]=wx.Colour(r,g,b)
        self.Refresh()

    def OnLedPanelSize(self, event):
        event.Skip()
        self.Refresh()

    def OnLedPanelPaint(self, event):
        dc = wx.AutoBufferedPaintDC(self.m_ledpanel)
        dc.Clear()
        size = int(self.m_spinLEDSize.GetTextValue())
        distance = int(self.m_spinDistance.GetTextValue())
        offset= self.m_ledpanel.GetClientSize()[0]/2 - (0.5 * self.led_count * (2* size + distance)) 
        for i, led in enumerate(self.leds):
            dc.SetPen(wx.Pen(led, 1, wx.PENSTYLE_SOLID))
            dc.SetBrush(wx.Brush(led))
            dc.DrawCircle(int(size + i*(2*size+distance) + offset),int(self.m_ledpanel.GetClientSize()[1]/2), int(size))

if __name__ == '__main__':
    app = wx.App(False)
    frame = Simulator(None)
    frame.Show(True)
    app.MainLoop()

