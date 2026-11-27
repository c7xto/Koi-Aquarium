"""Drawing code: scenery and koi on one pixel grid. Designed on 320x180 and adapted to other sizes."""
import math, random
from PIL import Image, ImageDraw

W, H, SCALE, N = 320, 180, 3, 96
SIZES = {"wide": (320, 180), "banner": (420, 140), "square": (200, 200)}


def resize(name):
    global W, H
    W, H = SIZES[name]


def X(x):
    """A design x position (0..320) on the current canvas."""
    return int(round(x * W / 320))


def Y(y):
    """A design y position that stays anchored to the floor."""
    return y + H - 180


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
TAU = math.tau


def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def dith(x, y, t, n):
    """Pick an index 0..n-1 for t in 0..1 with ordered dithering."""
    v = max(0, min(.999, t)) * (n - 1)
    i = int(v)
    return min(n - 1, i + (1 if (v - i) * 16 > BAYER[y % 4][x % 4] + .5 else 0))


THEMES = {
    "planted": dict(water=["#2b8f9e", "#1f7488", "#175a72", "#10425a", "#0b2d42"],
                      gravel=["#0b0c10", "#17191f", "#272a33", "#454a57"],
                      leaf=["#0f3d2a", "#1e6b3c", "#37a04e", "#86d368"], leaf2=["#4a1230", "#8e1f4e", "#d63f6c", "#ff8fa8"],
                      rock=["#1c2229", "#343d47", "#55616d", "#8793a0"],
                      blooms=["#ff6fb0", "#ffd23f", "#b57bff", "#ff8a3d", "#f4f4ff"],
                      koi=("#f4f1ea", "#f05a23", "#23242c"), night=False, extra="wood"),
    "japanese": dict(water=["#63b9c4", "#3f95ad", "#2b7292", "#1d5276", "#133657"],
                       gravel=["#0a0a0c", "#19181c", "#2c2a2f", "#4d494e"],
                       leaf=["#123f33", "#1f6e4f", "#3aa66b", "#9adf8a"], leaf2=["#5a2010", "#a8431a", "#e8772b", "#ffb85c"],
                       rock=["#23262b", "#41474c", "#697177", "#a2abad"],
                       blooms=["#ff8fc0", "#ffffff", "#ff5470", "#ffc43d", "#d9a2ff"],
                       koi=("#f7f4ee", "#d9262e", "#1d1d24"), night=False, extra="lantern"),
    "night": dict(water=["#15305c", "#10244a", "#0b1a38", "#071128", "#040a1a"],
                    gravel=["#050508", "#0e0f16", "#1b1d29", "#34384c"],
                    leaf=["#0a2b35", "#10585c", "#18a393", "#7dfbd0"], leaf2=["#23104a", "#4b2393", "#8a4fe0", "#d6a2ff"],
                    rock=["#0f1424", "#1f2942", "#344366", "#5d71a0"],
                    blooms=["#ff5fd2", "#5ff2ff", "#fff27a", "#c79bff", "#ff8a8a"],
                      koi=("#ffe9a8", "#f5a623", "#7a3d0a"), night=True, extra="wood"),
    "sunset": dict(water=["#f2a26b", "#c96f7c", "#8a4d83", "#523673", "#2c2352"],
                   gravel=["#0d090e", "#1d151f", "#312433", "#57435a"],
                   leaf=["#14342f", "#235c4c", "#3f8f6a", "#a2d49a"], leaf2=["#5c1830", "#a52c48", "#ee5d5d", "#ffab8a"],
                   rock=["#2a1f33", "#493752", "#6c5575", "#a48aa8"],
                   blooms=["#ff5d8f", "#ffe066", "#ff8c42", "#c77dff", "#ffd1dc"],
                   koi=("#fff4e0", "#ff7a1a", "#3a1c2c"), night=False, extra="wood"),
    "reef": dict(water=["#35c3cf", "#1c9fc0", "#1478a8", "#0f568a", "#0b3a68"],
                 gravel=["#2a1f1a", "#4a382c", "#6e5641", "#a08664"],
                 leaf=["#5c1d3a", "#a8335c", "#ee5a7e", "#ffa6b4"], leaf2=["#5a3206", "#a8640e", "#f09a1f", "#ffd067"],
                 rock=["#232b3f", "#3b4a66", "#5a7090", "#8fa8c4"],
                 blooms=["#ff6f91", "#ffc75f", "#c34fd6", "#4ff0c0", "#ffffff"],
                 koi=("#ffffff", "#ff8a1f", "#15161c"), night=False, extra="coral"),
    "dark": dict(water=["#1a1f29", "#151a23", "#11151d", "#0d1117", "#0d1117"],
                 gravel=["#06070a", "#101218", "#1e212a", "#3a3f4d"],
                 leaf=["#0d2a1f", "#17503a", "#2b7a57", "#6fbf8f"], leaf2=["#2b1630", "#4f2a58", "#7d4689", "#bd86c9"],
                 rock=["#161a22", "#272d39", "#3c4453", "#677183"],
                 blooms=["#e56b9f", "#e8c15a", "#9a7ad6", "#e08a54", "#e6e8f0"],
                 koi=("#f4f1ea", "#f05a23", "#23242c"), night=False, extra="wood"),
}


class Canvas:
    def __init__(s):
        s.im = Image.new("RGB", (W, H))
        s.px = s.im.load()

    def put(s, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            s.px[x, y] = c

    def sprite(s, cells, outline=None):
        if outline:
            for (x, y) in cells:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (x + dx, y + dy) not in cells:
                        s.put(x + dx, y + dy, outline)
        for (x, y), c in cells.items():
            s.put(x, y, c)


def blob(cx, cy, rx, ry, pal, seed=0, flat_bottom=False):
    cells = {}
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            a = math.atan2(y - cy, x - cx)
            wob = 1 + .09 * math.sin(3 * a + seed) + .06 * math.sin(5 * a + seed * 2)
            u, v = (x - cx) / (rx * wob), (y - cy) / (ry * wob)
            if u * u + v * v <= 1 and not (flat_bottom and y > cy + ry * .55):
                light = .55 - .5 * v - .28 * u + .08 * math.sin(x * .9 + seed) * math.sin(y * 1.1)
                cells[(x, y)] = pal[dith(x, y, light, len(pal))]
    return cells


def line_cells(cells, pts, width, colour_at):
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for k in range(steps + 1):
            t = k / steps
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            f = (i + t) / (len(pts) - 1)
            w = width(f)
            for dx in range(-int(w), int(w) + 1):
                cells[(int(round(x)) + dx, int(round(y)))] = colour_at(f, dx, w)


def grass(c, th, x, base, height, n, phase, pal, dim=0):
    rnd = random.Random(x * 7 + n)
    for _ in range(n):
        h, lean = height * rnd.uniform(.55, 1), rnd.uniform(-14, 14)
        x0, off = x + rnd.randint(-9, 9), rnd.random() * TAU
        pts = [(x0 + lean * f * f + 3.4 * f * math.sin(phase + off - f * 2.2), base - h * f) for f in [j / 9 for j in range(10)]]
        cells = {}
        shade = rnd.choice([1, 2, 2])
        line_cells(cells, pts, lambda f: 1.6 * (1 - f) + .2,
                   lambda f, dx, w: pal[3] if f > .86 else pal[max(0, shade - 1)] if dx < 0 else pal[shade])
        if dim:
            cells = {k: mix(v, hexc(th["water"][3]), dim) for k, v in cells.items()}
        c.sprite(cells, mix(pal[0], hexc(th["water"][4]), .5))


def broadleaf(c, th, x, base, stems, phase, pal):
    rnd = random.Random(x)
    for _ in range(stems):
        h, lean, off = rnd.uniform(22, 62), rnd.uniform(-22, 22), rnd.random() * TAU
        tip = (x + lean + 2.5 * math.sin(phase + off), base - h)
        stem = {}
        line_cells(stem, [(x, base), (x + lean * .35, base - h * .6), tip], lambda f: 0, lambda *a: pal[1])
        c.sprite(stem)
        rx, ry = rnd.uniform(5, 9), rnd.uniform(3, 5)
        leaf = {}
        for (px, py), col in blob(tip[0], tip[1], rx, ry, pal, off).items():
            leaf[(px, py)] = pal[3] if abs((py - tip[1]) - (px - tip[0]) * .12) < .6 else col
        c.sprite(leaf, pal[0])


def flower(c, x, y, colour, size, phase):
    col = hexc(colour)
    pal = [mix(col, (20, 10, 40), .45), mix(col, (20, 10, 40), .18), col, mix(col, (255, 255, 255), .55)]
    y += int(round(math.sin(phase)))
    for ang, ln in ((-155, .8), (-25, .8), (-130, 1), (-50, 1), (-108, 1.12), (-72, 1.12), (-90, 1.2)):
        a = math.radians(ang)
        L = size * ln
        mx, my = x + math.cos(a) * L * .5, y + math.sin(a) * L * .5
        petal = {}
        for py in range(int(y - L) - 2, y + 3):
            for px in range(int(x - L) - 2, int(x + L) + 3):
                u = (px - mx) * math.cos(a) + (py - my) * math.sin(a)
                v = -(px - mx) * math.sin(a) + (py - my) * math.cos(a)
                if (u / (L * .55)) ** 2 + (v / (size * .24)) ** 2 <= 1:
                    petal[(px, py)] = pal[dith(px, py, .35 + .65 * (u / L + .5), 4)]
        c.sprite(petal, pal[0])
    c.sprite(blob(x, y - 1, size * .28, size * .18, [hexc("#b86a00"), hexc("#f2a900"), hexc("#ffd84a"), hexc("#fff3a6")]))


def background(c, th, f, plants=True):
    ph = TAU * f / N
    water = [hexc(x) for x in th["water"]]
    for y in range(H):
        for x in range(W):
            c.px[x, y] = water[dith(x, y, y / (H - 30), len(water))]
    for i, (x0, wid) in enumerate([(X(52), 13), (X(128), 8), (X(214), 17), (X(282), 7)]):  # light shafts
        sway = 5 * math.sin(ph + i * 1.7)
        for y in range(18, H - 40):
            left = int(x0 + sway * (y / (H - 40)) - y * .22)
            strength = (1 - y / (H - 40)) * (7 if not th["night"] else 5)
            for x in range(left, left + wid + y // 14):
                if 0 <= x < W and BAYER[y % 4][x % 4] < strength:
                    c.put(x, y, mix(c.px[x, y], (200, 240, 255), .2))
    deep = water[3]
    for cx, cy, rx, ry in [(40, 142, 46, 30), (250, 146, 60, 34), (310, 138, 30, 24), (150, 152, 34, 16)]:
        c.sprite({k: mix(v, deep, .68) for k, v in blob(X(cx), Y(cy), rx, ry, [hexc(x) for x in th["rock"]], cx).items()})
    for x, h in [(20, 70), (98, 52), (190, 64), (232, 45), (300, 86)] if plants else []:
        grass(c, th, X(x), Y(148), min(h, H - 60), 7, ph, [hexc(v) for v in th["leaf"]], dim=.58)


def gravel(c, th):
    g = [hexc(x) for x in th["gravel"]]

    def top(x):
        return Y(146) + 4 * math.sin(x * .025 + 1) + 2 * math.sin(x * .081)

    for x in range(W):
        for y in range(int(top(x)), H):
            c.px[x, y] = g[1] if BAYER[y % 4][x % 4] < 7 else g[0]
    rnd = random.Random(11)
    for row in range(Y(150), H + 3, 3):
        r = 1.2 + (row - Y(146)) / 34 * 1.9
        x = rnd.uniform(-3, 3)
        while x < W + 3:
            yy = row + rnd.uniform(-1.5, 1.5)
            if yy > top(max(0, min(W - 1, int(x)))) + 1:
                pal = g
                if rnd.random() < .05:
                    bloom = hexc(rnd.choice(th["blooms"]))
                    pal = [g[0]] + [mix(bloom, g[1], t) for t in (.75, .6, .45)]
                c.sprite(blob(x, yy, r * rnd.uniform(.8, 1.3), r * .75, pal, x), g[0])
            x += r * 1.75


def decor(c, th):
    dx, dy = X(230) - 230, H - 180
    rock = [hexc(x) for x in th["rock"]]
    if th["extra"] == "wood":
        wood = [hexc(x) for x in ("#1e120c", "#3a2314", "#5c3a1f", "#8a5c30")]
        if th["night"]:
            wood = [mix(w, (20, 30, 80), .45) for w in wood]
        cells = {}
        for pts, wd in [([(188, 160), (206, 142), (222, 128), (236, 108), (252, 98)], 5), ([(214, 136), (204, 118), (190, 108)], 3),
                        ([(234, 112), (232, 92), (240, 80)], 2.4), ([(206, 142), (240, 146), (272, 156)], 4)]:
            line_cells(cells, [(x + dx, y + dy) for x, y in pts], lambda t, wd=wd: wd * (1 - .75 * t) + .4,
                       lambda t, dx, w: wood[3] if dx <= -w + 1 else wood[2] if dx < 1 else wood[1])
        c.sprite(cells, wood[0])
    elif th["extra"] == "coral":
        coral(c, th, X(232), Y(160))
    else:
        stone = [mix(r, (190, 190, 175), .22) for r in rock]

        def slab(x0, y0, x1, y1):
            x0, x1, y0, y1 = x0 + dx, x1 + dx, y0 + dy, y1 + dy
            cells = {}
            for x in range(x0, x1 + 1):
                for y in range(y0, y1 + 1):
                    light = .85 - (x - x0) / (x1 - x0 + 1) * .55 - (.25 if y == y1 else 0) + (.1 if y == y0 else 0)
                    cells[(x, y)] = stone[dith(x, y, light, 4)]
            c.sprite(cells, stone[0])

        slab(228, 150, 262, 156)
        slab(240, 126, 250, 149)
        slab(232, 120, 258, 125)
        slab(235, 102, 255, 119)
        for i in range(8):
            slab(226 + i * 2, 100 - i * 2, 264 - i * 2, 101 - i * 2)
        slab(243, 80, 247, 85)
        for y in range(106, 116):
            for x in range(241, 250):
                c.put(x + dx, y + dy, hexc("#ffcf5a") if x != 245 else stone[1])


def coral(c, th, x, base):
    def branch(x0, y0, angle, length, width, pal, depth):
        x1, y1 = x0 + math.cos(angle) * length, y0 + math.sin(angle) * length
        cells = {}
        line_cells(cells, [(x0, y0), (x1, y1)], lambda t: width * (1 - .4 * t),
                   lambda t, d, w: pal[2] if d < 1 else pal[1])
        c.sprite(cells, pal[0])
        if depth:
            branch(x1, y1, angle - .55, length * .75, width * .68, pal, depth - 1)
            branch(x1, y1, angle + .5, length * .72, width * .68, pal, depth - 1)
        else:
            c.sprite(blob(x1, y1, 2.4, 2.4, pal, int(x1)), pal[0])

    warm = [hexc(v) for v in th["leaf"]]
    gold = [hexc(v) for v in th["leaf2"]]
    branch(x, base, -1.57, 22, 3.6, warm, 3)
    branch(x + 30, base, -1.35, 16, 3, gold, 2)
    branch(x - 28, base + 4, -1.8, 13, 2.6, gold, 2)


def rocks(c, th):
    rock = [hexc(x) for x in th["rock"]]
    for cx, cy, rx, ry, s in [(58, 154, 26, 17, 1), (84, 160, 15, 10, 4), (36, 162, 14, 9, 7), (280, 158, 22, 14, 2), (160, 168, 13, 8, 5)]:
        c.sprite(blob(X(cx), Y(cy), rx, ry, rock, s, True), mix(rock[0], (0, 0, 0), .5))


def surface(c, th, f, flowers=True):
    ph = TAU * f / N
    light = mix(hexc(th["water"][0]), (255, 255, 255), .6 if not th["night"] else .3)
    sky = mix(hexc(th["water"][0]), (255, 255, 255), .25 if not th["night"] else .05)
    for x in range(W):
        y = int(round(17 + 1.4 * math.sin(x * .11 + ph * 2) + .8 * math.sin(x * .047 - ph)))
        for yy in range(0, y):
            c.put(x, yy, sky if BAYER[yy % 4][x % 4] > 2 else light)
        c.put(x, y, light)
        if (x + f // 3) % 7 < 4:
            c.put(x, y + 2, mix(light, hexc(th["water"][0]), .6))
    leaf = [hexc(v) for v in th["leaf"]]
    for i, (x, rx) in enumerate([(X(30), 18), (X(63), 12), (X(262), 19), (X(298), 13)] if flowers else []):
        bob = int(round(math.sin(ph + i * 1.9)))
        root = {}
        line_cells(root, [(x, 20 + bob), (x + 3 * math.sin(ph + i), 38), (x - 4 + 5 * math.sin(ph + i + 1), 58 + i * 5)],
                   lambda t: 0, lambda *a: leaf[1])
        c.sprite(root)
        pad = {k: v for k, v in blob(x, 17 + bob, rx, 4, leaf, i).items() if not (k[0] > x + rx * .45 and k[1] < 17 + bob)}
        c.sprite(pad, leaf[0])
    for i, (x, s) in enumerate([(X(30), 10), (X(262), 11), (X(298), 7)] if flowers else []):
        flower(c, x - 4, 16 + int(round(math.sin(ph + i * 1.9))), th["blooms"][(0, 2, 3)[i]], s, ph + i)


def koi(c, th, f, theta, length, base_y, look=None):
    """Side view with a little depth: theta walks an oval, front half toward the viewer."""
    ph = TAU * f / N
    facing = 1 if math.cos(theta) >= 0 else -1
    squash = max(.34, abs(math.cos(theta)) ** .6)
    depth = math.cos(theta)
    L = length * (1 + .2 * depth)
    look = look or {}
    swing = 112 * W / 320 if W >= 320 else W / 2 - 44
    cx = W / 2 - 2 + swing * math.sin(theta)
    cy = base_y + 14 * depth + 5 * math.sin(theta * 2)
    white, patch, dark = [hexc(x) for x in look.get("colors") or th["koi"]]
    fin_white = hexc("#ffd34d") if look.get("gold_fins") else white
    flow = look.get("fins", 1.0)
    haze = max(0, -depth) * .42
    far = hexc(th["water"][3])

    def tone(col, lvl):
        col = (mix(col, (14, 12, 46), .52), mix(col, (30, 24, 70), .24), col, mix(col, (255, 255, 255), .5))[lvl]
        return mix(col, far, haze)

    rnd = random.Random(5)
    spots = [(rnd.uniform(.06, .9), rnd.uniform(-1, .45), rnd.uniform(.07, .17), rnd.uniform(.35, .8), patch) for _ in range(6)]
    spots += [(rnd.uniform(.3, .8), rnd.uniform(-1, -.55), rnd.uniform(.022, .04), rnd.uniform(.13, .22), dark) for _ in range(5)]
    Hh = L * .19

    def bend(u):
        return L * .075 * (max(0, u) ** 1.7) * math.sin(ph * 6 - u * 4.2)

    keys = [(0, .14), (.03, .40), (.08, .62), (.17, .86), (.30, 1.0), (.45, .97), (.60, .78), (.74, .52), (.86, .31), (.94, .24), (1, .25)]

    def prof(u):
        for (u0, r0), (u1, r1) in zip(keys, keys[1:]):
            if u0 <= u <= u1:
                return Hh * (r0 + (r1 - r0) * (u - u0) / (u1 - u0))
        return 0

    def world(u, v):
        return (cx + facing * squash * (L * (.46 - u)), cy + bend(u) + v)

    def fin(points, col, lvl=2):
        poly = [world(u, v) for u, v in points]
        m = Image.new("1", (W, H), 0)
        ImageDraw.Draw(m).polygon(poly, fill=1)
        box = m.getbbox()
        if not box:
            return
        mp = m.load()
        cells = {}
        for y in range(box[1], box[3]):
            for x in range(box[0], box[2]):
                if mp[x, y]:
                    ray = (x * facing + y * 2) % 4 == 0
                    cells[(x, y)] = tone(col, 3 if ray else lvl if (x + y) % 2 else max(1, lvl - 1))
        c.sprite(cells, tone(col, 0))

    wag = math.sin(ph * 6 - 5.2) * Hh * .35
    tail = [(.94, -.22, 0), (1.01, -.55, .3), (1.09, -.98, .7), (1.18, -1.2, 1), (1.27, -1.18, 1.1), (1.22, -.86, 1), (1.16, -.45, .9),
            (1.13, 0, .8), (1.16, .45, .9), (1.21, .82, 1), (1.25, 1.1, 1.1), (1.16, 1.12, 1), (1.07, .88, .7), (1.0, .52, .3), (.94, .22, 0)]
    fin([(.94 + (u - .94) * flow, v * Hh * (1 + (flow - 1) * .5) + wag * w) for u, v, w in tail], fin_white)
    fin([(.28, Hh * .5), (.36, Hh * 1.22), (.44, Hh * 1.38), (.45, Hh * .9)], fin_white, 1)
    fin([(.27, -prof(.27) + 1), (.33, -prof(.33) - Hh * .45), (.40, -prof(.40) - Hh * .58), (.52, -prof(.52) - Hh * .46),
         (.64, -prof(.64) - Hh * .34), (.73, -prof(.73) - Hh * .10), (.72, -prof(.72) + 2), (.5, -prof(.5) + 2)], patch)
    fin([(.66, prof(.66) - 1), (.72, prof(.72) + Hh * .42), (.80, prof(.80) + Hh * .48), (.81, prof(.81) - 1)], fin_white, 1)

    body = {}
    steps = int(L * squash * 2) + 4
    for i in range(steps + 1):
        u = i / steps
        r = prof(u)
        xw, yw = world(u, 0)
        x = int(round(xw))
        for y in range(int(round(yw - r)), int(round(yw + r)) + 1):
            v = (y - yw) / max(r, .1)
            col = white
            for su, sv, ru, rv, sc in spots:
                if ((u - su) / ru) ** 2 + ((v - sv) / rv) ** 2 <= 1 + .35 * math.sin(u * 40 + v * 7):
                    col = sc
            light = .66 - .30 * v - .42 * max(0, abs(v + .25) - .45) + (.30 if -.62 < v < -.38 and .1 < u < .8 else 0)
            lvl = dith(x, y, light, 4)
            gx, gy = int(u * L), int(round(y - yw))
            if .26 < u < .88 and abs(v) < .72 and gy % 3 == 0 and (gx + (gy // 3) * 2) % 4 == 0:
                lvl = max(0, lvl - 1)  # scales
            if abs(u - .23 - .035 * (1 - v * v)) < .012 and abs(v) < .75:
                lvl = max(0, lvl - 1)  # gill
            body[(x, y)] = tone(col, lvl)
    c.sprite(body, mix(hexc("#0c0a1e"), far, haze))

    flap = math.sin(ph * 4) * Hh * .22
    fin([(.23, Hh * .30), (.29, Hh * .92 + flap), (.37, Hh * 1.18 + flap), (.42, Hh * 1.02 + flap), (.37, Hh * .62), (.30, Hh * .28)], fin_white)
    ex, ey = [int(round(v)) for v in world(.1, -Hh * .2)]
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            c.put(ex + dx, ey + dy, mix(hexc("#ffd36b"), far, haze))
    for dx, dy in ((0, 0), (facing, 0), (0, 1), (facing, 1)):
        c.put(ex + dx, ey + dy, hexc("#0a0a14"))
    c.put(ex, ey, (255, 255, 255))
    if look.get("dragon"):
        for sx in (.13, .21):
            for k in range(int(Hh * .9)):
                hx, hy = world(sx + k * .006, -prof(sx) - k * .8 + 2)
                for d in range(2):
                    c.put(int(round(hx)) + d, int(round(hy)), mix(hexc("#ffd34d"), far, haze))
    for k in range(int(5 * look.get("whiskers", 1))):
        bx, by = world(-.005 - k * .008, Hh * .2 + k * 1.1 + math.sin(ph * 3 + k * .6) * .6)
        c.put(int(round(bx)), int(round(by)), tone(white, 1))
    mx, my = world(.012, Hh * .12)
    c.put(int(round(mx)), int(round(my)), tone(dark, 0))
    return cx, cy, squash * L, Hh


def bubbles(c, th, f, rising=True):
    rnd = random.Random(3)
    for i in range(20 if rising else 0):
        x0 = X(rnd.choice([84, 172, 288])) + rnd.randint(-3, 3)
        start, r = rnd.random(), rnd.choice([1, 1, 1, 2])
        t = (f / N * 2 + start) % 1
        y, x = int(Y(150) - t * (Y(150) - 22)), int(x0 + 3 * math.sin(t * 14 + i))
        light = mix(c.px[max(0, min(W - 1, x)), max(0, min(H - 1, y))], (255, 255, 255), .55)
        for dx, dy in ([(0, -r), (r, 0), (0, r), (-r, 0)] if r > 1 else [(0, 0), (1, 0)]):
            c.put(x + dx, y + dy, light)
        if r > 1:
            c.put(x - 1, y - 1, (255, 255, 255))
    if th["night"]:
        for i in range(34):
            x, y = rnd.randrange(8, W - 8), rnd.randrange(22, H - 40)
            b = math.sin(TAU * f / N * rnd.choice([1, 2, 3]) + rnd.random() * TAU)
            if b > .2:
                x += int(round(3 * math.sin(TAU * f / N + i)))
                col = hexc(th["blooms"][i % 3])
                c.put(x, y, col)
                if b > .8:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        c.put(x + dx, y + dy, mix(col, c.px[x, y + 3], .55))
