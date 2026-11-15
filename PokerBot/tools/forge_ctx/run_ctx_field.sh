#!/bin/bash
# FORGE pre-registered runs (channel 20261115-093000). Run from PokerBot/:
#   bash tools/forge_ctx/run_ctx_field.sh PYTHON > tools/forge_ctx/ctx_field_results.txt 2>&1
PY=${1:-python}
G=submissions/G_v7_final/bot.py
GC=tools/cands/g_ctx_v1.py
A=tools/forge_ctx/arena_t4.py
F="field=|cand|base|DIFF|ERR|WARN"
echo "## A0 G vs G, t4ctx, 960x300, seed 73501"; $PY $A $G $G --tables 960 --hands 300 --field t4ctx --seed 73501 | grep -E "$F"
echo "## P1 g_ctx_v1 vs G, t4ctx, 1920x300, seed 73502"; $PY $A $GC $G --tables 1920 --hands 300 --field t4ctx --seed 73502 | grep -E "$F"
echo "## C1 g_ctx_v1 vs G, t4v2, 1920x300, seed 73503"; $PY $A $GC $G --tables 1920 --hands 300 --field t4v2 --seed 73503 | grep -E "$F"
echo "## S1 forge_ctx_v1 vs N_real, t4ctx, 1920x300, seed 73504"; $PY $A tools/cands/forge_ctx_v1.py tools/cands/N_real.py --tables 1920 --hands 300 --field t4ctx --seed 73504 | grep -E "$F"
echo "## S2 g_ctx_v1 vs G, t4ctx, 576x1000, seed 73505"; $PY $A $GC $G --tables 576 --hands 1000 --field t4ctx --seed 73505 | grep -E "$F"
echo done
