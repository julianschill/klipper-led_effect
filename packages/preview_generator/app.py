import argparse
import sys
from klippermock import *
from PIL import Image, ImageDraw

def run(layers, fps, seconds, leds, diameter, margin, output):
    config = mockConfig()
    config.setint("ledcount", leds)
    config.setint("framerate", fps)
    config.set("layers", layers)
    printer = mockPrinter(config)
    printer._handle_ready()

    width = leds*diameter + margin*(leds+1)
    height = diameter+margin*2
    progressThickness = 3
    frames = []
    
    for i in range(seconds*fps):
        frame = printer.led_effect.getFrame(i)[0]
        img = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line([(0, height-progressThickness), (width*i/(seconds*fps), height-progressThickness)], fill="black", width=progressThickness)
        for j in range(0, len(frame), 4):
            led = j/4
            x0 = margin + led*(diameter+margin)
            y0 = margin
            x1 = x0 + diameter
            y1 = y0 + diameter

            [r, g, b, a] = frame[j:j+4]
            draw.ellipse([(x0, y0), (x1, y1)], width=2, outline="black", fill=(int(r*255), int(g*255), int(b*255), 255))
        frames.append(img)
    
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=1000/fps, loop=0)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                        prog='Preview-Generator',
                        description='Generates an animated image of a given layer')
    parser.add_argument('layers', type=str, nargs='?', default=sys.stdin)
    parser.add_argument('--fps', default=24, type=int)
    parser.add_argument('--seconds', '-s', default=10, type=int)
    parser.add_argument('--diameter', '-d', default=50, type=int)
    parser.add_argument('--margin', '-m', default=5, type=int)
    parser.add_argument('--leds', '-l', default=10, type=int)
    parser.add_argument('--output', '-o', default='output.gif')
    args = parser.parse_args()

    layers = args.layers if args.layers != sys.stdin else sys.stdin.read()
    
    run(layers, args.fps, args.seconds, args.leds, args.diameter, args.margin, args.output)

