import pytest
from klippermock import *

NUM_FRAMES = 100

@pytest.mark.golden_test("golden/*.yml")
def test_led_effects_reference(golden):
    config = mockConfig()
    config.setint("ledcount", 10)
    config.set("layers",
        golden["input"])
    printer = mockPrinter(config)
    printer._handle_ready()

    frames = [ list(printer.led_effect.getFrame(i)) for i in range(NUM_FRAMES) ]
    assert frames == golden.out["output"]
