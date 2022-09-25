# Support for addressable LED visual effects
# using neopixel and dotstar LEDs
#
# Copyright (C) 2020  Paul McGowan <mental405@gmail.com>
# co-authored by Julian Schill <j.schill@web.de>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

from math import cos, exp, pi
from random import randint

ANALOG_SAMPLE_TIME  = 0.001
ANALOG_SAMPLE_COUNT = 5
ANALOG_REPORT_TIME  = 0.05

######################################################################
# Custom color value list, returns lists of [r, g ,b] values
# from a one dimensional list
######################################################################

class colorArray(list):
    def __getitem__(self, a):
        if isinstance(a, int):
            return super(colorArray, self).__getitem__(
                            slice(a*3, a*3+3))
        if isinstance(a, slice):
                start = a.start*3 if a.start != None else None
                stop = a.stop*3 if a.stop != None else None
                return colorArray(
                        super(colorArray, self).__getitem__(
                            slice(start, stop, a.step)))
    def __getslice__(self, a, b):
        return self.__getitem__(slice(a,b))
    def __setitem__(self, a, v):
        if isinstance(a, int):
            super(colorArray, self).__setitem__(a*3  , v[0])
            super(colorArray, self).__setitem__(a*3+1, v[1])
            super(colorArray, self).__setitem__(a*3+2, v[2])
    def __len__(self):
        return super(colorArray, self).__len__() // 3
    def reverse(self):
        self.__init__([c for cl in range(len(self)-1,-1, -1)
                        for c in self[cl]])
    def shift(self, shift=1, direction=True):
        if direction:
            #shift array to the right
            self.__init__(self[-shift:] + self[:-shift])
        else:
            #shift array to the left
            self.__init__(self[shift:] + self[:shift])
    def padLeft(self, v, a):
        self.__init__(v * a + self)
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
        self.printer.register_event_handler('klippy:ready', self._handle_ready)
        self.ledChains=[]
        self.gcode.register_command('STOP_LED_EFFECTS',
                                    self.cmd_STOP_LED_EFFECTS,
                                    desc=self.cmd_STOP_LED_EFFECTS_help)

    cmd_STOP_LED_EFFECTS_help = 'Stops all led_effects'

    def _handle_ready(self):
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
        for effect in self.effects:
            if not effect.runOnShutown:
                for chain in self.ledChains:
                    chain.led_helper.set_color(None, (0.0, 0.0, 0.0, 0.0))
                    chain.led_helper.update_func(chain.led_helper.led_state, None)

        pass

    def addEffect(self, effect):

        if effect.heater:
            effect.heater=effect.heater.strip('\"\'')
            if effect.heater.startswith("temperature_fan "):
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
        return eventtime + 1

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

    # Todo: Make color temperature configurable in Neopixel config and 
    # maybe move conversion function to Neopixel module
    def _rgb_to_rgbw(self, colors, color_temp_of_w = (1.0,0.705,0.420)):

        minWhite = min( colors[0] / color_temp_of_w[0], 
                        colors[1] / color_temp_of_w[1], 
                        colors[2] / color_temp_of_w[2])

        color_output = [0 for _ in range(4)]

        for i in range(3):
            color_output[i] = colors[i] - minWhite * color_temp_of_w[i]
        color_output[3] = minWhite
        return color_output

    def _getColorData(self, colors, has_white, fade):
        clamp = (lambda x : 0.0 if x < 0.0 else 1.0 if x > 1.0 else x)
        colors = [x*clamp(fade) for x in colors]
        if has_white:
            colors = self._rgb_to_rgbw(colors)
        else:
            colors = colors + [0.0]
        colors = [clamp(x) for x in colors]
        return tuple(colors)

    def _getFrames(self, eventtime):
        chainsToUpdate = set()

        #first set all LEDs to 0, that should be updated
        for effect in self.effects:
            frame, update = effect.getFrame(eventtime)
            if update:
                for i in range(effect.ledCount):
                    chain,index=effect.leds[i]
                    chain.led_helper.led_state[index] = (0.0, 0.0, 0.0, 0.0)
                    chainsToUpdate.add(chain)

        #then sum up all effects for that LEDs
        for effect in self.effects:
            frame, update = effect.getFrame(eventtime)
            if update:
                for i in range(effect.ledCount):
                    chain,index=effect.leds[i]
                    
                    has_white = False
                    if hasattr(chain, 'color_map'):
                        has_white = (len(chain.color_map) == 4)

                    current_state=list(chain.led_helper.led_state[index])
                    effect_state=self._getColorData(frame[i*3:i*3+3], 
                                                    has_white, 
                                                    effect.fadeValue)

                    next_state=[min(1.0,a+b) for a,b in \
                                 zip(current_state, effect_state)]

                    chain.led_helper.led_state[index] = tuple(next_state)
                    chainsToUpdate.add(chain)

        for chain in chainsToUpdate:
            if hasattr(chain,"prev_data"):
                chain.prev_data = None # workaround to force update of dotstars
            chain.led_helper.update_func(chain.led_helper.led_state, None)
        if self.effects:
            next_eventtime=min(self.effects, key=lambda x: x.nextEventTime)\
                            .nextEventTime
        else:
            next_eventtime = eventtime
        # run at least with 10Hz
        next_eventtime=min(next_eventtime, eventtime + 0.1) 
        return next_eventtime

    def cmd_STOP_LED_EFFECTS(self, gcmd):
        led_param = gcmd.get('LEDS', "")

        for effect in self.effects:
            if led_param in effect.configChains or led_param == "":
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
        self.configLayers = config.get('layers')
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
            chain = chain.strip()
            parms = [parameter.strip() for parameter in chain.split()
                        if parameter.strip()]

            if parms:
                ledChain     = self.printer.lookup_object(parms[0]\
                                                .replace(':',' '))
                ledIndices   = ''.join(parms[1:]).strip('()').split(',')

                #Add each discrete chain to the collection
                if ledChain not in self.ledChains:
                    self.ledChains.append(ledChain)


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
                                self.leds.append((ledChain, int(i)))
                        else:
                            for i in led.split(','):
                                self.leds.append((ledChain, \
                                                (int(i)-1)))
                    else:
                        for i in range(ledChain.led_helper.get_led_count()):
                            self.leds.append((ledChain, int(i)))

        self.ledCount = len(self.leds)
        self.frame = [0.0] * 3 * self.ledCount

        #enumerate all effects from the subclasses of _layerBase...
        availableLayers = {str(c).rpartition('.layer')[2]\
                                 .replace("'>", "")\
                                 .lower() : c
                                   for c in self._layerBase.__subclasses__()
                                   if str(c).startswith("<class")}

        st = (lambda x : x.strip(('( )')))

        for layer in [line for line \
            in self.configLayers.split('\n') if line.strip()]:

            parms = [st(parameter) for parameter \
                in layer.split() if st(parameter)]

            if not parms[0] in availableLayers:
                raise self.printer\
                    .config_error("LED Effect '%s' in section '%s' is not a \
                        valid effect layer" % (parms[0], self.name))

            if not parms[3] in self.blendingModes:
                raise self.printer.config_error("Blending mode '%s' in section\
                     '%s' is not a valid blending mode" % (parms[3], self.name))

            layer = availableLayers[parms[0]]

            palette = \
                [float(st(c)) for t in parms[4:] for c in t.split(',') if st(c)]

            self.layers.insert(0, layer(handler       = self,
                                        frameHandler  = self.handler,
                                        effectRate    = float(parms[1]),
                                        effectCutoff  = float(parms[2]),
                                        paletteColors = palette,
                                        frameRate     = self.frameRate,
                                        ledCount      = len(self.leds),
                                        blendingMode  = parms[3]))

        self.handler.addEffect(self)

    def getFrame(self, eventtime):
        if not self.enabled and self.fadeValue <= 0.0:
            if self.nextEventTime < self.handler.reactor.NEVER:
                # Effect has just been disabled. Set colors to 0 and update once.
                self.nextEventTime = self.handler.reactor.NEVER
                self.frame = [0.0] * 3 * self.ledCount
                update = True
            else:
                update = False
        else:
            update = True
            if eventtime > self.nextEventTime:
                self.nextEventTime = eventtime + self.frameRate

                self.frame = [0.0] * 3 * self.ledCount
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
        self.enabled = state
        if self.enabled:
            self.nextEventTime = self.handler.reactor.NOW
    
    def set_fade_time(self, fadetime):
        self.fadeTime = fadetime
        self.fadeEndTime = self.handler.reactor.monotonic() + fadetime

    def cmd_SET_LED_EFFECT(self, gcmd):
        self.set_fade_time(gcmd.get_float('FADETIME', 0.0))
        if gcmd.get_int('STOP', 0) == 1:
            if self.enabled:
                self.set_fade_time(gcmd.get_float('FADETIME', 0.0))
            self.set_enabled(False)
        else:
            self.set_fade_time(gcmd.get_float('FADETIME', 0.0))
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
            self.paletteColors   = colorArray(kwargs['paletteColors'])
            self.effectRate      = kwargs['effectRate']
            self.effectCutoff    = kwargs['effectCutoff']
            self.frameRate       = kwargs['frameRate']
            self.blendingMode    = kwargs['blendingMode']
            self.frameNumber     = 0
            self.thisFrame       = []
            self.frameCount      = 1
            self.lastAnalog      = 0

        def nextFrame(self, eventtime):
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
                for x in range(2, int(p / rate)+3):
                    b = exp(1)**-(x/r)
                    frame.append(b*(b>.01))

            return frame

        def _gradient(self, palette, steps, reverse=False, toFirst=False):
            palette = colorArray(palette[:])
            if reverse: palette.reverse()

            if len(palette) == 1:
                return colorArray(palette * steps)

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
                    z = [((1-r)*palette[k][m] + r*palette[k+1][m]) for m in range(3)]
                gradient += z
            return gradient

    #Individual effects inherit from the LED Effect Base class
    #each effect must support the nextFrame() method either by
    #using the method from the base class or overriding it.

    #Solid color
    class layerStatic(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerStatic, self).__init__(**kwargs)

            self.paletteColors = colorArray(self.paletteColors)

            gradientLength = int(self.ledCount)
            gradient = colorArray(self._gradient(self.paletteColors, 
                                                gradientLength))

            self.thisFrame.append(gradient[0:self.ledCount])
            self.frameCount = len(self.thisFrame)

    #Slow pulsing of color
    class layerBreathing(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerBreathing, self).__init__(**kwargs)

            brightness = []

            p = (1 / self.frameRate) * (self.effectRate * 0.5)
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

            gradientLength = int(self.effectRate / self.frameRate) 
            if gradientLength == 0: gradientLength = 1

            gradient   = colorArray(self._gradient(self.paletteColors, 
                                                   gradientLength, toFirst=True))

            for i in range(gradientLength):
                self.thisFrame.append(gradient[i]*self.ledCount)

            self.frameCount = len(self.thisFrame)

    #Turns the entire strip on and off
    class layerBlink(_layerBase):
        def __init__(self, **kwargs):
            super(ledEffect.layerBlink, self).__init__(**kwargs)

            dutyCycle= max(0,min(1.0, self.effectCutoff))
            frameCountOn = int(( 1.0 / self.frameRate ) * self.effectRate\
                 * dutyCycle)
            frameCountOff = int(( 1.0 / self.frameRate ) * self.effectRate\
                 * (1-dutyCycle))

            for c in range(0, len(self.paletteColors)):
                color = self.paletteColors[c]
                self.thisFrame += [color * self.ledCount] * frameCountOn
                self.thisFrame += [[0,0,0] * self.ledCount] * frameCountOff

            self.frameCount = len(self.thisFrame)

    #Random flashes with decay
    class layerTwinkle(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerTwinkle, self).__init__(**kwargs)

            self.thisFrame = colorArray([0.0, 0.0, 0.0] * self.ledCount)
            self.lastBrightness  = [-1] * self.ledCount
            self.decayTable = self._decayTable(factor=1 / self.effectCutoff)
            self.decayLen = len(self.decayTable)
            self.colorCount = len(self.paletteColors) - 1

        def nextFrame(self, eventtime):

            for i in range(0, self.ledCount):

                r = randint(0, self.colorCount)
                color = self.paletteColors[r]

                if randint(0, 255) > 254 - self.effectRate:
                    self.lastBrightness[i] = 0
                    self.thisFrame[i] = color

                if self.lastBrightness[i] != -1:
                    if self.lastBrightness[i] == self.decayLen:
                        self.lastBrightness[i] = -1
                        self.thisFrame[i] = [0.0, 0.0, 0.0]
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

            frameRate  = int(1.0 / self.frameRate)
            frameCount = int(frameRate * self.effectRate)

            decayTable = self._decayTable(factor=1 / self.effectCutoff,
                                          rate=self.effectRate)

            if len(decayTable) > frameRate:
                decayTable = decayTable[:frameRate]
            else:
                decayTable += [0.0] * (self.frameRate - len(decayTable))

            for c in range(0, len(self.paletteColors)):
                color = self.paletteColors[c]

                for b in decayTable:
                    self.thisFrame += [[b * i for i in color] * self.ledCount]

            self.frameCount = len(self.thisFrame)

    #Lights move sequentially with decay
    class layerComet(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerComet, self).__init__(**kwargs)
            if self.effectRate > 0:
                self.direction = True
            else:
                self.direction = False
                self.effectRate *= -1

            if self.effectCutoff <= 0: self.effectCutoff = .1

            decayTable = self._decayTable(factor=len(self.paletteColors) * \
                                            self.effectCutoff, rate=1)

            gradient   = self.paletteColors[0] + \
                self._gradient(self.paletteColors[1:], len(decayTable)+1)

            decayTable = [c for b in zip(decayTable, decayTable, decayTable) \
                for c in b]

            comet = colorArray([a * b for a, b in zip(gradient,decayTable)])

            comet.padRight([0.0,0.0,0.0], self.ledCount - len(comet))

            if self.direction: comet.reverse()

            if self.effectRate == 0:
                self.thisFrame.append(comet[0:self.ledCount])
            else:                           
                for i in range(len(comet)):
                    comet.shift(int(self.effectRate+(self.effectRate < 1)), 
                                self.direction)
                    self.thisFrame.append(comet[0:self.ledCount])

                    for x in range(int((1/self.effectRate)-(self.effectRate <= 1))):
                        self.thisFrame.append(comet[0:self.ledCount])

            self.frameCount = len(self.thisFrame)

    #Lights move sequentially with decay
    class layerChase(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerChase, self).__init__(**kwargs)
            
            if self.effectRate > 0:
                self.direction = True
            else:
                self.direction = False
                self.effectRate *= -1

            decayTable = self._decayTable(factor=len(self.paletteColors) * \
                            self.effectCutoff, rate=1)

            gradient   = self.paletteColors[0] + \
                self._gradient(self.paletteColors[1:], len(decayTable)+1)

            decayTable = [c for b in zip(decayTable, decayTable, decayTable) \
                for c in b]
            gradient  = colorArray([a * b
                            for a, b in zip(gradient,decayTable)])

            chase = gradient

            for i in range(int(self.ledCount/len(gradient))):
                chase += gradient

            if self.direction: chase.reverse()
            if self.effectRate == 0:
                self.thisFrame.append(chase[0:self.ledCount])
            else:                                                   
                for i in range(len(chase)):
                    chase.shift(int(self.effectRate+(self.effectRate < 1)), 
                                self.direction)
                    self.thisFrame.append(chase[0:self.ledCount])

                    for x in range(int((1/self.effectRate)-(self.effectRate <= 1))):
                        self.thisFrame.append(chase[0:self.ledCount])

            self.frameCount = len(self.thisFrame)

    #Color gradient over all LEDs
    class layerGradient(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerGradient, self).__init__(**kwargs)

            direction = -1 if self.effectRate < 0 else 1

            if self.effectRate == 0: 
                gradientLength = self.ledCount
            else:
                gradientLength=abs(int(1/(self.effectRate * self.frameRate)))
            gradient = colorArray(self._gradient(self.paletteColors, 
                                                  gradientLength,
                                                  toFirst=True))

            for i in range(gradientLength if self.effectRate != 0 else 1):
                frame = colorArray([0.0, 0.0, 0.0] * self.ledCount)
                for led in range(self.ledCount):
                    frame[led] = gradient[ int(i*direction + \
                        self.effectCutoff * gradientLength * led \
                        / self.ledCount ) % gradientLength]
                self.thisFrame.append(frame)

            self.frameCount = len(self.thisFrame)
            
    #Responds to heater temperature
    class layerHeater(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerHeater, self).__init__(**kwargs)

            if len(self.paletteColors) == 1:
                self.paletteColors += self.paletteColors

            gradient = colorArray(self._gradient(self.paletteColors[:-1], 200) +
                                    self.paletteColors[-1:])

            for i in range(len(gradient)):
                self.thisFrame.append(gradient[i] * self.ledCount)

            self.frameCount = len(self.thisFrame)

        def nextFrame(self, eventtime):
            if self.frameHandler.heaterTarget[self.handler.heater] > 0.0 and \
               self.frameHandler.heaterCurrent[self.handler.heater] > 0.0:

                if self.frameHandler.heaterCurrent[self.handler.heater] <= \
                   self.frameHandler.heaterTarget[self.handler.heater]-2:

                    s = int((self.frameHandler.
                                heaterCurrent[self.handler.heater] / 
                                self.frameHandler.
                                heaterTarget[self.handler.heater]) * 200)
                    s = min(len(self.thisFrame)-1,s)
                    return self.thisFrame[s]
                elif self.effectCutoff > 0:
                    return None
                else:
                    return self.thisFrame[-1]
            elif self.effectRate > 0 and \
                 self.frameHandler.heaterCurrent[self.handler.heater] > 0.0:
                if self.frameHandler.heaterCurrent[self.handler.heater] >= \
                    self.effectRate and \
                    self.frameHandler.heaterLast[self.handler.heater] > 0:

                    s = int(((self.frameHandler.
                                heaterCurrent[self.handler.heater] - 
                                self.effectRate) / 
                                self.frameHandler.
                                heaterLast[self.handler.heater]) * 200)
                    s = min(len(self.thisFrame)-1,s)
                    return self.thisFrame[s]

            return None

    #Responds to analog pin voltage
    class layerAnalogPin(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerAnalogPin, self).__init__(**kwargs)

            if len(self.paletteColors) == 1:
                self.paletteColors = [0.0,0.0,0.0] + self.paletteColors

            gradient   = colorArray(self._gradient(self.paletteColors, 101))

            for i in range(len(gradient)):
                self.thisFrame.append(gradient[i] * self.ledCount)

        def nextFrame(self, eventtime):
            v = int(self.handler.analogValue * self.effectRate)

            if v > 100: v = 100

            if v > self.effectCutoff:
                return self.thisFrame[v]
            else:
                return self.thisFrame[0]

    #Lights illuminate relative to stepper position
    class layerStepper(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerStepper, self).__init__(**kwargs)

            if self.effectRate < 0:
                self.effectRate = self.ledCount

            if self.effectCutoff < 0:
                self.effectCutoff = self.ledCount

            if self.effectRate == 0:
                trailing = colorArray([0.0,0.0,0.0] * self.ledCount)
            else:
                trailing = colorArray(self._gradient(self.paletteColors[1:],
                                                     int(self.effectRate), True))
                trailing.padLeft([0.0,0.0,0.0], self.ledCount)

            if self.effectCutoff == 0:
                leading = colorArray([0.0,0.0,0.0] * self.ledCount)
            else:
                leading = colorArray(self._gradient(self.paletteColors[1:],
                                                    int(self.effectCutoff), False))
                leading.padRight([0.0,0.0,0.0], self.ledCount)

            gradient = colorArray(trailing + self.paletteColors[0] + leading)
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

     #Shameless port of Fire2012 by Mark Kriegsman

    #Shamelessly appropriated from the Arduino FastLED example files
    #Fire2012.ino by Daniel Garcia
    class layerFire(_layerBase):
        def __init__(self,  **kwargs):
            super(ledEffect.layerFire, self).__init__(**kwargs)

            self.heatMap    = [0.0] * self.ledCount
            self.gradient   = colorArray(self._gradient(self.paletteColors, 
                                                                        102))
            self.frameLen   = len(self.gradient)
            self.heatLen    = len(self.heatMap)
            self.heatSource = int(self.ledCount / 10.0)
            self.effectRate = int(self.effectRate)

            if self.heatSource < 1:
                self.heatSource = 1

        def nextFrame(self, eventtime):
            frame = []

            for h in range(self.heatLen):
                c = randint(0,self.effectCutoff)
                self.heatMap[h] -= (self.heatMap[h] - c >= 0 ) * c

            for i in range(self.ledCount - 1, self.heatSource, -1):
                d = (self.heatMap[i - 1] +
                     self.heatMap[i - 2] +
                     self.heatMap[i - 3] ) / 3

                self.heatMap[i] = d * (d >= 0)

            if randint(0, 100) < self.effectRate:
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

            self.heatMap    = [0.0] * self.ledCount
            self.gradient   = colorArray(self._gradient(self.paletteColors, 
                                                                        102))
            self.frameLen   = len(self.gradient)
            self.heatLen    = len(self.heatMap)
            self.heatSource = int(self.ledCount / 10.0)
            self.effectRate = 0

            if self.heatSource < 1:
                self.heatSource = 1

        def nextFrame(self, eventtime):
            frame = []
            spark = 0
            heaterTarget  = self.frameHandler.heaterTarget[self.handler.heater]
            heaterCurrent = self.frameHandler.heaterCurrent[self.handler.heater]
            heaterLast    = self.frameHandler.heaterLast[self.handler.heater]

            if heaterTarget > 0.0 and heaterCurrent > 0.0:
                if heaterCurrent <= heaterTarget-2:
                    spark = int((heaterCurrent / heaterTarget) * 80)
                    brightness = int((heaterCurrent / heaterTarget) * 100)
                elif self.effectCutoff > 0:
                    spark = 0
                else:
                    spark = 80
                    brightness = 100
            elif self.effectRate > 0 and heaterCurrent > 0.0:
                if heaterCurrent >= self.effectRate:
                    spark = int(((heaterCurrent - self.effectRate)
                                      / heaterLast) * 80)
                    brightness = int(((heaterCurrent - self.effectRate)
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

            if self.effectRate < 0:
                self.effectRate = self.ledCount

            if self.effectCutoff < 0:
                self.effectCutoff = self.ledCount

            if self.effectRate == 0:
                trailing = colorArray([0.0,0.0,0.0] * self.ledCount)
            else:
                trailing = colorArray(self._gradient(self.paletteColors[1:],
                                                     int(self.effectRate), True))
                trailing.padLeft([0.0,0.0,0.0], self.ledCount)

            if self.effectCutoff == 0:
                leading = colorArray([0.0,0.0,0.0] * self.ledCount)
            else:
                leading = colorArray(self._gradient(self.paletteColors[1:],
                                                    int(self.effectCutoff), False))
                leading.padRight([0.0,0.0,0.0], self.ledCount)

            gradient = colorArray(trailing + self.paletteColors[0] + leading)
            gradient.shift(len(trailing), 0)
            frames = [gradient[:self.ledCount]]

            for i in range(0, self.ledCount):
                gradient.shift(1,1)
                frames.append(gradient[:self.ledCount])

            self.thisFrame.append(colorArray([0.0,0.0,0.0] * self.ledCount))
            for i in range(1, 101):
                x = int((i / 101.0) * self.ledCount)
                self.thisFrame.append(frames[x])

            self.frameCount = len(self.thisFrame)

        def nextFrame(self, eventtime):
            p = self.frameHandler.printProgress
            return self.thisFrame[p] #(p - 1) * (p > 0)]

def load_config_prefix(config):
    return ledEffect(config)
