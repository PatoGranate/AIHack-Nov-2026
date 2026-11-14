# Research synthesis, Candidate J gate, and code-audit findings

Source-linked training analysis is in `ExternalAnalysis/External_Algorithm_Review_20261114.md`.

Recommended direction: keep I live; continue MCCFR/blueprint training offline; test depth-limited imperfect-information search and bet-size abstraction under strict latency limits; avoid live opponent-specific exploitation until it transfers on held-out pools. Pluribus (Science 2019) is the closest multiplayer reference; its supplement identifies depth-limited search as key to tractable six-player poker. CFR+/MCCFR are reasonable blueprint methods. DeepStack/Libratus/ReBeL inform methods, but are mostly heads-up; ReBeL's guarantee does not directly transfer to multiplayer.

Independent J gate review: Candidate J's strategy matches gen08 `best.py`, but there is no direct J gate. K/L are positive and below z=2; approximate combined z is 1.63 late / 1.80 real / 1.63 held-out. There is no G comparison. `gate_J.txt` is unrelated gen05 real-IP ablation. K/L scripts also need fail-closed execution and complete logs.

Independent code review found no obvious decision/EV/legalization correctness defect in targeted paths. One important observability issue: `Agent.act` catches policy exceptions and silently falls back to check/fold unless DEBUG is enabled. Count and surface these fallbacks in gate/fuzz results; require zero. J adds bet candidates, so measure total `act()` p95/p99 under the actual 25 ms limit, not only simulation loop time; include timeout, error, bank-out and internal-fallback counts.

Please run one bounded actual-J comparison versus I and G with independent seeds, frozen source/opponent hashes, late/real/held-out/archive coverage where available, fail-closed command handling and full logs. Keep I live pending results; no upload requested.