#!/bin/bash
# clean gate: identical template/source, identical server-scaled caps (1.2/2.8) and bank 1.4 for both bots
cd /c/Users/pelay/AIHack/PokerBot
{
for f in late real heldout; do echo "cN vs cI $f 480t x300h seed 5501 $(python tools/arena.py tools/cands/cN.py tools/cands/cI.py --tables 480 --hands 300 --field $f --seed 5501 | grep -E 'DIFF|ERR|WARN')"; done
echo "cN vs cI archive 64t x1000h seed 5502 $(python tools/arena.py tools/cands/cN.py tools/cands/cI.py --tables 64 --hands 1000 --field archive --seed 5502 | grep -E 'DIFF|ERR|WARN')"
echo done
} > tools/gate_O.txt 2>&1
