# Independent gen13 interpretation and exact identity

Independent audit confirms gen13 SHA256 `3c79e149077e0699d575137e95225b511e040857775580d38b5d2f5be6b1f167`; `best.py` and params match it. It is gen12 plus `o_ep 0.22→0.241` (wider early-position opening cutoffs) and `real_oop 1.02→1.117` (higher preflop OOP call value multiplier on applicable non-premium/non-all-in hands). Code outside the parameter dictionary did not change at this step. It still uses 1.2/2.8 ms and bank7, versus deployed I's 6/14 ms and bank7.

Its confirmation is essentially inconclusive: +1.9 bb/100, SE6.7, z≈0.28; approximate 95% interval [-11.2,+15.0]. Combined z2.02 is driven by the favorable +19.0 screen. Gen13 inherits earlier gen09-12 changes and fallback instrumentation, so this is not an isolated OEP/OOP parameter effect and does not establish benefit over I. Deployed `kit/bot.py` remains exact I hash `d45a39…f46c`.

Keep gen13 as a research variant only. Please preserve exact hashes and the prior plan for one independent fixed-sample confirmation against I using same code, matched 6/14 ms and bank7, untouched opponents/seeds, and runtime/failure/fallback telemetry. No promotion from this `ACCEPT`.