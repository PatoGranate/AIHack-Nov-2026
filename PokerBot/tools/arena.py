"""Duplicate A/B arena.

    python tools/arena.py CAND.py BASE.py --tables 64 --hands 500 --field mix

For each table seed we draw 7 opponents from the field, then play the same
cards twice: once with CAND in the hero seat and once with BASE. The paired
difference removes most card luck. Reports bb/100 of each and of the diff (+-SE).
"""
import sys, os, random, argparse, importlib.util, glob, math
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "kit"))
sys.path.insert(0, os.path.join(ROOT, "tools", "opponents"))
from engine import FixedHandsTable  # noqa
from engine.players import LocalPlayer  # noqa

ARCH = sorted(os.path.relpath(p, ROOT).replace("\\", "/") for p in glob.glob(os.path.join(ROOT, "tools/opponents/a_*.py")))
HOUSE = ["kit/examples/tight_aggressive.py", "kit/examples/calling_station.py", "kit/examples/random_bot.py",
         "tools/opponents/starter.py"]
VERSIONS = ["tools/opponents/v1.py", "tools/opponents/v2_uploaded.py"]
_cache = {}


def load(path):
    if path not in _cache:
        full = path if os.path.isabs(path) else os.path.join(ROOT, path)
        name = "m%d_%s" % (len(_cache), os.path.basename(path)[:-3])
        spec = importlib.util.spec_from_file_location(name, full)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _cache[path] = m.Agent
    return _cache[path]


REAL = []
_wf = os.path.join(ROOT, "tools/opponents/real/weights.txt")
if os.path.exists(_wf):
    import math as _math
    for _l in open(_wf, encoding="utf-8"):
        _parts = _l.split()
        _f, _h = _parts[0], int(_parts[1])
        _bb = float(_parts[2]) if len(_parts) > 2 else 0.0
        # strength-weighted: winners drawn more often, losers kept at a floor
        _w = min(4.0, max(0.35, _math.exp(_bb / 120.0))) * min(2.0, _math.sqrt(_h / 1000.0))
        REAL += [_f.replace("\\", "/")] * max(1, int(round(_w * 4)))


def field_list(field, base, extra):
    if field == "archive":
        return ["submissions/%s/bot.py" % d for d in ("A_v2_safe", "B_v3_balanced", "C_v3_aggressive",
                "D_v3_max_aggressive", "E_v3_balanced_fast", "F_v3_tuned")]
    if field == "late":
        return [l.strip() for l in open(os.path.join(ROOT, "tools/opponents/late/list.txt"), encoding="utf-8") if l.strip()]
    if field == "heldout":
        return [l.strip() for l in open(os.path.join(ROOT, "tools/opponents/heldout/list.txt"), encoding="utf-8") if l.strip()] + VERSIONS
    if field == "real":
        return REAL
    if field == "realself":
        return REAL + [base] * 2 + extra
    if field == "pool":
        return ARCH + HOUSE
    if field == "self":
        return [base] * 3 + VERSIONS + extra
    if field == "strong":  # competent-ish bots only
        return VERSIONS + [base] + extra + ["tools/opponents/a_tag.py", "tools/opponents/a_lag.py", "tools/opponents/a_nit.py"]
    # mix
    return ARCH + HOUSE + VERSIONS * 2 + [base] * 2 + extra * 2


def run(args):
    cand, base, seed, hands, betting, field, extra, cap = args
    rng = random.Random(seed * 7919 + 13)
    fl = field_list(field, base, extra)
    ns = 7 if field.startswith("real") else 8 if field not in ("heldout", "late") else random.Random(seed).choice([7, 8])
    opps = [rng.choice(fl) for _ in range(ns - 1)]
    hero = seed % ns
    chips = []
    errors = []
    for who in (cand, base):
        seats = list(opps)
        seats.insert(hero, who)
        players = [LocalPlayer(load(p)) for p in seats]
        res = FixedHandsTable(players, hands=hands, config={"betting": betting, "raise_cap": cap}, seed=seed).play()
        chips.append(res["chips"][hero])
        errs = players[hero].stats.errors
        if errs:
            errors.append(("ERR", who, errs, players[hero].stats.error_samples[:1]))
        oerr = sum(pl.stats.errors for i, pl in enumerate(players) if i != hero)
        if oerr:
            errors.append(("OPPERR", who, oerr, [pl.stats.error_samples[:1] for pl in players if pl.stats.errors][:1]))
    return {"chips": chips, "errors": errors}, opps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cand"); ap.add_argument("base")
    ap.add_argument("--tables", type=int, default=64)
    ap.add_argument("--hands", type=int, default=500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--field", default="mix")
    ap.add_argument("--betting", default="no_limit")
    ap.add_argument("--cap", type=int, default=0)
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--by-opp", action="store_true")
    a = ap.parse_args()
    jobs = [(a.cand, a.base, a.seed * 100000 + t, a.hands, a.betting, a.field, a.extra, a.cap) for t in range(a.tables)]
    diffs, cs, bs = [], [], []
    byopp = {}
    nerr = 0
    with Pool() as pool:
        for out, opps in pool.imap_unordered(run, jobs):
            c, b = out["chips"]
            for x in out["errors"]:
                print(x)
                nerr += 1
            k = 100.0 / 20 / a.hands
            cs.append(c * k); bs.append(b * k); diffs.append((c - b) * k)
            for o in set(opps):
                byopp.setdefault(o, []).append((c - b) * k)
    n = len(diffs)
    mean = lambda v: sum(v) / len(v)
    def se(v):
        m = mean(v)
        return math.sqrt(sum((x - m) ** 2 for x in v) / max(1, len(v) - 1) / len(v))
    print("field=%s tables=%d hands=%d" % (a.field, n, a.hands))
    print("  cand %-32s %+8.1f bb/100 (se %.1f)" % (a.cand, mean(cs), se(cs)))
    print("  base %-32s %+8.1f bb/100 (se %.1f)" % (a.base, mean(bs), se(bs)))
    print("  DIFF                                  %+8.1f bb/100 (se %.1f)  z=%.2f" % (mean(diffs), se(diffs), mean(diffs) / max(1e-9, se(diffs))))
    if nerr:
        print("  WARNING: %d tables had bot errors; results invalid" % nerr)
    if a.by_opp:
        for o, v in sorted(byopp.items(), key=lambda kv: mean(kv[1])):
            print("    with %-40s %+7.1f (n=%d)" % (o, mean(v), len(v)))


if __name__ == "__main__":
    main()
