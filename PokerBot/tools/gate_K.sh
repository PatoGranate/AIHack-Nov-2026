#!/bin/bash
cd /c/Users/pelay/AIHack/PokerBot
{
for f in late real heldout; do echo "gen08 vs srv_I $f $(python tools/arena.py tools/cands/gen08.py tools/cands/srv_I.py --tables 320 --hands 300 --field $f --seed 9911 | grep -E 'DIFF|ERR|WARN')"; done
echo "gen08 vs srv_I archive $(python tools/arena.py tools/cands/gen08.py tools/cands/srv_I.py --tables 64 --hands 1000 --field archive --seed 9912 | grep -E 'DIFF|ERR|WARN')"
echo done
} > tools/gate_K.txt 2>&1
