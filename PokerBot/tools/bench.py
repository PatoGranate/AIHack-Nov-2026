"""Fast in-process benchmark: python tools/bench.py botA.py [botB.py ...] --rounds N --hands H
Each named bot gets a seat; the rest are filled with house bots + starter. Runs rounds in parallel."""
import sys, os, random, argparse, importlib.util
from multiprocessing import Pool
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "kit"))
from engine import FixedHandsTable
from engine.players import LocalPlayer
POOL = ["kit/examples/tight_aggressive.py", "kit/examples/calling_station.py", "kit/examples/random_bot.py", "tools/opponents/starter.py"]

def load(path, tag):
    spec = importlib.util.spec_from_file_location("b%d_%s" % (tag, os.path.basename(path)[:-3]), os.path.join(ROOT, path) if not os.path.isabs(path) else path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m.Agent

def run(args):
    bots, seed, hands, betting = args
    rng = random.Random(seed)
    seats = list(bots)
    while len(seats) < 8: seats.append(rng.choice(POOL))
    rng.shuffle(seats)
    players = [LocalPlayer(load(p, i)) for i, p in enumerate(seats)]
    res = FixedHandsTable(players, hands=hands, config={"betting": betting}, seed=seed).play()
    out = {}
    for i, p in enumerate(seats):
        out.setdefault(p, [0, 0]); out[p][0] += res["chips"][i]; out[p][1] += hands
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("bots", nargs="+"); ap.add_argument("--rounds", type=int, default=16)
    ap.add_argument("--hands", type=int, default=500); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--betting", default="no_limit")
    a = ap.parse_args()
    tot = {}
    with Pool() as pool:
        for out in pool.imap_unordered(run, [(a.bots, a.seed * 1000 + r, a.hands, a.betting) for r in range(a.rounds)]):
            for k, (c, h) in out.items():
                t = tot.setdefault(k, [0, 0]); t[0] += c; t[1] += h
    for k, (c, h) in sorted(tot.items(), key=lambda kv: -kv[1][0] / kv[1][1]):
        print("%-40s %+9.1f bb/100  (%d hands)" % (k, c / 20 / h * 100, h))
