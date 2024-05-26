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
        
        self.axes_max = [100,100,100]
        self.axes_min = [0,0,0]
        self.stepper_pos = 0

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
            elif o == "query_adc":
                return self
            elif o == "buttons":
                return self
            elif o == "gcode_macro":
                return self
        return None
    def register_event_handler(self, event, callback):
        pass
    def register_mux_command(self, cmd, foo, name, command, desc):
        pass
    def register_command(self, cmd, callback, desc):
        pass
    def register_timer(self, callback, time):
        pass
    def register_buttons(self, pins, callback):
        pass
    def get_reactor(self):
        return self
    def register_timer(self, callback, time):
        pass
    def get_temp(self, time):
        return self.temp
    def get_kinematics(self):
        return self
    def set_stepper_pos(self, pos):
        self.led_effect.handler.stepperPositions=[pos,pos,pos]
    def setup_pin(self, name, pin):
        return self
    def setup_minmax(self, min, max):
        pass
    def setup_adc_callback(self, time, adcCallback):
        pass
    def register_adc(self, name, mcu):
        pass
    def lookup_heater(self, name):
        return self
    def set_heater(self, min, max, temp):
        self.led_effect.handler.heaterLast["bed"]  = self.led_effect.handler.heaterCurrent["bed"]
        self.led_effect.handler.heaterCurrent["bed"] = temp
        self.led_effect.handler.heaterTarget["bed"]  = max
    def set_progress (self, progress):
        self.led_effect.handler.printProgress=progress
    def set_analog(self, value):
        self.led_effect.analogValue=value
    def load_template(self, config, name):
        self.template = config.get(name)
        return self
    def render(self, context=None):
        return self.template
    def create_template_context(self):
        return {'printer': self}


class mockConfig:
    def __init__(self):
        self.config={
            "frame_rate" : "24.0",
            "autostart" : "False",
            "run_on_error" : "False",
            "recalculate": "False",
            "heater" : "bed",
            "analog_pin" : "PA0",
            "stepper" : "x",
            "layers"  : """gradient       1 1 top  (1, 0.0, 0.0),(0, 1, 0.0),(0.0, 0.0, 1)""",
            "leds" : "leds:leds",
            "endstops" : "x",
            "button_pins" : "PA0"
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
    def getlist(self,key,default):
        return list(self.config[key])
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

