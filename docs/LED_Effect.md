# LED Effects


Addressable LEDs are beginning to supercede RGB LEDs for their
flexibility and relative ease of use. With each individual element
capable of displaying an entire spectrum of colors at very high speed,
they can be used to create a variety of lighting effects.

<!-- DEMO GIF GOES HERE -->

At this time, klipper supports most WS2812 compatible (neopixels)
and APA102 compatible (dotstar) chips for LED Effects.

## Wiring WS2812 compatible (neopixel) LEDs

Neopixel type LEDs require one digital IO pin and a supply of power.
Most are 5V but can be driven from a 3V source. Check manufacturer
specifications to ensure they will work with your board. Each individual
emitter has 4 pins. VCC, GND, Din, and Dout. Neopixel strips typically
have 3 solder pads or a connector with 3 pins and arrows indicating
the direction of the data. The D pins are unidirectional and cannot be
reversed. When attaching them to your printer, the Din or D→ connection
should be attached to an available digital IO pin on the MCU board.
The VCC connection is attached to a supply voltages that is compatible
with the LED strip. Neopixels will typically use 60mA of current per
emitter at full brightness so depending on the power capabilities of
your printer board, it is recommended that they be powered from a
separate power source. It is important that a GND wire be run from
the neopixel chain back to the MCU board in addition to the GND to
the power source. This will ensure the board can communicate with
the strips.

At the present time, Klipper only supports 18 discrete emitters per
IO pin. It is possible to wire two strips to the same data pin and
have them show the same colors. It is also possible to specify
multiple LED chains on different IO pins in the LED Effects
configuration settings.

## Wiring APA102 compatible (dotstar) LEDs

APA102 dotstar LEDs are similar to the neopixel LEDs with the exception
that dotstar uses one-way SPI for communication. This requires the
addition of a clock signal for the emitters. Multiple strips should be
able to share the same clock pin but they each require their own
data line.

# Configuring the strips

In your config file, each strip or chain connected to an IO pin must
have a definition. Following the example in [config/example-extras.cfg](example-extras.cfg)
each strips data pin (and clock pin if applicable) is defined along
with the number of LEDs in the chain. The LED Effect instances are
capable of using multiple strips of different types and color orders
concurrently, but each strip must first be defined by its type.

```
[neopixel panel_ring]
pin:                     ar6
chain_count:             16
```

# Configuring the effects

Effects are, in a more abstract sense, a _state_ that the strips
exist in. Effects can be comprised of 1 led or 100. There can be
one effect layer or 10. It is all arbitrary and extensible. This
means the only limit to how many layers and leds can be run
concurrently is how much processing power the host OS is capable
of handling. During initial testing, upwards of 100 LEDs and 12
effect layers were run concurrently on a Raspberry Pi 4 at 24 FPS.

## Basic layer definition

For our example printer, there is one neopixel ring with 16 leds
that is situated on the front panel, and a short segment of
neopixel LEDs next to the hot end for illuminating the print.

There are also 5 dotstar LEDs located underneath the bed.
Pin numbers listed here are completely made-up.

```
[neopixel panel_ring]
pin:                     ar6
chain_count:             16

[neopixel tool_lights]
pin:                     ar15
chain_count:             6

[neopixel bed_lights]
data_pin:                ar21
clock_pin                ar22
chain_count:             5
```

We would like the ring to turn on a light shade of blue when the
printer comes online and we want the brightness to _breathe_ in and out.

```
[led_effect panel_idle]
autostart:              true
frame_rate:             24
leds:
    neopixel:panel_ring
layers:
    breathing  .5 1 top [(.5,.5,1)]
```

This has defined an effect called `panel_idle` that can be controlled
via the gcode command `SET_LED_EFFECT EFFECT=panel_idle`

### Additional effect level parameters

autostart: true
Setting this to true
frame_rate

run_on_error

heater

analog_pin

stepper

## Defining LEDs

the `leds:` section is a list of neopixel or dotstar strips that will
make up the effect. Both types can be used for the same effect. Each
strip is defined on a separate line and indented beneath the `leds:`
section.

```
leds:
    neopixel:panel_ring
    neopixel:tool_lights
    dotstar:bed_lights
```

Additionally, one may decide to only have certain LEDs displaying the
effect. This is accomplished by providing the index of the LEDs to be
used after the strip name. The index can be a list or a range. If the
indices are omitted, the entire strip is used.

As well, if for some reason you needed to, the same strip can be used
twice in an effect with different emitters being specified.

```
leds:
    neopixel:tool_lights
    neopixel:panel_ring  (1-7)
    neopixel:panel_ring  (9-16)
    dotstar:bed_lights   (1,3,5)
```

## Defining Effect Layers
Effects are generated as frames. Each frame contains the number of pixels
equal to the number of LEDs defined for the effect. So an effect with 22
LEDs specified would have 22 pixels per frame.

Each effect layer is generated as a frame. Each layer frame is blended with
the next to generate the effect. Blending is cumulative and how colors are
blended is defined by the blending mode of the top layer.
Each effect layer is listed on its own line and each has its own settings.

Most effect layers such as breathing and gradient are pre-rendered when
Klipper starts in order to save on computing them later. Others such as
Fire and Twinkle are rendered on demand.

Each layer is defined with the following parameters
 * Layer name
 * Effect Rate
 * Cutoff
 * Blending mode
 * Color palette

Each layer must be on a single line and each line must be indented.
Color palettes can be of unlimited length but may be compressed depending
on the size of the frame or number of LEDs on a strip. Colors are defined
as groups of Red, Green, and Blue. The range for each color is a decimal
number from 0.0 to 1.0. So for yellow, you would use ( 1.0, 1.0, 0.0 ).

Individual colors should be wrapped in parenthesis and separated by commas.

Some Sample Palettes:

    Rainbow    (1.0, 0.0, 0.0),(0.0, 1.0, 0.0),(0.0, 0.0, 1.0)
    Fire       (0.0, 0.0, 0.0),(1.0, 0.0, 0.0),(1.0, 1.0, 0.0),(1.0, 1.0, 1.0)
    Blue Comet (0.8, 1.0, 1.0),(0.0, 0.8, 1.0),(0.0, 0.0, 1.0)

```
layers:
   breathing  .5 screen (0,.1,1), (0,1,.5), (0, 1,1), (0,.1,.5)
   static     1  bottom (1,.1,0), (1,.1,0), (1,.1,0), (1,1,0)
```
There are several effects to choose from.

#### Static
    Effect Rate:  Not used but must be provided
    Cutoff:       Not used but must be provided
    Palette:      Colors are blended evenly across the strip
A single color is displayed and it does not change. If a palette of multiple
colors is provided, colors will be evenly blended along the LEDs based on
difference in hue.

#### Breathing
    Effect Rate:  3   Duration of a complete cylce
    Cutoff:       0   Not used but must be provided
    Palette:          Colors are cycled in order

Colors fade in and out. If a palette of multiple colors is provided, it will
cycle through those colors in the order they are specified in the palette.
The effect speed parameter controls how long it takes to "breathe" one time.

#### Blink
    Effect Rate:  1   Duration of a complete cylce
    Cutoff:       0   Not used but must be provided
    Palette:          Colors are cycled in order

LEDs are turned fully on and fully off based on the effect speed. If a palette
of multiple colors is provided, it will cycle through those colors in order.

#### Strobe
    Effect Rate:  1   Number of times per second to strobe
    Cutoff:       1.5 Determines decay rate. A higher number yields quicker decay
    Palette:          Colors are cycled in order

LEDs are turned fully on and then faded out over time with a decay. If a palette
of multiple colors is provided, it will cycle through those colors in order. The
effect rate controls how many times per second the lights will strobe. The cutoff
parameter controls the decay rate. A good decay rate is 1.5.

#### Twinkle
    Effect Rate:  1   Increases the probability that an LED will illuminate.
    Cutoff:       .25 Determines decay rate. A higher number yields quicker decay
    Palette:          Random color chosen
Random flashes of light with decay along a strip. If a palette is specified,
a random color is chosen from the palette.

#### Gradient
    Effect Rate:  1   How fast to cycle through the gradient
    Cutoff:       0   Not used but must be provided
    Palette:          Linear gradient with even spacing.
Colors from the palette are blended into a linear gradient across the length
of the strip. The effect rate parameter controls the speed at which the colors
are cycled through. A negative value for the effect rate changes the direction
the gradient cycles (right to left vs left to right)

#### Comet
    Effect Rate:  1   How fast the comet moves, negative values change direction
    Cutoff:       1   Length of tail (somewhat arbitrary)
    Palette:          Color of "head" and gradient of "tail"
A light moves through the LEDs with a decay trail. Direction can be controlled
by using a negative effect rate value. The palette colors determine the color
of the comet and the tail. The first color of the palette defines the color of
the "head" of the comet and the remaining colors are blended into the "tail"

#### Chase
    Effect Rate:  1   How fast the comet moves, negative values change direction
    Cutoff:       1   Length of tail (somewhat arbitrary)
    Palette:          Color of "head" and gradient of "tail"
Identical settings as Comet, but with multiple lights chasing each other.

#### Heater
    Effect Rate:  1   Minimum temperature to activate effect
    Cutoff:       0   Disable effect once temp is reached
    Palette:          Color values to blend from Cold to Hot
This effect becomes active when the specified heater is active or the temperature
is greater than the minimum specified temperature. For instance, if a heater is
turned on and set to a target temperature, the LEDs will cycle through the gradient
colors until the target temperature is met. Once it has been met, the last color
of the gradient is used and the effect is essentially a static color until the.
Heater state changes. If the cutoff parameter is supplied, the effect will be
disabled once the targe temperature is met. If the heater is turned off,
the colors will follow this pattern in reverse until the temperature falls
below the minimum temperature specified in the config. This can be used to
indicate the hotend or bed is in a safe state to touch.

#### Fire
    Effect Rate:  45  Probability of "sparking"
    Cutoff:       40  Rate of "cooling"
    Palette:          Color values to blend from "Cold" to "Hot"
The FastLED library for Arduino has a sample sketch called Fire2012WithPalette
included with it. This effect is a port of that sketch. It simulates a flame by
"sparking" an LED. The "heat" from that LED travels down the length of the LEDs
where it gradually cools. A higher rate of sparking causes a greater amount
of heat to accumulate at the base of the strip resulting a more intense flame.
Changing the rate of cooling results in longer or shorter overall flames.

#### HeaterFire
    Effect Rate:  1  Minimum temperature to activate effect
    Cutoff:       0   Disable effect once temp is reached
    Palette:          Color values to blend from "Cold" to "Hot"
The fire effect but responsive to the temperature of the specified heater.
The flame starts as a small ember and increases in intensity as the heater's
target temperature is reached. If the cutoff parameter is set to 1, the effect
will be disabled once the target temperature is reached, otherwise it will
stay active until the heater is disabled.

#### AnalogPin
    Effect Rate:  10  Multiplier for input signal
    Cutoff:       40  Minimum threshold to trigger effect
    Palette:          Color values to blend
This effect uses the value read from an analog pin to determine the color.
If multiple colors are specified in the palette, it chooses one based on the
value of the pin. If only one color is specified, the brightness is proportional
to the pin value. An example usage would be attaching an analog potentiometer
that controls the brightness of an LED strip. Internally, input voltage is measured
as a percentage of voltage vs aref. Another use could be to attach the RPM wire
from a fan if the fan has a tachometer. It must be used with care as too much
current or too high a voltage can damage a pin or destroy a controller board.

#### Stepper
    Effect Rate:  4   Number of trailing LEDs
    Cutoff:       4   Number of leading LEDs
    Palette:          Color values to blend
The position of the specified stepper motor is represented by the first color
in the palette. The remaining colors in the gradient are blended and mirrored
on either side. As the stepper position changes relative to the axis length,
the lights move up and down the strip. It should be noted that the effect
itself updates stepper position every half second based on the reported position
of the stepper similar to the GET_POSITION gcode command. It will not be realtime.
A neagive value in effect rate will fill the entire strip leading up to the stepper
postion, a negative value in cutoff will fill the entire strip after the stepper position.

#### Progress
    Effect Rate:  4   Number of trailing LEDs
    Cutoff:       4   Number of leading LEDs
    Palette:          Color values to blend
Exact same configuration as Stepper but instead of reporting stepper position, this
layer reports print progress.

## Effect Layer Blending
If you have ever used image editing software you may be familiar with
color blending between image layers. Several common color blending
techniques have been added to blend LEDS layers together. Layers defined
in the configuration are ordered top to bottom.

If there are 3 layers defined, the bottom layer is first blended with the
middle layer. The resultant layer is then blended with the top. The bottom
layer will never be blended with anything even if a blending mode is specified.

Layer blending is always evaluated from the bottom up.

Since values cannot exceed 100% brightness and 0% darkness, they are clamped
to this range as a floating point number ( 0.0 - 1.0 )

#### bottom
No blending is done, the value from the color channel of the bottom layer is used.

#### top
No blending is done, the value from the color channel of the top layer is used.

#### add
```
    ( t + b )
```
Color channels (Red, Green, and Blue) are added to one another. This results
in channels becoming brighter.

#### subtract
```
    ( t - b )
```
The the bottom layer is subtracted from the top layer. This results in darkening
similar colors.

#### difference
```
    ( t - b ) or ( b - t )
```
The darker of the layers is subtracted from the brighter of the two

#### average
```
    ( t + b ) / 2
```
The average of the channels is taken

#### multiply
```
    ( t * b )
```
The channels are multiplied together, this is useful to darken colors

#### divide
```
    ( t / b )
```
The channels are divided, this results in brightening colors, often to white

#### screen
```
    1 - ( 1 - t ) * ( 1 - b )
```
The values are inverted, multiplied, and then inverted again. Similar to
divide, it results in brighter colors

#### lighten
```
    ( t if t > b else b )
```
The brigther of the color channels is used

#### darken
```
    ( t if t < b else b )
```
The opposite of lighten, the darker of color channels is used

#### overlay
```
    ( 2ab if a > .5 else 1 - 2( 1 - a )( 1 - b ) )
```
Overlay is a combination of multiply and screen. This has a similar effect
of increasing contrast.

# Sample Configurations

## das Blinkenlights
In the event of critical error, all LED strips breath red in unision to
provide a visible indicator of an error condition with the printer. This
effect is disabled during normal operation and only starts when the MCU
enters a shutdown state.

```
[led_effect critical_error]
leds:
    neopixel:tool_lights
    neopixel:bed_lights
layers:
    strobe         1  1.5   add        (1.0,  1.0, 1.0)
    breathing      2  0     difference (0.95, 0.0, 0.0)
    static         1  0     top        (1.0,  0.0, 0.0)
autostart:                             false
frame_rate:                            24
run_on_error:                          true
```

## Bed Idle with Temperature
```
[led_effect bed_effects]
leds:
    neopixel:bed_lights
autostart:                          true
frame_rate:                         24
heater:                             heater_bed
layers:
    heating 50 0 add    (1,1,0),(1,0,0)
    static  0  0 top    (1,0,0)
```

## Brightness Controlled By Potentiometer
This is an example of how to combine the Analog Pin effect with
layer blending so it controls the brightness of the lights. One
could connect a potentiometer to a thermistor port and use the
voltage reading from that pin to determine the amount of color
to subtract from the base layers. The potentiometer would need
to be wired so that when it is turned "down" the voltage on the
analog pin is on full output and when  it is turned up it is on
minimum output. This way, when the potentiometer is "down", the
color (1.0, 1.0, 1.0) (Full white) is being subtracted from the
colors of the layer, resulting in (0.0, 0.0, 0.0) (Full Black).
The effect rate and cutoff would need to be tuned to the specific
potentiometer and board combination.
```
[led_effect bed_effects]
leds:
    neopixel:bed_lights
autostart:                          true
frame_rate:                         24
analog_pin:                         ar52
layers:
    analogpin 10 0 subtract    (1,1,1)
    static    0  0 top         (1,1,1)
```

## Progress Bar
Using a single strip of LEDs, print progress
is displayed as a light blue line over
a dark blue background

```
[led_effect progress_bar]
leds:
    neopixel:progress_lights
autostart:                          true
frame_rate:                         24
analog_pin:                         ar52
layers:
    progress  -1  0 add         ( 0, 0,   1),( 0, 0.1, 0.6)
    static     0  0 top         ( 0, 0, 0.1)
```

# Frequently Asked Questions

## My LEDs are flickering randomly

This is usuall due to some sort of signal issue. Most addressable
LEDS have a specific protocol they use for communication. It typically
involves sending bits of data at a specific interval followed by a
reset latch to signal them to light up. They will stay the last color
they were set until told to do something different.

With most implementations of addressable LEDs in printer firmware, the
color data is sent once when the gcode command is executed and not sent
again. As long as that initial signal is read, they will stay that color.

With this particular implementation, the color data is being updated at
regular intervals determined by the effect frame rate. So 10 frames per
second would result in 10 color updates to the LEDs per second.

The data lines are susceptible to electromagnetic interference from other
electronics on the printer. When this interference is present, it can
result in malformed data going to the LEDs.

To mitigate this, one can try insulating or isolating the data line from
other wires. Try to keep the data lines as short as possible. This is
especially problematic for 32 bit boards which typically output the
data signal at 3.3V.

Another source of flickering is voltage drop. Addressable LEDs consume
between 20 and 60mA of power each depending on how bright they are set.
If they are being run on a supply that cannot supply enough power, such
as the internal voltage regulator of a printer board, it could manifest
as flickering or overall dimness with the strips.

## My LEDs at the ends of the strips are not as bright as the rest

This typically has to do with the LEDs at the ends of the strip not
getting enough power compared to the LEDs at the beginning of the strip.
The solution is to solder a VCC and GND wire to the end of the strip.
These additional power lines will allow the LEDs at the ends to draw
the power they need. This usually only occurs on very long strips or
if the power supply is already at its limit. It is always recommended
to power LEDs like this from a separate 5V source from the board.

## My colors arent correct

Different chip manufacturers and chip styles use slightly different
protocols for color data. Some specify the color order be Red, Green,
then Blue others specify Green, Red, Blue. The configuration for the
LED strip has an optional parameter that can be set to change the color
order.

``color_order_GRB:                    true``

If you are unsure of the color order of your LEDs and want to test this,
you can comment out or disable all of the effects you have configured
and use a gcode command to set the color of the led strips directly.

``SET_LED LED=<config_name> RED=1 GREEN=0 BLUE=0 TRANSMIT=1``

This command should turn the entire strip red. If the strip turns green,
then it uses a GRB color order.
