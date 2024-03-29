import pytest
from klippermock import *


def test_legacy_works():
    config = mockConfig()
    config.setint("ledcount", 10)
    config.set(
        "layers", "gradient 2 3 top (1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0) ")
    printer = mockPrinter(config)
    printer._handle_ready()
    layer = printer.led_effect.handler.effects[0].layers[0]

    assert layer.speed == 2
    assert layer.count == 3
    assert layer.blendingMode == "top"
    assert layer.paletteColors == [1.0, 0.0, 0.0,
                                   0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]


def test_new_params_work():
    config = mockConfig()
    config.setint("ledcount", 10)
    config.set(
        "layers", "gradient(speed=2, count=3) top (1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0,1.0) ")
    printer = mockPrinter(config)
    printer._handle_ready()
    layer = printer.led_effect.handler.effects[0].layers[0]

    assert layer.speed == 2
    assert layer.count == 3
    assert layer.blendingMode == "top"
    assert layer.paletteColors == [1.0, 0.0, 0.0,
                                   0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]


def test_missing_param_throws():
    config = mockConfig()
    config.setint("ledcount", 10)
    config.set(
        "layers", "gradient(count=3) top (1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0,1.0) ")
    with pytest.raises(Exception):
        printer = mockPrinter(config)
        printer._handle_ready()


def test_allow_layer_specific_heater():
    config = mockConfig()
    config.setint("ledcount", 1)
    config.set(
        "layers", """
            heater(minTemp=10,disableOnceReached=0,heater=heater_bed) add (1.0,0.0,0.0)
            heater(minTemp=10,disableOnceReached=0,heater=hotend) add (0,0.0,1.0)
            """)
    printer = mockPrinter(config)
    printer._handle_ready()
    printer.set_heater(None, 200, 100, "heater_bed")
    assert printer.led_effect.getFrame(0) == ([1.0, 0.0, 0.0, 0.0], True)
    printer.set_heater(None, 200, 100, "hotend")
    assert printer.led_effect.getFrame(1) == ([1.0, 0.0, 1.0, 0.0], True)


def test_color_blending_colorspace_rgb_default():
    config = mockConfig()
    config.setint("ledcount", 3)
    config.set(
        "layers", """
            static() top (1, 0, 0), (0, 0, 1)
            """)
    printer = mockPrinter(config)
    printer._handle_ready()
    assert printer.led_effect.getFrame(0) == ([
        1.0, 0.0, 0.0, 0.0,
        0.5, 0.0, 0.5, 0.0,
        0.0, 0.0, 1.0, 0.0
    ], True)


def test_color_blending_colorspace_hsl():
    config = mockConfig()
    config.setint("ledcount", 10)
    config.set(
        "layers", """
            static(colorSpace=hsl) top (1, 0, 0), (0, 0, 1)
            """)
    printer = mockPrinter(config)
    printer._handle_ready()
    assert printer.led_effect.getFrame(0) == (
        [1.0, 0.0, 0.0, 0.0, 1.0, 0.44313725490196076, 0.0, 0.0, 1.0, 0.8901960784313725, 0.0, 0.0, 0.6666666666666666, 1.0, 0.0, 0.0, 0.2235294117647059, 1.0, 0.0, 0.0, 0.0, 1.0, 0.2235294117647059, 0.0, 0.0, 1.0, 0.6666666666666666, 0.0, 0.0, 0.8901960784313725, 1.0, 0.0, 0.0, 0.44313725490196076, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0], True)


def test_color_blending_colorspace_none():
    config = mockConfig()
    config.setint("ledcount", 4)
    config.set(
        "layers", """
            static(colorSpace=none) top (1, 0, 0), (0, 0, 1)
            """)
    printer = mockPrinter(config)
    printer._handle_ready()
    assert printer.led_effect.getFrame(0) == ([
        1.0, 0.0, 0.0, 0.0,
        1.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 1.0, 0.0
    ], True)


def test_default_heater_gradient_length():
    config = mockConfig()
    config.setint("ledcount", 1)
    config.set(
        "layers", """
            heater(heater=heater_bed,minTemp=0,disableOnceReached=0) top (1, 0, 0),  (0, 0, 1), (0, 0, 1)
            """)
    printer = mockPrinter(config)
    printer._handle_ready()
    printer.set_heater(None, 100, 50, "heater_bed")
    assert printer.led_effect.getFrame(0) == ([
        0.4974874371859297, 0.0, 0.5025125628140703, 0.0
    ], True)


def test_changing_heater_gradient_length():
    config = mockConfig()
    config.setint("ledcount", 1)
    config.set(
        "layers", """
            heater(heater=heater_bed,minTemp=0,disableOnceReached=0,gradientSteps=3) top (1, 0, 0),  (0, 0, 1), (0, 0, 1)
            """)
    printer = mockPrinter(config)
    printer._handle_ready()
    printer.set_heater(None, 100, 50, "heater_bed")
    assert printer.led_effect.getFrame(0) == ([
        0.5, 0.0, 0.5, 0.0
    ], True)

def test_it_should_not_switch_off_leds_if_autostart_is_off():
    config = mockConfig()
    config.setint("ledcount", 1)
    config.setbool("autostart", False)
    config.set(
        "layers", """
            static() top (0.5, 0.5, 0.5, 0.5)
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
            static() top (0.5, 0.5, 0.5, 0.5)
            """)
    printer = mockPrinter(config)
    printer.led_helper.led_state = [(1, 1, 1, 1)]
    printer._handle_ready()
    [printer.led_effect.handler._getFrames(x) for x in range(0, 10)]
    assert printer.led_helper.led_state == [(0.5, 0.5, 0.5, 0.5)]
    printer.led_effect.set_enabled(False)
    assert printer.led_helper.led_state == [(0, 0, 0, 0)]
