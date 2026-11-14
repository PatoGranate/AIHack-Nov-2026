"""Our live results by preflop line and position (G rounds)."""
import json, glob, collections
B = collections.defaultdict(lambda: [0, 0.0]); Pn = collections.defaultdict(lambda: [0, 0.0])
for f in sorted(glob.glob('Hand_data/SaturdayRealRounds/saturday_r0*.json')):
    d = json.load(open(f, encoding='utf-8')); me = d['seat']; n = len(d['players'])
    for h in d['hands']:
        nr = 0; line = []; first_in = True
        for e in h['events']:
            if e[0] == 'board': break
            if e[0] != 'act': continue
            s, a = e[1], e[2]
            if s == me:
                if a == 'raise': line.append(['open' if first_in else 'iso', '3bet', '4bet', '5bet+'][min(nr, 3)])
                elif a == 'call': line.append(['limp', 'call-open', 'call-3bet', 'call-4bet+'][min(nr, 3)])
                elif a == 'fold': line.append('fold' + ('-to-%s' % ['', 'open', '3bet', '4bet+'][min(nr, 3)] if line else ''))
                elif a == 'check': line.append('check')
            if a == 'raise': nr += 1
            if a in ('raise', 'call'): first_in = False
        k = ' > '.join(line) or 'walk'
        pos = (me - h['button']) % n
        pn = {0: 'BTN', 1: 'SB', 2: 'BB'}.get(pos, 'CO' if pos == n - 1 else 'EP/MP')
        B[k][0] += 1; B[k][1] += h['results'][me] / 20.0
        if line and line[0] != 'fold': Pn[pn + ' | ' + line[0]][0] += 1; Pn[pn + ' | ' + line[0]][1] += h['results'][me] / 20.0
print('%-34s %6s %9s %8s' % ('preflop line', 'n', 'net bb', 'bb/hand'))
for k, (c, v) in sorted(B.items(), key=lambda kv: kv[1][1]):
    if c >= 8: print('%-34s %6d %+9.0f %+8.2f' % (k, c, v, v / c))
print()
for k, (c, v) in sorted(Pn.items()):
    if c >= 15: print('%-34s %6d %+9.0f %+8.2f' % (k, c, v, v / c))
