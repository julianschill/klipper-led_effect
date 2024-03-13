import re
import zlib
import os
import argparse
from preview_generator import generate_preview
from preview_generator import markdown_regex

args = None

def replace_with_preview(match):
    content = match.group('block')
    layers = match.group('layers')
    output_dir = os.path.dirname(args.markdown.name)
    filename = os.path.join(output_dir, args.directory, "preview_" + str(zlib.crc32(layers.encode('utf-8')))+".gif")
    relative_filename = "./"+os.path.relpath(filename, os.path.dirname(args.markdown.name))
    # If file doesn't exist
    if not os.path.exists(filename):
        print("Generating "+filename)
        generate_preview(layers, args.fps, args.seconds, args.leds, args.diameter, args.margin, filename)
    else:
        print("Using existing "+filename)
    return """![Preview](%s)

%s""" % (relative_filename, content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                        prog='Preview-Generator',
                        description='Generates an animated image of a given layer')
    parser.add_argument('markdown', type=argparse.FileType('r'))
    parser.add_argument('--fps', default=24, type=int)
    parser.add_argument('--seconds', '-s', default=10, type=int)
    parser.add_argument('--directory', default=".", type=str)
    parser.add_argument('--diameter', '-d', default=50, type=int)
    parser.add_argument('--margin', '-m', default=5, type=int)
    parser.add_argument('--leds', '-l', default=10, type=int)
    args = parser.parse_args()
    
    if not os.path.exists(os.path.join(os.path.dirname(args.markdown.name), args.directory)):
        os.makedirs(os.path.join(os.path.dirname(args.markdown.name), args.directory))

    markdown = args.markdown.read()
    args.markdown.close()
    markdown = markdown_regex.sub(replace_with_preview, markdown)
    file = open(args.markdown.name, 'w')
    file.write(markdown)
    file.close()


    