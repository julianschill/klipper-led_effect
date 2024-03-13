import re
from . import markdown_regex

def test_with_one_lines():
    text = """
Long text

```layers
static
```
"""
    match = markdown_regex.search(text)
    assert match.groupdict() == {
        'block': '```layers\nstatic\n```',
        'layers': 'static'
    }

def test_with_two_lines():
    text = """
Long text

```layers
static
breathing
```
"""
    match = markdown_regex.search(text)
    assert match.groupdict() == {
        'block': '```layers\nstatic\nbreathing\n```', 
        'layers': 'static\nbreathing'
    }

def test_with_layers_on_extra_line_with_colon():
    text = """
Long text

```
layers:
  static
  breathing
```
"""
    match = markdown_regex.search(text)
    assert match.groupdict() == {
        'block': '```\nlayers:\n  static\n  breathing\n```', 
        'layers': '  static\n  breathing'
    }


def test_with_preceeding_preview_image():
    text = """
Long text

![Preview](./woop.png)

```
layers:
  static
  breathing
```
"""
    match = markdown_regex.search(text)
    assert match.group(0) == """![Preview](./woop.png)

```
layers:
  static
  breathing
```"""
    assert match.groupdict() == {
        'block': '```\nlayers:\n  static\n  breathing\n```', 
        'layers': '  static\n  breathing'
    }
