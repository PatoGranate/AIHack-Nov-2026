"""Fold-prediction calibration for our postflop bets/raises (offline diagnostic).

    python tools/calibration.py tools/cands/v7.py --tables 40 --hands 300 --seed 1 [--field real|pool]

For every HEADS-UP postflop bet/raise our bot makes (exactly one live opponent,
that opponent not all-in, our amount below our own all-in), record the bot's
predicted fold probability for the chosen size and the opponent's actual next
action on that street. The bot source is NOT modified: the script subclasses
its Agent at runtime.

Predicted fold = weighted mean over a fresh sample of the opponent's modelled
range of (1 - cc[L]), using exactly the bot's simulate() ingredients:
  range slice ALLC[lo:hi] from opp_models, level L from the same board-texture
  classification, sample weight w[L] (floored at 1e-4), size exponent
  e = min(2.5, (add/pot / 0.6) ** size_exp), cc = cont[L] ** e for L<3,
  cc[3] = 1.0 (0.92 if e >= 2), and the fold_vs_raise scaling when facing a bet.

Outputs tools/calibration_log.csv (raw rows) and a printed summary.
"""
import sys, os, random, argparse, importlib.util, csv, math
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import arena  # noqa: E402  (sets sys.path for kit/ and tools/opponents/, provides load/ARCH/HOUSE/REAL)
from engine import FixedHandsTable  # noqa: E402
from engine.players import LocalPlayer  # noqa: E402

LOG = os.path.join(ROOT, "tools", "calibration_log.csv")
FIELDS = ["table", "hand", "street", "kind", "size", "size_bucket", "add", "pot", "opp", "opp_seat",
          "pred_fold", "n_samp", "response", "folded"]
_bot_cache = {}


def load_bot(path):
    if path in _bot_cache:
        return _bot_cache[path]
    full = path if os.path.isabs(path) else os.path.join(ROOT, path)
    spec = importlib.util.spec_from_file_location("calib_bot", full)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _bot_cache[path] = (mod, make_wrapper(mod))
    return _bot_cache[path]


def level_fn(mod, board):
    """Return f(h1, h2) -> L, a copy of the level classification in mod.Agent.simulate."""
    CP, CB, RT, FL = mod.CP, mod.CB, mod.RT, mod.FL
    bd = [mod.to_int(c) for c in board]
    need = 5 - len(bd)
    bprod = 1
    bsc = [0, 0, 0, 0]
    bsm = [0, 0, 0, 0]
    brc = [0] * 13
    for c in bd:
        bprod *= CP[c]
        bsc[c & 3] += 1
        bsm[c & 3] |= CB[c]
        brc[c >> 2] += 1
    top = max(c >> 2 for c in bd)
    bpairs = set(r for r in range(13) if brc[r] >= 2)
    draw_st = need > 0

    def lev(h1, h2):
        v = RT[bprod * CP[h1] * CP[h2]]
        s1, s2 = h1 & 3, h2 & 3
        for s in range(4):
            cnt = bsc[s] + (s1 == s) + (s2 == s)
            if cnt >= 5:
                fv = FL[bsm[s] | (CB[h1] if s1 == s else 0) | (CB[h2] if s2 == s else 0)]
                if fv > v:
                    v = fv
            elif cnt == 4 and draw_st and (s1 == s or s2 == s):
                v = -1 if v < (1 << 20) else v
        if v == -1:
            return 1
        cat = v >> 20
        if cat >= 4:
            return 3
        if cat == 3:
            return 0 if brc[(v >> 8) & 15] >= 3 else 3
        if cat == 2:
            p1, p2 = (v >> 8) & 15, (v >> 4) & 15
            if p1 in bpairs and p2 in bpairs:
                return 0
            if p1 in bpairs or p2 in bpairs:
                o = p2 if p1 in bpairs else p1
                return 2 if o >= top else 1
            return 3
        if cat == 1:
            p = (v >> 12) & 15
            return 0 if p in bpairs else (2 if p >= top else 1)
        return 0
    return lev


def pred_fold(mod, rng, hole, board, m, add, pot, raising, nsamp):
    P = mod.P
    sz = max(0.05, add / float(max(1, pot)))
    e = min(2.5, (sz / 0.6) ** P["size_exp"])
    cont, w = m[4], m[3]
    cc = (cont[0] ** e, cont[1] ** e, cont[2] ** e, 1.0 if e < 2.0 else 0.92)
    fvr = P["fold_vs_raise"] if raising else 1.0
    if fvr != 1.0:
        cc = tuple(mod.clamp(1 - (1 - x) * fvr, 0.0, 1.0) for x in cc)
    dead = set(mod.to_int(c) for c in hole) | set(mod.to_int(c) for c in board)
    deck = [c for c in range(52) if c not in dead]
    lev = level_fn(mod, board)
    lo, hi = m[1], m[2]
    W = F = 0.0
    for _ in range(nsamp):
        for _t in range(40):
            h = mod.ALLC[rng.randrange(lo, hi)]
            if h[0] not in dead and h[1] not in dead:
                break
        else:
            h = tuple(rng.sample(deck, 2))
        L = lev(h[0], h[1])
        wt = max(1e-4, w[L])
        W += wt
        F += wt * (1 - cc[L])
    return F / W


def make_wrapper(mod):
    Base = mod.Agent

    class CalibAgent(Base):
        nsamp = 600

        def __init__(self):
            Base.__init__(self)
            self._crng = random.Random()
            self._pending = []
            self.records = []
            self._cap = None

        def opp_models(self, state, me):
            ms = Base.opp_models(self, state, me)
            if self._cap is not None:
                self._cap["models"] = ms
            return ms

        def act(self, state):
            self._cap = {}
            out = Base.act(self, state)   # timing/budget untouched by our extra work below
            cap, self._cap = self._cap, None
            try:
                self._maybe_record(state, out, cap)
            except Exception:
                pass
            return out

        def _maybe_record(self, state, out, cap):
            if state["street"] == "preflop" or out.get("action") != "raise":
                return
            ms = cap.get("models")
            if not ms or len(ms) != 1:
                return
            m = ms[0]
            if m[5]:          # opponent all-in, cannot act
                return
            me = state["seat"]
            R = int(out["amount"])
            if state.get("max_raise_to") is not None and R >= state["max_raise_to"]:
                return        # our all-in
            my_bet = state["bets"][me]
            add = R - my_bet
            pot = state["pot"]
            raising = state["to_call"] > 0
            pf = pred_fold(mod, self._crng, state["hole_cards"], state["board"], m, add, pot, raising, self.nsamp)
            size = add / float(max(1, pot))
            self._pending.append({
                "hand": state["hand_number"], "street": state["street"],
                "kind": "raise" if raising else "bet", "size": round(size, 4),
                "size_bucket": "<0.4" if size < 0.4 else ("0.4-0.8" if size <= 0.8 else ">0.8"),
                "add": add, "pot": pot, "opp_seat": m[0], "pred_fold": round(pf, 4),
                "n_samp": self.nsamp, "_idx": len(state["history"]), "_me": me,
            })

        def on_hand_end(self, summary):
            hist = summary.get("history") or []
            for r in self._pending:
                i = r.pop("_idx")
                me = r.pop("_me")
                if i >= len(hist) or hist[i].get("seat") != me or hist[i].get("action") != "raise":
                    continue
                resp = None
                for h in hist[i + 1:]:
                    if h.get("street") != r["street"]:
                        break
                    if h.get("seat") == r["opp_seat"]:
                        resp = h.get("action")
                        break
                if resp not in ("fold", "call", "raise"):
                    continue
                r["response"] = resp
                r["folded"] = 1 if resp == "fold" else 0
                self.records.append(r)
            self._pending = []
            return Base.on_hand_end(self, summary)

    return CalibAgent


def field(name):
    if name == "real":
        return arena.REAL
    if name == "pool":
        return arena.ARCH + arena.HOUSE
    raise SystemExit("unknown field %s" % name)


def run(job):
    bot, seed, hands, fname, nsamp = job
    mod, W = load_bot(bot)
    W.nsamp = nsamp
    rng = random.Random(seed * 7919 + 13)
    fl = field(fname)
    ns = 7
    opps = [rng.choice(fl) for _ in range(ns - 1)]
    hero = seed % ns
    seats = list(opps)
    seats.insert(hero, None)
    players = [LocalPlayer(W) if p is None else LocalPlayer(arena.load(p)) for p in seats]
    FixedHandsTable(players, hands=hands, seed=seed).play()
    ag = players[hero].agent
    recs = []
    for r in ag.records:
        r["table"] = seed
        r["opp"] = os.path.basename(seats[r["opp_seat"]])[:-3]
        recs.append(r)
    return recs, players[hero].stats.errors


def summarize(rows, title):
    n = len(rows)
    if not n:
        print("  %-28s n=0" % title)
        return
    pm = sum(r["pred_fold"] for r in rows) / n
    om = sum(r["folded"] for r in rows) / n
    brier = sum((r["pred_fold"] - r["folded"]) ** 2 for r in rows) / n
    # reference: Brier of always predicting the observed base rate
    ref = om * (1 - om)
    se = math.sqrt(max(om * (1 - om), 1e-9) / n)
    print("  %-28s n=%5d  pred %.3f  obs %.3f (se %.3f)  diff %+.3f  brier %.4f (base-rate %.4f)"
          % (title, n, pm, om, se, om - pm, brier, ref))


def reliability(rows):
    print("  reliability (deciles of predicted fold prob):")
    print("    %-11s %6s %8s %8s" % ("pred bin", "n", "pred", "obs"))
    for b in range(10):
        lo, hi = b / 10.0, (b + 1) / 10.0
        rs = [r for r in rows if lo <= r["pred_fold"] < hi or (b == 9 and r["pred_fold"] >= 1.0)]
        if rs:
            print("    [%.1f,%.1f)  %6d %8.3f %8.3f" % (lo, hi, len(rs), sum(r["pred_fold"] for r in rs) / len(rs),
                                                     sum(r["folded"] for r in rs) / len(rs)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bot")
    ap.add_argument("--tables", type=int, default=40)
    ap.add_argument("--hands", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--field", default="real", choices=["real", "pool"])
    ap.add_argument("--samples", type=int, default=600, help="range samples per predicted-fold estimate")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--by-opp", action="store_true")
    a = ap.parse_args()
    jobs = [(a.bot, a.seed * 100000 + t, a.hands, a.field, a.samples) for t in range(a.tables)]
    rows, errs = [], 0
    with Pool(max(1, min(4, a.workers))) as pool:
        for recs, e in pool.imap_unordered(run, jobs):
            rows += recs
            errs += e
    rows.sort(key=lambda r: (r["table"], r["hand"]))
    with open(LOG, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS)
        wr.writeheader()
        for r in rows:
            wr.writerow(r)
    print("bot=%s field=%s tables=%d hands=%d  records=%d  bot_errors=%d  log=%s"
          % (a.bot, a.field, a.tables, a.hands, len(rows), errs, os.path.relpath(LOG, ROOT)))
    resp = {}
    for r in rows:
        resp[r["response"]] = resp.get(r["response"], 0) + 1
    print("  responses: " + ", ".join("%s=%d" % kv for kv in sorted(resp.items())) + "  (continue = call+raise)")
    summarize(rows, "ALL")
    reliability(rows)
    print("  by kind:")
    for k in ("bet", "raise"):
        summarize([r for r in rows if r["kind"] == k], k)
    print("  by street x size (pot fraction):")
    for st in ("flop", "turn", "river"):
        for sb in ("<0.4", "0.4-0.8", ">0.8"):
            summarize([r for r in rows if r["street"] == st and r["size_bucket"] == sb], "%s %s" % (st, sb))
    print("  by kind x street:")
    for k in ("bet", "raise"):
        for st in ("flop", "turn", "river"):
            summarize([r for r in rows if r["kind"] == k and r["street"] == st], "%s %s" % (k, st))
    if a.by_opp:
        print("  by opponent:")
        for o in sorted(set(r["opp"] for r in rows)):
            summarize([r for r in rows if r["opp"] == o], o[:28])


if __name__ == "__main__":
    main()
