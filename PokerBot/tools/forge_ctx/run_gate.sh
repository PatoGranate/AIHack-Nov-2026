#!/bin/bash
# FORGE paired A/B: forge_ctx_v1 vs its parent N_real (= submissions/N_v10_tuned/bot.py), seeds 73xxx only.
# Run from PokerBot/:  bash tools/forge_ctx/run_gate.sh PYTHON > tools/forge_ctx/gate_results.txt 2>&1
PY=${1:-python}
C=tools/cands/forge_ctx_v1.py
B=tools/cands/N_real.py
for spec in "late 73101" "real 73102" "heldout 73103"; do
  set -- $spec
  echo "## arena.py --field $1 --tables 480 --hands 300 --seed $2"
  $PY tools/arena.py $C $B --tables 480 --hands 300 --field $1 --seed $2 | grep -E "field=|cand|base|DIFF|ERR|WARN"
done
echo "## arena.py --field archive --tables 64 --hands 1000 --seed 73104"
$PY tools/arena.py $C $B --tables 64 --hands 1000 --field archive --seed 73104 | grep -E "field=|cand|base|DIFF|ERR|WARN"
for spec in "t4real 73201" "t4heldout 73202"; do
  set -- $spec
  echo "## forge_ctx/arena_t4.py --field $1 --tables 480 --hands 300 --seed $2"
  $PY tools/forge_ctx/arena_t4.py $C $B --tables 480 --hands 300 --field $1 --seed $2 | grep -E "field=|cand|base|DIFF|ERR|WARN"
done
echo done
