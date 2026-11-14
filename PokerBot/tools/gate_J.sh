#!/bin/bash
cd /c/Users/pelay/AIHack/PokerBot
{
for f in late real heldout; do echo "gen05 vs srv_I $f $(python tools/arena.py tools/cands/gen05.py tools/cands/srv_I.py --tables 320 --hands 300 --field $f --seed 9901 | grep -E 'DIFF|ERR|WARN')"; done
echo "gen05 vs srv_I archive $(python tools/arena.py tools/cands/gen05.py tools/cands/srv_I.py --tables 64 --hands 1000 --field archive --seed 9902 | grep -E 'DIFF|ERR|WARN')"
echo done
} > tools/gate_J.txt 2>&1
