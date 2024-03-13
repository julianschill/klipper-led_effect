import re

markdown_regex = re.compile(r'(\!\[Preview\]\(.+?\)\n\n)?(?P<block>```(layers|\nlayers\:)\n(?P<layers>.*?)\n```)', re.DOTALL)