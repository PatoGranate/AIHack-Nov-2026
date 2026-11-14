cd /c/Users/pelay/AIHack/PokerBot
{
echo "I sha256 $(sha256sum tools/cands/I.py | cut -c1-64); clones $(python -c "import json;print(json.load(open('tools/opponents/real/MANIFEST.json'))['combined_sha256'][:16])")"
for f in late real heldout; do echo "srv_I vs srv_G $f $(python tools/arena.py tools/cands/srv_I.py tools/cands/srv_G.py --tables 320 --hands 300 --field $f --seed 8801 | grep -E 'DIFF|ERR|WARN')"; done
echo "srv_I vs srv_G archive $(python tools/arena.py tools/cands/srv_I.py tools/cands/srv_G.py --tables 64 --hands 1000 --field archive --seed 8802 | grep -E 'DIFF|ERR|WARN')"
for f in late real; do echo "srv_H25 vs srv_H $f (more time only) $(python tools/arena.py tools/cands/srv_H25.py tools/cands/srv_H.py --tables 320 --hands 300 --field $f --seed 8803 | grep -E 'DIFF|ERR|WARN')"; done
for f in late real; do echo "srv_I vs srv_H25 $f (strategy only) $(python tools/arena.py tools/cands/srv_I.py tools/cands/srv_H25.py --tables 320 --hands 300 --field $f --seed 8804 | grep -E 'DIFF|ERR|WARN')"; done
(cd kit && python local_sim.py ../tools/cands/I.py --rounds 2 --timeout 25 | grep -E "I.py|bot ")
} > tools/gate_I.txt 2>&1
