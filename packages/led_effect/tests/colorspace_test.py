import pytest
from colormath.color_conversions import convert_color
from colormath.color_objects import (
    sRGBColor,
    LabColor,
    HSLColor
)
from hypothesis import given, settings, strategies as st
from hypothesis import assume as hypothesis_assume

from led_effect import color_conversions



@given(st.integers(0, 255), st.integers(0, 255), st.integers(0, 255))
@settings(max_examples=1000)
def test_rgb_to_hsl(r, g, b):
    rgb = (r, g, b)
    hsl = color_conversions.rgb_to_hsl(rgb)

    hsl_test = convert_color(sRGBColor(r/255, g/255, b/255), HSLColor)
    hsl_test = (hsl_test.hsl_h, hsl_test.hsl_s, hsl_test.hsl_l)
    assert hsl == pytest.approx(hsl_test)

    back_to_rgb = color_conversions.hsl_to_rgb(hsl)
    assert back_to_rgb == rgb