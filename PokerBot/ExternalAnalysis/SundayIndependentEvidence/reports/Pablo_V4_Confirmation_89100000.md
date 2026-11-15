# Frozen Pablo v4 versus G: preregistered32-pair confirmation

This is one new confirmation run, separate from the earlier exploratory five-pair +2.249/SE25.386 result. Exact frozen v4 SHA8458e3b17263d808607917fcef1b1d3188b776bff912a9b097c3cce3ec749108; frozenG raw-byte SHAb8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a. Manifest was written before compute, all32fresh seeds89100000-89100031 used once, no parameter tuning or repeated seed fishing. 32paired1000hand tables=64000total table-hands. Existing A-v-A evidence reused only after byte-hash checks of unchanged models, loader/helper and all seven field files. The same previously validated frozen loader applies fixed32MC work and per-decision seeding to both heroes and all clones; production clock/bank stopping is overridden only in diagnostic memory. Four complete hero seat rotations; every table contains each of seven sunday_v2 clones once. These are frequency-based opponent approximations, not actual opponent policies. No independent real-opponent holdout or production-runtime certification is established. Matching work isolates strategy from the original unequal G/v4 compute budgets but is itself a low-work approximation. Future production gate must restore exact exported runtime/bank settings, assess exceptions/timeouts/fallbacks in subprocesses over complete rounds, and confirm platform limits separately.

Run command (once only): `python tools/independent_pablo/run_confirmation.py` from PokerBot. Raw per-table chips/window chips/actions/error samples: `ExternalAnalysis/AgentReports/Pablo_V4_Confirmation_89100000/paired_tables.jsonl`. Pre-run manifest: `preregistered_manifest.json`; machine-readable results: `summary.json`, same directory. Raw and manifest hashes are included below. Secondary blocks/windows/actions are descriptive; no favorable window is substituted for the preregistered primary endpoint.

```json
{
  "completed_utc": "2026-11-15T00:17:30.164368+00:00",
  "manifest_sha256": "cfb2797096c3329d60e4f544b1d672ba6f1fec89eb71ceed9842aa01ecfd61ef",
  "raw_path": "C:\\Users\\pelay\\AIHack\\PokerBot\\ExternalAnalysis\\AgentReports\\Pablo_V4_Confirmation_89100000\\paired_tables.jsonl",
  "raw_sha256": "cf3323e1f2575932121e4cba818d3270f928f0f037c28a011588b0e3c7288188",
  "primary": {
    "pairs": 32,
    "pablo_bb100": 32.23046875,
    "G_bb100": 47.46203125,
    "diff_bb100": -15.231562499999999,
    "paired_se": 9.468358536668656,
    "t95_CI": [
      -34.542407050837944,
      4.079282050837946
    ],
    "positive_pairs": 13,
    "negative_pairs": 19,
    "zero_pairs": 0
  },
  "secondary_blocks": {
    "1-8": {
      "pairs": 8,
      "pablo_bb100": 20.07625,
      "G_bb100": 19.08,
      "diff_bb100": 0.9962500000000021,
      "paired_se": 25.811769857366286,
      "t95_CI": [
        -60.038886981259935,
        62.03138698125994
      ],
      "positive_pairs": 5,
      "negative_pairs": 3,
      "zero_pairs": 0
    },
    "9-16": {
      "pairs": 8,
      "pablo_bb100": 78.688125,
      "G_bb100": 92.430625,
      "diff_bb100": -13.7425,
      "paired_se": 13.148468542001382,
      "t95_CI": [
        -44.83368758572128,
        17.348687585721283
      ],
      "positive_pairs": 4,
      "negative_pairs": 4,
      "zero_pairs": 0
    },
    "17-24": {
      "pairs": 8,
      "pablo_bb100": 13.914375000000001,
      "G_bb100": 32.865,
      "diff_bb100": -18.950625000000002,
      "paired_se": 19.481724321360318,
      "t95_CI": [
        -65.01758279313358,
        27.11633279313358
      ],
      "positive_pairs": 2,
      "negative_pairs": 6,
      "zero_pairs": 0
    },
    "25-32": {
      "pairs": 8,
      "pablo_bb100": 16.243125,
      "G_bb100": 45.4725,
      "diff_bb100": -29.229374999999994,
      "paired_se": 17.36407036602706,
      "t95_CI": [
        -70.28887689387118,
        11.830126893871185
      ],
      "positive_pairs": 2,
      "negative_pairs": 6,
      "zero_pairs": 0
    }
  },
  "secondary_windows": {
    "1-50": {
      "pairs": 32,
      "pablo_bb100": 28.209375,
      "G_bb100": 57.324999999999996,
      "diff_bb100": -29.115624999999994,
      "paired_se": 33.01910832081804,
      "t95_CI": [
        -96.45854040832792,
        38.22729040832793
      ],
      "positive_pairs": 18,
      "negative_pairs": 14,
      "zero_pairs": 0
    },
    "51-200": {
      "pairs": 32,
      "pablo_bb100": 27.23125,
      "G_bb100": 19.546874999999996,
      "diff_bb100": 7.684375000000003,
      "paired_se": 26.434312861702573,
      "t95_CI": [
        -46.22876152769191,
        61.597511527691914
      ],
      "positive_pairs": 17,
      "negative_pairs": 15,
      "zero_pairs": 0
    },
    "201-1000": {
      "pairs": 32,
      "pablo_bb100": 33.419140625000004,
      "G_bb100": 52.0796875,
      "diff_bb100": -18.660546874999998,
      "paired_se": 10.551756480989434,
      "t95_CI": [
        -40.18099610107839,
        2.8599023510784
      ],
      "positive_pairs": 11,
      "negative_pairs": 21,
      "zero_pairs": 0
    }
  },
  "all_seat_errors": {
    "pablo_v4": 0,
    "G": 0
  },
  "action_counts": {
    "pablo_v4": {
      "1-50|flop|call": 25,
      "1-50|flop|check": 17,
      "1-50|flop|fold": 34,
      "1-50|flop|raise": 93,
      "1-50|preflop|call": 113,
      "1-50|preflop|check": 5,
      "1-50|preflop|fold": 1365,
      "1-50|preflop|raise": 219,
      "1-50|river|check": 6,
      "1-50|river|fold": 3,
      "1-50|river|raise": 4,
      "1-50|turn|call": 7,
      "1-50|turn|check": 11,
      "1-50|turn|fold": 10,
      "1-50|turn|raise": 16,
      "201-1000|flop|call": 430,
      "201-1000|flop|check": 371,
      "201-1000|flop|fold": 775,
      "201-1000|flop|raise": 1480,
      "201-1000|preflop|call": 2123,
      "201-1000|preflop|check": 82,
      "201-1000|preflop|fold": 21646,
      "201-1000|preflop|raise": 3616,
      "201-1000|river|call": 48,
      "201-1000|river|check": 149,
      "201-1000|river|fold": 72,
      "201-1000|river|raise": 118,
      "201-1000|turn|call": 120,
      "201-1000|turn|check": 222,
      "201-1000|turn|fold": 165,
      "201-1000|turn|raise": 372,
      "51-200|flop|call": 89,
      "51-200|flop|check": 62,
      "51-200|flop|fold": 156,
      "51-200|flop|raise": 265,
      "51-200|preflop|call": 375,
      "51-200|preflop|check": 11,
      "51-200|preflop|fold": 4065,
      "51-200|preflop|raise": 631,
      "51-200|river|call": 10,
      "51-200|river|check": 24,
      "51-200|river|fold": 12,
      "51-200|river|raise": 23,
      "51-200|turn|call": 28,
      "51-200|turn|check": 36,
      "51-200|turn|fold": 30,
      "51-200|turn|raise": 75
    },
    "G": {
      "1-50|flop|call": 22,
      "1-50|flop|check": 4,
      "1-50|flop|fold": 48,
      "1-50|flop|raise": 161,
      "1-50|preflop|call": 206,
      "1-50|preflop|check": 5,
      "1-50|preflop|fold": 1290,
      "1-50|preflop|raise": 244,
      "1-50|river|call": 1,
      "1-50|river|check": 6,
      "1-50|river|fold": 5,
      "1-50|river|raise": 22,
      "1-50|turn|call": 1,
      "1-50|turn|check": 7,
      "1-50|turn|fold": 13,
      "1-50|turn|raise": 44,
      "201-1000|flop|call": 427,
      "201-1000|flop|check": 133,
      "201-1000|flop|fold": 787,
      "201-1000|flop|raise": 2993,
      "201-1000|preflop|call": 3694,
      "201-1000|preflop|check": 82,
      "201-1000|preflop|fold": 20284,
      "201-1000|preflop|raise": 4038,
      "201-1000|river|call": 54,
      "201-1000|river|check": 82,
      "201-1000|river|fold": 109,
      "201-1000|river|raise": 392,
      "201-1000|turn|call": 124,
      "201-1000|turn|check": 76,
      "201-1000|turn|fold": 188,
      "201-1000|turn|raise": 771,
      "51-200|flop|call": 92,
      "51-200|flop|check": 19,
      "51-200|flop|fold": 152,
      "51-200|flop|raise": 556,
      "51-200|preflop|call": 701,
      "51-200|preflop|check": 11,
      "51-200|preflop|fold": 3781,
      "51-200|preflop|raise": 716,
      "51-200|river|call": 11,
      "51-200|river|check": 18,
      "51-200|river|fold": 22,
      "51-200|river|raise": 68,
      "51-200|turn|call": 27,
      "51-200|turn|check": 13,
      "51-200|turn|fold": 46,
      "51-200|turn|raise": 159
    }
  }
}
```

## Primary decision

No demonstrated improvement; keep frozen G. Frozen Pablo v4 minus G is **-15.232bb/100, paired SE9.468, t95%CI[-34.542,+4.079]** across32fresh pairs. There were13positive and19negative pairs. Both arms had zero reported all-seat errors with diagnostic exception propagation enabled. The confidence interval includes zero, so this does not establish stable inferiority either; it supplies no basis to replace G with these v4 bytes.

This primary confirmation is separate from the earlier five-pair exploratory+2.249/SE25.386 result. No pooling, selected favorable hand window, or seed retry was used for the decision. Raw32-row output was checked for completeness and its hash rechecked after the run. Secondary block/window estimates remain exploratory and correlated within tables. No additional run is started.
