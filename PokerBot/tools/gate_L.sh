#!/bin/bash
cd /c/Users/pelay/AIHack/PokerBot
{
for f in late real heldout; do echo "gen08 vs srv_I $f (seed2) $(python tools/arena.py tools/cands/gen08.py tools/cands/srv_I.py --tables 480 --hands 300 --field $f --seed 7321 | grep -E 'DIFF|ERR|WARN')"; done
echo done
} > tools/gate_L.txt 2>&1
