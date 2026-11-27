"""Pixel-art koi aquarium for a GitHub profile README, drawn from GitHub activity.

Preview without GitHub:   python aquarium.py --total 600 --streak 8 --out preview.gif
Draw from real activity:  GH_TOKEN=... python aquarium.py --login octocat --out aquarium.gif
"""
import argparse, datetime, json, math, os, pathlib, re, urllib.request

from PIL import Image

import extras
import scene

TAU = math.tau

COLORS = {
    "kohaku": ("#f7f4ee", "#d9262e", "#1d1d24"),
    "orange": ("#f4f1ea", "#f05a23", "#23242c"),
    "gold": ("#ffe9a8", "#f5a623", "#7a3d0a"),
    "black": ("#4a4d58", "#17181f", "#f08c2e"),
    "blue": ("#eef5ff", "#2f7fd6", "#14233f"),
    "platinum": ("#f6f8fb", "#c3ccd8", "#7c8799"),
    "sakura": ("#fff5f7", "#ff8fb3", "#7a2d4c"),
}
HIDEABLE = ("decor", "rocks", "plants", "flowers", "bubbles")
STAGES = ((50, "fry"), (250, "young"), (1000, "adult"), (5000, "elder"), (10 ** 12, "dragon"))


# ---------------------------------------------------------------- settings

def words(text):
    return [w for w in re.split(r"[,\s]+", (text or "").strip().lower()) if w]


def parse_colors(text):
    """A preset name, 'languages', or one to three hex colours: body, markings, spots."""
    text = (text or "").strip().lower()
    if not text or text == "languages":
        return text or None
    if text in COLORS:
        return COLORS[text]
    found = words(text)
    if not 1 <= len(found) <= 3 or not all(re.fullmatch(r"#[0-9a-f]{6}", w) for w in found):
        raise SystemExit(f"colors: use one of {', '.join(COLORS)}, 'languages', or up to three #rrggbb values")
    return tuple(found + list(COLORS["orange"][len(found):]))


def parse_numbers(text, name):
    try:
        return sorted(int(w) for w in words(text))
    except ValueError:
        raise SystemExit(f"{name}: expected numbers such as 500,2000")


def parse_choice(text, allowed, name):
    found = words(text)
    unknown = [w for w in found if w not in allowed and w not in ("none", "all", "auto")]
    if unknown:
        raise SystemExit(f"{name}: unknown value {unknown[0]!r}. Choose from {', '.join(allowed)}")
    return found


def creature_list(text, total):
    found = parse_choice(text, list(extras.CREATURES), "creatures")
    if "all" in found:
        return list(extras.CREATURES)
    if "auto" in found:
        return [n for n, (_, needed) in extras.CREATURES.items() if total >= needed]
    return [w for w in found if w in extras.CREATURES]


def stage_for(total):
    return next(name for limit, name in STAGES if total < limit)


def state(options, total, yesterday, streak, languages):
    """Turn activity and settings into everything the picture needs."""
    length = round(min(92, 44 + 12 * math.log10(1 + total)))
    milestones = parse_numbers(options.milestones, "milestones")
    fish = min(5, max(1, options.max_fish), 1 + sum(total >= m for m in milestones))
    look = {}
    colors = parse_colors(options.colors)
    if colors == "languages":
        top = (list(languages) + [None, None])[:2]
        colors = ("#f4f1ea", top[0] or "#f05a23", top[1] or "#23242c")
    if colors:
        look["colors"] = colors
    stage = stage_for(total) if options.evolution else None
    if stage:
        length, extra = {"fry": (40, {"fins": .75, "whiskers": .4}), "young": (60, {}), "adult": (74, {}),
                         "elder": (82, {"fins": 1.35, "whiskers": 2}),
                         "dragon": (88, {"fins": 1.45, "whiskers": 3.5, "dragon": True, "gold_fins": True})}[stage]
        look.update(extra)
    reward = 0
    if options.streak_rewards:
        reward = 3 if streak >= 30 else 2 if streak >= 7 else 1 if streak >= 3 else 0
        if reward >= 2:
            look["gold_fins"] = True
    length = round(length * {"wide": 1, "banner": .8, "square": .85}[options.size])
    hidden = parse_choice(options.hide, HIDEABLE, "hide")
    return dict(length=length, fish=fish, look=look, reward=reward, stage=stage,
                ms=options.speed or (80 if yesterday > 0 else 130),
                hidden=set(HIDEABLE if "all" in hidden else hidden),
                creatures=creature_list(options.creatures, total),
                name=options.name, sign=(total, streak) if options.sign else None)


# ---------------------------------------------------------------- drawing

def frame(th, f, s):
    c = scene.Canvas.__new__(scene.Canvas)
    c.im = Image.new("RGB", (scene.W, scene.H))
    c.px = c.im.load()
    X, Y, ph = scene.X, scene.Y, TAU * f / scene.N
    theta = ph - .35
    hidden = s["hidden"]
    leaf = [scene.hexc(v) for v in th["leaf"]]
    leaf2 = [scene.hexc(v) for v in th["leaf2"]]
    plants, flowers = "plants" not in hidden, "flowers" not in hidden
    tall = scene.H - 70
    middle = scene.H - 98  # swimming height of the main koi
    swimmers = [(theta, s["length"], middle, True), (theta + 2.5, s["length"] * .55, middle - 20, False),
                (theta + 4.4, s["length"] * .45, middle + 22, False), (theta + 1.2, s["length"] * .4, middle - 32, False),
                (theta + 5.5, s["length"] * .35, middle + 8, False)][:s["fish"]]

    def swim(back):
        for angle, size, level, main in sorted(swimmers, key=lambda w: math.cos(w[0])):
            if (math.cos(angle) < 0) != back:
                continue
            if main and s["reward"] >= 3:
                swing = 112 * scene.W / 320 if scene.W >= 320 else scene.W / 2 - 44
                size_now = size * (1 + .2 * math.cos(angle))
                squash = max(.34, abs(math.cos(angle)) ** .6)
                spot = (scene.W / 2 - 2 + swing * math.sin(angle), level + 14 * math.cos(angle) + 5 * math.sin(angle * 2),
                        squash * size_now, size_now * .19)
                extras.aura(c, spot, (255, 214, 90))
            spot = scene.koi(c, th, f, angle, size, level, s["look"])
            if main and s["reward"]:
                extras.sparkles(c, f, spot, (0, 10, 18, 30)[s["reward"]], (255, 240, 160))

    scene.background(c, th, f, plants)
    swim(True)  # behind the plants and decor
    if plants:
        scene.grass(c, th, X(12), Y(158), min(96, tall), 11, ph, leaf)
        scene.broadleaf(c, th, X(112), Y(156), 8, ph, leaf2)
        scene.grass(c, th, X(200), Y(156), 54, 7, ph + 1, leaf)
        scene.grass(c, th, X(304), Y(160), min(104, tall), 12, ph + 2, leaf)
    scene.gravel(c, th)
    if "decor" not in hidden:
        scene.decor(c, th)
    if "rocks" not in hidden:
        scene.rocks(c, th)
    if plants:
        scene.broadleaf(c, th, X(46), Y(166), 5, ph + 2, leaf)
        scene.broadleaf(c, th, X(268), Y(168), 6, ph + 4, leaf2)
    if flowers:
        for i, (x, y, size) in enumerate([(100, 158, 9), (118, 166, 7), (214, 164, 8), (66, 142, 7), (292, 146, 7)]):
            scene.flower(c, X(x), Y(y), th["blooms"][i % 5], size, ph + i * 1.3)
    swim(False)
    if plants:
        scene.grass(c, th, X(136), Y(184), 34, 6, ph + 3, leaf)
        scene.grass(c, th, X(244), Y(184), 30, 5, ph + 5, leaf)
    for creature in s["creatures"]:
        extras.CREATURES[creature][0](c, f)
    if s["sign"]:
        extras.sign(c, *s["sign"])
    scene.bubbles(c, th, f, "bubbles" not in hidden)
    scene.surface(c, th, f, flowers)
    if s["name"]:
        extras.nametag(c, s["name"])
    return c.im


def render(theme, size, out, s):
    scene.resize(size)
    th = scene.THEMES[theme]
    frames = [frame(th, f, s) for f in range(scene.N)]
    sheet = Image.new("RGB", (scene.W, scene.H * scene.N))
    for i, im in enumerate(frames):
        sheet.paste(im, (0, i * scene.H))
    palette = sheet.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    big = (scene.W * scene.SCALE, scene.H * scene.SCALE)
    images = [im.quantize(palette=palette, dither=Image.Dither.NONE).resize(big, Image.NEAREST) for im in frames]
    out.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(out, save_all=True, append_images=images[1:], duration=s["ms"], loop=0, disposal=1)


# ---------------------------------------------------------------- activity

def streak_ending(days, yesterday):
    count, day = 0, yesterday
    while days.get(day.isoformat(), 0) > 0:
        count, day = count + 1, day - datetime.timedelta(days=1)
    return count


def activity(login, token):
    """All-time contributions, yesterday's count, current streak and top public languages."""
    def ask(query, variables):
        request = urllib.request.Request(
            "https://api.github.com/graphql", json.dumps({"query": query, "variables": variables}).encode(),
            {"Authorization": "bearer " + token, "User-Agent": "koi-aquarium"})
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.load(response)
        if body.get("errors"):
            raise SystemExit("GitHub API error: " + body["errors"][0]["message"])
        if not body["data"]["user"]:
            raise SystemExit(f"No GitHub user named {login!r} (organisations are not supported)")
        return body["data"]["user"]

    first = ask("query($l:String!){user(login:$l){contributionsCollection{contributionYears}"
                "repositories(first:100,ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false)"
                "{nodes{primaryLanguage{name color}}}}}", {"l": login})
    query = ("query($l:String!,$a:DateTime!,$b:DateTime!){user(login:$l){contributionsCollection(from:$a,to:$b)"
             "{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}")
    total, days = 0, {}
    for year in first["contributionsCollection"]["contributionYears"]:
        data = ask(query, {"l": login, "a": f"{year}-01-01T00:00:00Z", "b": f"{year}-12-31T23:59:59Z"})
        calendar = data["contributionsCollection"]["contributionCalendar"]
        total += calendar["totalContributions"]
        for week in calendar["weeks"]:
            for day in week["contributionDays"]:
                days[day["date"]] = day["contributionCount"]
    yesterday = datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=1)
    used = {}
    for repo in first["repositories"]["nodes"]:
        language = repo["primaryLanguage"]
        if language and re.fullmatch(r"#[0-9a-fA-F]{6}", language["color"] or ""):
            colour = language["color"].lower()
            used[colour] = used.get(colour, 0) + 1
    languages = sorted(used, key=lambda k: (-used[k], k))
    return total, days.get(yesterday.isoformat(), 0), streak_ending(days, yesterday), languages


# ---------------------------------------------------------------- command line

def flag(text):
    return str(text).strip().lower() in ("1", "true", "yes", "on")


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--theme", default="japanese", choices=sorted(scene.THEMES))
    p.add_argument("--dark-theme", default="", help="also draw this theme for dark-mode visitors")
    p.add_argument("--size", default="wide", choices=sorted(scene.SIZES))
    p.add_argument("--colors", default="", help=f"{', '.join(COLORS)}, languages, or #rrggbb,#rrggbb,#rrggbb")
    p.add_argument("--name", default="", help="name tag, up to 16 characters")
    p.add_argument("--hide", default="", help="any of " + ", ".join(HIDEABLE))
    p.add_argument("--milestones", default="500,2000", help="contributions at which another koi joins")
    p.add_argument("--max-fish", type=int, default=3, help="1 to 5")
    p.add_argument("--creatures", default="none", help="none, auto, all, or any of " + ", ".join(extras.CREATURES))
    p.add_argument("--evolution", type=flag, nargs="?", const=True, default=False)
    p.add_argument("--streak-rewards", type=flag, nargs="?", const=True, default=False)
    p.add_argument("--sign", type=flag, nargs="?", const=True, default=False)
    p.add_argument("--speed", type=int, default=0, help="milliseconds per frame, 40-400 (0 = from activity)")
    p.add_argument("--out", type=pathlib.Path, default=pathlib.Path("aquarium.gif"))
    p.add_argument("--login", help="read activity for this account (needs GH_TOKEN)")
    p.add_argument("--total", type=int, default=250, help="preview: all-time contributions")
    p.add_argument("--yesterday", type=int, default=1, help="preview: contributions yesterday")
    p.add_argument("--streak", type=int, default=1, help="preview: current streak in days")
    p.add_argument("--languages", default="#3572a5,#f1e05a", help="preview: language colours")
    return p


def main(argv=None):
    options = parser().parse_args(argv)
    if options.dark_theme and options.dark_theme not in scene.THEMES:
        raise SystemExit(f"dark-theme: choose from {', '.join(sorted(scene.THEMES))}")
    if options.speed and not 40 <= options.speed <= 400:
        raise SystemExit("speed: use 40 to 400 milliseconds, or 0")
    total, yesterday, streak, languages = options.total, options.yesterday, options.streak, words(options.languages)
    if options.login:
        total, yesterday, streak, languages = activity(options.login, os.environ["GH_TOKEN"])
    s = state(options, total, yesterday, streak, languages)
    print(f"contributions={total} yesterday={yesterday} streak={streak} fish={s['fish']} "
          f"length={s['length']} stage={s['stage']} creatures={s['creatures']}")
    render(options.theme, options.size, options.out, s)
    if options.dark_theme:
        render(options.dark_theme, options.size, options.out.with_name(f"{options.out.stem}-dark.gif"), s)


if __name__ == "__main__":
    main()
