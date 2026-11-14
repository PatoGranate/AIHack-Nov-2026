# Rook: independent validation of the leaderboard-difference increments used by 01/03 (PR #7).
# Usage (from PokerBot/): python -I ExternalAnalysis/AgentReports/ROOK_PR7_validation/lb_validate.py .
import csv, json, glob, collections, sys, os
root = sys.argv[1]; D = root + '/ExternalAnalysis/SaturdayFieldPostmortem/data/'
rows = list(csv.DictReader(open(D + 'leaderboard_history_r13_r48.csv', encoding='utf-8-sig')))
print('rows', len(rows), 'columns', list(rows[0]))
# 1. capture ordering / duplicates
caps = [r['captured_at'] for r in rows]
order_breaks = sum(1 for a, b in zip(caps, caps[1:]) if b < a)
print('captured_at decreases between consecutive rows:', order_breaks)
dup_rows = len(rows) - len({tuple(r.values()) for r in rows})
dup_team_cap = len(rows) - len({(r['captured_at'], r['team']) for r in rows})
print('exact duplicate rows:', dup_rows, '| duplicate (captured_at, team) keys:', dup_team_cap)
bycap = collections.defaultdict(list)
for r in rows: bycap[r['captured_at']].append(r)
print('snapshots:', len(bycap), 'teams per snapshot (min/max):', min(map(len, bycap.values())), max(map(len, bycap.values())))
played_vals = collections.Counter(r['played'] for r in rows)
bad_played = {k: v for k, v in played_vals.items() if k in ('', 'None')}
print('rows with empty/None played:', bad_played)
mixed = [c for c, L in bycap.items() if len({r['played'] for r in L}) > 1]
print('snapshots with mixed played values:', len(mixed))
# played monotone over capture time?
seq = [(c, bycap[c][0]['played']) for c in sorted(bycap)]
pv = [int(p) for _, p in seq if p not in ('', 'None')]
print('played decreases over capture time:', sum(1 for a, b in zip(pv, pv[1:]) if b < a))
P = sorted({int(p) for p in played_vals if p not in ('', 'None')})
print('played values present:', P[0], '-', P[-1], '| missing:', [x for x in range(P[0], P[-1] + 1) if x not in P])
# 2. within one played value, do team chips change between captures? (first vs last matters)
state = collections.defaultdict(lambda: collections.defaultdict(set))
for c in sorted(bycap):
    for r in bycap[c]:
        if r['played'] in ('', 'None'): continue
        state[int(r['played'])][r['team']].add((r['chips'], r['rounds'], r['hands']))
unstable = [(p, t, sorted(v)) for p in state for t, v in state[p].items() if len(v) > 1]
print('(played, team) with >1 distinct chips/rounds/hands across captures:', len(unstable))
for u in unstable[:8]: print('   ', u)
# 3. rounds-count changes between consecutive played values
last = {}
for p in P:
    for t, v in state[p].items():
        last.setdefault(p, {})[t] = sorted(v, key=lambda x: int(x[1]))[-1]
dr = collections.Counter(); oddcases = []
for a, b in zip(P, P[1:]):
    for t, (c, nr, h) in last[b].items():
        if t not in last[a]: oddcases.append((b, t, 'new team')); continue
        d = int(nr) - int(last[a][t][1]); dr[d] += 1
        hd = int(h) - int(last[a][t][2])
        if d == 1 and hd != 1000: oddcases.append((b, t, 'rounds+1 but hands +%d' % hd))
        if d != 1: oddcases.append((b, t, 'rounds +%d, chips %+d' % (d, int(c) - int(last[a][t][0]))))
    for t in last[a]:
        if t not in last[b]: oddcases.append((b, t, 'team vanished'))
print('round-count delta distribution between consecutive played:', dict(dr))
print('irregular team-steps (%d):' % len(oddcases))
for o in oddcases[:25]: print('   ', o)
# 4. reconciliation vs hand-derived team-round results
inc = json.load(open(D + 'per_round_increments.json'))['inc']
files = sorted(glob.glob(root + '/Hand_data/SaturdayRealRounds/*.json') + glob.glob(root + '/Hand_data/ExternalTeamData/*/SaturdayRealRounds/*.json'))
obs = {}
for f in files:
    d = json.loads(open(f, 'rb').read().decode('utf-8-sig'))
    if 'practice' in d['ref']: continue
    rn = int(d['ref'].split('/')[-1][1:])
    for s, p in enumerate(d['players']):
        chips = sum(h['results'][s] for h in d['hands'])
        k = (p, rn)
        if k in obs and obs[k] != chips: print('   CONFLICT between hand files', k, obs[k], chips)
        obs[k] = chips
n = 0; exact = 0; disc = []
for (p, rn), chips in obs.items():
    if p in inc and str(rn) in inc[p]:
        n += 1; lb = inc[p][str(rn)] * 20 * 1000 / 100
        if abs(lb - chips) < 0.5: exact += 1
        else: disc.append((rn, p, chips, round(lb)))
print('team-rounds observed in hands AND in leaderboard increments: %d; exact chip match: %d; discrepant: %d' % (n, exact, len(disc)))
for x in sorted(disc)[:30]: print('    round %d %-24s hands %+d  leaderboard %+d' % x)
cover = collections.Counter(rn for (p, rn) in obs)
miss_inc = sorted({rn for (p, rn) in obs if 14 <= rn <= 48} - {int(k) for v in inc.values() for k in v})
print('hand-covered rounds in 14-48 with no increments at all:', miss_inc)
