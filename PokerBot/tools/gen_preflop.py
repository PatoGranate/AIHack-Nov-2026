"""Offline: preflop equity tables -> tools/preflop_tables.py
RANK: 169 classes ordered best->worst by HU equity vs random.
EQR[cls][j]: HU equity of cls vs top-F[j] of combos (by RANK order).
EQM[cls][k]: equity vs k random opponents (k=1..7)."""
import sys, os, random
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fasteval import RT, FL, CP, CB, RANKS

F = [0.03, 0.05, 0.08, 0.12, 0.17, 0.23, 0.30, 0.40, 0.55, 0.75, 1.0]
CLASSES = []
for i in range(12, -1, -1):
    for j in range(12, -1, -1):
        if i == j: CLASSES.append(RANKS[i] + RANKS[j])
        elif i > j: CLASSES.append(RANKS[i] + RANKS[j] + "s"); CLASSES.append(RANKS[i] + RANKS[j] + "o")

def combos(cls):
    a, b = RANKS.index(cls[0]), RANKS.index(cls[1])
    out = []
    for s1 in range(4):
        for s2 in range(4):
            c1, c2 = a * 4 + s1, b * 4 + s2
            if c1 == c2: continue
            if len(cls) == 2 and s1 >= s2: continue
            if len(cls) == 3 and cls[2] == "s" and s1 != s2: continue
            if len(cls) == 3 and cls[2] == "o" and s1 == s2: continue
            out.append((c1, c2))
    return out

def ev7(cs):
    p = 1; sc = [0]*4; sm = [0]*4
    for c in cs:
        p *= CP[c]; s = c & 3; sc[s] += 1; sm[s] |= CB[c]
    v = RT[p]
    for s in range(4):
        if sc[s] >= 5:
            f = FL[sm[s]]
            if f > v: v = f
    return v

def eq(args):
    cls, opp_list, k, n, seed = args
    rng = random.Random(seed)
    mine = combos(cls)
    tot = 0.0
    for it in range(n):
        h = mine[it % len(mine)]
        used = set(h)
        opps = []
        while len(opps) < k:
            o = opp_list[rng.randrange(len(opp_list))] if opp_list else tuple(rng.sample(range(52), 2))
            if o[0] in used or o[1] in used: continue
            used.update(o); opps.append(o)
        deck = [c for c in range(52) if c not in used]
        bd = rng.sample(deck, 5)
        me = ev7(list(h) + bd)
        best = 0; ties = 0
        for o in opps:
            v = ev7(list(o) + bd)
            if v > best: best, ties = v, 0
            elif v == best: ties += 1
        tot += 1 if me > best else (1.0 / (ties + 2) if me == best else 0)
    return cls, tot / n

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    OUT = sys.argv[2] if len(sys.argv) > 2 else "preflop_tables.py"
    with Pool() as pool:
        base = dict(pool.map(eq, [(c, None, 1, N * 2, 1) for c in CLASSES]))
        rank = sorted(CLASSES, key=lambda c: -base[c])
        allc = []
        for c in rank: allc.extend(combos(c))
        eqr = {c: [] for c in CLASSES}
        for f in F:
            top = allc[:max(1, int(round(f * 1326)))]
            for c, e in pool.map(eq, [(c, top, 1, N, 2) for c in CLASSES]):
                eqr[c].append(round(e, 3))
        eqm = {c: [] for c in CLASSES}
        for k in range(1, 8 if "--eqm" in sys.argv else 1):
            for c, e in pool.map(eq, [(c, None, k, N, 3 + k) for c in CLASSES]):
                eqm[c].append(round(e, 3))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT), "w") as fh:
        fh.write("RANK = %r\n" % rank)
        fh.write("F = %r\n" % F)
        fh.write("EQR = %r\n" % {c: eqr[c] for c in rank})
        fh.write("EQM = %r\n" % {c: eqm[c] for c in rank})
    print("done", rank[:20])
