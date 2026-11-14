"""Provenance fingerprint for Saturday real rounds (stdlib only, read-only).
Usage: python -I fp.py <dir with saturday_r*.json>
Prints, per server version (round.version):
  1. round metadata: rounds, hands, mean round bb/100, think_s range, timeouts, errors, bank-outs;
  2. first-in open rate by position, in two forms: 'unopened' (no raise AND no limp
     before hero) and 'incl-limp' (no raise before hero; limped pots count);
  3. distribution of hero first-in raise sizes in big blinds (BB = 20 chips, from the hand's 'bb' field);
  4. a two-proportion z test of the EP unopened open rate, v8 vs every other version.
Positions: seats after BB up to HJ = EP; HJ = 2 before BTN; CO = 1 before BTN.
"""
import json, glob, sys, collections, math
D = sys.argv[1]
def pos_name(seat, button, n):
    k = (seat - button) % n
    if k == 0: return 'BTN'
    if k == 1: return 'SB'
    if k == 2: return 'BB'
    return {1: 'CO', 2: 'HJ'}.get(n - k, 'EP')
meta = collections.defaultdict(lambda: {'rounds': 0, 'hands': 0, 'bb100': [], 'think': [], 'to': 0, 'err': 0, 'bo': 0, 'ids': []})
cnt = collections.defaultdict(collections.Counter)
sizes = collections.defaultdict(collections.Counter)
for f in sorted(glob.glob(D + '/saturday_r*.json')):
    d = json.load(open(f)); r = d['round']; v = 'v%d' % r['version']; me = d['seat']
    m = meta[v]; m['rounds'] += 1; m['hands'] += len(d['hands']); m['bb100'].append(r['bb100'])
    m['think'].append(r['think_s']); m['to'] += r['timeouts']; m['err'] += r['errors']; m['bo'] += r['bank_out']
    m['ids'].append(r['ref'].split('/')[-1])
    for h in d['hands']:
        p = pos_name(me, h['button'], len(h['start_stacks'])); bb = h.get('bb', 20)
        raised = limped = False
        for e in h['events']:
            if e[0] == 'board': break
            if e[0] != 'act': continue
            _, s, a, amt = e
            if s == me:
                if not raised:
                    keys = [(v, p, 'incl')] + ([] if limped else [(v, p, 'unop')])
                    for k in keys:
                        cnt[k]['fi'] += 1
                        if a == 'raise': cnt[k]['open'] += 1
                    if a == 'raise': sizes[v][round(amt / bb, 2)] += 1
                break
            if a == 'raise': raised = True
            elif a == 'call': limped = True
print('== round metadata')
for v in sorted(meta, key=lambda x: int(x[1:])):
    m = meta[v]
    print('%s %s-%s rounds=%d hands=%d mean_bb100=%+.1f think=%.2f-%.2fs timeouts=%d errors=%d bankouts=%d' % (
        v, m['ids'][0], m['ids'][-1], m['rounds'], m['hands'], sum(m['bb100']) / m['rounds'],
        min(m['think']), max(m['think']), m['to'], m['err'], m['bo']))
for kind in ('unop', 'incl'):
    print('== first-in open rate (%s)' % ('unopened only' if kind == 'unop' else 'incl. limped pots'))
    for v in sorted(meta, key=lambda x: int(x[1:])):
        row = ['%s %.3f(%d)' % (p, cnt[(v, p, kind)]['open'] / max(1, cnt[(v, p, kind)]['fi']), cnt[(v, p, kind)]['fi'])
               for p in ('EP', 'HJ', 'CO', 'BTN', 'SB')]
        print(v, ' '.join(row))
print('== first-in raise sizes (bb), top 4')
for v in sorted(meta, key=lambda x: int(x[1:])):
    print(v, 'n=%d' % sum(sizes[v].values()), sizes[v].most_common(4))
print('== EP unopened open rate, z vs v8')
b = cnt[('v8', 'EP', 'unop')]
for v in sorted(meta, key=lambda x: int(x[1:])):
    a = cnt[(v, 'EP', 'unop')]
    if v == 'v8' or not a['fi'] or not b['fi']: continue
    p = (a['open'] + b['open']) / (a['fi'] + b['fi'])
    z = (a['open'] / a['fi'] - b['open'] / b['fi']) / math.sqrt(p * (1 - p) * (1 / a['fi'] + 1 / b['fi']))
    print('%s %.3f vs v8 %.3f  z=%.2f' % (v, a['open'] / a['fi'], b['open'] / b['fi'], z))
