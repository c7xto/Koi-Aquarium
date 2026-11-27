import datetime
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from PIL import Image

import aquarium
import scene


def state(*args, total=250, yesterday=1, streak=1, languages=()):
    return aquarium.state(aquarium.parser().parse_args(list(args)), total, yesterday, streak, list(languages))


class Settings(unittest.TestCase):
    def test_koi_grows_and_gets_company(self):
        self.assertLess(state(total=10)["length"], state(total=900)["length"])
        self.assertEqual([state(total=t)["fish"] for t in (10, 500, 2000)], [1, 2, 3])

    def test_activity_sets_speed(self):
        self.assertLess(state(yesterday=3)["ms"], state(yesterday=0)["ms"])

    def test_extras_are_off_by_default(self):
        s = state(total=9000, streak=90)
        self.assertEqual((s["creatures"], s["stage"], s["reward"], s["sign"]), ([], None, 0, None))

    def test_creatures_unlock(self):
        self.assertEqual(state("--creatures", "auto", total=300)["creatures"], ["snail", "shrimp"])

    def test_bad_values_are_rejected(self):
        for args in (["--colors", "red"], ["--hide", "fish"], ["--milestones", "many"], ["--creatures", "shark"]):
            with self.assertRaises(SystemExit):
                state(*args)

    def test_streak_counts_back_from_yesterday(self):
        day = datetime.date(2026, 1, 10)
        days = {"2026-01-10": 1, "2026-01-09": 4, "2026-01-08": 0, "2026-01-07": 2}
        self.assertEqual(aquarium.streak_ending(days, day), 2)


class Drawing(unittest.TestCase):
    def tearDown(self):
        scene.resize("wide")

    def test_every_theme_and_size_draws(self):
        s = state("--sign", "--creatures", "all", "--name", "Test", total=6000, streak=40)
        for size, (w, h) in scene.SIZES.items():
            scene.resize(size)
            for theme in scene.THEMES.values():
                self.assertEqual(aquarium.frame(theme, 5, s).size, (w, h))

    def test_command_line_writes_both_gifs(self):
        with tempfile.TemporaryDirectory() as folder:
            out = pathlib.Path(folder) / "a.gif"
            aquarium.main(["--dark-theme", "night", "--size", "square", "--out", str(out)])
            for path in (out, out.with_name("a-dark.gif")):
                with Image.open(path) as im:
                    self.assertEqual(im.n_frames, scene.N)


if __name__ == "__main__":
    unittest.main()
