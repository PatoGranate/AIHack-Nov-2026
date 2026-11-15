"""Tests for the G profiling candidates.   python gbot/test_g_profile.py"""
import importlib.util
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)


def load(name):
    spec = importlib.util.spec_from_file_location(name[:-3] + "_t", os.path.join(HERE, name))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


G, GP, GT = load("G_frozen.py"), load("G_profile.py"), load("G_profile_td.py")


def hand(rng, p_play, n=8, villain=1):
    """Synthetic public history: villain opens with prob p_play else folds; others fold; BB checks/folds."""
    hist = [{"seat": 2, "action": "small_blind", "amount": 10, "street": "preflop"},
            {"seat": 3, "action": "big_blind", "amount": 20, "street": "preflop"}]
    raised = False
    for s in [4, 5, 6, 7, 0, villain]:
        if s == villain and rng.random() < p_play:
            hist.append({"seat": s, "action": "raise", "amount": 60, "street": "preflop"})
            raised = True
        else:
            hist.append({"seat": s, "action": "fold", "amount": 0, "street": "preflop"})
    hist.append({"seat": 2, "action": "fold", "amount": 0, "street": "preflop"})
    hist.append({"seat": 3, "action": "fold" if raised else "check", "amount": 0, "street": "preflop"})
    return {"history": hist, "shown": {}}


def feed(agent, rates, seed=1):
    rng = random.Random(seed)
    for p, k in rates:
        for _ in range(k):
            agent.on_hand_end(hand(rng, p))


class TestGProfile(unittest.TestCase):
    def test_unseen_seat_reads_match_G(self):
        g, gp = G.Agent(), GP.Agent()
        for f in ("vpip", "pfr", "bigrate", "ftb", "af", "ftr"):
            self.assertAlmostEqual(getattr(g, f)(5), getattr(gp, f)(5), places=12, msg=f)
        self.assertEqual(g.fold3(5), gp.fold3(5))

    def test_reads_match_G_before_window_or_shift(self):
        g, gp = G.Agent(), GP.Agent()
        feed(g, [(0.3, 250)])
        feed(gp, [(0.3, 250)])
        self.assertEqual(gp.gp_changed, {})
        for f in ("vpip", "pfr", "ftb", "af", "ftr"):
            self.assertAlmostEqual(getattr(g, f)(1), getattr(gp, f)(1), places=12, msg=f)

    def test_detects_policy_switch_and_uses_new_policy(self):
        gp = GP.Agent()
        feed(gp, [(0.10, 400), (0.60, 200)])
        self.assertIn(1, gp.gp_changed)
        g = G.Agent()
        feed(g, [(0.10, 400), (0.60, 200)])
        # whole-round G still believes ~27%; the profiled read follows the new ~60%
        self.assertLess(g.vpip(1), 0.35)
        self.assertGreater(gp.vpip(1), 0.5)

    def test_few_false_alarms_on_steady_opponent(self):
        flags = 0
        for seed in range(40):
            gp = GP.Agent()
            feed(gp, [(0.25, 1000)], seed=seed)
            flags += 1 in gp.gp_changed
        self.assertLessEqual(flags, 2, "false policy-change alarms: %d/40" % flags)

    def test_reads_cost_like_G(self):
        """G's reads run many times inside act() under a 3 ms hard deadline; the window must not slow them."""
        import time
        g, gp = G.Agent(), GP.Agent()
        feed(g, [(0.3, 500)])
        feed(gp, [(0.3, 500)])
        def cost(a):
            t = time.perf_counter()
            for _ in range(5000):
                a.vpip(1); a.pfr(1); a.ftb(1); a.af(1); a.fold3(1); a.ftr(1); a.bigrate(1)
            return time.perf_counter() - t
        self.assertLess(cost(gp), 3.0 * cost(g) + 0.01)

    def test_roster_prior_for_unseen_seat(self):
        gt = GT.Agent()
        self.assertAlmostEqual(gt.vpip(4), GT.GP_ROSTER["vpip"])
        self.assertAlmostEqual(gt.ftb(4), GT.GP_ROSTER["ftb"])

    def test_reads_match_G_on_real_engine_summaries(self):
        """Feed both agents the same 250 real hand-end summaries from the official engine."""
        from engine import FixedHandsTable
        from engine.players import LocalPlayer
        ex = os.path.join(ROOT, "..", "examples")
        opp = [load_path(os.path.join(ex, f)).Agent for f in
               ("tight_aggressive.py", "calling_station.py", "random_bot.py")]
        g, gp = G.Agent(), GP.Agent()

        class Spy(opp[0]):
            def on_hand_end(self, summary):
                g.on_hand_end(summary)
                gp.on_hand_end(summary)
        players = [LocalPlayer(Spy)] + [LocalPlayer(opp[i % 3]) for i in range(7)]
        FixedHandsTable(players, hands=250, seed=4242).play()
        self.assertEqual(g.hands_seen, 250)
        self.assertGreater(sum(len(v) for v in gp.gp_hist.values()), 500)
        self.assertEqual(gp.gp_changed, {})
        for s in range(1, 8):
            for f in ("vpip", "pfr", "bigrate", "ftb", "af", "ftr"):
                self.assertAlmostEqual(getattr(g, f)(s), getattr(gp, f)(s), places=12, msg="%s seat %d" % (f, s))
            self.assertEqual(g.fold3(s), gp.fold3(s))
            self.assertEqual(g.blindfold(s), gp.blindfold(s))


def load_path(p):
    spec = importlib.util.spec_from_file_location("x%d" % abs(hash(p)), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def seeded(cls):
    class S(cls):
        def __init__(self):
            cls.__init__(self)
            self.rng = random.Random(99)
    return S


if __name__ == "__main__":
    unittest.main(verbosity=1)
