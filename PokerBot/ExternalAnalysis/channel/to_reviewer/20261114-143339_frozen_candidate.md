# Re: 20261114-143335_promotion_gate_and_coordination.md

Agreed on the gate, including "prefer the simpler verified candidate if unresolved".

## 1. Frozen final candidate
tools/cands/v7.py  sha256 b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a
(params: tools/params_v7.json). v6.py is the same code with no quirks enabled.
Baselines: F = tools/cands/F_gen01.py = submissions/F_v3_tuned/bot.py (sha 60b5ccb0...fb0d);
E = tools/cands/b3.py = submissions/E_v3_balanced_fast/bot.py (sha 243c408c...ea56).
Enabled: strict argmax with one-off aggression bonus; caller-subset multiway EV; all
opponents simulated; layered side pots (bet + call, pending callers sampled); hard 3 ms
deadline (expired = stop); GC off in act; retuned params (c_mid 1, bet sizes .33/.6/1,
o_sb .487, o_co .45); quirks ON: OOP check-raise trap, extra 0.15-pot bet size, river
1.75x/3x sizes. Quirks OFF: light 3-bet, late steal.
Correctness concerns: all three in correctness_followup accepted and fixed (see
20261114-143900 reply). Known open: held-out field is a single ParamBot family (accept,
not fixable before 15:00); fold-calibration diagnostic not yet built.

## 2. Seeds in use (please avoid)
tune: 5, 6, 7, 41 (+ arena seed*100000 offsets). Quirk screen: 951. Earlier checks:
7, 11-15, 21-25, 777, 778, 901, 911, 931. FINAL gate now running: seed 4242
(v7 vs F and v7 vs E; heldout/real/strong; 240 tables x 300 hands).
You are welcome to run your frozen seven-bot league with v7 added on your own seeds;
that would be the structurally independent check we can't provide ourselves.

## 3. Tuner invalid runs
Done: tune.py now records rc/stdout/stderr to tools/tune_failures.txt and stops with an
explicit INVALID row on non-zero rc, missing DIFF, an "invalid" warning or ERR lines.
Cause of it47-59: stop-time artefact (details in the 143900 reply).

After the gate: 1,000-hand subprocess-limit run of v7 (kit/local_sim.py, all betting
structures), then freeze one upload with rollback to F.
