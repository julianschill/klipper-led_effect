# Support for addressable LED visual effects
# using neopixel and dotstar LEDs
#
# Copyright (C) 2020  Paul McGowan <mental405@gmail.com>
# co-authored by Julian Schill <j.schill@web.de>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

from math import cos, exp, pi
from random import randint
import logging
from colormath.color_conversions import convert_color
from colormath.color_objects import (
    sRGBColor,
    LabColor,
    HSLColor
)
from . import layer_parser

ANALOG_SAMPLE_TIME  = 0.001
ANALOG_SAMPLE_COUNT = 5
ANALOG_REPORT_TIME  = 0.05

COLORS = 4

######################################################################
# Custom color value list, returns lists of [r, g ,b] values
# from a one dimensional list
######################################################################

class colorArray(list):
    def __init__(self, num_colors, kwargs):
        self.n=num_colors
        super(colorArray,self).__init__(kwargs)
        
    def __getitem__(self, a):
        if isinstance(a, int):
            return super(colorArray, self).__getitem__(
                            slice(a*self.n, a*self.n+self.n))
        if isinstance(a, slice):
                start = a.start*self.n if a.start != None else None
                stop = a.stop*self.n if a.stop != None else None
                return colorArray(self.n,
                        super(colorArray, self).__getitem__(
                            slice(start, stop, a.step)))
    def __getslice__(self, a, b):
        return self.__getitem__(slice(a,b))
    def __setitem__(self, a, v):
        if isinstance(a, int):
            for i in range(self.n):
                super(colorArray, self).__setitem__(a*self.n + i, v[i])
    def __len__(self):
        return super(colorArray, self).__len__() // self.n
    def reverse(self):
        self.__init__(self.n, [c for cl in range(len(self)-1,-1, -1)
                        for c in self[cl]])
    def shift(self, shift=1, direction=True):
        if direction:
            shift *= -1
        self.__init__(self.n, self[shift:] + self[:shift])
    def padLeft(self, v, a):
        self.__init__(self.n, v * a + self)
    def padRight(self, v, a):
        self += v * a

######################################################################
# LED Effect handler
######################################################################

class ledFrameHandler:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode   = self.printer.lookup_object('gcode')
        self.printer.load_object(config, "display_status")
        self.heaters = {}
        self.printProgress = 0
        self.effects = []
        self.stepperPositions = [0.0,0.0,0.0]
        self.stepperTimer     = None
        self.heaterCurrent   = {}
        self.heaterTarget    = {}
        self.heaterLast      = {}
        self.heaterTimer     = None
        self.homing          = {}
        self.homing_start_flag = {}
        self.homing_end_flag = {}
        self.printer.register_event_handler('klippy:ready', self._handle_ready)
        self.printer.register_event_handler("homing:homing_move_begin",
                                            self._handle_homing_move_begin)
        self.printer.register_event_handler("homing:homing_move_end",
                                            self._handle_homing_move_end)
        self.ledChains=[]
        self.gcode.register_command('STOP_LED_EFFECTS',
                                    self.cmd_STOP_LED_EFFECTS,
                                    desc=self.cmd_STOP_LED_EFFECTS_help)
        self.shutdown = False

    cmd_STOP_LED_EFFECTS_help = 'Stops all led_effects'

    def _handle_ready(self):
        self.shutdown = False
        self.reactor = self.printer.get_reactor()
        self.printer.register_event_handler('klippy:shutdown', 
                                            self._handle_shutdown)
        self.printProgress = 0
        self.displayStatus = self.printer.lookup_object('display_status')
        self.progressTimer = self.reactor.register_timer(self._pollProgress, 
                                                         self.reactor.NOW)
        self.frameTimer    = self.reactor.register_timer(self._getFrames, 
                                                         self.reactor.NOW)

    def _handle_shutdown(self):
        self.shutdown = True
        for effect in self.effects:
            if not effect.runOnShutown:
                for chain in self.ledChains:
                    chain.led_helper.set_color(None, (0.0, 0.0, 0.0, 0.0))
                    chain.led_helper.update_func(chain.led_helper.led_state, None)

        pass
    
    def _handle_homing_move_begin(self, hmove):
        endstops_being_homed = [name for es,name in hmove.endstops]
        logging.info(endstops_being_homed)

        for endstop in endstops_being_homed:
            if endstop in self.homing_start_flag: 
                self.homing_start_flag[endstop] += 1
            else:
                self.homing_start_flag[endstop] = 0
                
            self.homing[endstop]=True
        
    def _handle_homing_move_end(self, hmove):
        endstops_being_homed = [name for es,name in hmove.endstops]

        for endstop in endstops_being_homed:
            if endstop in self.homing_end_flag: 
                self.homing_end_flag[endstop] += 1
            else:
                self.homing_end_flag[endstop] = 0
            self.homing[endstop]=False

    def addEffect(self, effect):

        if effect.heater:
            effect.heater=effect.heater.strip('\"\'')
            if effect.heater.startswith("temperature_fan ") or effect.heater.startswith("temperature_sensor "):
                self.heaters[effect.heater] = self.printer.lookup_object(effect.heater)
            else:
                pheater = self.printer.lookup_object('heaters')
                self.heaters[effect.heater] = pheater.lookup_heater(effect.heater)
            self.heaterLast[effect.heater] = 100
            self.heaterCurrent[effect.heater] = 0
            self.heaterTarget[effect.heater]  = 0

            if not self.heaterTimer:
                self.heaterTimer = self.reactor.register_timer(self._pollHeater,
                                                               self.reactor.NOW)

        for layer in [layer for layer in effect.layers if "heater" in layer.__dict__]:
            heater=layer.heater
            if heater.startswith("temperature_fan ") or heater.startswith("temperature_sensor "):
                self.heaters[heater] = self.printer.lookup_object(heater)
            else:
                pheater = self.printer.lookup_object('heaters')
                self.heaters[heater] = pheater.lookup_heater(heater)
            self.heaterLast[heater] = 100
            self.heaterCurrent[heater] = 0
            self.heaterTarget[heater]  = 0

            if not self.heaterTimer:
                self.heaterTimer = self.reactor.register_timer(self._pollHeater,
                                                               self.reactor.NOW)

        if effect.stepper:
            self.toolhead = self.printer.lookup_object('toolhead')
            self.kin = self.toolhead.get_kinematics()

            if not self.stepperTimer:
                self.stepperTimer = self.reactor.register_timer(
                                                self._pollStepper,
                                                self.reactor.NOW)

        self.effects.append(effect)

    def _pollHeater(self, eventtime):
        for heater in self.heaters.keys():
            current, target = self.heaters[heater].get_temp(eventtime)
            self.heaterCurrent[heater] = current
            self.heaterTarget[heater]  = target
            if target > 0:
                self.heaterLast[heater] = target
        return eventtime + 0.3 #sensors get updated every 300ms

    def _pollStepper(self, eventtime):

        kin_spos = {s.get_name(): s.get_commanded_position()
                    for s in self.kin.get_steppers()}
       
        pos = self.kin.calc_position(kin_spos)
        
        for i in range(3):
            if pos[i] >= self.kin.axes_min[i] and pos[i] <= self.kin.axes_max[i]:
                self.stepperPositions[i] = int(
                    ((pos[i] - self.kin.axes_min[i]) / \
                     (self.kin.axes_max[i] - self.kin.axes_min[i])
                    * 100)- 1)
        return eventtime + 0.5

    def _pollProgress(self, eventtime):
        status = self.displayStatus.get_status(eventtime)
        p = status.get('progress')
        if p is not None:
            self.printProgress = int(p * 100)
        return eventtime + 1

    def _getColorData(self, colors, fade):
        clamp = (lambda x : 0.0 if x < 0.0 else 1.0 if x > 1.0 else x)
        colors = [x*clamp(fade) for x in colors]
        colors=colors + [0.0] * (4 - len(colors))
        colors=colors[:4]
        colors = [clamp(x) for x in colors]
        return tuple(colors)

    def _getFrames(self, eventtime):
        chainsToUpdate = set()

        frames = [(effect, effect.getFrame(eventtime)) for effect in self.effects]

        #first set all LEDs to 0, that should be updated
        for effect, (frame, update) in frames:
            if update:
                for i in range(effect.ledCount):
                    chain,index=effect.leds[i]
                    chain.led_helper.led_state[index] = (0.0, 0.0, 0.0, 0.0)
                    chainsToUpdate.add(chain)

        #then sum up all effects for that LEDs
        for effect, (frame, update) in frames:
            if update:
                for i in range(effect.ledCount):
                    chain,index=effect.leds[i]
                    
                    current_state=list(chain.led_helper.led_state[index])
                    effect_state=self._getColorData(frame[i*COLORS:i*COLORS+COLORS], 
                                                    effect.fadeValue)

                    next_state=[min(1.0,a+b) for a,b in \
                                 zip(current_state, effect_state)]

                    chain.led_helper.led_state[index] = tuple(next_state)
                    chainsToUpdate.add(chain)

        for chain in chainsToUpdate:
            if hasattr(chain,"prev_data"):
                chain.prev_data = None # workaround to force update of dotstars
            if not self.shutdown: 
                chain.led_helper.update_func(chain.led_helper.led_state, None)
        if self.effects:
            next_eventtime=min(self.effects, key=lambda x: x.nextEventTime)\
                            .nextEventTime
        else:
            next_eventtime = eventtime
        # run at least with 10Hz
        next_eventtime=min(next_eventtime, eventtime + 0.1) 
        return next_eventtime
    
    def parse_chain(self, chain):
        chain = chain.strip()
        leds=[]
        parms = [parameter.strip() for parameter in chain.split()
                    if parameter.strip()]
        if parms:
            chainName=parms[0].replace(':',' ')
            ledIndices   = ''.join(parms[1:]).strip('()').split(',')
            for led in ledIndices:
                if led:
                    if '-' in led:
                        start, stop = map(int,led.split('-'))
                        if stop == start:
                            ledList = [start-1]
                        elif stop > start:
                            ledList = list(range(start-1, stop))
                        else:
                            ledList = list(reversed(range(stop-1, start)))
                        for i in ledList:
                            leds.append(int(i))
                    else:
                        for i in led.split(','):
                            leds.append(int(i)-1)

            return chainName, leds
        else:
            return None, None

    def cmd_STOP_LED_EFFECTS(self, gcmd):
        ledParam = gcmd.get('LEDS', "")
        stopAll = (ledParam == "")

        for effect in self.effects:
            stopEffect = stopAll
            if not stopAll:
                try:
                    chainName, ledIndices = self.parse_chain(ledParam)
                    chain = self.printer.lookup_object(chainName)
                except Exception as e:
                    raise gcmd.error("Unknown LED '%s'" % (ledParam,))

                if ledIndices == [] and chain in effect.ledChains: 
                    stopEffect = True
                else:
                    for index in ledIndices:
                        if (chain,index) in effect.leds: 
                            stopEffect=True

            if stopEffect:
                if effect.enabled:
                    effect.set_fade_time(gcmd.get_float('FADETIME', 0.0))
                effect.set_enabled(False)

def load_config(config):
    return ledFrameHandler(config)

######################################################################
# LED Effect
######################################################################

class ledEffect:
    def __init__(self, config):
        self.config       = config
        self.printer      = config.get_printer()
        self.gcode        = self.printer.lookup_object('gcode')
        self.gcode_macro  = self.printer.lookup_object('gcode_macro')
        self.handler      = self.printer.load_object(config, 'led_effect')
        self.frameRate    = 1.0 / config.getfloat('frame_rate', 
                                        default=24, minval=1, maxval=60)
        self.enabled      = False
        self.iteration    = 0
        self.layers       = []
        self.analogValue  = 0
        self.fadeValue    = 1.0
        self.fadeTime     = 0.0
        self.fadeEndTime  = 0

        #Basic functions for layering colors. t=top and b=bottom color
        self.blendingModes  = {
            'top'       : (lambda t, b: t ),
            'bottom'    : (lambda t, b: b ),
            'add'       : (lambda t, b: t + b ),
            'subtract'  : (lambda t, b: (b - t) * (b - t > 0)),
            'subtract_b': (lambda t, b: (t - b) * (t - b > 0)),
            'difference': (lambda t, b: (t - b) * (t > b) + (b - t) * (t <= b)),
            'average'   : (lambda t, b: 0.5 * (t + b)),
            'multiply'  : (lambda t, b: t * b),
            'divide'    : (lambda t, b: t / b if b > 0 else 0 ),
            'divide_inv': (lambda t, b: b / t if t > 0 else 0 ),
            'screen'    : (lambda t, b: 1.0 - (1.0-t)*(1.0-b) ),
            'lighten'   : (lambda t, b: t * (t > b) +  b * (t <= b)),
            'darken'    : (lambda t, b: t * (t < b) +  b * (t >= b)),
            'overlay'   : (lambda t, b: \
                                2.0 * t * b if t > 0.5 else \
                                1.0 - (2.0 * (1.0-t) * (1.0-b)))
           }

        self.name         = config.get_name().split()[1]

        self.autoStart    = config.getboolean('autostart', False)
        self.runOnShutown = config.getboolean('run_on_error', False)
        self.heater       = config.get('heater', None)
        self.analogPin    = config.get('analog_pin', None)
        self.stepper      = config.get('stepper', None)
        self.recalculate  = config.get('recalculate', False)
        self.endstops     = [x.strip() for x in config.get('endstops','').split(',')]
        self.layerTempl   = self.gcode_macro.load_template(config, 'layers')
        self.configLayers = []
        self.configLeds   = config.get('leds')

        self.nextEventTime = 0
        self.printer.register_event_handler('klippy:ready', self._handle_ready)
        self.gcode.register_mux_command('SET_LED_EFFECT', 'EFFECT', self.name,
                                         self.cmd_SET_LED_EFFECT,
                                         desc=self.cmd_SET_LED_help)

        if self.analogPin:
            ppins = self.printer.lookup_object('pins')
            self.mcu_adc = ppins.setup_pin('adc', self.analogPin)
            self.mcu_adc.setup_minmax(ANALOG_SAMPLE_TIME, ANALOG_SAMPLE_COUNT)
            self.mcu_adc.setup_adc_callback(ANALOG_REPORT_TIME, self.adcCallback)
            query_adc = self.printer.load_object(self.config, 'query_adc')
            query_adc.register_adc(self.name, self.mcu_adc)

    cmd_SET_LED_help = 'Starts or Stops the specified led_effect'

    def _handle_ready(self):
        self.configChains = self.configLeds.split('\n')
        self.ledChains    = []
        self.leds         = []
        self.enabled = self.autoStart
        self.printer.register_event_handler('klippy:shutdown', 
                                    self._handle_shutdown)
        #map each LED from the chains to the "pixels" in the effect frame
        for chain in self.configChains:
            chainName, ledIndices = self.handler.parse_chain(chain)
            if chainName is not None:
                ledChain = self.printer.lookup_object(chainName)

                #Add each discrete chain to the collection
                if ledChain not in self.ledChains:
                    self.ledChains.append(ledChain)

                if ledIndices == [] :
                    for i in range(ledChain.led_helper.get_led_count()):
                        self.leds.append((ledChain, int(i)))
                else:
                    for led in ledIndices:
                        self.leds.append((ledChain, led))

        self.ledCount = len(self.leds)
        self.frame = [0.0] * COLORS * self.ledCount

        #enumerate all effects from the subclasses of _layerBase...
        self.availableLayers = {str(c).rpartition('.layer')[2]\
                                 .replace("'>", "")\
                                 .lower() : c
                                   for c in self._layerBase.__subclasses__()
                                   if str(c).startswith("<class")}
        self._generateLayers()

    def _generateLayers(self, context=None):
        self.layers = []
        if context is None:
            context = self.gcode_macro.create_template_context()
            context.update({'params': {}, 'rawparams': ''})
        self.configLayers = self.layerTempl.render(context)
        for layer in [line for line \
            in self.configLayers.split('\n') if line.strip()]:

            parms = [parameter.strip() for parameter \
                in layer.split() if parameter.strip()]

            parsed_layer = layer_parser.parse(layer)
            if parsed_layer is None:
                raise self.printer.config_error("Error parsing layer: %s" % (layer,))
            
            effect = parsed_layer["effect"]
            parameters = parsed_layer["parameters"]
            blend = parsed_layer["blend"]
            palette = parsed_layer["palette"]

            if not effect in self.availableLayers:
                raise self.printer\
                    .config_error("LED Effect '%s' in section '%s' is not a " \
                        "valid effect layer" % (effect, self.name))

            if not blend in self.blendingModes:
                raise self.printer.config_error("Blending mode '%s' in section "
                     "'%s' is not a valid blending mode"\
                         % (parms[3], self.name))

            layer = self.availableLayers[effect]
            pad = lambda x: list(x) + [0.0] * (COLORS - len(x))
                
            try:
                for i in palette: 
                    if len(i) > COLORS: 
                        raise Exception(
                            "Color %s has too many elements." % (str(i),))
                palette=[pad(c) for c in palette]                               # pad to COLORS colors
                palette=[k for c in palette for k in c]                         # flatten list
            except Exception as e:
                raise self.printer.config_error(
                    "Error parsing palette in '%s' for layer \"%s\": %s"\
                        % (self.config.get_name(), effect, e,))
            self.layers.insert(0, layer(handler       = self,
                                        frameHandler  = self.handler,
                                        paletteColors = palette,
                                        frameRate     = self.frameRate,
                                        ledCount      = len(self.leds),
                                        blendingMode  = blend,
                                        **parameters))

        self.handler.addEffect(self)

    def getFrame(self, eventtime):
        if not self.enabled and self.fadeValue <= 0.0:
            if self.nextEventTime < self.handler.reactor.NEVER:
                # Effect has just been disabled. Set colors to 0 and update once.
                self.nextEventTime = self.handler.reactor.NEVER
                self.frame = [0.0] * COLORS * self.ledCount
                update = True
            else:
                update = False
        else:
            update = True
            if eventtime >= self.nextEventTime:
                self.nextEventTime = eventtime + self.frameRate

                self.frame = [0.0] * COLORS * self.ledCount
                for layer in self.layers:
                    layerFrame = layer.nextFrame(eventtime)

                    if layerFrame:
                        blend = self.blendingModes[layer.blendingMode]
                        self.frame = [blend(t, b) for t, b in zip(layerFrame, self.frame)]

                if (self.fadeEndTime > eventtime) and (self.fadeTime > 0.0):
                    remainingFade = ((self.fadeEndTime - eventtime) / self.fadeTime)
                else:
                    remainingFade = 0.0    

                self.fadeValue = 1.0-remainingFade if self.enabled else remainingFade

        return self.frame, update

    def set_enabled(self, state):
        if self.enabled != state:
            self.enabled = state
            self.nextEventTime = self.handler.reactor.NOW
            self.handler._getFrames(self.handler.reactor.NOW)
    
    def reset_frame(self):
        for layer in self.layers:
            layer.frameNumber = 0

    def set_fade_time(self, fadetime):
        self.fadeTime = fadetime
        self.fadeEndTime = self.handler.reactor.monotonic() + fadetime
        if self.fadeTime == 0.0:
            self.fadeValue = 0.0

    def cmd_SET_LED_EFFECT(self, gcmd):
        parmFadeTime = gcmd.get_float('FADETIME', 0.0)

        if gcmd.get_int('STOP', 0) >= 1:
            if self.enabled:
                self.set_fade_time(parmFadeTime)
            self.set_enabled(False)
        else:
            if self.recalculate:
                kwargs = self.layerTempl.create_template_context()
                kwargs['params'] = gcmd.get_command_parameters()
                kwargs['rawparams'] = gcmd.get_raw_command_parameters()
                self._generateLayers(kwargs)
            if gcmd.get_int('REPLACE',0) >= 1:
                for led in self.leds:
                    for effect in self.handler.effects:
                        if effect is not self and led in effect.leds:
                            if effect.enabled:
                                effect.set_fade_time(parmFadeTime)
                            effect.set_enabled(False)

            if not self.enabled:
                self.set_fade_time(parmFadeTime)
            if gcmd.get_int('RESTART', 0) >= 1:
                self.reset_frame()
            self.set_enabled(True)

    def _handle_shutdown(self):
        self.set_enabled(self.runOnShutown)

    def adcCallback(self, read_time, read_value):
        self.analogValue = int(read_value * 1000.0) / 10.0

    ######################################################################
    # LED Effect layers
    ######################################################################

    # super class for effect animations. new animations should
    # inherit this and return 1 frame of [r, g, b] * <number of leds>
    # per call of nextFrame()
    class _layerBase(object):
        def __init__(self, **kwargs):
            self.handler         = kwargs['handler']
            self.frameHandler    = kwargs['frameHandler']
            self.ledCount        = kwargs['ledCount']
            self.paletteColors   = colorArray(COLORS, kwargs['paletteColors'])
            self.frameRate       = kwargs['frameRate']
            self.blendingMode    = kwargs['blendingMode']
            self.colorSpace      = kwargs['colorSpace'] if 'colorSpace' in kwargs else 'rgb'
            self.frameNumber     = 0
            self.thisFrame       = []
            self.frameCount      = 1
            self.lastAnalog      = 0

        def nextFrame(self, eventtime):
            if not self.frameCount:
                return [0] * COLORS * self.ledCount
            self.frameNumber += 1
            self.frameNumber = self.frameNumber * \
                ( self.frameNumber < self.frameCount )
            self.lastFrameTime = eventtime

            return self.thisFrame[self.frameNumber]

        def _decayTable(self, factor=1, rate=1):

            frame = []

            p = (1.0 / self.frameRate)
            r = (p/15.0)*factor

            for s in range(0, int((rate<1)+rate)):
                frame.append(1.0)
                for x in range(2, int(p / rate)):
                    b = exp(1)**-(x/r)
                    if b>.004:
                        frame.append(b)
            return frame

        def _mixColorInColorSpace(self, color1, color2, r, colorSpace):
            if colorSpace == "none":
                return color1 if r <= 0.5 else color2
            
            a = color1[3]*(1-r) + color2[3]*r
            c1 = sRGBColor(color1[0], color1[1], color1[2])
            c2 = sRGBColor(color2[0], color2[1], color2[2])

            if colorSpace == 'hsl':
                c1 = convert_color(c1, HSLColor).get_value_tuple()
                c2 = convert_color(c2, HSLColor).get_value_tuple()
                mix = [((1-r)*c1[m] + r*c2[m]) for m in range(3)]
                mix = HSLColor(mix[0], mix[1], mix[2])
                mix = convert_color(mix, sRGBColor).get_value_tuple()
                return [mix[0], mix[1], mix[2], a]

            if colorSpace == 'lab':
                c1 = convert_color(c1, LabColor).get_value_tuple()
                c2 = convert_color(c2, LabColor).get_value_tuple()
                mix = [((1-r)*c1[m] + r*c2[m]) for m in range(3)]
                mix = LabColor(mix[0], mix[1], mix[2])
                mix = convert_color(mix, sRGBColor).get_value_tuple()
                return [mix[0], mix[1], mix[2], a]


            return [((1-r)*color1[m] + r*color2[m]) for m in range(4)]

        def _gradient(self, palette, steps, reverse=False, toFirst=False):
            palette = colorArray(COLORS, palette[:])
            if reverse: palette.reverse()

            if len(palette) == 1:
                return colorArray(COLORS, palette * steps)

            if toFirst:
                palette += palette[0]

            paletteIntervals = len(palette)-1
            stepIntervals = steps if toFirst else steps-1
            if stepIntervals != 0:
                intervals_per_step = float(paletteIntervals) / stepIntervals
            else:
                intervals_per_step = 0

            gradient=palette[0]

            for i in range(1,steps):
                j = intervals_per_step * i
                k = int(j) 
                r = j-k
                k = min(k, len(palette)-1)

                if ( (k+1) >= len(palette) ) | (r == 0.0) :
                    z = palette[k]
                else:
                    z = self._mixColorInColorSpace(palette[k], palette[k+1], r, self.colorSpace)
                gradient += z
            return gradient

    #Individual effects inherit from the LED Effect Base class
    #each effect must support the nextFrame() method either by
    #using the method from the base class or overriding it.

    #Solid color
    class layerStatic(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerStatic, self).__init__(**kwargs)

            self.paletteColors = colorArray(COLORS, self.paletteColors)

            gradientLength = int(self.ledCount)
            gradient = colorArray(COLORS, self._gradient(self.paletteColors, 
                                                gradientLength))

            self.thisFrame.append(gradient[0:self.ledCount])
            self.frameCount = len(self.thisFrame)

    #Slow pulsing of color
    class layerBreathing(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerBreathing, self).__init__(**kwargs)
            self.duration = kwargs["duration"] if "duration" in kwargs else kwargs["effectRate"]

            brightness = []

            p = (1 / self.frameRate) * (self.duration * 0.5)
            o = int(p)
            f = 2 * pi

            for x in range(0, int(p)):
                if x < p:
                    v  = (exp(-cos((f / p) * (x+o)))-0.367879) / 2.35040238
                else:
                    v = 0

                #clamp values
                if v > 1.0:
                    v = 1.0
                elif v < 0.0:
                    v = 0.0

                brightness.append(v)

            for c in range(0, len(self.paletteColors)):
                color = self.paletteColors[c]

                for b in brightness:
                    self.thisFrame += [[b * i for i in color] * self.ledCount]

            self.frameCount = len(self.thisFrame)
    class layerLinearFade(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerLinearFade, self).__init__(**kwargs)
            self.duration = kwargs["duration"] if "duration" in kwargs else kwargs["effectRate"]

            gradientLength = int(self.duration / self.frameRate) 
            if gradientLength == 0: gradientLength = 1

            gradient   = colorArray(COLORS, self._gradient(self.paletteColors, 
                                                   gradientLength, toFirst=True))

            for i in range(gradientLength):
                self.thisFrame.append(gradient[i]*self.ledCount)

            self.frameCount = len(self.thisFrame)

    #Turns the entire strip on and off
    class layerBlink(_layerBase):
        def __init__(self, **kwargs):
            super(ledEffect.layerBlink, self).__init__(**kwargs)
            self.duration = kwargs["duration"] if "duration" in kwargs else kwargs["effectRate"]
            self.onRatio = kwargs["onRatio"] if "onRatio" in kwargs else kwargs["effectCutoff"]

            dutyCycle= max(0,min(1.0, self.onRatio))
            frameCountOn = int(( 1.0 / self.frameRate ) * self.duration\
                 * dutyCycle)
            frameCountOff = int(( 1.0 / self.frameRate ) * self.duration\
                 * (1-dutyCycle))

            for c in range(0, len(self.paletteColors)):
                color = self.paletteColors[c]
                self.thisFrame += [color * self.ledCount] * frameCountOn
                self.thisFrame += [[0]*COLORS * self.ledCount] * frameCountOff

            self.frameCount = len(self.thisFrame)

    #Random flashes with decay
    class layerTwinkle(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerTwinkle, self).__init__(**kwargs)
            self.probability = kwargs["probability"] if "probability" in kwargs else kwargs["effectRate"]
            self.decayRate = kwargs["decayRate"] if "decayRate" in kwargs else kwargs["effectCutoff"]

            self.thisFrame = colorArray(COLORS, ([0.0]*COLORS) * self.ledCount)
            self.lastBrightness  = [-1] * self.ledCount
            self.decayTable = self._decayTable(factor=1 / self.decayRate)
            self.decayLen = len(self.decayTable)
            self.colorCount = len(self.paletteColors) - 1

        def nextFrame(self, eventtime):

            for i in range(0, self.ledCount):

                r = randint(0, self.colorCount)
                color = self.paletteColors[r]

                if randint(0, 255) > 254 - self.probability * 255:
                    self.lastBrightness[i] = 0
                    self.thisFrame[i] = color

                if self.lastBrightness[i] != -1:
                    if self.lastBrightness[i] == self.decayLen:
                        self.lastBrightness[i] = -1
                        self.thisFrame[i] = ([0.0]*COLORS)
                    else:
                        x = self.lastBrightness[i]
                        self.lastBrightness[i] += 1
                        self.thisFrame[i] = [self.decayTable[x] * l
                                                for l in self.thisFrame[i]]

            return self.thisFrame

    #Blinking with decay
    class layerStrobe(_layerBase):
        def __init__(self, **kwargs):
            super(ledEffect.layerStrobe, self).__init__(**kwargs)
            self.frequency = kwargs["frequency"] if "frequency" in kwargs else kwargs["effectRate"]
            self.decayRate = kwargs["decayRate"] if "decayRate" in kwargs else kwargs["effectCutoff"]

            frameRate  = int(1.0 / self.frameRate)
            if self.frequency==0: 
                frameCount = 1
            else:
                frameCount = max(1,int(frameRate / self.frequency))
            if self.decayRate==0: self.decayRate=0.001
            decayTable = self._decayTable(factor=1 / self.decayRate,
                                          rate=1)
            if len(decayTable) > frameCount:
                decayTable = decayTable[:frameCount]
            else:
                decayTable += [0.0] * (frameCount - len(decayTable))

            for c in range(0, len(self.paletteColors)):
                color = self.paletteColors[c]

                for b in decayTable:
                    self.thisFrame += [[b * i for i in color] * self.ledCount]

            self.frameCount = len(self.thisFrame)

    #Lights move sequentially with decay
    class layerComet(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerComet, self).__init__(**kwargs)
            self.speed = kwargs["speed"] if "speed" in kwargs else kwargs["effectRate"]
            self.tailLength = kwargs["tailLength"] if "tailLength" in kwargs else kwargs["effectCutoff"]
            if self.speed > 0:
                self.direction = True
            else:
                self.direction = False
                self.speed *= -1

            if self.tailLength <= 0: self.tailLength = .1

            decayTable = self._decayTable(factor=len(self.paletteColors) * \
                                            self.tailLength, rate=1)

            gradient   = self.paletteColors[0] + \
                self._gradient(self.paletteColors[1:], len(decayTable)+1)

            decayTable = [c for b in zip(decayTable, decayTable, decayTable, decayTable) \
                for c in b]

            comet = colorArray(COLORS, [a * b for a, b in zip(gradient,decayTable)])

            comet.padRight([0.0]*COLORS, self.ledCount - len(comet))

            if self.direction: comet.reverse()
            else: comet.shift(self.ledCount - len(comet))

            if self.speed == 0:
                self.thisFrame.append(comet[0:self.ledCount])
            else:                           
                for i in range(len(comet)):
                    comet.shift(int(self.speed+(self.speed < 1)), 
                                self.direction)
                    self.thisFrame.append(comet[:self.ledCount])

                    for x in range(int((1/self.speed)-(self.speed <= 1))):
                        self.thisFrame.append(comet[:self.ledCount])

            self.frameCount = len(self.thisFrame)

    #Lights move sequentially with decay
    class layerChase(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerChase, self).__init__(**kwargs)
            self.speed = kwargs["speed"] if "speed" in kwargs else kwargs["effectRate"]
            self.tailLength = kwargs["tailLength"] if "tailLength" in kwargs else kwargs["effectCutoff"]
            
            if self.speed > 0:
                self.direction = True
            else:
                self.direction = False
                self.speed *= -1

            if len(self.paletteColors) == 1:
                self.paletteColors += colorArray(COLORS,COLORS*[0])

            decayTable = self._decayTable(factor=len(self.paletteColors) * \
                            self.tailLength, rate=1)

            gradient   = self.paletteColors[0] + \
                self._gradient(self.paletteColors[1:], len(decayTable)+1)

            decayTable = [c for b in zip(decayTable, decayTable, decayTable, decayTable) \
                for c in b]
            gradient  = colorArray(COLORS, [a * b
                            for a, b in zip(gradient,decayTable)])

            k=int(self.ledCount/len(gradient))+1
            chase = colorArray(COLORS,k*gradient)

            if self.direction: chase.reverse()
            if self.speed == 0:
                self.thisFrame.append(chase[0:self.ledCount])
            else:                                                   
                for _ in range(len(chase)):
                    chase.shift(int(self.speed+(self.speed < 1)), 
                                self.direction)
                    self.thisFrame.append(chase[0:self.ledCount])

                    for _ in range(int((1/self.speed)-(self.speed <= 1))):
                        self.thisFrame.append(chase[0:self.ledCount])

            self.frameCount = len(self.thisFrame)

    #Color gradient over all LEDs
    class layerGradient(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerGradient, self).__init__(**kwargs)
            self.speed = kwargs["speed"] if "speed" in kwargs else kwargs["effectRate"]
            self.count = kwargs["count"] if "count" in kwargs else kwargs["effectCutoff"]

            direction = -1 if self.speed < 0 else 1

            if self.speed == 0: 
                gradientLength = self.ledCount
            else:
                gradientLength=abs(int(1/(self.speed * self.frameRate)))
            gradient = colorArray(COLORS, self._gradient(self.paletteColors, 
                                                  gradientLength,
                                                  toFirst=True))

            for i in range(gradientLength if self.speed != 0 else 1):
                frame = colorArray(COLORS, ([0.0]*COLORS) * self.ledCount)
                for led in range(self.ledCount):
                    frame[led] = gradient[ int(i*direction + \
                        self.count * gradientLength * led \
                        / self.ledCount ) % gradientLength]
                self.thisFrame.append(frame)

            self.frameCount = len(self.thisFrame)

    class layerPattern(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerPattern, self).__init__(**kwargs)
            self.duration = kwargs["duration"] if "duration" in kwargs else kwargs["effectRate"]
            self.shift = kwargs["shift"] if "shift" in kwargs else kwargs["effectCutoff"]

            self.paletteColors = colorArray(COLORS, self.paletteColors)
            frame = colorArray(COLORS, [])

            for i in range(int(self.ledCount/len(self.paletteColors))+1):
                frame+=(self.paletteColors)

            if int(self.duration/self.frameRate) == 0:
                self.thisFrame.append(frame)
            else:
                for _ in range(len(self.paletteColors) * (self.ledCount-1)):
                    for _ in range(int(self.duration/self.frameRate)):
                        self.thisFrame.append(colorArray(COLORS, frame)[:COLORS*self.ledCount])
                    frame.shift(int(self.shift))
                
            self.frameCount = len(self.thisFrame)
            
    #Responds to heater temperature
    class layerHeater(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerHeater, self).__init__(**kwargs)
            self.minTemp = kwargs["minTemp"] if "minTemp" in kwargs else kwargs["effectRate"]
            self.disableOnceReached = kwargs["disableOnceReached"] if "disableOnceReached" in kwargs else kwargs["effectCutoff"]
            self.heater = kwargs["heater"] if "heater" in kwargs else self.handler.heater
            self.gradientSteps = int(kwargs["gradientSteps"]) if "gradientSteps" in kwargs else 200

            if len(self.paletteColors) == 1:
                self.paletteColors += self.paletteColors

            gradient = colorArray(COLORS, self._gradient(self.paletteColors[:-1], self.gradientSteps) +
                                    self.paletteColors[-1:])

            for i in range(len(gradient)):
                self.thisFrame.append(gradient[i] * self.ledCount)

            self.frameCount = len(self.thisFrame)

        def nextFrame(self, eventtime):
            heaterTarget  = self.frameHandler.heaterTarget[self.heater]
            heaterCurrent = self.frameHandler.heaterCurrent[self.heater]
            heaterLast    = self.frameHandler.heaterLast[self.heater]

            if heaterTarget > 0.0 and heaterCurrent > 0.0:
                if (heaterCurrent >= self.minTemp):
                    if (heaterCurrent <= heaterTarget-2):
                        s = int(((heaterCurrent - self.minTemp) / heaterTarget) * self.gradientSteps)
                        s = min(len(self.thisFrame)-1,s)
                        return self.thisFrame[s]
                    elif self.disableOnceReached > 0:
                        return None
                    else:
                        return self.thisFrame[-1]
                else:
                    return None

            elif self.minTemp > 0 and heaterCurrent > 0.0:
                if heaterCurrent >= self.minTemp and heaterLast > 0:
                    s = int(((heaterCurrent - self.minTemp) / heaterLast) * self.gradientSteps)
                    s = min(len(self.thisFrame)-1,s)
                    return self.thisFrame[s]

            return None

    #Responds to heater temperature
    class layerTemperature(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerTemperature, self).__init__(**kwargs)
            self.minTemp = kwargs["minTemp"] if "minTemp" in kwargs else kwargs["effectRate"]
            self.maxTemp = kwargs["maxTemp"] if "maxTemp" in kwargs else kwargs["effectCutoff"]

            if len(self.paletteColors) == 1:
                self.paletteColors = colorArray(COLORS, ([0.0]*COLORS)) + self.paletteColors
            gradient = colorArray(COLORS, self._gradient(self.paletteColors, 200))
            for i in range(len(gradient)):
                self.thisFrame.append(gradient[i] * self.ledCount)
            self.frameCount = len(self.thisFrame)
        def nextFrame(self, eventtime):
            if self.maxTemp == self.minTemp:
                s = 200 if self.frameHandler.heaterCurrent[self.handler.heater] >= self.minTemp else 0
            else:
                s = int(((self.frameHandler.heaterCurrent[self.handler.heater] - 
                            self.minTemp) / 
                            (self.maxTemp - self.minTemp)) * 200)
                
            s = min(len(self.thisFrame)-1,s)
            s = max(0,s)
            return self.thisFrame[s]
            
    #Responds to analog pin voltage
    class layerAnalogPin(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerAnalogPin, self).__init__(**kwargs)
            self.multiplier = kwargs["multiplier"] if "multiplier" in kwargs else kwargs["effectRate"]
            self.threshold = kwargs["threshold"] if "threshold" in kwargs else kwargs["effectCutoff"]

            if len(self.paletteColors) == 1:
                self.paletteColors = [0.0]*COLORS + self.paletteColors

            gradient   = colorArray(COLORS, self._gradient(self.paletteColors, 101))

            for i in range(len(gradient)):
                self.thisFrame.append(gradient[i] * self.ledCount)

        def nextFrame(self, eventtime):
            v = int(self.handler.analogValue * self.multiplier)

            if v > 100: v = 100

            if v > self.threshold:
                return self.thisFrame[v]
            else:
                return self.thisFrame[0]

    #Lights illuminate relative to stepper position
    class layerStepper(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerStepper, self).__init__(**kwargs)
            self.trailingLedCount = kwargs["trailingLedCount"] if "trailingLedCount" in kwargs else kwargs["effectRate"]
            self.leadingLedCount = kwargs["leadingLedCount"] if "leadingLedCount" in kwargs else kwargs["effectCutoff"]

            if self.trailingLedCount < 0:
                self.trailingLedCount = self.ledCount

            if self.leadingLedCount < 0:
                self.leadingLedCount = self.ledCount

            if self.trailingLedCount == 0:
                trailing = colorArray(COLORS, [0.0]*COLORS * self.ledCount)
            else:
                trailing = colorArray(COLORS, self._gradient(self.paletteColors[1:],
                                                     int(self.trailingLedCount), True))
                trailing.padLeft([0.0]*COLORS, self.ledCount)

            if self.leadingLedCount == 0:
                leading = colorArray(COLORS, [0.0]*COLORS * self.ledCount)
            else:
                leading = colorArray(COLORS, self._gradient(self.paletteColors[1:],
                                                    int(self.leadingLedCount), False))
                leading.padRight([0.0]*COLORS, self.ledCount)

            gradient = colorArray(COLORS, trailing + self.paletteColors[0] + leading)
            gradient.shift(len(trailing)-1, 0)
            frames = [gradient[:self.ledCount]]

            for i in range(0, self.ledCount):
                gradient.shift(1,1)
                frames.append(gradient[:self.ledCount])

            for i in range(101):
                x = int((i / 101.0) * self.ledCount)
                self.thisFrame.append(frames[x])

            self.frameCount = len(self.thisFrame)

        def nextFrame(self, eventtime):
            if self.handler.stepper == 'x': axis = 0
            elif self.handler.stepper == 'y': axis = 1
            else: axis = 2

            p = self.frameHandler.stepperPositions[int(axis)]

            if p < 0 : p=0
            if p > 100 : p=100
            return self.thisFrame[int((p - 1) * (p > 0))]

    class layerStepperColor(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerStepperColor, self).__init__(**kwargs)
            self.positionScaling = kwargs["positionScaling"] if "positionScaling" in kwargs else kwargs["effectRate"]
            self.positionOffset = kwargs["positionOffset"] if "positionOffset" in kwargs else kwargs["effectCutoff"]

            if len(self.paletteColors) == 1:
                self.paletteColors = [0.0]*COLORS + self.paletteColors

            gradient   = colorArray(COLORS, self._gradient(self.paletteColors, 101))

            for i in range(len(gradient)):
                self.thisFrame.append(gradient[i] * self.ledCount)

        def nextFrame(self, eventtime):
            if self.handler.stepper == 'x': axis = 0
            elif self.handler.stepper == 'y': axis = 1
            else: axis = 2

            p = self.frameHandler.stepperPositions[int(axis)]*self.positionScaling+self.positionOffset
                        
            if p < 0 : p=0
            if p > 100 : p=100

            return self.thisFrame[int(p)]

    #Shameless port of Fire2012 by Mark Kriegsman

    #Shamelessly appropriated from the Arduino FastLED example files
    #Fire2012.ino by Daniel Garcia
    class layerFire(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerFire, self).__init__(**kwargs)
            self.sparkProbability = kwargs["sparkProbability"] if "sparkProbability" in kwargs else kwargs["effectRate"]
            self.coolingRate = kwargs["coolingRate"] if "coolingRate" in kwargs else kwargs["effectCutoff"]

            self.heatMap    = [0.0] * self.ledCount
            self.gradient   = colorArray(COLORS, self._gradient(self.paletteColors, 
                                                                        102))
            self.frameLen   = len(self.gradient)
            self.heatLen    = len(self.heatMap)
            self.heatSource = int(self.ledCount / 10.0)
            self.sparkProbability = int(self.sparkProbability)

            if self.heatSource < 1:
                self.heatSource = 1

        def nextFrame(self, eventtime):
            frame = []

            for h in range(self.heatLen):
                c = randint(0,self.coolingRate)
                self.heatMap[h] -= (self.heatMap[h] - c >= 0 ) * c

            for i in range(self.ledCount - 1, self.heatSource, -1):
                d = (self.heatMap[i - 1] +
                     self.heatMap[i - 2] +
                     self.heatMap[i - 3] ) / 3

                self.heatMap[i] = d * (d >= 0)

            if randint(0, 100) < self.sparkProbability:
                h = randint(0, self.heatSource)
                self.heatMap[h] += randint(90,100)
                if self.heatMap[h] > 100:
                    self.heatMap[h] = 100

            for h in self.heatMap:
                frame += self.gradient[int(h)]

            return frame

    #Fire that responds relative to actual vs target temp
    class layerHeaterFire(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerHeaterFire, self).__init__(**kwargs)
            self.minTemp = kwargs["minTemp"] if "minTemp" in kwargs else kwargs["effectRate"]
            self.disableOnceReached = kwargs["disableOnceReached"] if "disableOnceReached" in kwargs else kwargs["effectCutoff"]
            self.heater = kwargs["heater"] if "heater" in kwargs else self.handler.heater

            self.heatMap    = [0.0] * self.ledCount
            self.gradient   = colorArray(COLORS, self._gradient(self.paletteColors, 
                                                                        102))
            self.frameLen   = len(self.gradient)
            self.heatLen    = len(self.heatMap)
            self.heatSource = int(self.ledCount / 10.0)
            # Bug?
            self.minTemp = 0

            if self.heatSource < 1:
                self.heatSource = 1

        def nextFrame(self, eventtime):
            frame = []
            spark = 0
            heaterTarget  = self.frameHandler.heaterTarget[self.heater]
            heaterCurrent = self.frameHandler.heaterCurrent[self.heater]
            heaterLast    = self.frameHandler.heaterLast[self.heater]

            if heaterTarget > 0.0 and heaterCurrent > 0.0:
                if heaterCurrent <= heaterTarget-2:
                    spark = int((heaterCurrent / heaterTarget) * 80)
                    brightness = int((heaterCurrent / heaterTarget) * 100)
                elif self.disableOnceReached > 0:
                    spark = 0
                else:
                    spark = 80
                    brightness = 100
            elif self.minTemp > 0 and heaterCurrent > 0.0:
                if heaterCurrent >= self.minTemp:
                    spark = int(((heaterCurrent - self.minTemp)
                                      / heaterLast) * 80)
                    brightness = int(((heaterCurrent - self.minTemp)
                                      / heaterLast) * 100)

            if spark > 0:
                cooling = int((heaterCurrent / heaterTarget) * 20)

                for h in range(self.heatLen):
                    c = randint(0, cooling)
                    self.heatMap[h] -= (self.heatMap[h] - c >= 0 ) * c

                for i in range(self.ledCount - 1, self.heatSource, -1):
                    d = (self.heatMap[i - 1] +
                         self.heatMap[i - 2] +
                         self.heatMap[i - 3] ) / 3

                    self.heatMap[i] = d * (d >= 0)

                if randint(0, 100) < spark:
                    h = randint(0, self.heatSource)
                    self.heatMap[h] += brightness
                    if self.heatMap[h] > 100:
                        self.heatMap[h] = 100

                for h in self.heatMap:
                    frame += self.gradient[int(h)]

                return frame

            else:
                return None

    #Progress bar using M73 gcode command
    class layerProgress(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerProgress, self).__init__(**kwargs)
            self.trailingLedCount = kwargs["trailingLedCount"] if "trailingLedCount" in kwargs else kwargs["effectRate"]
            self.leadingLedCount = kwargs["leadingLedCount"] if "leadingLedCount" in kwargs else kwargs["effectCutoff"]

            if self.trailingLedCount < 0:
                self.trailingLedCount = self.ledCount

            if self.leadingLedCount < 0:
                self.leadingLedCount = self.ledCount

            if self.trailingLedCount == 0:
                trailing = colorArray(COLORS, [0.0]*COLORS * self.ledCount)
            else:
                trailing = colorArray(COLORS, self._gradient(self.paletteColors[1:],
                                                     int(self.trailingLedCount), True))
                trailing.padLeft([0.0]*COLORS, self.ledCount)

            if self.leadingLedCount == 0:
                leading = colorArray(COLORS, [0.0]*COLORS * self.ledCount)
            else:
                leading = colorArray(COLORS, self._gradient(self.paletteColors[1:],
                                                    int(self.leadingLedCount), False))
                leading.padRight([0.0]*COLORS, self.ledCount)

            gradient = colorArray(COLORS, trailing + self.paletteColors[0] + leading)
            gradient.shift(len(trailing), 0)
            frames = [gradient[:self.ledCount]]

            for i in range(0, self.ledCount):
                gradient.shift(1,1)
                frames.append(gradient[:self.ledCount])

            self.thisFrame.append(colorArray(COLORS, [0.0]*COLORS * self.ledCount))
            for i in range(1, 101):
                x = int((i / 101.0) * self.ledCount)
                self.thisFrame.append(frames[x])

            self.frameCount = len(self.thisFrame)

        def nextFrame(self, eventtime):
            p = self.frameHandler.printProgress
            return self.thisFrame[p] #(p - 1) * (p > 0)]

    class layerHoming(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerHoming, self).__init__(**kwargs)
            self.decayRate = kwargs["decayRate"] if "decayRate" in kwargs else kwargs["effectRate"]

            self.paletteColors = colorArray(COLORS, self.paletteColors)

            gradientLength = int(self.ledCount)
            gradient = colorArray(COLORS, self._gradient(self.paletteColors, 
                                                gradientLength))

            for c in range(0, len(self.paletteColors)):
                color = self.paletteColors[c]
                self.thisFrame.append(colorArray(COLORS,color*self.ledCount))

            self.decayTable = self._decayTable(factor=self.decayRate)
            self.decayTable.append(0.0)
            self.decayLen = len(self.decayTable)
            self.counter=self.decayLen-1
            self.coloridx=-1
            self.my_flag={}
            for endstop in self.handler.endstops:
                logging.info(endstop)
                self.frameHandler.homing_end_flag[endstop] = 0
                self.my_flag[endstop] = self.frameHandler.homing_end_flag[endstop]

        def nextFrame(self, eventtime):
            for endstop in self.handler.endstops:

                if self.my_flag[endstop] != self.frameHandler.homing_end_flag[endstop]:
                    self.counter = 0
                    self.coloridx = (self.coloridx + 1) % len(self.paletteColors)
                    self.my_flag[endstop] = self.frameHandler.homing_end_flag[endstop]

            frame = [self.decayTable[self.counter] * i for i in self.thisFrame[self.coloridx ]]
            if self.counter < self.decayLen-1:
                self.counter += 1 
            
            return frame


def load_config_prefix(config):
    return ledEffect(config)
