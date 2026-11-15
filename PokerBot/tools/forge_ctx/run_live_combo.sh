#!/bin/bash
# FORGE pre-registration 2 (channel 20261115-093500). Run from PokerBot/:
#   bash tools/forge_ctx/run_live_combo.sh PYTHON > tools/forge_ctx/live_combo_results.txt 2>&1
PY=${1:-python}
G=submissions/G_v7_final/bot.py
LIVE=tools/cands/G_profile_td_sunday_s1_r003.py
COMBO=tools/cands/forge_gctx_profile_r003.py
A=tools/forge_ctx/arena_t4.py
F="field=|cand|base|DIFF|ERR|WARN"
echo "## L0 live vs live, t4ctxh, 960x300, seed 73601"; $PY $A $LIVE $LIVE --tables 960 --hands 300 --field t4ctxh --seed 73601 | grep -E "$F"
echo "## L1 combo vs live, t4ctxh, 1920x300, seed 73602"; $PY $A $COMBO $LIVE --tables 1920 --hands 300 --field t4ctxh --seed 73602 | grep -E "$F"
echo "## L2 combo vs live, t4v2, 1920x300, seed 73603"; $PY $A $COMBO $LIVE --tables 1920 --hands 300 --field t4v2 --seed 73603 | grep -E "$F"
echo "## H1 g_ctx_v1 vs G, t4ctxh, 1920x300, seed 73604"; $PY $A tools/cands/g_ctx_v1.py $G --tables 1920 --hands 300 --field t4ctxh --seed 73604 | grep -E "$F"
echo "## H2 forge_ctx_v2 vs forge_ctx_v1, t4ctxh, 1920x300, seed 73605"; $PY $A tools/cands/forge_ctx_v2.py tools/cands/forge_ctx_v1.py --tables 1920 --hands 300 --field t4ctxh --seed 73605 | grep -E "$F"
echo "## K1a forge_k1a_r003 vs live r003 (ftb pseudo-count 8 -> 20, 400-hand window), t4ctxh, 1920x300, seed 73607"; $PY $A tools/cands/forge_k1a_r003.py $LIVE --tables 1920 --hands 300 --field t4ctxh --seed 73607 | grep -E "$F"
echo "## K1b forge_k1b_r003 vs live r003 (pseudo-count 20 + full-round counts), t4ctxh, 1920x300, seed 73608"; $PY $A tools/cands/forge_k1b_r003.py $LIVE --tables 1920 --hands 300 --field t4ctxh --seed 73608 | grep -E "$F"
echo "## S1 (rescheduled) forge_ctx_v1 vs N_real, t4ctx, 1920x300, seed 73504"; $PY $A tools/cands/forge_ctx_v1.py tools/cands/N_real.py --tables 1920 --hands 300 --field t4ctx --seed 73504 | grep -E "$F"
echo done
