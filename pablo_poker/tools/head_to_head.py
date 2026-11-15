"""Head-to-head: several real bot files at the same tables, duplicate style, so luck cancels out.

    python tools/head_to_head.py bot.py bot_v32.py path/to/their_best.py [...] --tables 40 --hands 1000

Each table seed is played once per bot rotation: the same cards are dealt every time and the bots
move one seat along, so every bot holds every seat's cards once. Free seats (up to 8) are filled with
the data-driven clones of the real field (sim/fieldbot.py); --fill none plays the files alone
(needs at least 2). --field A = clones answer every bettor alike, B = clones adapt to aggressive
bettors (see tools/bench2.py). Prints each bot's bb/100 with its standard error, and the paired
difference against the first file. Bots keep their own timing logic, so this runs at real speed.
"""
import argparse
import multiprocessing as mp
import os
import shutil
import statistics as st
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def one(job):
    seed, rot, files, hands, fill, field = job
    os.environ["FB_ADAPT"] = "off" if field == "A" else os.path.join(ROOT, "data", "field_adapt.json")
    import sim.fieldbot as fb
    from sim import arena, opponents
    from engine import FixedHandsTable
    fb._MODEL.clear()
    fb.model()
    nb = len(files)
    seats = 8 if fill == "clones" else nb
    clones = opponents.lineup(seed, seats - nb, mix=fb.mix("recent")) if seats > nb else []
    # bot k sits at seat (base_k + rot) % seats, base seats spread evenly round the table
    base = [round(k * seats / nb) for k in range(nb)]
    specs = [None] * seats
    owner = {}
    for k, f in enumerate(files):
        s = (base[k] + rot) % seats
        specs[s] = {"kind": "file", "path": f, "name": "b%d" % k}
        owner[s] = k
    it = iter(clones)
    for s in range(seats):
        if specs[s] is None:
            specs[s] = next(it)
    players = [arena.SeatPlayer(opponents.make(sp, seed * 31 + s), record=False, strategy_id="x")
               for s, sp in enumerate(specs)]
    res = FixedHandsTable(players, hands=hands, config={"betting": "no_limit", "raise_cap": 0}, seed=seed).play()
    return seed, {owner[s]: res["chips"][s] / 20.0 / hands * 100 for s in owner}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("bots", nargs="+")
    ap.add_argument("--tables", type=int, default=40, help="card seeds (each played once per rotation)")
    ap.add_argument("--hands", type=int, default=1000)
    ap.add_argument("--fill", choices=["clones", "none"], default="clones")
    ap.add_argument("--field", choices=["A", "B"], default="A")
    ap.add_argument("--seed0", type=int, default=990000)
    a = ap.parse_args()
    # each file gets its own copy so that two entries never share module state
    tmp = tempfile.mkdtemp(prefix="h2h_", dir=ROOT)
    files = []
    for k, f in enumerate(a.bots):
        dst = os.path.join(tmp, "bot%d_%s" % (k, os.path.basename(f)))
        shutil.copy(f, dst)
        files.append(os.path.relpath(dst, ROOT).replace("\\", "/"))
    nrot = 8 if a.fill == "clones" else len(files)
    jobs = [(a.seed0 + t, r, files, a.hands, a.fill, a.field) for t in range(a.tables) for r in range(nrot)]
    per = {}
    try:
        with mp.Pool(max(2, mp.cpu_count() - 1)) as pool:
            for seed, r in pool.imap_unordered(one, jobs, chunksize=1):
                acc = per.setdefault(seed, {})
                for k, v in r.items():
                    acc.setdefault(k, []).append(v)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    rows = [{k: st.mean(v) for k, v in d.items()} for d in per.values() if all(len(v) == nrot for v in d.values())]
    print("%d card seeds x %d rotations x %d hands, field %s, fill %s" % (len(rows), nrot, a.hands, a.field, a.fill))
    for k, f in enumerate(a.bots):
        x = [r[k] for r in rows]
        d = [r[k] - r[0] for r in rows]
        se = st.stdev(x) / len(x) ** 0.5 if len(x) > 1 else 0.0
        sd = st.stdev(d) / len(d) ** 0.5 if len(d) > 1 else 0.0
        print("  %-40s %+7.1f bb/100 (se %.1f)   vs %s: %+6.1f (se %.1f)" % (
            f[-40:], st.mean(x), se, os.path.basename(a.bots[0]), st.mean(d), sd))
