
# ===================================================================== G profiling adapter
# Appended to frozen G (PokerBot/submissions/G_v7_final/bot.py) by gbot/export_g_profile.py.
# G's betting/EV code is untouched. Only the opponent reads it already consumes change:
#   vpip, pfr, bigrate, fold3, blindfold, ftr, ftb, af
# 1. Rolling window: G's own per-hand counters are kept per hand; reads use the last
#    GP_WINDOW hands. Every GP_CHECK hands the last GP_HALF hands are compared with the
#    GP_HALF before; a sharp shift (two-proportion z > GP_Z on any key rate) marks the
#    seat as changed and reads then use the recent half only (new policy, stale evidence).
# 2. Optional roster prior (GP_ROSTER_PRIOR): every unseen seat starts from the pooled
#    tendencies of the known Sunday opponents instead of G's generic priors. No seat is
#    ever matched to a team name, so a wrong identification cannot happen.
GP_WINDOW = 400
GP_HALF = 150
GP_CHECK = 25
GP_Z = 4.5
GP_KEYS = ("hands", "vpip", "pfr", "big", "pbet", "pcall", "pcheck", "faced", "ffold",
           "f3", "f3fold", "o3", "o3fold", "bdef", "bfold")
# pooled Table D tendencies (data/v3_model.json, Saturday rounds, recency-weighted)
GP_ROSTER = {"vpip": 0.2671, "pfr": 0.1791, "big": 0.0035, "f3": 0.6739, "ftr": 0.7662,
             "ftb": 0.4164, "af": 0.321}
GP_ROSTER_PRIOR = False

_GBase = Agent


class Agent(_GBase):
    def __init__(self):
        _GBase.__init__(self)
        self.gp_hist = {}       # seat -> per-hand count tuples (in GP_KEYS order), last GP_WINDOW+ kept
        self.gp_sw = {}         # seat -> running sums over the last GP_WINDOW hands
        self.gp_sh = {}         # seat -> running sums over the last GP_HALF hands
        self.gp_w = {}          # seat -> cached dict G's reads use (O(1) inside act; act time is budgeted)
        self.gp_changed = {}    # seat -> hand index when a shift was detected
        self.gp_fail = 0

    def _learn(self, summary):
        before = {s: tuple(getattr(o, k) for k in GP_KEYS) for s, o in self.st.items()}
        _GBase._learn(self, summary)
        try:
            for s, o in self.st.items():
                now = tuple(getattr(o, k) for k in GP_KEYS)
                b = before.get(s)
                d = now if b is None else tuple(x - y for x, y in zip(now, b))
                if d[0] == 0:
                    continue
                h = self.gp_hist.setdefault(s, [])
                h.append(d)
                sw = self.gp_sw.setdefault(s, [0] * len(GP_KEYS))
                sh = self.gp_sh.setdefault(s, [0] * len(GP_KEYS))
                for i, v in enumerate(d):
                    sw[i] += v
                    sh[i] += v
                if len(h) > GP_HALF:
                    for i, v in enumerate(h[-GP_HALF - 1]):
                        sh[i] -= v
                if len(h) > GP_WINDOW:
                    for i, v in enumerate(h[-GP_WINDOW - 1]):
                        sw[i] -= v
                if len(h) > 2 * GP_WINDOW:
                    del h[:GP_WINDOW]
                if len(h) >= 2 * GP_HALF and len(h) % GP_CHECK == 0 and s not in self.gp_changed:
                    self._gp_check(s, h)
                self.gp_w[s] = dict(zip(GP_KEYS, sh if s in self.gp_changed else sw))
        except Exception:
            self.gp_fail += 1

    def _gp_check(self, s, h):
        a = self._gp_sum(h[-GP_HALF:])
        b = self._gp_sum(h[-2 * GP_HALF:-GP_HALF])
        for num, den in (("vpip", "hands"), ("pfr", "hands"), ("ffold", "faced"), ("pbet", None)):
            if den is None:
                na, nb = a["pbet"] + a["pcall"] + a["pcheck"], b["pbet"] + b["pcall"] + b["pcheck"]
            else:
                na, nb = a[den], b[den]
            if na < 20 or nb < 20:
                continue
            pa, pb = a[num] / float(na), b[num] / float(nb)
            p = (a[num] + b[num]) / float(na + nb)
            se = (p * (1 - p) * (1.0 / na + 1.0 / nb)) ** 0.5
            if se > 0 and abs(pa - pb) / se > GP_Z:
                self.gp_changed[s] = len(h)
                return

    @staticmethod
    def _gp_sum(rows):
        out = dict.fromkeys(GP_KEYS, 0)
        for r in rows:
            for k, v in zip(GP_KEYS, r):
                out[k] += v
        return out

    def W(self, s):
        """Counts G's reads use: last GP_WINDOW hands, or the last GP_HALF after a detected change."""
        return self.gp_w.get(s)

    def _gp_pri(self, key, generic):
        return GP_ROSTER[key] if GP_ROSTER_PRIOR else generic

    def vpip(self, s):
        o = self.W(s)
        if o is None:
            return _GBase.vpip(self, s) if not GP_ROSTER_PRIOR else self._gp_pri("vpip", P["pri_vpip"])
        return (o["vpip"] + self._gp_pri("vpip", P["pri_vpip"]) * 12) / (o["hands"] + 12)

    def pfr(self, s):
        o = self.W(s)
        if o is None:
            return _GBase.pfr(self, s) if not GP_ROSTER_PRIOR else self._gp_pri("pfr", P["pri_pfr"])
        return (o["pfr"] + self._gp_pri("pfr", P["pri_pfr"]) * 12) / (o["hands"] + 12)

    def bigrate(self, s):
        o = self.W(s) or dict.fromkeys(GP_KEYS, 0)
        return (o["big"] + self._gp_pri("big", 0.05) * 10) / (o["hands"] + 10)

    def fold3(self, s):
        o = self.W(s) or dict.fromkeys(GP_KEYS, 0)
        return (o["o3fold"] + self._gp_pri("f3", 0.5) * 4) / (o["o3"] + 4), o["o3"]

    def blindfold(self, s):
        o = self.W(s) or dict.fromkeys(GP_KEYS, 0)
        return (o["bfold"] + 0.6 * 6) / (o["bdef"] + 6), o["bdef"]

    def ftr(self, s):
        o = self.W(s) or dict.fromkeys(GP_KEYS, 0)
        return (o["f3fold"] + self._gp_pri("ftr", 0.75) * 10) / (o["f3"] + 10)

    def ftb(self, s):
        o = self.W(s) or dict.fromkeys(GP_KEYS, 0)
        return (o["ffold"] + self._gp_pri("ftb", P["pri_ftb"]) * 8) / (o["faced"] + 8)

    def af(self, s):
        o = self.W(s) or dict.fromkeys(GP_KEYS, 0)
        return (o["pbet"] + self._gp_pri("af", 0.3) * 10) / (o["pbet"] + o["pcall"] + o["pcheck"] + 10)
