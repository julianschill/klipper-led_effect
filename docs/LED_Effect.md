# LED Effects


Addressable LEDs are beginning to supersede RGB LEDs for their
flexibility and relative ease of use. With each individual element
capable of displaying an entire spectrum of colors at very high speed,
they can be used to create a variety of lighting effects.

<!-- DEMO GIF GOES HERE -->

At this time, Klipper supports most WS2812 compatible (Neopixels)
and APA102 compatible (Dotstar) chips for LED Effects.

## Wiring WS2812 compatible (Neopixel) LEDs

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
the Neopixel chain back to the MCU board in addition to the GND to
the power source. This will ensure the board can communicate with
the strips.

The number of discrete emitters per IO pin is limited. It is possible
to wire two strips to the same data pin and have them show the same colors.
It is also possible to specify multiple LED chains on different IO pins
in the LED Effects configuration settings.

## Wiring APA102 compatible (Dotstar) LEDs

APA102 Dotstar LEDs are similar to the Neopixel LEDs with the exception
that Dotstar uses one-way SPI for communication. This requires the
addition of a clock signal for the emitters. Multiple strips should be
able to share the same clock pin but they each require their own
data line.

# Configuring the strips

In your config file, each strip or chain connected to an IO pin must
have a definition. Each strips data pin (and clock pin if applicable)
is defined along with the number of LEDs in the chain. The LED Effect
instances are capable of using multiple strips of different types and
color orders concurrently, but each strip must first be defined by its
type.

```
[neopixel panel_ring]
pin:                     ar6
chain_count:             16
```

# Configuring the effects

Effects are, in a more abstract sense, a _state_ that the strips
exist in. Effects can be comprised of 1 led or 100. There can be
one effect layer or 10. It is all arbitrary and extensible. This
means the only limit to how many layers and LEDs can be run
concurrently is how much processing power the host OS is capable
of handling. During initial testing, upwards of 100 LEDs and 12
effect layers were run concurrently on a Raspberry Pi 4 at 24 FPS.

## Basic layer definition

For our example printer, there is one Neopixel ring with 16 LEDs
that is situated on the front panel, and a short segment of
Neopixel LEDs next to the hot end for illuminating the print.

There are also 5 Dotstar LEDs located underneath the bed.
Pin numbers listed here are completely made-up.

```
[neopixel panel_ring]
pin:                     ar6
chain_count:             16

[neopixel tool_lights]
pin:                     ar15
chain_count:             6

[dotstar bed_lights]
data_pin:                ar21
clock_pin                ar22
chain_count:             5
```

We would like the ring to turn on a light shade of blue when the
printer comes online, and we want the brightness to _breathe_ in and out.

```
[led_effect panel_idle]
autostart:              true
frame_rate:             24
leds:
    neopixel:panel_ring
layers:
    breathing  10 1 top (.5,.5,1)
```

This has defined an effect called `panel_idle`.

### Controlling the effects
Effects can be active or inactive. Inactive effects don't output any color
data, while active effects return color data, that is summed up for each LED
they run on.

#### Activating and deactivating effects
Our example effect can be activated by running the GCode command
`SET_LED_EFFECT EFFECT=panel_idle`. To stop all effects which are currently
running on the LEDs the new effect is using, set the `REPLACE` parameter to 1:
`SET_LED_EFFECT EFFECT=panel_idle REPLACE=1`
Running the command `SET_LED_EFFECT EFFECT=panel_idle STOP=1` deactivates this
particular effect again.
To deactivate all effects we can use the GCode command `STOP_LED_EFFECTS`.
To only deactivate effects for certain LEDs we can specify the LEDS parameter:
`STOP_LED_EFFECTS LEDS="neopixel:panel_ring"` You can also specify indeces (see
below): `STOP_LED_EFFECTS LEDS="neopixel:panel_ring (1-7)"`. Only one
LED parameter can be specified at a time. To stop the effects for multiple LEDs
we have to run the command multiple times.

#### Fading in and out
Effects can be faded in and out by specifying the `FADETIME` parameter:
`SET_LED_EFFECT EFFECT=panel_idle FADETIME=1.0` fades the effect in during one
second. Running `SET_LED_EFFECT EFFECT=panel_idle STOP=1 FADETIME=1.0` fades it
out in one second. We can also fade out all effects by running
`STOP_LED_EFFECTS FADETIME=1.0`. It is also possible to crossfade effects by
using the `REPLACE` parameter with `SET_LED_EFFECT` (see above):
`SET_LED_EFFECT EFFECT=panel_idle REPLACE=1 FADETIME=1.0`

#### Restarting Effects
When an effect is stopped and then started again, it resumes from the frame where
it last left off.  To restart the effect from the beginning, specify the `RESTART`
parameter: `SET_LED_EFFECT EFFECT=panel_idle RESTART=1`.

#### Template processing
The effect layers are processed as (templates)[https://www.klipper3d.org/Command_Templates.html#template-expansion].
That means that they can contain the same control logic that Klipper macros do.
However, processing layers can be computationally intensive, which may affect the
performance of the Raspberry Pi host. Therefore, layers are only evaluated as
templates on effect creation (when the config is read in).

If there is a need to evaluate the layers everytime the effect is activated,
set the `recalculate` effect-level parameter to `true`.

Setting the `recalculate` setting to `true` will also allow the effect to accept
parameters just like `gcode_macro`. Parameters can be passed through the
`SET_LED_EFFECT` command.

The following is an example of a layer that accepts parameters:

```
[led_effect param_effect]
autostart: false
recalculate: true
leds:
    neopixel:leds
layers:
    blink {params.DURATION|default(1)|float} {params.CYCLE|default(0.5)|float} top (1.0, 0.0, 0.0)
```

To activate the effect with different values for both the effect rate and cutoff,
use the following commend:

`SET_LED_EFFECT EFFECT=param_effect DURATION=3 CYCLE=0.2`

It is important to note that because effects are pre-evaluated when they are
first processed, each parameter that is used in the `layers` should have a
default value set. This is required because the initial evaluation of the effect
is not done in the context of a GCode command and, therefore, there is no way
to pass any parameters.

### Additional effect level parameters

`autostart: true`  
Starts the effect on startup

`frame_rate: 24`  
Sets the frame rate in frames per second for the effect

`run_on_error: true`  
(Needs patched MCU firmware. Currently not supported.)

`recalculate: true`  
Enable layer template recalculation on effect activation.

`heater: heater_bed`  
Specifies the default heater to use for a heater effect. Use `extruder` for the
extruder and `heater_bed` for the bed. For temperature fans or  sensors add the
type and use quotes.
Example: `heater: "temperature_fan myfan"`

`analog_pin`  
Specifies the pin to use for effects using an analog signal.

`stepper: x`  
Specifies the axis to use for the stepper effect. Possible values are:
`x`, `y` and `z`.

`endstops: x, y`  
Specifies the endstops the homing effect triggers on. Multiple endstops can be
specified as a comma seprated list. Possible values are: `x`, `y`, `z` and `probe`.


## Defining LEDs

The `leds:` section is a list of Neopixel or Dotstar strips that will
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
used after the strip name. The index can be a list or a range. The range can
also be inversed to invert the effect. If the indices are omitted, the entire
strip is used.

As well, if for some reason you needed to, the same strip can be used
twice in an effect with different emitters being specified.

```
leds:
    neopixel:tool_lights
    neopixel:panel_ring  (1-7)
    neopixel:panel_ring  (16-9)
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
on the size of the frame or number of LEDs on a strip. 

Colors are defined
as groups of Red, Green, Blue and (optional) White. The white channel only used on RGBW LEDs and ignored on RGB LEDs. 

Colors can be specified as decimals, hex-values (with `$` instead of `#` due to klipper's configuration parser) or rgbw values:

```
# White
(1.0, 1.0, 1.0)
(1.0, 1.0, 1.0, 1.0)
$FFFFFF
$FFFFFFFF
rgb(255, 255, 255)
rgbw(255, 255, 255, 255)
```

A palette is a comma-separated list of colors, e.g. 
```
(1.0, 0.0, 0.0),(0.0, 1.0, 0.0),(0.0, 0.0, 1.0)
```

Some example palettes: 

#### Rainbow

![Preview](./img/preview_1930266136.gif)

```layers
static 0 0 top (1.0, 0.0, 0.0),(0.0, 1.0, 0.0),(0.0, 0.0, 1.0)
```

#### Fire
![Preview](./img/preview_2265218385.gif)

```layers
static 0 0 top (0.0, 0.0, 0.0),(1.0, 0.0, 0.0),(1.0, 1.0, 0.0),(1.0, 1.0, 1.0)
```

#### Blue Comet 
![Preview](./img/preview_3153431017.gif)

```layers
static 0 0 top (0.8, 1.0, 1.0),(0.0, 0.8, 1.0),(0.0, 0.0, 1.0)
```

### Color Space Parameters **new syntax only**

For every effect that generates a gradient, the colorSpace used for creating the gradient can be specified. This can lead to more natural looking gradients, or avoid white-out transitions between colors.

![Preview](./img/preview_522736447.gif)

```layers
static(colorSpace=rgb) top $0000FF, $00FF00, $FFFF00, $FF0000
```


![Preview](./img/preview_1603059860.gif)

```layers
static(colorSpace=hsl) top $0000FF, $00FF00, $FFFF00, $FF0000
```

![Preview](./img/preview_2206497488.gif)

```layers
static(colorSpace=lab) top $0000FF, $00FF00, $FFFF00, $FF0000
```

`none` disables mixing and just repeats the palette evenly among the leds.
![Preview](./img/preview_1038093354.gif)

```layers
static(colorSpace=none) top $0000FF, $00FF00, $FFFF00, $FF0000
```

### Effects

#### Static
    Effect Rate:  Not used but must be provided
    Cutoff:       Not used but must be provided
    Palette:      Colors are blended evenly across the strip

A single color is displayed and it does not change. If a palette of multiple
colors is provided, colors will be evenly blended along the LEDs based on
difference in hue.

![Preview](./img/preview_372644514.gif)

```layers
static 1 1 top $FF0000
```

![Preview](./img/preview_2185841352.gif)

```layers
static 1 1 top $FF0000, $00FF00, $0000FF
```


#### LinearFade
    Effect Rate:  3   Duration of a complete cycle (`duration`)
    Cutoff:       0   Not used but must be provided
    Palette:          Colors are cycled in order

LEDs fade through the colors. If a palette of multiple colors is provided, it
will cycle through those colors in the order they are specified in the palette.
The effect rate parameter controls how long it takes to go through all colors.

![Preview](./img/preview_3828332067.gif)

```layers
linearfade(duration=1) top $FF0000, $00FF00, $0000FF
```

#### Breathing
    Effect Rate:  3   Duration of a complete cycle (`duration`)
    Cutoff:       0   Not used but must be provided
    Palette:          Colors are cycled in order

Colors fade in and out. If a palette of multiple colors is provided, it will
cycle through those colors in the order they are specified in the palette.
The effect rate parameter controls how long it takes to "breathe" one time.

![Preview](./img/preview_947365406.gif)

```layers
breathing(duration=2) top $FF0000, $00FF00
```

#### Blink
    Effect Rate:  1   Duration of a complete cycle (`duration`)
    Cutoff:       0.5 Ratio of the time the LEDs are on (between 0 and 1) (`onRatio`)
    Palette:          Colors are cycled in order

LEDs are turned fully on and fully off based on the effect speed. If a palette
of multiple colors is provided, it will cycle through those colors in order.

![Preview](./img/preview_1114876585.gif)

```layers
blink(duration=2,onRatio=0.2) top $FF0000, $0000FF
```

#### Strobe
    Effect Rate:  1   Number of times per second to strobe
    Cutoff:       1.5 Determines decay rate. A higher number yields quicker decay
    Palette:          Colors are cycled in order

LEDs are turned fully on and then faded out over time with a decay. If a palette
of multiple colors is provided, it will cycle through those colors in order. The
effect rate controls how many times per second the lights will strobe. The cutoff
parameter controls the decay rate. A good decay rate is 1.5.

![Preview](./img/preview_2796306561.gif)

```layers
strobe(frequency=0.5,decayRate=0.1) top $FF0000, $0000FF
```


#### Twinkle
    Effect Rate:  1   Increases the probability that an LED will illuminate. (0 = never, 254 = always)
    Cutoff:       .25 Determines decay rate. A higher number yields quicker decay
    Palette:          Random color chosen
Random flashes of light with decay along a strip. If a palette is specified,
a random color is chosen from the palette.

![Preview](./img/preview_2771514037.gif)

```layers
twinkle(probability=0.1,decayRate=0.01) top $00FF00
```

#### Gradient
    Effect Rate:  1   How fast to cycle through the gradient, negative values change direction.
    Cutoff:       1   Number of gradients on chain
    Palette:          Linear gradient with even spacing.
Colors from the palette are blended into a linear gradient across the length
of the strip. The effect rate parameter controls the speed at which the colors
are cycled through. A negative value for the effect rate changes the direction
the gradient cycles (right to left vs left to right). The Cutoff determines the
length of the gradient in relation to the chain length. The bigger the value,
the shorter the gradient (e.g. the value 2 means 2 gradients on the length of
the chain)

![Preview](./img/preview_152731936.gif)

```layers
gradient(speed=1,count=1) top $FF0000, $00FFFF
```

![Preview](./img/preview_1235035691.gif)

```layers
gradient(speed=1,count=1,colorSpace=hsl) top $FF0000, $00FFFF
```

![Preview](./img/preview_3029361392.gif)

```layers
gradient(speed=1,count=1,colorSpace=none) top $FF0000, $00FFFF
```

#### Pattern
    Effect Rate:  1   Time between pattern shifts
    Cutoff:       1   How far the pattern gets shifted
    Palette:          The pattern to be shifted
The palette is applied as a recurring pattern on the chain and shifted along the
chain. The effect rate determines the time between the shifts in seconds, the
cutoff determines the amount of LED positions the pattern gets shifted.

![Preview](./img/preview_3769006074.gif)

```layers
pattern(duration=2,shift=1) top $FF0000, $00FFFF
```


#### Comet
    Effect Rate:  1   How fast the comet moves, negative values change direction
    Cutoff:       1   Length of tail (somewhat arbitrary)
    Palette:          Color of "head" and gradient of "tail"
A light moves through the LEDs with a decay trail. Direction can be controlled
by using a negative effect rate value. The palette colors determine the color
of the comet and the tail. The first color of the palette defines the color of
the "head" of the comet and the remaining colors are blended into the "tail"

![Preview](./img/preview_2002574259.gif)

```layers
comet(speed=0.5,tailLength=5,colorSpace=hsl) top $FF6C11, $FF3864, $2DE2E6, $261447, $0D0221, $023788
```

#### Chase
    Effect Rate:  1   How fast the comet moves, negative values change direction
    Cutoff:       1   Length of tail (somewhat arbitrary)
    Palette:          Color of "head" and gradient of "tail"
Identical settings as Comet, but with multiple lights chasing each other.

![Preview](./img/preview_1561632303.gif)

```layers
chase(speed=0.5,tailLength=2,colorSpace=hsl) top $FF6C11, $FF3864, $2DE2E6, $261447, $0D0221, $023788
```

#### Heater
    Effect Rate:  1   Minimum temperature to activate effect
    Cutoff:       0   Disable effect once temp is reached
    Palette:          Color values to blend from Cold to Hot
This effect becomes active when the specified heater is active or the temperature
is greater than the minimum specified temperature. For instance, if a heater is
turned on and set to a target temperature, the LEDs will cycle through the gradient
colors until the target temperature is met. Once it has been met, the last color
of the gradient is used and the effect is essentially a static color until the
Heater state changes. If the cutoff parameter is supplied, the effect will be
disabled once the target temperature is met. If the heater is turned off,
the colors will follow this pattern in reverse until the temperature falls
below the minimum temperature specified in the config. This can be used to
indicate the hotend or bed is in a safe state to touch.

![Preview](./img/preview_2786598551.gif)

```layers
heater(minTemp=10,disableOnceReached=1,heater=heater_bed) top (0.227,0.427,0.705),(0.113,1,0.168),(1,0.85,0.168),(1.00,0.47,0.00),(1,0.392,0.196),(1,0.313,0.156),(1,0.078,0.078),(1,0,0),(1,0,0)
```

#### Temperature
    Effect Rate:  20  Cold Temperature
    Cutoff:       80  Hot Temperature
    Palette:          Color values to blend from Cold to Hot
The temperature of the configured heater determines the color in a gradient over
the palette. When only one color is defined in the palette, the brightness of
that color is defined by the temperature.

![Preview](./img/preview_4037467609.gif)

```layers
temperature(minTemp=10,maxTemp=60,heater=heater_bed) top (0.227,0.427,0.705),(0.113,1,0.168),(1,0.85,0.168),(1.00,0.47,0.00),(1,0.392,0.196),(1,0.313,0.156),(1,0.078,0.078),(1,0,0),(1,0,0)
```

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

![Preview](./img/preview_4157309777.gif)

```layers
fire(sparkProbability=45,coolingRate=40) top $FF0000, $AA0000
```

#### HeaterFire
    Effect Rate:  1   Minimum temperature to activate effect
    Cutoff:       0   Disable effect once temp is reached
    Palette:          Color values to blend from "Cold" to "Hot"
The fire effect but responsive to the temperature of the specified heater.
The flame starts as a small ember and increases in intensity as the heater's
target temperature is reached. If the cutoff parameter is set to 1, the effect
will be disabled once the target temperature is reached, otherwise it will
stay active until the heater is disabled.

![Preview](./img/preview_2663755680.gif)

```layers
heaterfire(minTemp=10,disableOnceReached=0) top $0000FF, $AA0000
```


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
A negative value in effect rate will fill the entire strip leading up to the stepper
position, a negative value in cutoff will fill the entire strip after the stepper position.

#### StepperColor
    Effect Rate:  1   Scaling of position
    Cutoff:       0   Offset of position
    Palette:          Color values to blend
The color of the LEDs are determined by the position of the stepper motor. The
position is determined between 0 and 100 and is multiplied with the effect rate
and the cutoff is added as offset. This then determines the value in the
palette, that is calculated as a gradient over the specified color values.

#### Progress
    Effect Rate:  4   Number of trailing LEDs
    Cutoff:       4   Number of leading LEDs
    Palette:          Color values to blend
Exact same configuration as Stepper but instead of reporting stepper position, this
layer reports print progress.

![Preview](./img/preview_3222577365.gif)

```layers
progress(trailingLedCount=2,leadingLedCount=2) top $0000FF, $AA0000
```


#### Homing
    Effect Rate:  1   Determines decay rate. A higher number yields slower decay
    Cutoff:       0   Not used, but must be provided
    Palette:          Colors are cycled in order

LEDs turn on during homing when the endstop is triggered and fade out again. The
effect rate determines the time for the fade out. If a palette of multiple colors
is provided, it will cycle through those colors in order.

## Effect Layer Blending
If you have ever used image editing software you may be familiar with
color blending between image layers. Several common color blending
techniques have been added to blend LED layers together. Layers defined
in the configuration are ordered top to bottom.

If there are 3 layers defined, the bottom layer is first blended with the
middle layer. The resultant layer is then blended with the top. The bottom
layer will never be blended with anything even if a blending mode is specified.

Layer blending is always evaluated from the bottom up.

Since values cannot exceed 100% brightness and 0% darkness, they are clamped
to this range as a floating-point number ( 0.0 - 1.0 )

We'll blend the following colors to illustrate:

![Preview](./img/preview_1173196264.gif)

```layers
static 0 0 top (1, 0.5, 0)
```

![Preview](./img/preview_1808171867.gif)

```layers
static 0 0 top (0, 0.5, 1)
```


#### bottom
No blending is done, the value from the color channel of the bottom layer is used.

![Preview](./img/preview_3176149258.gif)

```layers
static 0 0 bottom (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```

*The bottom layer needs to be `top` so that it is used at all*


#### top
No blending is done, the value from the color channel of the top layer is used.


![Preview](./img/preview_3462693145.gif)

```layers
static 0 0 top (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```


#### add
```
    ( t + b )
```
Color channels (Red, Green, and Blue) are added to one another. This results
in channels becoming brighter.

![Preview](./img/preview_3234791021.gif)

```layers
static 0 0 add (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```


#### subtract
```
    ( b - t )
```
The the top layer is subtracted from the bottom layer. This results in darkening
similar colors.

![Preview](./img/preview_3009762427.gif)

```layers
static 0 0 subtract (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```


#### subtract_b
```
    ( t - b )
```
The the bottom layer is subtracted from the top layer. This results in darkening
similar colors.

![Preview](./img/preview_1082126048.gif)

```layers
static 0 0 subtract_b (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```


#### difference
```
    ( t - b ) or ( b - t )
```
The darker of the layers is subtracted from the brighter of the two

![Preview](./img/preview_2689310554.gif)

```layers
static 0 0 difference (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```


#### average
```
    ( t + b ) / 2
```
The average of the channels is taken

![Preview](./img/preview_2546082449.gif)

```layers
static 0 0 average (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```


#### multiply
```
    ( t * b )
```
The channels are multiplied together, this is useful to darken colors

![Preview](./img/preview_2991711774.gif)

```layers
static 0 0 multiply (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```

This is useful, e.g. if you want to create a pulsing animation of e.g. a heater:

![Preview](./img/preview_2969376940.gif)

```layers
linearfade 1 0 multiply (0.2,0.2,0.2),(1,1,1)
heater  0 0 top (0, 0, 1), (0, 1, 0), (1, 0, 0), (1, 0, 0)
```



#### divide
```
    ( t / b )
```
The channels are divided, this results in brightening colors, often to white

![Preview](./img/preview_2508875843.gif)

```layers
static 0 0 divide (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```


#### divide_inv
```
    ( b / t )
```
Like divide, but bottom divided by top

![Preview](./img/preview_2728533037.gif)

```layers
static 0 0 divide_inv (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```

#### screen
```
    1 - ( 1 - t ) * ( 1 - b )
```
The values are inverted, multiplied, and then inverted again. Similar to
divide, it results in brighter colors

![Preview](./img/preview_3006598880.gif)

```layers
static 0 0 screen (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```


#### lighten
```
    ( t if t > b else b )
```
The brighter of the color channels is used

![Preview](./img/preview_479940560.gif)

```layers
static 0 0 lighten (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```

#### darken
```
    ( t if t < b else b )
```
The opposite of lighten, the darker of color channels is used

![Preview](./img/preview_3323396353.gif)

```layers
static 0 0 darken (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```

#### overlay
```
    ( 2ab if a > .5 else 1 - 2( 1 - a )( 1 - b ) )
```
Overlay is a combination of multiply and screen. This has a similar effect
of increasing contrast.

![Preview](./img/preview_2872927478.gif)

```layers
static 0 0 overlay (0, 0.5, 1)
static 0 0 top (1, 0.5, 0)
```


# Sample Configurations

## das Blinkenlights
In the event of critical error, all LED strips breath red in unison to
provide a visible indicator of an error condition with the printer. This
effect is disabled during normal operation and only starts when the MCU
enters a shutdown state (currently not supported).

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
    heater  50 0 add    (1,1,0),(1,0,0)
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
layers:
    progress  -1  0 add         ( 0, 0,   1),( 0, 0.1, 0.6)
    static     0  0 top         ( 0, 0, 0.1)
```

# Frequently Asked Questions

## My LEDs are flickering randomly

This is usually due to some sort of signal issue. Most addressable
LEDs have a specific protocol they use for communication. It typically
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

Signal integrity can also be deteriorated by ringing and reflections on
the data line. Especially, when the cable to the first LED is rather long.
This can be reduced by adding a 700 Ohm resistor in line to the data line
directly in front of the first LED.

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

## My colors aren't correct

Different chip manufacturers and chip styles use slightly different
protocols for color data. Some specify the color order be Red, Green,
then Blue others specify Green, Red, Blue. The configuration for the
LED strip has an optional parameter that can be set in the 'neopixel'
section to change the color order.

``
color_order: GRB``

If you are unsure of the color order of your LEDs and want to test this,
you can comment out or disable all of the effects you have configured
and use a gcode command to set the color of the led strips directly.

``SET_LED LED=<config_name> RED=1 GREEN=0 BLUE=0 TRANSMIT=1``

This command should turn the entire strip red. If the strip turns green,
then it uses a GRB color order.

Some LEDs, like the SK6812, also have a white channel. For that the color order
can be set to:

``color_order: GRBW``
