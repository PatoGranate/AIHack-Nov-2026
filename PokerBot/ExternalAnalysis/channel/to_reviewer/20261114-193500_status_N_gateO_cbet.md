# Status (19:35) - answers to 191922 + audits since 182300

1) N is live: user confirms site v8 = N (v7 = G re-uploaded; v5 = old G). Artifact = submissions/N_v10_tuned/bot.py = tools/cands/N_real.py, sha 5c2b4b2c0ed3ddd5...; 6/14 ms, bank 7. Attribute only rounds tagged v8 to N; v5+v7 = G baseline; v6 = I. No v8 round confirmed yet.
2) c-bet attribution: fixed in tools/analyze.py (last preflop raiser) and tools/review/build_review_data.py (cbet uses last_raiser; first_raiser kept for its other uses). Re-run pending. Agree 96.7% is a model tendency (bet EV + bet_margin), not a bug; G has the same policy.
3) Gate_N budget confound accepted (N at bank 7 vs srv_I bank 1.4; also template now has fallback counter). Running gate_O (tools/gate_O.sh): cI/cN built from the SAME current template with identical caps 1.2/2.8 and bank 1.4 (params_I vs params_N), seeds 5501/5502, 480 tables x 300 hands for late/real/heldout + archive 64x1000. 'late' clones were refit through r046 and N's tuning only saw r037, so late is a partial temporal holdout (r038-r046 unseen). Output: tools/gate_O.txt.
4) Tuner selection bias: agreed, none of the ACCEPTs is release evidence; N goes live only as a labelled experiment (G rollback), user decides from live rounds.
5) no-jam: sandbox only, nothing from me; screens are noise-level (your seeds). I am not pursuing it.
6) gate_T: ablation only; no change to budget. Exact commands: arena.py tools/cands/srv_t{3,4}.py tools/cands/srv_I.py --tables 320 --hands 300 --field {late,real} --seed 4401. latency.py total act() only (LocalPlayer), no IPC; agreed it cannot certify the server cap.
7) Python: mine is Python 3.13 (Windows Store); interpreter path available if you need it.
