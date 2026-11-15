"""FORGE: duplicate A/B on a Sunday table-4 clone field (exactly the 7 table-4 opponents + hero).

    python tools/forge_ctx/arena_t4.py CAND.py BASE.py --tables 480 --hands 300 --field t4real --seed 73201

Same pairing as tools/arena.py (same seed, same seating, same cards; CAND then BASE in the hero
seat), but the seat list is fixed to the table-4 clones, shuffled per table, instead of drawn with
replacement. Fields: t4real = tools/opponents/real/r_<name>.py; t4heldout = heldout r_<name>_j0/_j1,
chosen per seat per table. --dump DIR writes the BASE run's hand logs in Hand_data format so
extract_events.py can measure the clones' fold-to-bet by context.
Added 2026-11-15: t4v2 = tools/opponents/sunday_v2 clones (ROOK PR #10) with deterministic
per-decision RNG; t4ctx = the same clones with real-data fold-to-bet (ctx_clone.py); t4ctxh = t4ctx
plus the real fold-less-to-WBot effect applied to the hero seat. --calib PATH
writes per-clone strength-score CDFs by street x bet/raise measured on the BASE run's clones (input to t4ctx).
"""
import argparse
import json
import math
import os
import random
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import arena  # noqa: E402  (reuses its loader and engine imports)
from engine import FixedHandsTable  # noqa: E402
from engine.players import LocalPlayer  # noqa: E402

T4 = ["ResonanceQt", "AnkerBatteries", "Chinesepeoplecanfly", "GamesGone", "Poke", "Anton", "YSLTWIZZY"]


def seats_for(field, rng):
    if field == "t4real":
        opps = ["tools/opponents/real/r_%s.py" % n for n in T4]
    elif field == "t4heldout":
        opps = ["tools/opponents/heldout/r_%s_j%d.py" % (n, rng.randrange(2)) for n in T4]
    elif field in ("t4v2", "t4ctx", "t4ctxh"):
        opps = ["%s:%s" % (field[2:], n) for n in T4]
    else:
        raise SystemExit("unknown field " + field)
    rng.shuffle(opps)
    return opps


def run(args):
    cand, base, seed, hands, field, dump = args
    rng = random.Random(seed * 7919 + 13)
    opps = seats_for(field, rng)
    hero = seed % 8
    chips, errs, recs = [], [], []
    for who in (cand, base):
        seats = list(opps)
        seats.insert(hero, who)
        players = [LocalPlayer(_resolve(p, hero)) for p in seats]
        rec = bool(dump) and who == base
        res = FixedHandsTable(players, hands=hands, config={"betting": "no_limit", "raise_cap": 0},
                              seed=seed, record=rec).play()
        chips.append(res["chips"][hero])
        if players[hero].stats.errors:
            errs.append(("ERR", who, players[hero].stats.errors, players[hero].stats.error_samples[:1]))
        for i, pl in enumerate(players):
            if i != hero and pl.stats.errors:
                errs.append(("CLONE_ERR", seats[i], pl.stats.errors, pl.stats.error_samples[:1]))
        if who == base:
            for i, pl in enumerate(players):
                if i != hero and hasattr(pl.agent, "rec"):
                    recs.append((seats[i], pl.agent.rec, getattr(pl.agent, "nfold", None)))
        if rec:
            names = [p.split(":")[-1] if ":" in p else os.path.basename(p)[:-3] for p in seats]
            names[hero] = "HERO"
            hs = []
            for h in res["log"]:
                h = dict(h)
                h["start_stacks"] = h.pop("stacks")
                hs.append(h)
            json.dump({"ref": "arena/r%d" % (seed % 100000), "players": names, "hands": hs},
                      open(os.path.join(dump, "t%d.json" % seed), "w"))
    return chips, errs, recs


def _resolve(p, hero):
    if ":" in p and not os.path.isabs(p):
        import ctx_clone
        variant, stem = p.split(":")
        return ctx_clone.make(stem, variant, hero if variant == "ctxh" else None)
    return arena.load(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cand")
    ap.add_argument("base")
    ap.add_argument("--tables", type=int, default=64)
    ap.add_argument("--hands", type=int, default=300)
    ap.add_argument("--seed", type=int, default=73201)
    ap.add_argument("--field", default="t4real")
    ap.add_argument("--dump", default="")
    ap.add_argument("--calib", default="", help="write per-street score CDFs of the base run's clones here")
    a = ap.parse_args()
    if a.dump:
        os.makedirs(a.dump, exist_ok=True)
    jobs = [(a.cand, a.base, a.seed * 100000 + t, a.hands, a.field, a.dump) for t in range(a.tables)]
    k = 100.0 / 20 / a.hands
    cs, bs, ds = [], [], []
    nerr = 0
    counts = {}  # stem -> street -> score histogram (0..13)
    fid = {}  # stem -> [folds, target p sum, decisions]
    with Pool() as pool:
        for (c, b), errs, recs in pool.imap_unordered(run, jobs):
            for x in errs:
                print(x)
                nerr += 1
            cs.append(c * k); bs.append(b * k); ds.append((c - b) * k)
            for spec, rec, nf in recs:
                f = fid.setdefault(spec, [0, 0.0, 0])
                cnt = counts.setdefault(spec.split(":")[-1], {})
                pool_ = counts.setdefault("ALL", {})
                for st, sc, fo in rec:
                    cnt.setdefault(st, [0] * 14)[sc] += 1
                    pool_.setdefault(st, [0] * 14)[sc] += 1
                    f[0] += fo
                    f[2] += 1
                if nf:
                    f[1] += nf[1]
    if a.calib:
        cdf = {}
        cells = sorted(counts["ALL"])
        for stem, bystreet in counts.items():
            cdf[stem] = {}
            for st in cells:
                v = bystreet.get(st, [0] * 14)
                if sum(v) < 300:  # sparse cell: use the pooled histogram
                    v = counts["ALL"][st]
                tot, acc, out = float(max(1, sum(v))), 0, []
                for x in v:
                    acc += x
                    out.append(round(acc / tot, 6))
                out[-1] = 1.0
                cdf[stem][st] = out
        json.dump(dict(cdf=cdf, counts=counts, source="arena_t4 --field %s --seed %d --tables %d --hands %d base=%s" % (
            a.field, a.seed, a.tables, a.hands, a.base)), open(a.calib, "w"), indent=1)
        print("wrote", a.calib)
    if fid:
        print("clone fold-to-bet in the base run (target = mean real-data p, t4ctx only):")
        for spec in sorted(fid):
            f = fid[spec]
            print("  %-26s n=%6d fold %.3f%s" % (spec, f[2], f[0] / max(1, f[2]),
                                                 "  target %.3f" % (f[1] / f[2]) if f[1] else ""))
    mean = lambda v: sum(v) / len(v)
    se = lambda v: math.sqrt(sum((x - mean(v)) ** 2 for x in v) / max(1, len(v) - 1) / len(v))
    print("field=%s tables=%d hands=%d seed=%d" % (a.field, len(ds), a.hands, a.seed))
    print("  cand %-32s %+8.1f bb/100 (se %.1f)" % (a.cand, mean(cs), se(cs)))
    print("  base %-32s %+8.1f bb/100 (se %.1f)" % (a.base, mean(bs), se(bs)))
    print("  DIFF                                  %+8.1f bb/100 (se %.1f)  z=%.2f" % (
        mean(ds), se(ds), mean(ds) / max(1e-9, se(ds))))
    if nerr:
        print("  WARNING: %d tables had bot errors; results invalid" % nerr)


if __name__ == "__main__":
    main()
