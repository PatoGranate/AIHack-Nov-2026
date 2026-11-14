"""Realized value of our final decisions in live rounds (value relative to folding at that point)."""
import json, glob, collections, sys
files = sorted(glob.glob('Hand_data/SaturdayRealRounds/saturday_r0*.json'))
if len(sys.argv) > 1: files = [f for f in files if any(a in f for a in sys.argv[1:])]
B = collections.defaultdict(lambda: [0, 0.0, 0, 0])
ex = collections.defaultdict(list)
for f in files:
    d = json.load(open(f, encoding='utf-8')); me = d['seat']; names = d['players']
    for h in d['hands']:
        inv = collections.defaultdict(int); stb = collections.defaultdict(int); st = 'preflop'; pot = 0
        evs = h['events']; nagg = collections.defaultdict(int)
        for i, e in enumerate(evs):
            if e[0] == 'post': inv[e[1]] += e[2]; stb[e[1]] += e[2]; pot += e[2]
            elif e[0] == 'board': st = e[1]; stb = collections.defaultdict(int); 
            elif e[0] == 'act':
                s, a, amt = e[1], e[2], e[3]
                cur = max(stb.values()) if stb else 0
                tc = cur - stb[s]
                if s == me and st != 'preflop' and a in ('call', 'raise'):
                    before = inv[me]
                    add = amt if a == 'call' else amt - stb[s]
                    allin = before + add >= 1990
                    later = any(x[0] == 'act' and x[1] == me for x in evs[i+1:])
                    vs_fold = h['results'][me] + before   # realized value relative to folding now
                    oppagg = max([nagg[j] for j in nagg if j != me] or [0])
                    key = None
                    if a == 'call' and (st == 'river' or allin) :
                        r = add / max(1, pot)
                        key = 'CALL %s %s' % ('all-in' if allin else 'river', '<.4' if r < .4 else '<.8' if r < .8 else '>=.8')
                    elif a == 'raise' and allin and tc > 0:
                        key = 'SHOVE over bet (%s, opp aggr x%d)' % (st, min(oppagg, 3))
                    elif a == 'raise' and allin:
                        key = 'SHOVE as bet (%s)' % st
                    elif a == 'raise' and tc > 0 and not later:
                        key = 'RAISE over bet non-allin (%s)' % st
                    if key:
                        b = B[key]; b[0] += 1; b[1] += vs_fold / 20.0; b[2] += h['results'][me] > 0; b[3] += pot
                        ex[key].append((vs_fold / 20.0, f[-8:-5], h['n']))
                if a == 'call': inv[s] += amt; stb[s] += amt; pot += amt
                elif a == 'raise':
                    ad = amt - stb[s]; inv[s] += ad; stb[s] = amt; pot += ad
                    if st != 'preflop': nagg[s] += 1
print('%-40s %5s %12s %10s %6s %9s' % ('decision', 'n', 'value vs fold', 'per time', 'win%', 'avg pot'))
for k in sorted(B):
    n, v, w, p = B[k]
    print('%-40s %5d %+12.0f %+10.1f %5.0f%% %9.0f' % (k, n, v, v / n, 100 * w / n, p / n / 20))
