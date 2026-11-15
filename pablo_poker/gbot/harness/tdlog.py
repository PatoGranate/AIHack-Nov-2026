"""Play Table D tables with one hero file and write real-format logs (for adaptation-slope checks).
    python tools/tdlog.py HERO.py OUTDIR --field td_fb --tables 16 --hands 1000 --seed 61"""
import os, sys, json, random, argparse
from multiprocessing import Pool
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tdarena as A
from engine import FixedHandsTable
from engine.players import LocalPlayer
def one(job):
    hero, out, field, seed, hands = job
    opps = list(A.field_list(field, None, [])); random.Random(seed).shuffle(opps)
    hs = seed % 8; seats = opps[:]; seats.insert(hs, hero)
    ps = [LocalPlayer(A.load(p)) for p in seats]
    res = FixedHandsTable(ps, hands=hands, seed=seed, record=True).play()
    names = ["HERO" if i == hs else os.path.basename(p)[2:-3] for i, p in enumerate(seats)]
    hl = []
    for r in res["log"]:
        r["results"] = [e - s for e, s in zip(r["end"], r["stacks"])]; r.setdefault("showdown", {}); hl.append(r)
    d = {"players": names, "seat": hs, "round": {"slot": "td-%d" % seed}, "hands": hl}
    json.dump(d, open(os.path.join(out, "saturday_r%03d.json" % (seed % 1000)), "w"))
    return seed
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("hero"); ap.add_argument("out")
    ap.add_argument("--field", default="td_fb"); ap.add_argument("--tables", type=int, default=16)
    ap.add_argument("--hands", type=int, default=1000); ap.add_argument("--seed", type=int, default=61)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    with Pool() as p:
        list(p.imap_unordered(one, [(a.hero, a.out, a.field, a.seed * 1000 + t, a.hands) for t in range(a.tables)]))
    print("wrote", a.tables)
