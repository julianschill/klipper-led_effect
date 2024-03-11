import argparse
import sys
from preview_generator import generate_preview


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
    
    generate_preview(layers, args.fps, args.seconds, args.leds, args.diameter, args.margin, args.output)

