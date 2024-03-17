def rgb_to_hsl(rgb):
    r, g, b = rgb
    r, g, b = r / 255.0, g / 255.0, b / 255.0

    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val-min_val

    if max_val == min_val:
        h = 0
    elif max_val == r:
        h = (60 * ((g-b)/diff) + 360) % 360
    elif max_val == g:
        h = (60 * ((b-r)/diff) + 120) % 360
    elif max_val == b:
        h = (60 * ((r-g)/diff) + 240) % 360

    l = (max_val + min_val) / 2

    if max_val == min_val:
        s = 0
    elif l <= 0.5:
        s = diff / (max_val + min_val)
    else:
        s = diff / (2 - max_val - min_val)

    return h, s, l


def hsl_to_rgb(hsl):
    h, s, l = hsl

    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c/2

    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    r, g, b = (r + m) * 255, (g + m) * 255, (b + m) * 255

    return round(r), round(g), round(b)
