from distutils.command.config import config
import sys

from pathlib import Path # if you haven't already done so
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[2]
print(root)
sys.path.append(str(root))
from pathlib import Path
from src.led_effect import ledEffect, ledFrameHandler

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

class mockLedHelper:
    def __init__(self,config):
        self.led_count = config.getint("ledcount", 1, 1, 1024)
    def get_led_count(self):
        return self.led_count

