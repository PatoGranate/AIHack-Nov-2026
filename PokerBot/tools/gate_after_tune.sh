#!/bin/bash
# waits for the tuning run to finish, then gates its final best candidate vs G (v7); results -> tools/gate_H.txt
cd /c/Users/pelay/AIHack/PokerBot
until grep -q "it49 " tools/tune_log.txt || grep -q "INVALID" tools/tune_log.txt; do sleep 60; done
sleep 30
cp tools/cands/best.py tools/cands/H.py
python - <<'PY'
import sys, json, importlib.util
sys.path.insert(0, 'tools'); from build import build
p = json.load(open('tools/params_best.json')); json.dump(p, open('tools/params_H.json', 'w'), indent=1)
q = dict(p); q.update(max_ms=p['max_ms'] / 5, hard_ms=p['hard_ms'] / 5, max_sims=5000); build('tools/cands/emu_H_core.py', q)
src = open('tools/cands/emu_S1.py', encoding='utf-8').read().replace('emu_S1_core', 'emu_H_core').replace('core_S1', 'core_H')
open('tools/cands/emu_H.py', 'w', encoding='utf-8').write(src)
PY
{
echo "H sha256: $(sha256sum tools/cands/H.py | cut -c1-64)"
echo "accepted changes:"; sed -n '/strength-weighted tuning start/,$p' tools/tune_log.txt | grep ACCEPT
for f in late heldout real; do echo "H vs G $f: $(python tools/arena.py tools/cands/H.py tools/cands/v7.py --tables 240 --hands 300 --field $f --seed 4711 | grep -E 'DIFF|ERR|WARN')"; done
echo "H vs G archive: $(python tools/arena.py tools/cands/H.py tools/cands/v7.py --tables 64 --hands 1000 --field archive --seed 4712 | grep -E 'DIFF|ERR|WARN')"
echo "emuH vs emuG(S1) late: $(python tools/arena.py tools/cands/emu_H.py tools/cands/emu_S1.py --tables 240 --hands 300 --field late --seed 4713 | grep -E 'DIFF|ERR|WARN')"
python tools/fuzz.py tools/cands/H.py | grep -c "errors 0" | sed 's/^/fuzz clean configs (of 8): /'
(cd kit && python local_sim.py ../tools/cands/H.py --rounds 2 | grep -E "H.py|bot ")
} > tools/gate_H.txt 2>&1
echo done
