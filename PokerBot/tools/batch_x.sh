cd /c/Users/pelay/AIHack/PokerBot
for c in x_tight_ep x_tighter x_open30 x_open25 x_tight_30 x_call3b; do for f in late real; do echo "$c vs H $f $(python tools/arena.py tools/cands/$c.py tools/cands/H.py --tables 200 --hands 300 --field $f --seed 5150 | grep -E 'DIFF|ERR|WARN')"; done; done > tools/batch_x.txt 2>&1
