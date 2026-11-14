import re, ast, glob, hashlib, json, os, random, math
f='tools/opponents/real/r_Gherkers.py'; t=open(f,encoding='utf-8').read()
d=ast.literal_eval(re.search(r"PARAMS = (\{.*\})", t).group(1)); d.update(trapper=True, trap_min=2)
open(f,'w',encoding='utf-8').write(t.replace(re.search(r"PARAMS = (\{.*\})", t).group(1), repr(d)))
rng = random.Random(4040)
for g in glob.glob('tools/opponents/heldout/*.py'): os.remove(g)
out = []
for line in open('tools/opponents/real/weights.txt', encoding='utf-8'):
    fn, h, bb = line.split(); h = int(h); bb = float(bb)
    w = min(4.0, max(0.35, math.exp(bb / 120.0))) * min(2.0, math.sqrt(h / 1000.0))
    t = open(fn, encoding='utf-8').read(); d = ast.literal_eval(re.search(r"PARAMS = (\{.*\})", t).group(1))
    for v in range(2):
        q = dict(d)
        for k, x in d.items():
            if isinstance(x, float) and k != 'open_size': q[k] = round(min(0.95, max(0.0, x * rng.uniform(0.7, 1.3))), 3)
            if k in ('call_min', 'bet_min') and rng.random() < 0.3: q[k] = max(0, x + rng.choice([-1, 1]))
        q['bet_frac'] = rng.choice([0.4, 0.6, 0.75, 1.0])
        name = 'tools/opponents/heldout/' + os.path.basename(fn)[:-3] + '_j%d.py' % v
        open(name, 'w', encoding='utf-8').write(t.replace(repr(d), repr(q)))
        out += [name] * max(1, int(round(w * 2)))
open('tools/opponents/heldout/list.txt', 'w', encoding='utf-8').write('\n'.join(out))
files = sorted(f for f in glob.glob('tools/opponents/real/*') + glob.glob('tools/opponents/heldout/*') if os.path.isfile(f) and not f.endswith('MANIFEST.json')) + ['tools/opponents/_common.py', 'tools/opponents/a_trapper.py']
for fn in files: open(fn,'rb').read().decode('utf-8')
man = {fn.replace(chr(92),'/'): hashlib.sha256(open(fn,'rb').read()).hexdigest() for fn in files}
comb = hashlib.sha256(''.join(k+v for k,v in sorted(man.items())).encode()).hexdigest()
json.dump({'combined_sha256': comb, 'files': man, 'weighting': 'w=clip(exp(bb100/120),0.35,4)*min(2,sqrt(hands/1000))'}, open('tools/opponents/real/MANIFEST.json','w',encoding='utf-8'), indent=1)
print('combined', comb)
import sys, collections
sys.path.insert(0,'tools'); import arena
c = collections.Counter(os.path.basename(x)[2:-3] for x in arena.REAL); tot = sum(c.values())
bbm = {l.split()[0].split('/')[-1][2:-3]: float(l.split()[2]) for l in open('tools/opponents/real/weights.txt', encoding='utf-8')}
strong = sum(v for k, v in c.items() if bbm[k] > 30); weak = sum(v for k, v in c.items() if bbm[k] < 0)
print('seat draw share: strong(>+30) %.0f%%  middling %.0f%%  losing %.0f%%' % (100*strong/tot, 100*(tot-strong-weak)/tot, 100*weak/tot))
for k, v in c.most_common(6): print('  %-24s %4.1f%%  (bb/100 %+.0f)' % (k, 100*v/tot, bbm[k]))
for k, v in sorted(c.items(), key=lambda kv: bbm[kv[0]])[:3]: print('  %-24s %4.1f%%  (bb/100 %+.0f)' % (k, 100*v/tot, bbm[k]))
