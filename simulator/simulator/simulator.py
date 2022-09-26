from distutils.command.config import config
import sys
from pathlib import Path # if you haven't already done so
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[2]
print(root)
sys.path.append(str(root))
from pathlib import Path

import wx
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


class SimFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(SimFrame, self).__init__(*args, **kw)
        self.SetBackgroundColour("white")
        self.SetClientSize(500,500)
        panel = wx.Panel(self) 
        
        self.led_panel = LEDPanel(panel,-1)
        self.led_ctrl=wx.SpinCtrl(panel, -1, min=1, max=128, initial=20)
        self.led_ctrl.Bind(wx.EVT_SPINCTRL,self.OnLed_ctrl_changed) 

        self.layer_txt = wx.TextCtrl(panel, id=-1, value='gradient       1 1 top  (1.0, 0.0, 0.0),(0.0, 1.0, 0.0),(0.0, 0.0, 1.0)', pos=wx.DefaultPosition,
                            size=(700,100),
                            style= wx.TE_MULTILINE | wx.SUNKEN_BORDER|wx.TE_PROCESS_TAB)
        font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.NORMAL)
        self.layer_txt.SetFont(font)
        self.btnApply = wx.Button(panel,-1,"Apply")
        self.btnApply.Bind(wx.EVT_BUTTON,self.OnApplyClicked) 

        topSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer.Add(self.led_panel,0, wx.EXPAND|wx.ALL)
        topSizer.Add(self.led_ctrl,0,wx.ALL)
        topSizer.Add(self.layer_txt,1,wx.EXPAND|wx.ALL)
        topSizer.Add(self.btnApply,0,wx.ALL)

        panel.SetSizer(topSizer) 
        topSizer.Fit(self)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.timer.Start(1/24.0)

        self.config = mockConfig()
        self.config.setint("ledcount",self.led_ctrl.GetValue())
        
        self.init_printer()

    def init_printer(self):
        self.printer = mockPrinter(self.config)
        self.printer._handle_ready()
        self.printer.led_effect.set_enabled(True)

    def OnLed_ctrl_changed(self, event):
        self.config.setint("ledcount",self.led_ctrl.GetValue())
        self.init_printer()
    
    def OnApplyClicked(self, event):
        self.config.set("layers", self.layer_txt.GetValue())
        self.init_printer()


    def OnExit(self, event):
        self.Close(True)

    def update(self, event):
        ledframe, update = self.printer.led_effect.getFrame(time.monotonic())
        if update:
            led_count = self.printer.led_helper.get_led_count()
            self.led_panel.setLedCount( led_count )
            for led_index in range(led_count):
                self.led_panel.setLeds(led_index, 
                    int(255.0*ledframe[led_index * 3]),
                    int(255.0*ledframe[led_index * 3 + 1]),
                    int(255.0*ledframe[led_index * 3 + 2]))
    
class LEDPanel(wx.Panel):
    def __init__(self, parent, id):
        # create a panel
        wx.Panel.__init__(self, parent, id, size=(800,200))
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetBackgroundColour("black")
        self.led_count = 0
        self.leds = [wx.Colour("black")] * self.led_count

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        
    
    def on_size(self, event):
        event.Skip()
        self.Refresh()

    def setLedCount(self, count):
        self.led_count = count
        self.leds=[wx.Colour("black")] * self.led_count
        
    def setLeds(self,index, r,g,b):
        self.leds[index]=wx.Colour(r,g,b)
        self.Refresh()

    def OnPaint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.Clear()
        for i, led in enumerate(self.leds):
            dc.SetPen(wx.Pen(led, 1, wx.PENSTYLE_SOLID))
            dc.SetBrush(wx.Brush(led))
            dc.DrawCircle(30 + i*30,self.GetClientSize()[1]/2,15)

if __name__ == '__main__':
    app = wx.App(False)
    frame = SimFrame(None, wx.ID_ANY, "LED Effect Simulator")
    
    frame.Show(True)
    app.MainLoop()