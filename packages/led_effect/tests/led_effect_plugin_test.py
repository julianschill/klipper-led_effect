import pytest
from klippermock import *

def test_parsing_basics_works():
    config = mockConfig()
    config.setint("ledcount", 10)
    config.set(
        "layers", "gradient 2 3 top (1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0) ")
    printer = mockPrinter(config)
    printer._handle_ready()
    layer = printer.led_effect.handler.effects[0].layers[0]

    assert layer.effectRate == 2
    assert layer.effectCutoff == 3
    assert layer.blendingMode == "top"
    assert layer.paletteColors == [1.0, 0.0, 0.0,
                                   0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]

def test_color_blending_colorspace_rgb_default():
    config = mockConfig()
    config.setint("ledcount", 3)
    config.set(
        "layers", """
            static 0 0 top (1, 0, 0), (0, 0, 1)
            """)
    printer = mockPrinter(config)
    printer._handle_ready()
    assert printer.led_effect.getFrame(0) == ([
        1.0, 0.0, 0.0, 0.0,
        0.5, 0.0, 0.5, 0.0,
        0.0, 0.0, 1.0, 0.0
    ], True)



def test_it_should_not_switch_off_leds_if_autostart_is_off():
    config = mockConfig()
    config.setint("ledcount", 1)
    config.setbool("autostart", False)
    config.set(
        "layers", """
            static 0 0 top (0.5, 0.5, 0.5, 0.5)
            """)
    printer = mockPrinter(config)
    printer.led_helper.led_state = [(1, 1, 1, 1)]
    printer._handle_ready()
    printer.led_effect.handler._getFrames(1)
    printer.led_effect.handler._getFrames(2)
    assert printer.led_helper.led_state == [(1, 1, 1, 1)]

def test_it_should_support_disabling_an_effect():
    config = mockConfig()
    config.setint("ledcount", 1)
    config.setbool("autostart", True)
    config.set(
        "layers", """
            static 0 0 top (0.5, 0.5, 0.5, 0.5)
            """)
    printer = mockPrinter(config)
    printer.led_helper.led_state = [(1, 1, 1, 1)]
    printer._handle_ready()
    [printer.led_effect.handler._getFrames(x) for x in range(0, 10)]
    assert printer.led_helper.led_state == [(0.5, 0.5, 0.5, 0.5)]
    printer.led_effect.set_enabled(False)
    assert printer.led_helper.led_state == [(0, 0, 0, 0)]
