cd /c/Users/pelay/AIHack/PokerBot
until ! grep -q . /dev/null && [ "$(grep -c DIFF tools/batch_y.txt 2>/dev/null)" -ge 9 ]; do sleep 30; done
{
for f in late real heldout; do echo "Hfast vs G $f $(python tools/arena.py tools/cands/Hfast.py tools/cands/v7.py --tables 320 --hands 300 --field $f --seed 7370 | grep -E 'DIFF|ERR|WARN')"; done
echo "Hfast vs G archive $(python tools/arena.py tools/cands/Hfast.py tools/cands/v7.py --tables 64 --hands 1000 --field archive --seed 7371 | grep -E 'DIFF|ERR|WARN')"
echo "Hfast vs H late $(python tools/arena.py tools/cands/Hfast.py tools/cands/H.py --tables 320 --hands 300 --field late --seed 7372 | grep -E 'DIFF|ERR|WARN')"
python tools/fuzz.py tools/cands/Hfast.py | grep -c "errors 0" | sed 's/^/fuzz clean (of 8): /'
python tools/timing.py tools/cands/Hfast.py 5 | head -1
(cd kit && python local_sim.py ../tools/cands/Hfast.py --rounds 2 | grep -E "Hfast|bot ")
} > tools/gate_Hfast.txt 2>&1
