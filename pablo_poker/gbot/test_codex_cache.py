"""Codex v4 profiling candidates: cached opponent reads equal fresh reads; cache resets every hand.
    python gbot/test_codex_cache.py"""
import glob, importlib.util, json, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
from gbot.calib_drift_real import summaries
METHODS = ("vpip", "pfr", "bigrate", "fold3", "ftb", "af")


def load(p):
    s = importlib.util.spec_from_file_location("cc_" + os.path.basename(p)[:-3], os.path.join(ROOT, p))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


class TestCache(unittest.TestCase):
    def check(self, path):
        d = json.load(open(sorted(glob.glob(os.path.join(ROOT, "hands/external/WBot/saturday_r05*.json")))[0], encoding="utf-8"))
        a = load(path).Agent()
        a.on_table_start({"seat": d["seat"], "num_players": len(d["players"]), "hands": 1000, "starting_stack": 2000})
        seats = [x for x in range(len(d["players"])) if x != d["seat"]]
        for i, (s, hh) in enumerate(zip(summaries(d), d["hands"])):
            if i >= 300:
                break
            a._decision_hand = i + 1; a._decision_button = hh["button"]
            s["hand_number"] = i + 1; s["board"] = hh.get("board") or []
            a.on_hand_end(s)
            self.assertEqual(a._read_cache, {})
            if i % 50 == 49:
                for x in seats:
                    for m in METHODS:
                        self.assertEqual(getattr(a, m)(x), getattr(a, "_%s_uncached" % m)(x), (m, x, i))
        self.assertTrue(a.context_model.live)

    def test_identity_bot(self):
        self.check("sunday/v4_identity_bot.py")

    def test_cold_accounting_bot(self):
        self.check("sunday/v4_cold_accounting_bot.py")


if __name__ == "__main__":
    unittest.main(verbosity=1)
