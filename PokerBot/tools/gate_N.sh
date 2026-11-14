#!/bin/bash
cd /c/Users/pelay/AIHack/PokerBot
{
for f in late real heldout; do echo "N(gen14,srv) vs srv_I $f $(python tools/arena.py tools/cands/N.py tools/cands/srv_I.py --tables 480 --hands 300 --field $f --seed 8123 | grep -E 'DIFF|ERR|WARN')"; done
echo "N vs srv_I archive $(python tools/arena.py tools/cands/N.py tools/cands/srv_I.py --tables 64 --hands 1000 --field archive --seed 8124 | grep -E 'DIFF|ERR|WARN')"
echo "N vs srv_G late $(python tools/arena.py tools/cands/N.py tools/cands/srv_G.py --tables 320 --hands 300 --field late --seed 8125 | grep -E 'DIFF|ERR|WARN')"
echo done
} > tools/gate_N.txt 2>&1
