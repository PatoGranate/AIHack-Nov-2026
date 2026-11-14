# Independent audit of gate_M.txt

The gate_M output alone is not sufficient to promote J. It has four aggregate rows but no corresponding script/transcript, seeds, sample counts, opponent-pool manifest, frozen config hashes, or runtime/failure evidence. The reported J(gen08)-I differences (-0.8 late, +0.8 real) are effectively zero with wide SEs. I-G is promising in these reported fields, but without run provenance it cannot be reproduced or used to compare J with G.

Hashes confirm I `d45a39…f46c`, actual J `1c2686…06576`, gen08 `64ecb4…24b47`. J and gen08 differ only in max_ms/hard_ms (J 6/14 vs gen08 1.2/2.8), so these rows are a scaled strategy test, not evidence for exact J runtime behavior.

Minimum remaining release evidence: frozen exact J/I/G and opponent manifests; reproducible paired seeds and counts; late plus untouched holdout and relevant real/external/archive pools; declared effect/uncertainty bar; fail-closed logs; full-act p95/p99 and timeout/error/bank-out/caught-exception-fallback counts under the 25 ms cap. Recommendation remains keep I; no promotion based on gate_M.