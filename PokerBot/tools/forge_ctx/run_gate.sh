#!/bin/bash
# FORGE paired A/B, seeds 73xxx only. Run from PokerBot/:
#   bash tools/forge_ctx/run_gate.sh PYTHON [CAND BASE SEEDBLOCK] > tools/forge_ctx/gate_results.txt 2>&1
# defaults: forge_ctx_v1 vs N_real (= submissions/N_v10_tuned/bot.py), seed block 731 -> 73101-73104, 73201-73202
# v2 vs v1:  bash tools/forge_ctx/run_gate.sh PY tools/cands/forge_ctx_v2.py tools/cands/forge_ctx_v1.py 733
#            -> seeds 73301-73304, 73401-73402
PY=${1:-python}
C=${2:-tools/cands/forge_ctx_v1.py}
B=${3:-tools/cands/N_real.py}
K=${4:-731}
K2=$((K + 1))
for spec in "late ${K}01" "real ${K}02" "heldout ${K}03"; do
  set -- $spec
  echo "## arena.py --field $1 --tables 480 --hands 300 --seed $2"
  $PY tools/arena.py $C $B --tables 480 --hands 300 --field $1 --seed $2 | grep -E "field=|cand|base|DIFF|ERR|WARN"
done
echo "## arena.py --field archive --tables 64 --hands 1000 --seed ${K}04"
$PY tools/arena.py $C $B --tables 64 --hands 1000 --field archive --seed ${K}04 | grep -E "field=|cand|base|DIFF|ERR|WARN"
for spec in "t4real ${K2}01" "t4heldout ${K2}02"; do
  set -- $spec
  echo "## forge_ctx/arena_t4.py --field $1 --tables 480 --hands 300 --seed $2"
  $PY tools/forge_ctx/arena_t4.py $C $B --tables 480 --hands 300 --field $1 --seed $2 | grep -E "field=|cand|base|DIFF|ERR|WARN"
done
echo done
