"""Optional extras: creatures, name tag, stats sign and streak effects."""
import math, random

import scene
from scene import blob, hexc, line_cells, mix

TAU = math.tau

# 3x5 pixel font, one string of 15 bits per character
FONT = dict(zip(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.!?",
    ("010101111101101 110101110101110 011100100100011 110101101101110 111100110100111 111100110100100 "
     "011100101101011 101101111101101 111010010010111 001001001101010 101101110101101 100100100100111 "
     "101111111101101 110101101101101 010101101101010 110101110100100 010101101110011 110101110101101 "
     "011100010001110 111010010010010 101101101101111 101101101101010 101101111111101 101101010101101 "
     "101101010010010 111001010100111 010101101101010 010110010010111 110001010100111 110001010001110 "
     "101101111001001 111100110001110 011100110101010 111001010010010 010101010101010 010101011001110 "
     "000000000000000 000000111000000 000000000000111 000000000000010 010010010000010 110001010000010").split()))


def clean(text, limit=16):
    return "".join(ch for ch in text.upper() if ch in FONT)[:limit].strip()


def width(text):
    return max(0, len(text) * 4 - 1)


def write(c, x, y, text, colour, shadow=None):
    for i, ch in enumerate(text):
        for k, bit in enumerate(FONT[ch]):
            if bit == "1":
                px, py = x + i * 4 + k % 3, y + k // 3
                if shadow:
                    c.put(px + 1, py + 1, shadow)
                c.put(px, py, colour)


def board(c, x0, y0, x1, y1):
    wood = [hexc(v) for v in ("#2a170c", "#5a371c", "#80522a", "#a97440")]
    cells = {}
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            cells[(x, y)] = wood[3] if y == y0 else wood[1] if y == y1 or (y - y0) % 5 == 4 else wood[2]
    c.sprite(cells, wood[0])


def nametag(c, name):
    """A hanging plank just under the water line."""
    text = clean(name)
    if not text:
        return
    w = width(text) + 8
    x0, y0 = scene.W // 2 - w // 2, 25
    for x in (x0 + 3, x0 + w - 3):
        for y in range(17, y0):
            c.put(x, y, hexc("#2a170c"))
    board(c, x0, y0, x0 + w, y0 + 10)
    write(c, x0 + 4, y0 + 3, text, hexc("#fff3d6"), hexc("#2a170c"))


def sign(c, total, streak):
    """A wooden stats sign planted in the gravel."""
    lines = [f"{min(total, 999999)} TOTAL", f"{min(streak, 9999)} DAY STREAK"]
    w = max(width(t) for t in lines) + 8
    x0 = min(scene.X(128), scene.W - w - 4)
    y1 = scene.Y(167)
    for y in range(y1, y1 + 9):
        for x in (x0 + w // 2 - 1, x0 + w // 2, x0 + w // 2 + 1):
            c.put(x, y, hexc("#5a371c"))
    board(c, x0, y1 - 17, x0 + w, y1)
    for i, text in enumerate(lines):
        write(c, x0 + (w - width(text)) // 2, y1 - 14 + i * 7, text, hexc("#fff3d6"), hexc("#2a170c"))


def snail(c, f):
    ph = TAU * f / scene.N
    x = scene.X(250) + int(round(7 * math.sin(ph)))
    y = scene.Y(171)
    skin = [hexc(v) for v in ("#3b2c1a", "#8d7448", "#c4a86c", "#ecd9a0")]
    shell = [hexc(v) for v in ("#3a1608", "#8e3a16", "#cf6a24", "#f6ae4e")]
    c.sprite({k: v for k, v in blob(x + 2, y + 2, 9, 2.6, skin, 2).items()}, skin[0])
    for dx in (8, 11):
        for k in range(5):
            c.put(x + dx, y - k, skin[1])
        c.put(x + dx, y - 5, hexc("#fff4d0"))
    c.sprite(blob(x - 2, y - 4, 7, 6, shell, 5), shell[0])
    for k in range(70):
        a = k * .22
        r = 5.2 - k * .07
        c.put(int(round(x - 2 + math.cos(a) * r)), int(round(y - 4 + math.sin(a) * r * .85)), shell[0])


def shrimp(c, f):
    ph = TAU * f / scene.N
    x = scene.X(98) + int(round(5 * math.sin(ph)))
    y = scene.Y(150) + int(round(3 * math.sin(ph * 3)))
    pal = [hexc(v) for v in ("#5c1410", "#b9362a", "#f06a4c", "#ffb49a")]
    for i in range(6):
        c.sprite(blob(x - i * 3, y + int((i - 2) ** 2 * .45), 3.2 - i * .25, 3 - i * .25, pal, i), pal[0])
    for k in range(10):
        c.put(x + 2 + k, y - 2 - k // 2 + int(round(math.sin(ph * 4 + k * .5))), pal[1])
        c.put(x + 2 + k, y - 1 + k // 5, pal[1])
    for i in range(4):
        step = int(round(math.sin(ph * 6 + i)))
        for k in range(3):
            c.put(x - i * 3 + step, y + 3 + k, pal[1])
    c.put(x + 2, y - 1, (10, 10, 20))


def turtle(c, f):
    ph = TAU * f / scene.N
    facing = 1 if math.cos(ph) >= 0 else -1
    x = scene.X(92) + int(round(scene.X(34) * math.sin(ph)))
    y = 48 + int(round(4 * math.sin(ph * 2)))
    skin = [hexc(v) for v in ("#0f2e1b", "#2f6b34", "#57a04a", "#a5d676")]
    shell = [hexc(v) for v in ("#23170a", "#5c4318", "#90702a", "#cfa94a")]
    flap = math.sin(ph * 6) * 4
    for sx, sy, d in ((6, 4, 1), (-8, 4, -.6)):
        cells = {}
        line_cells(cells, [(x + sx * facing, y + sy), (x + (sx - 4) * facing, y + sy + 6 + flap * d)],
                   lambda t: 2.2 - t * 1.4, lambda *a: skin[2])
        c.sprite(cells, skin[0])
    c.sprite(blob(x + 15 * facing, y - 1, 5, 4, skin, 3), skin[0])
    c.sprite({k: v for k, v in blob(x, y, 12, 9, shell, 8).items() if k[1] <= y + 3}, shell[0])
    for dx, dy in ((-5, -3), (1, -5), (6, -2), (-1, 0)):
        c.sprite(blob(x + dx, y + dy, 2.5, 2, shell, dx), shell[0])
    for dx in range(-11, 12):
        c.put(x + dx, y + 4, skin[3])
    c.put(x + 17 * facing, y - 2, (10, 10, 20))
    c.put(x - 13 * facing, y + 3, skin[2])


def jellyfish(c, f):
    ph = TAU * f / scene.N
    x = scene.X(214) + int(round(6 * math.sin(ph)))
    y = 52 + int(round(8 * math.sin(ph * 2)))
    pulse = math.sin(ph * 4)
    rx, ry = 9 + pulse * 1.5, 8 - pulse
    pal = [hexc(v) for v in ("#5b2a86", "#9b5fd0", "#d79bf0", "#ffe3ff")]
    for i in range(-2, 3):
        for k in range(16):
            tx = int(round(x + i * 3.2 + 2 * math.sin(ph * 4 - k * .45 + i)))
            c.put(tx, y + 2 + k, mix(pal[2], c.px[max(0, min(scene.W - 1, tx)), max(0, min(scene.H - 1, y + 2 + k))], k / 20))
    bell = {k: v for k, v in blob(x, y, rx, ry, pal, 1).items() if k[1] <= y + 1}
    c.sprite({(px, py): v for (px, py), v in bell.items() if (px + py) % 2 or py < y - ry * .45}, pal[0])


CREATURES = {"snail": (snail, 100), "shrimp": (shrimp, 250), "turtle": (turtle, 750), "jellyfish": (jellyfish, 1500)}


def sparkles(c, f, spot, count, colour):
    """Twinkles that travel with the koi, for streak rewards."""
    cx, cy, length, half = spot
    rnd = random.Random(21)
    for _ in range(count):
        dx, dy = rnd.uniform(-.62, .62) * length, rnd.uniform(-2.0, 2.0) * half
        beat = math.sin(TAU * f / scene.N * rnd.choice([2, 3, 4]) + rnd.random() * TAU)
        if beat > .35:
            x, y = int(cx + dx), int(cy + dy)
            c.put(x, y, colour)
            if beat > .8:
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    c.put(x + ox, y + oy, colour)


def aura(c, spot, colour):
    """A dithered halo drawn behind the koi."""
    cx, cy, length, half = spot
    rx, ry = length * .68, half * 2.2
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if 0 <= x < scene.W and 0 <= y < scene.H:
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d < 1 and scene.BAYER[y % 4][x % 4] < (1 - d) * 11:
                    c.px[x, y] = mix(c.px[x, y], colour, .45)
