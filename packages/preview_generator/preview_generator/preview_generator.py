from klippermock import *
from PIL import Image, ImageDraw


def generate_preview(layers, fps, seconds, leds, diameter, margin, output):
    config = mockConfig()
    config.setint("ledcount", leds)
    config.setint("framerate", fps)
    config.set("layers", layers)
    printer = mockPrinter(config)
    printer._handle_ready()
    printer.led_effect.handler.heaterCurrent = {"heater_bed": 0, "hotend": 0}
    printer.led_effect.handler.heaterTarget = {"heater_bed": 60, "hotend": 250}
    printer.led_effect.handler.heaterLast = {"heater_bed": 0, "hotend": 0}

    width = leds*diameter + margin*(leds+1)
    height = diameter+margin*2
    progressThickness = 3
    frames = []

    totalFrameCount = (seconds*fps)

    if len(printer.led_effect.layers) == 1 and len(printer.led_effect.layers[0].thisFrame) > 0:
        totalFrameCount = len(printer.led_effect.layers[0].thisFrame)

    for i in range(totalFrameCount):
        printer.led_effect.handler.heaterCurrent["hotend"] = 250*i/(
            totalFrameCount)
        printer.led_effect.handler.heaterCurrent["heater_bed"] = 60*i/(
            totalFrameCount)
        printer.set_progress(int(100*i/(totalFrameCount)))
        frame = printer.led_effect.getFrame(i)[0]
        img = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line([(0, height-progressThickness), (width*i/(totalFrameCount),
                  height-progressThickness)], fill="black", width=progressThickness)
        for j in range(0, len(frame), 4):
            led = j/4
            x0 = margin + led*(diameter+margin)
            y0 = margin
            x1 = x0 + diameter
            y1 = y0 + diameter

            [r, g, b, a] = frame[j:j+4]
            draw.ellipse([(x0, y0), (x1, y1)], width=2, outline="black", fill=(
                int(r*255), int(g*255), int(b*255), 255))
        frames.append(img)

    frames[0].save(output, save_all=True,
                   append_images=frames[1:], duration=1000/fps, loop=0)
