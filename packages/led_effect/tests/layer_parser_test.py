import pytest
from led_effect import layer_parser

legacy_format_data = [
    ("breathing  .5 0 screen (0,.1,1), (0,1,.5), (0, 1,1), (0,.1,.5)", "breathing",
     0.5, 0, "screen", [(0, 0.1, 1), (0, 1, 0.5), (0, 1, 1), (0, 0.1, 0.5)]),
    ("breathing  .5 0 screen (0,.1,1,0.5), (0,1,.5), (0, 1,1), (0,.1,.5)", "breathing",
     0.5, 0, "screen", [(0, 0.1, 1, 0.5), (0, 1, 0.5), (0, 1, 1), (0, 0.1, 0.5)]),
    ("strobe         1  1.5   add        (1.0,  1.0, 1.0)",
     "strobe", 1, 1.5, "add", [(1, 1, 1)]),
    ("breathing      2  0     difference (0.95, 0.0, 0.0)",
     "breathing", 2, 0, "difference", [(0.95, 0, 0)]),
    ("static         1  0     top        (1.0,  0.0, 0.0)",
     "static", 1, 0, "top", [(1, 0, 0)]),
    ("static         1  0     top        #FF0000",
     "static", 1, 0, "top", [(1, 0, 0)]),
]

parameterized_line_format_data = [
    ("static()     top        (1.0,  0.0, 0.0)",
     "static", {}, "top", [(1, 0, 0)]),
    ("breathing(duration=.5) screen (0,.1,1), (0,1,.5), (0, 1,1), (0,.1,.5)", "breathing",
     {"duration": 0.5}, "screen", [(0, 0.1, 1), (0, 1, 0.5), (0, 1, 1), (0, 0.1, 0.5)]),
    ("breathing(duration=.5) screen (0,.1,1, 0.5), (0,1,.5), (0, 1,1), (0,.1,.5)", "breathing",
     {"duration": 0.5}, "screen", [(0, 0.1, 1, 0.5), (0, 1, 0.5), (0, 1, 1), (0, 0.1, 0.5)]),
    ("    strobe(frequency=1,decay=1.5)   add        (1.0,  1.0, 1.0)",
     "strobe", {"frequency": 1, "decay": 1.5}, "add", [(1, 1, 1)]),
    ("    strobe(frequency=1, decay=1.5)   add        (1.0,  1.0, 1.0)",
     "strobe", {"frequency": 1, "decay": 1.5}, "add", [(1, 1, 1)]),
    ("    heater(heater=heater_bed, decay=1.5)   add        (1.0,  1.0, 1.0)",
     "heater", {"heater": "heater_bed", "decay": 1.5}, "add", [(1, 1, 1)]),
    ("    heater(heater=heater_bed, decay=1.5)   add        #FFFFFF",
     "heater", {"heater": "heater_bed", "decay": 1.5}, "add", [(1, 1, 1)]),
    ("    heater(heater=heater_bed, decay=1.5)   add        $FFFFFF",
     "heater", {"heater": "heater_bed", "decay": 1.5}, "add", [(1, 1, 1)]),
]


@pytest.mark.parametrize("line,effect,rate,cutoff,blend,palette", legacy_format_data)
def test_parses_the_legacy_format(line, effect, rate, cutoff, blend, palette):
    assert layer_parser.parse(line) == {
        "effect": effect, "parameters": {"effectRate": rate, "effectCutoff": cutoff}, "blend": blend, "palette": palette}


@pytest.mark.parametrize("line,effect,parameters,blend,palette", parameterized_line_format_data)
def test_parses_the_parameterized_format(line, effect, parameters, blend, palette):
    assert layer_parser.parse(line) == {
        "effect": effect, "blend": blend, "palette": palette, "parameters": parameters}
