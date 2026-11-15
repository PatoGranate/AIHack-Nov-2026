import os, sys, random
from multiprocessing import Pool
sys.argv += []
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tdarena as A
from engine import FixedHandsTable
from engine.players import LocalPlayer
HERO = sys.argv[1]
def one(job):
    field, seed = job
    opps = list(A.field_list(field, None, [])); random.Random(seed).shuffle(opps)
    seats = opps[:]; seats.insert(0, HERO)
    ps = [LocalPlayer(A.load(p)) for p in seats]
    FixedHandsTable(ps, hands=1000, seed=seed).play()
    ag = ps[0].agent
    return field, len([s for s in ag.gp_changed if s != 0]), sorted(ag.gp_changed.values())
if __name__ == "__main__":
    with Pool() as p:
        R = p.map(one, [(f, 500 + i) for f in ("td_switch", "td") for i in range(20)])
    for f in ("td_switch", "td"):
        r = [x for x in R if x[0] == f]
        print("%-9s flagged %d of %d opponent-rounds; detection hand (window index) median %s" % (
            f, sum(x[1] for x in r), 7 * len(r), sorted(h for x in r for h in x[2])[len([h for x in r for h in x[2]]) // 2] if any(x[2] for x in r) else "-"))
