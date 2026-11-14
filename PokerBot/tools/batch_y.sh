cd /c/Users/pelay/AIHack/PokerBot
for c in y_real_up y_open28 y_real_up_open28; do for f in late real heldout; do echo "$c vs H $f $(python tools/arena.py tools/cands/$c.py tools/cands/H.py --tables 320 --hands 300 --field $f --seed 6260 | grep -E 'DIFF|ERR|WARN')"; done; done > tools/batch_y.txt 2>&1
