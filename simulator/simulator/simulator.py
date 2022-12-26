import wx
import simulator.simgui as simgui
from simulator.klippermock import *
import time
import math

USE_BUFFERED_DC = True

class Simulator( simgui.SimFrame ):
    def __init__( self, parent ):
        simgui.SimFrame.__init__( self, parent )
        self.config = mockConfig()
        self.setLedCount(self.m_spinLED.GetValue())
        self.config.setint("ledcount",self.led_count)
        self.config.set("layers", "gradient 1 1 top (1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0) ")
        self.init_printer()
        self._calc_coordinates()

        effect_list=list(self.printer.led_effect.availableLayers)
        blend_list=list(self.printer.led_effect.blendingModes)

        self.m_cbEffect.Set(effect_list)
        self.m_cbBlending.Set(blend_list)

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
        self.OnStepperSlider(None)
        self.OnHeaterSlider(None)
        self.OnProgressSlider(None)
        self.OnAnalogSlider(None)

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

    def _insert_in_list(self, list_ctrl, row, item):
        r = list_ctrl.InsertItem(row,"")
        for c,v in enumerate(item):
            list_ctrl.SetItem(r,c,v)
        
    def _remove_from_list(self, list_ctrl, index):
        list_ctrl.DeleteItem(index)
        index=min(index, list_ctrl.GetItemCount()-1)
        list_ctrl.Select(index)

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
    
    def OnStepperSlider(self, event):
        self.printer.set_stepper_pos(self.m_slStepper.GetValue())

    def OnHeaterSlider(self, event):
        self.printer.set_heater(self.m_slHeater.GetMin(), self.m_slHeater.GetMax(), self.m_slHeater.GetValue())
    
    def OnProgressSlider(self, event):
        self.printer.set_progress(self.m_slProgress.GetValue())
        
    def OnAnalogSlider(self, event):
        self.printer.set_analog(self.m_slAnalog.GetValue())

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
        self._calc_coordinates()
        
    def setLeds(self,index, r,g,b):
        r = min(r,255)
        g = min(g,255)
        b = min(b,255)
        self.leds[index]=wx.Colour(r,g,b)
        self.Refresh()

    def OnLedPanelSize(self, event):
        event.Skip()
        self.Refresh()

    def OnLayoutChanged(self, event):
        self._calc_coordinates()

    def _calc_coordinates(self):
        self.led_coordinates=[]
        size = int(self.m_spinLEDSize.GetTextValue())
        distance = int(self.m_spinDistance.GetTextValue())
        lines = int(self.m_spinLines.GetValue())
        leds_per_line = math.ceil(self.led_count/lines)
        
        if self.m_cbLayout.GetValue()=="Rectangle":
            self.m_spinLines.Enable(True)
            for l in range(lines):
                for i in range(leds_per_line):
                    x = int(size + i*(distance) - (0.5 * leds_per_line * distance) )
                    y = int(l*distance - (0.5 * lines * distance))
                    self.led_coordinates += [(x,y,size)]

        elif self.m_cbLayout.GetValue()=="Circle":
            self.m_spinLines.Enable(False)
            r = distance * self.led_count/(2*math.pi)
            for i in range(self.led_count):
                a = 2 * math.pi/self.led_count * i
                x = r * math.sin(a)
                y = r * math.cos(a)
                self.led_coordinates += [(x,y,size)]

        elif self.m_cbLayout.GetValue()=="Triangle":
            self.m_spinLines.Enable(False)
            leds_per_side = math.ceil(self.led_count/3)
            side_length=(leds_per_side+1)*distance
            height=((side_length)-distance) * math.sin(math.radians(60))
            for i in range(leds_per_side):
                x = math.cos(math.radians(60)) * i * side_length/(leds_per_side+1) 
                y = math.sin(math.radians(60)) * i * side_length/(leds_per_side+1) - height/2
                self.led_coordinates += [(x,y,size)]            
            for i in range(leds_per_side):
                x = -i * side_length/(leds_per_side+1) + (side_length-distance)/2
                y = 0 + height/2
                self.led_coordinates += [(x,y,size)]
            for i in range(leds_per_side):
                x = math.cos(math.radians(-60)) * i * side_length/(leds_per_side+1 ) - (side_length-distance)/2
                y = math.sin(math.radians(-60)) * i * side_length/(leds_per_side+1) + height/2
                self.led_coordinates += [(x,y,size)]

        elif self.m_cbLayout.GetValue()=="Voron Logo":
            sln = math.ceil(self.led_count / 2)
            fln = tln = math.ceil(self.led_count / 4)

            s = distance * (sln-1) * math.sin(math.radians(60))
            xy_ratio = 1/math.tan(math.radians(60))

            fls = ( (-1/2 + (xy_ratio/3)), -1/2 )
            flg = ( -1/2,                  (1/3 - 1/2) )

            sls = ( xy_ratio/2,            -1/2 )
            slg = ( -xy_ratio/2,           1/2 )

            tls = ( 1/2,                   (2/3 - 1/2) )
            tlg = ( (-xy_ratio/3 + 1/2),   1/2)

            for i in range(fln):
                x = s * (fls[0] + i/(fln-1) * (flg[0]-fls[0]))
                y = s * (fls[1] + i/(fln-1) * (flg[1]-fls[1]))
                self.led_coordinates += [(x,y,size)]

            for i in range(sln):
                x = s *( sls[0] + i/(sln-1) * (slg[0]-sls[0]))
                y = s * (sls[1] + i/(sln-1) * (slg[1]-sls[1]))
                self.led_coordinates += [(x,y,size)]

            for i in range(tln):
                x = s * (tls[0] + i/(tln-1) * (tlg[0]-tls[0]))
                y = s * (tls[1] + i/(tln-1) * (tlg[1]-tls[1]))
                self.led_coordinates += [(x,y,size)]

    def OnLedPanelPaint(self, event):
        dc = wx.AutoBufferedPaintDC(self.m_ledpanel)
        dc.Clear()
        offset_x= self.m_ledpanel.GetClientSize()[0]//2 
        offset_y= self.m_ledpanel.GetClientSize()[1]//2 

        for i, led in enumerate(self.leds):
            dc.SetPen(wx.Pen(led, 1, wx.PENSTYLE_SOLID))
            dc.SetBrush(wx.Brush(led))
            if self.m_cbShape.GetValue() == "Circle":
                dc.DrawCircle(self.led_coordinates[i][0] + offset_x, self.led_coordinates[i][1] + offset_y, self.led_coordinates[i][2]//2 )
            elif self.m_cbShape.GetValue() == "Square":
                dc.DrawRectangle(self.led_coordinates[i][0] + offset_x, self.led_coordinates[i][1] + offset_y, self.led_coordinates[i][2], self.led_coordinates[i][2])
