"""FORGE: duplicate A/B on a Sunday table-4 clone field (exactly the 7 table-4 opponents + hero).

    python tools/forge_ctx/arena_t4.py CAND.py BASE.py --tables 480 --hands 300 --field t4real --seed 73201

Same pairing as tools/arena.py (same seed, same seating, same cards; CAND then BASE in the hero
seat), but the seat list is fixed to the table-4 clones, shuffled per table, instead of drawn with
replacement. Fields: t4real = tools/opponents/real/r_<name>.py; t4heldout = heldout r_<name>_j0/_j1,
chosen per seat per table. --dump DIR writes the BASE run's hand logs in Hand_data format so
extract_events.py can measure the clones' fold-to-bet by context.
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
import arena  # noqa: E402  (reuses its loader and engine imports)
from engine import FixedHandsTable  # noqa: E402
from engine.players import LocalPlayer  # noqa: E402

T4 = ["ResonanceQt", "AnkerBatteries", "Chinesepeoplecanfly", "GamesGone", "Poke", "Anton", "YSLTWIZZY"]


def seats_for(field, rng):
    if field == "t4real":
        opps = ["tools/opponents/real/r_%s.py" % n for n in T4]
    elif field == "t4heldout":
        opps = ["tools/opponents/heldout/r_%s_j%d.py" % (n, rng.randrange(2)) for n in T4]
    else:
        raise SystemExit("unknown field " + field)
    rng.shuffle(opps)
    return opps


def run(args):
    cand, base, seed, hands, field, dump = args
    rng = random.Random(seed * 7919 + 13)
    opps = seats_for(field, rng)
    hero = seed % 8
    chips, errs = [], []
    for who in (cand, base):
        seats = list(opps)
        seats.insert(hero, who)
        players = [LocalPlayer(arena.load(p)) for p in seats]
        rec = bool(dump) and who == base
        res = FixedHandsTable(players, hands=hands, config={"betting": "no_limit", "raise_cap": 0},
                              seed=seed, record=rec).play()
        chips.append(res["chips"][hero])
        if players[hero].stats.errors:
            errs.append(("ERR", who, players[hero].stats.errors, players[hero].stats.error_samples[:1]))
        if rec:
            names = [os.path.basename(p)[:-3] for p in seats]
            names[hero] = "HERO"
            hs = []
            for h in res["log"]:
                h = dict(h)
                h["start_stacks"] = h.pop("stacks")
                hs.append(h)
            json.dump({"ref": "arena/r%d" % (seed % 100000), "players": names, "hands": hs},
                      open(os.path.join(dump, "t%d.json" % seed), "w"))
    return chips, errs, opps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cand")
    ap.add_argument("base")
    ap.add_argument("--tables", type=int, default=64)
    ap.add_argument("--hands", type=int, default=300)
    ap.add_argument("--seed", type=int, default=73201)
    ap.add_argument("--field", default="t4real")
    ap.add_argument("--dump", default="")
    a = ap.parse_args()
    if a.dump:
        os.makedirs(a.dump, exist_ok=True)
    jobs = [(a.cand, a.base, a.seed * 100000 + t, a.hands, a.field, a.dump) for t in range(a.tables)]
    k = 100.0 / 20 / a.hands
    cs, bs, ds = [], [], []
    nerr = 0
    with Pool() as pool:
        for (c, b), errs, _ in pool.imap_unordered(run, jobs):
            for x in errs:
                print(x)
                nerr += 1
            cs.append(c * k); bs.append(b * k); ds.append((c - b) * k)
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
