# Re: gate_M audit, J gate, wild experiments, r028-r038

Agreed: keep I live, no promotion of J. Facts:
- gate_M (tools/gate_M.sh not saved; command was) `arena.py tools/cands/gen08.py tools/cands/srv_I.py --tables 320 --hands 300 --field {late,real} --seed 6601` and `srv_I vs srv_G ... --seed 6602`. gen08 = J strategy at server-scaled budget (max_ms 1.2/hard 2.8); J itself = same params at 6/14 (tools/params_J.json). Clones refit through r037 (refresh_data combined hash in its output). Gate scripts: tools/gate_J/K/L.sh; gate_J was gen05 (real_ip) ablation, rejected.
- Pooled J-I over K+L+M: ~+3 bb/100, no claim of edge. G comparison for J not run; I-G is +16.5 late / +23.3 real.
- Live: I r024-r038 +20.9 vs G +26.8 over 23 rounds: indistinguishable at these SEs (18 / 12).
- Fallback observability: Agent.act now counts swallowed exceptions in `self.fallbacks` (template tools/src_bot.py; submitted I unchanged). Will add to fuzz/gate output.
Plan: overnight tuner run 3 from I is running (fresh clones). Wild-experiment shortlist will follow once screened; first candidates: (1) randomized bet sizing, (2) conservative exploit mixture vs Red/Kaiser-type high fold-to-raise profiles, (3) adversarial exploiter population against I. Nothing goes live without a gate against I and explicit user decision.
