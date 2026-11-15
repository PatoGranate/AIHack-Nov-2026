# Pablo models: independent inventory and bounded review

Reviewed pablo-poker commit24653c92256ad1b7b14c37b0b206254cf1a4c6c5. No AGENTS.md exists in this branch inventory. README and candidate/README.txt were read; autonomous lab, fetchers, workers, dashboard and exporters were not launched. Selected current root bot.py (v4 export), not a claim of strongest proven model. Other exports are distinct policies: bot_gen7.py, bot_v31.py and bot_v32.py. No online-result identity is established for these bytes.

The latest root export is a self-contained stdlib Agent compatible with the official engine loader. candidate/export.py instead requires baseline_params.json and live_model_snapshot.json absent from the branch, so that path is not reproducible from committed inputs; no replacement model was invented. README describes earlier strategy/lab workflows and is partly stale relative to v4.

Reviewed bench2.py before running anything: it uses its own fieldbot simulator, seeded lineup,500MC with very large clock limits, and adaptation fieldsA/B. Such tuning results are not independent confirmation of v4, especially when policy and simulator are updated together. This review uses the official PokerBot engine and independently fitted sunday_v2 frequency clones instead.

Run: `python tools/independent_pablo/run_review.py` from PokerBot. Imported fixed diagnostic helper and input hashes are below. Both builds and all clones receive per-decision RNG seeding. Hero simulate exits after32samples, budget override.001 in both builds; DEBUG=True exposes swallowed exceptions in this sandbox only. These modified diagnostic conditions do not certify the unmodified export's timing or live strength. Before the pilot, G and v4 each passed20hand A-v-A twice (80hands). Exact v4 bytes also received a20hand official SubprocessPlayer protocol smoke at25ms/10s bank. Five paired1000hand tables fresh87100000-87100004 add10000hands; total10100 table-hands. Every table contains the seven sunday_v2 clones once; hero seats0-4 rotate, opponents seeded-shuffle. Clones remain imperfect public-frequency approximations.

Protocol smoke is intentionally small and cannot establish full1000hand bank performance or a safe deployment deadline margin. Subprocess errors/timeouts are distinct from legal-action success and generic internal silent fallbacks.

```json
{
  "branch_commit": "24653c92256ad1b7b14c37b0b206254cf1a4c6c5",
  "hashes": {
    "tools/independent_pablo/bot.py": "8458e3b17263d808607917fcef1b1d3188b776bff912a9b097c3cce3ec749108",
    "tools/independent_pablo/bot_gen7.py": "e4495ee82fff494067724007fafc3d71dad979b4cf123864b543dfc58448ba0f",
    "tools/independent_pablo/bot_v31.py": "c97d1eaf6a5a88dcaf54330dc157a7203a6698a44e2a0c71c2f89fd1ac70838d",
    "tools/independent_pablo/bot_v32.py": "e9a0de8370d9130045a7cbb1a447512800a9fc7f77b3f7d8558e8bb386cc2a99",
    "tools/independent_pablo/pokerbot/v2.py": "efbed10da9774496e16fd29a379916166c304107ba0403d9b1ab1dd07aefd0d2",
    "tools/independent_pablo/pokerbot/strategy.py": "98e3adc863b87017033a33eeb7a23ff7dede55c240ddbc3f5802241d73b31825",
    "tools/independent_pablo/candidate/engine.py": "52b7a4eb5285eec89aeb36f30c64ae08f562a2917e7cda16d7d8c441853f8d9c",
    "tools/independent_pablo/candidate/export.py": "5dddfa0dcc87fe40d6797858c07536a34d29d2979585cde18ee8d5f71a1cb6ce",
    "tools/independent_pablo/tools/bench2.py": "3b6bb0b373dfce75b5349f2ef3feaff3d74e95b15ab0ccf9f1a4ab711445f08d",
    "tools/independent_pablo/data/v4_params.json": "df8095758d5f3f1d629f9e6297256245608a941e69b87f62befa456786aa08e5",
    "submissions/G_v7_final/bot.py": "b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a",
    "submissions/I_v9_25ms/bot.py": "d45a39b72c0e990efe06c8a233c7f2061f468a5c1f3279924c5ae07fc060f46c",
    "submissions/N_v10_tuned/bot.py": "5c2b4b2c0ed3ddd5177fe758959e1c32e3a113f8c500a373f6b5d11d5bb7845f",
    "tools/independent_pablo/run_review.py": "929e3b0945dbb02f7a216476ee749e4ee1164d72457a292091855e88633b676a",
    "tools/sunday_early_adapt_pilot.py": "e71dd55352233bbd764d1121d4c6473e2619f8c46c92656fb9e6e41f1e760d68",
    "tools/independent_ctx_pr11/opponents/sunday_v2/r_ResonanceQt.py": "6622fb3a6b0973ba35578eb25973e68c0a035e4a1ae15fb7e0b68f9c17dca560",
    "tools/independent_ctx_pr11/opponents/sunday_v2/r_AnkerBatteries.py": "35d35b77b9643b89d37b6d2fe5fc5aa13490ea8b166786fdea8b47285170e030",
    "tools/independent_ctx_pr11/opponents/sunday_v2/r_Chinesepeoplecanfly.py": "42479fa43200a6a553de08c0cfc5fea16ff31c5b1874f54d35316ad229c7037c",
    "tools/independent_ctx_pr11/opponents/sunday_v2/r_GamesGone.py": "3a9beb40e7f60df6633d38af24355c7fc76618289a349fbff7b7ff5ef22bc906",
    "tools/independent_ctx_pr11/opponents/sunday_v2/r_Poke.py": "f84ecef6a499bd9b78aef0ff757e648ae81e10adf2ed99820ab9d051848073b3",
    "tools/independent_ctx_pr11/opponents/sunday_v2/r_Anton.py": "44da98d81e83e38b3462e69f3a092da5d49c53881134aff85c59fb5d817e462b",
    "tools/independent_ctx_pr11/opponents/sunday_v2/r_YSLTWIZZY.py": "f287f330c9660c6e9629947e0e7c84125829c2103628f6bf61124ef704d25564"
  },
  "inventory": {
    "tools/independent_pablo/bot.py": {
      "params": {
        "pri_vpip": 0.28,
        "pri_pfr": 0.17,
        "pri_ftb": 0.6,
        "r3_mult": 0.35,
        "call_lo": 0.6,
        "bb_raise": 0.08,
        "open_size": 3.5,
        "loose_add": 1.0,
        "o_btn": 0.7,
        "o_sb": 0.487,
        "o_co": 0.36,
        "o_hj": 0.26,
        "o_mp": 0.16,
        "o_ep": 0.12,
        "steal_k": 1.5,
        "iso_mult": 0.9,
        "overlimp": 0.3,
        "sb_limp": 0.0,
        "multi_exp": 0.75,
        "real_ip": 1.05,
        "real_oop": 0.92,
        "eq_3b": 0.52,
        "eq_4b": 0.56,
        "3b_ip": 3.6,
        "3b_oop": 4.3,
        "pf_call_margin": 0.0,
        "bluff_base": 0.15,
        "bluff_af": 0.4,
        "w_r_air": 0.5,
        "w_r_weak": 0.25,
        "w_r_mid": 0.6,
        "w_b_weak": 0.45,
        "w_b_mid": 0.85,
        "c_air": 0.15,
        "c_weak": 0.55,
        "c_mid": 1,
        "size_exp": 1.0,
        "max_sims": 6000,
        "max_ms": 4.0,
        "bet_sizes": [
          0.33,
          0.6,
          1.0
        ],
        "raise_sizes": [
          1.0,
          2.0
        ],
        "shove_spr": 5,
        "chk_ip": 0.8,
        "chk_oop": 0.7,
        "bet_margin": 0.0,
        "call_tax": 0.0,
        "fold_vs_raise": 1.0,
        "raise_margin": -0.04,
        "hard_ms": 8.0,
        "q_steal": 0,
        "q_steal_ftr": 0.8,
        "q_steal_f": 0.75,
        "q_3bet": 0,
        "q_3bet_range": 0.35,
        "q_3bet_ftr": 0.8,
        "q_river_extra": [
          1.75,
          3.0
        ],
        "q_small_extra": [
          0.15
        ],
        "q_trap": 1,
        "q_trap_eq": 0.8,
        "q_trap_af": 0.45,
        "q_min_obs": 8,
        "sd_cal": 0,
        "sd_prior": 0.42,
        "sd_k": 6,
        "real_sb": 0.92,
        "size_read": 1.0,
        "fold_cal": 0,
        "ident": 1,
        "vs3_pct": 0.1,
        "vs4_pct": 0.04,
        "id_k": 40,
        "ans_cal": 1,
        "raise_lam": [
          0.1,
          0.2,
          1.0,
          4.0
        ],
        "raise_x": 3.5,
        "agg_prior": 0.7,
        "tb_pct": 0.14,
        "tb_open_max": 4.5,
        "bb_def": 0.25,
        "chk_r_ip": 1.0,
        "chk_r_oop": 0.85,
        "rm_street": [
          0.0,
          0.0,
          0.0
        ],
        "bank_s": 7.0
      },
      "config_diff_vs_G": {
        "3b_ip": [
          3.0,
          3.6
        ],
        "3b_oop": [
          3.6,
          4.3
        ],
        "agg_prior": [
          null,
          0.7
        ],
        "ans_cal": [
          null,
          1
        ],
        "bank_s": [
          null,
          7.0
        ],
        "bb_def": [
          null,
          0.25
        ],
        "bet_margin": [
          -0.08,
          0.0
        ],
        "bluff_af": [
          1.2,
          0.4
        ],
        "chk_r_ip": [
          null,
          1.0
        ],
        "chk_r_oop": [
          null,
          0.85
        ],
        "fold_cal": [
          null,
          0
        ],
        "hard_ms": [
          3.0,
          8.0
        ],
        "id_k": [
          null,
          40
        ],
        "ident": [
          null,
          1
        ],
        "max_ms": [
          1.2,
          4.0
        ],
        "max_sims": [
          1500,
          6000
        ],
        "o_co": [
          0.45,
          0.36
        ],
        "o_ep": [
          0.22,
          0.12
        ],
        "o_hj": [
          0.36,
          0.26
        ],
        "o_mp": [
          0.28,
          0.16
        ],
        "raise_lam": [
          null,
          [
            0.1,
            0.2,
            1.0,
            4.0
          ]
        ],
        "raise_x": [
          null,
          3.5
        ],
        "real_sb": [
          null,
          0.92
        ],
        "rm_street": [
          null,
          [
            0.0,
            0.0,
            0.0
          ]
        ],
        "sd_cal": [
          null,
          0
        ],
        "sd_k": [
          null,
          6
        ],
        "sd_prior": [
          null,
          0.42
        ],
        "size_read": [
          null,
          1.0
        ],
        "tb_open_max": [
          null,
          4.5
        ],
        "tb_pct": [
          null,
          0.14
        ],
        "vs3_pct": [
          null,
          0.1
        ],
        "vs4_pct": [
          null,
          0.04
        ],
        "w_b_weak": [
          0.55,
          0.45
        ]
      }
    },
    "tools/independent_pablo/bot_gen7.py": {
      "params": {
        "agg_tighten": 0.55,
        "bb_defend": 0.22,
        "bet_bluff": 0.55,
        "bet_value": 0.8,
        "bluff_freq": 0.5,
        "call_3bet": 0.08,
        "call_margin": 0.06,
        "call_open": 0.11,
        "cbet_freq": 0.85,
        "commit_penalty": 0.1,
        "draw_discount": 0.08,
        "ev_mode": 0,
        "exploit": 1.0,
        "exploit_ramp": 0,
        "explore": 0.0,
        "fourbet_value": 0.03,
        "iso_tighten": 0.8,
        "jam_call": 0.03,
        "jam_equity": 0,
        "mc_iters": 260,
        "mc_ms": 6.0,
        "open_btn": 0.42,
        "open_co": 0.27,
        "open_ep": 0.13,
        "open_mp": 0.18,
        "open_sb": 0.36,
        "open_size": 2.5,
        "portfolio": 0,
        "raise_eq": 0.76,
        "real_ip": 0.85,
        "real_oop": 0.7,
        "river_overbet": 0.0,
        "sd_read": 0.0,
        "semibluff_eq": 0.38,
        "size_k": 0.5,
        "tag_counter": 0,
        "threebet_bluff": 0.02,
        "threebet_size": 3.2,
        "threebet_value": 0.035,
        "value_flop": 0.58,
        "value_river": 0.66,
        "value_turn": 0.62
      },
      "config_diff_vs_G": {
        "3b_ip": [
          3.0,
          null
        ],
        "3b_oop": [
          3.6,
          null
        ],
        "agg_tighten": [
          null,
          0.55
        ],
        "bb_defend": [
          null,
          0.22
        ],
        "bb_raise": [
          0.08,
          null
        ],
        "bet_bluff": [
          null,
          0.55
        ],
        "bet_margin": [
          -0.08,
          null
        ],
        "bet_sizes": [
          [
            0.33,
            0.6,
            1.0
          ],
          null
        ],
        "bet_value": [
          null,
          0.8
        ],
        "bluff_af": [
          1.2,
          null
        ],
        "bluff_base": [
          0.15,
          null
        ],
        "bluff_freq": [
          null,
          0.5
        ],
        "c_air": [
          0.15,
          null
        ],
        "c_mid": [
          1,
          null
        ],
        "c_weak": [
          0.55,
          null
        ],
        "call_3bet": [
          null,
          0.08
        ],
        "call_lo": [
          0.6,
          null
        ],
        "call_margin": [
          null,
          0.06
        ],
        "call_open": [
          null,
          0.11
        ],
        "call_tax": [
          0.0,
          null
        ],
        "cbet_freq": [
          null,
          0.85
        ],
        "chk_ip": [
          0.8,
          null
        ],
        "chk_oop": [
          0.7,
          null
        ],
        "commit_penalty": [
          null,
          0.1
        ],
        "draw_discount": [
          null,
          0.08
        ],
        "eq_3b": [
          0.52,
          null
        ],
        "eq_4b": [
          0.56,
          null
        ],
        "ev_mode": [
          null,
          0
        ],
        "exploit": [
          null,
          1.0
        ],
        "exploit_ramp": [
          null,
          0
        ],
        "explore": [
          null,
          0.0
        ],
        "fold_vs_raise": [
          1.0,
          null
        ],
        "fourbet_value": [
          null,
          0.03
        ],
        "hard_ms": [
          3.0,
          null
        ],
        "iso_mult": [
          0.9,
          null
        ],
        "iso_tighten": [
          null,
          0.8
        ],
        "jam_call": [
          null,
          0.03
        ],
        "jam_equity": [
          null,
          0
        ],
        "loose_add": [
          1.0,
          null
        ],
        "max_ms": [
          1.2,
          null
        ],
        "max_sims": [
          1500,
          null
        ],
        "mc_iters": [
          null,
          260
        ],
        "mc_ms": [
          null,
          6.0
        ],
        "multi_exp": [
          0.75,
          null
        ],
        "o_btn": [
          0.7,
          null
        ],
        "o_co": [
          0.45,
          null
        ],
        "o_ep": [
          0.22,
          null
        ],
        "o_hj": [
          0.36,
          null
        ],
        "o_mp": [
          0.28,
          null
        ],
        "o_sb": [
          0.487,
          null
        ],
        "open_btn": [
          null,
          0.42
        ],
        "open_co": [
          null,
          0.27
        ],
        "open_ep": [
          null,
          0.13
        ],
        "open_mp": [
          null,
          0.18
        ],
        "open_sb": [
          null,
          0.36
        ],
        "open_size": [
          3.5,
          2.5
        ],
        "overlimp": [
          0.3,
          null
        ],
        "pf_call_margin": [
          0.0,
          null
        ],
        "portfolio": [
          null,
          0
        ],
        "pri_ftb": [
          0.6,
          null
        ],
        "pri_pfr": [
          0.17,
          null
        ],
        "pri_vpip": [
          0.28,
          null
        ],
        "q_3bet": [
          0,
          null
        ],
        "q_3bet_ftr": [
          0.8,
          null
        ],
        "q_3bet_range": [
          0.35,
          null
        ],
        "q_min_obs": [
          8,
          null
        ],
        "q_river_extra": [
          [
            1.75,
            3.0
          ],
          null
        ],
        "q_small_extra": [
          [
            0.15
          ],
          null
        ],
        "q_steal": [
          0,
          null
        ],
        "q_steal_f": [
          0.75,
          null
        ],
        "q_steal_ftr": [
          0.8,
          null
        ],
        "q_trap": [
          1,
          null
        ],
        "q_trap_af": [
          0.45,
          null
        ],
        "q_trap_eq": [
          0.8,
          null
        ],
        "r3_mult": [
          0.35,
          null
        ],
        "raise_eq": [
          null,
          0.76
        ],
        "raise_margin": [
          -0.04,
          null
        ],
        "raise_sizes": [
          [
            1.0,
            2.0
          ],
          null
        ],
        "real_ip": [
          1.05,
          0.85
        ],
        "real_oop": [
          0.92,
          0.7
        ],
        "river_overbet": [
          null,
          0.0
        ],
        "sb_limp": [
          0.0,
          null
        ],
        "sd_read": [
          null,
          0.0
        ],
        "semibluff_eq": [
          null,
          0.38
        ],
        "shove_spr": [
          5,
          null
        ],
        "size_exp": [
          1.0,
          null
        ],
        "size_k": [
          null,
          0.5
        ],
        "steal_k": [
          1.5,
          null
        ],
        "tag_counter": [
          null,
          0
        ],
        "threebet_bluff": [
          null,
          0.02
        ],
        "threebet_size": [
          null,
          3.2
        ],
        "threebet_value": [
          null,
          0.035
        ],
        "value_flop": [
          null,
          0.58
        ],
        "value_river": [
          null,
          0.66
        ],
        "value_turn": [
          null,
          0.62
        ],
        "w_b_mid": [
          0.85,
          null
        ],
        "w_b_weak": [
          0.55,
          null
        ],
        "w_r_air": [
          0.5,
          null
        ],
        "w_r_mid": [
          0.6,
          null
        ],
        "w_r_weak": [
          0.25,
          null
        ]
      }
    },
    "tools/independent_pablo/bot_v31.py": {
      "params": {
        "pri_vpip": 0.28,
        "pri_pfr": 0.17,
        "pri_ftb": 0.6,
        "r3_mult": 0.35,
        "call_lo": 0.6,
        "bb_raise": 0.08,
        "open_size": 3.5,
        "loose_add": 1.0,
        "o_btn": 0.7,
        "o_sb": 0.487,
        "o_co": 0.45,
        "o_hj": 0.36,
        "o_mp": 0.28,
        "o_ep": 0.22,
        "steal_k": 1.5,
        "iso_mult": 0.9,
        "overlimp": 0.3,
        "sb_limp": 0.0,
        "multi_exp": 0.75,
        "real_ip": 1.05,
        "real_oop": 0.92,
        "eq_3b": 0.52,
        "eq_4b": 0.56,
        "3b_ip": 3.0,
        "3b_oop": 3.4,
        "pf_call_margin": 0.0,
        "bluff_base": 0.15,
        "bluff_af": 0.4,
        "w_r_air": 0.5,
        "w_r_weak": 0.25,
        "w_r_mid": 0.6,
        "w_b_weak": 0.45,
        "w_b_mid": 0.85,
        "c_air": 0.15,
        "c_weak": 0.55,
        "c_mid": 1,
        "size_exp": 1.0,
        "max_sims": 6000,
        "max_ms": 5.0,
        "bet_sizes": [
          0.33,
          0.6,
          1.0
        ],
        "raise_sizes": [
          1.0,
          2.0
        ],
        "shove_spr": 5,
        "chk_ip": 0.8,
        "chk_oop": 0.7,
        "bet_margin": -0.08,
        "call_tax": 0.0,
        "fold_vs_raise": 1.0,
        "raise_margin": -0.04,
        "hard_ms": 8.0,
        "q_steal": 0,
        "q_steal_ftr": 0.8,
        "q_steal_f": 0.75,
        "q_3bet": 0,
        "q_3bet_range": 0.35,
        "q_3bet_ftr": 0.8,
        "q_river_extra": [
          1.75,
          3.0
        ],
        "q_small_extra": [
          0.15
        ],
        "q_trap": 1,
        "q_trap_eq": 0.8,
        "q_trap_af": 0.45,
        "q_min_obs": 8,
        "sd_cal": 0,
        "sd_prior": 0.42,
        "sd_k": 6,
        "real_sb": 0.92,
        "size_read": 0.6,
        "fold_cal": 0,
        "ident": 1,
        "id_k": 40,
        "bank_s": 7.0
      },
      "config_diff_vs_G": {
        "3b_oop": [
          3.6,
          3.4
        ],
        "bank_s": [
          null,
          7.0
        ],
        "bluff_af": [
          1.2,
          0.4
        ],
        "fold_cal": [
          null,
          0
        ],
        "hard_ms": [
          3.0,
          8.0
        ],
        "id_k": [
          null,
          40
        ],
        "ident": [
          null,
          1
        ],
        "max_ms": [
          1.2,
          5.0
        ],
        "max_sims": [
          1500,
          6000
        ],
        "real_sb": [
          null,
          0.92
        ],
        "sd_cal": [
          null,
          0
        ],
        "sd_k": [
          null,
          6
        ],
        "sd_prior": [
          null,
          0.42
        ],
        "size_read": [
          null,
          0.6
        ],
        "w_b_weak": [
          0.55,
          0.45
        ]
      }
    },
    "tools/independent_pablo/bot_v32.py": {
      "params": {
        "pri_vpip": 0.28,
        "pri_pfr": 0.17,
        "pri_ftb": 0.6,
        "r3_mult": 0.35,
        "call_lo": 0.6,
        "bb_raise": 0.08,
        "open_size": 3.5,
        "loose_add": 1.0,
        "o_btn": 0.7,
        "o_sb": 0.487,
        "o_co": 0.36,
        "o_hj": 0.26,
        "o_mp": 0.16,
        "o_ep": 0.12,
        "steal_k": 1.5,
        "iso_mult": 0.9,
        "overlimp": 0.3,
        "sb_limp": 0.0,
        "multi_exp": 0.75,
        "real_ip": 1.05,
        "real_oop": 0.92,
        "eq_3b": 0.52,
        "eq_4b": 0.56,
        "3b_ip": 3.0,
        "3b_oop": 3.4,
        "pf_call_margin": 0.0,
        "bluff_base": 0.15,
        "bluff_af": 0.4,
        "w_r_air": 0.5,
        "w_r_weak": 0.25,
        "w_r_mid": 0.6,
        "w_b_weak": 0.45,
        "w_b_mid": 0.85,
        "c_air": 0.15,
        "c_weak": 0.55,
        "c_mid": 1,
        "size_exp": 1.0,
        "max_sims": 6000,
        "max_ms": 5.0,
        "bet_sizes": [
          0.33,
          0.6,
          1.0
        ],
        "raise_sizes": [
          1.0,
          2.0
        ],
        "shove_spr": 5,
        "chk_ip": 0.8,
        "chk_oop": 0.7,
        "bet_margin": -0.08,
        "call_tax": 0.0,
        "fold_vs_raise": 1.0,
        "raise_margin": -0.04,
        "hard_ms": 8.0,
        "q_steal": 0,
        "q_steal_ftr": 0.8,
        "q_steal_f": 0.75,
        "q_3bet": 0,
        "q_3bet_range": 0.35,
        "q_3bet_ftr": 0.8,
        "q_river_extra": [
          1.75,
          3.0
        ],
        "q_small_extra": [
          0.15
        ],
        "q_trap": 1,
        "q_trap_eq": 0.8,
        "q_trap_af": 0.45,
        "q_min_obs": 8,
        "sd_cal": 0,
        "sd_prior": 0.42,
        "sd_k": 6,
        "real_sb": 0.92,
        "size_read": 1.0,
        "fold_cal": 0,
        "ident": 1,
        "vs3_pct": 0.1,
        "vs4_pct": 0.04,
        "id_k": 40,
        "bank_s": 7.0
      },
      "config_diff_vs_G": {
        "3b_oop": [
          3.6,
          3.4
        ],
        "bank_s": [
          null,
          7.0
        ],
        "bluff_af": [
          1.2,
          0.4
        ],
        "fold_cal": [
          null,
          0
        ],
        "hard_ms": [
          3.0,
          8.0
        ],
        "id_k": [
          null,
          40
        ],
        "ident": [
          null,
          1
        ],
        "max_ms": [
          1.2,
          5.0
        ],
        "max_sims": [
          1500,
          6000
        ],
        "o_co": [
          0.45,
          0.36
        ],
        "o_ep": [
          0.22,
          0.12
        ],
        "o_hj": [
          0.36,
          0.26
        ],
        "o_mp": [
          0.28,
          0.16
        ],
        "real_sb": [
          null,
          0.92
        ],
        "sd_cal": [
          null,
          0
        ],
        "sd_k": [
          null,
          6
        ],
        "sd_prior": [
          null,
          0.42
        ],
        "size_read": [
          null,
          1.0
        ],
        "vs3_pct": [
          null,
          0.1
        ],
        "vs4_pct": [
          null,
          0.04
        ],
        "w_b_weak": [
          0.55,
          0.45
        ]
      }
    },
    "tools/independent_pablo/pokerbot/v2.py": {
      "params": {
        "pri_vpip": 0.28,
        "pri_pfr": 0.17,
        "pri_ftb": 0.6,
        "r3_mult": 0.35,
        "call_lo": 0.6,
        "bb_raise": 0.08,
        "open_size": 3.5,
        "loose_add": 1.0,
        "o_btn": 0.7,
        "o_sb": 0.487,
        "o_co": 0.45,
        "o_hj": 0.36,
        "o_mp": 0.28,
        "o_ep": 0.22,
        "steal_k": 1.5,
        "iso_mult": 0.9,
        "overlimp": 0.3,
        "sb_limp": 0.0,
        "multi_exp": 0.75,
        "real_ip": 1.05,
        "real_oop": 0.92,
        "eq_3b": 0.52,
        "eq_4b": 0.56,
        "3b_ip": 3.0,
        "3b_oop": 3.6,
        "pf_call_margin": 0.0,
        "bluff_base": 0.15,
        "bluff_af": 1.2,
        "w_r_air": 0.5,
        "w_r_weak": 0.25,
        "w_r_mid": 0.6,
        "w_b_weak": 0.55,
        "w_b_mid": 0.85,
        "c_air": 0.15,
        "c_weak": 0.55,
        "c_mid": 1,
        "size_exp": 1.0,
        "max_sims": 1500,
        "max_ms": 1.2,
        "bet_sizes": [
          0.33,
          0.6,
          1.0
        ],
        "raise_sizes": [
          1.0,
          2.0
        ],
        "shove_spr": 5,
        "chk_ip": 0.8,
        "chk_oop": 0.7,
        "bet_margin": -0.08,
        "call_tax": 0.0,
        "fold_vs_raise": 1.0,
        "raise_margin": -0.04,
        "hard_ms": 3.0,
        "q_steal": 0,
        "q_steal_ftr": 0.8,
        "q_steal_f": 0.75,
        "q_3bet": 0,
        "q_3bet_range": 0.35,
        "q_3bet_ftr": 0.8,
        "q_river_extra": [
          1.75,
          3.0
        ],
        "q_small_extra": [
          0.15
        ],
        "q_trap": 1,
        "q_trap_eq": 0.8,
        "q_trap_af": 0.45,
        "q_min_obs": 8,
        "sd_cal": 0,
        "sd_prior": 0.42,
        "sd_k": 6,
        "real_sb": 0.92,
        "size_read": 0.0,
        "fold_cal": 0,
        "ident": 0,
        "vs3_pct": 1.0,
        "vs4_pct": 1.0,
        "id_k": 30,
        "ans_cal": 0,
        "raise_lam": [
          0.15,
          0.3,
          1.0,
          2.5
        ],
        "raise_x": 3.5,
        "agg_prior": 0.7,
        "tb_pct": 0.0,
        "tb_open_max": 4.5,
        "bb_def": 1.0,
        "chk_r_ip": 0.0,
        "chk_r_oop": 0.0,
        "rm_street": [
          0.0,
          0.0,
          0.0
        ]
      },
      "config_diff_vs_G": {
        "agg_prior": [
          null,
          0.7
        ],
        "ans_cal": [
          null,
          0
        ],
        "bb_def": [
          null,
          1.0
        ],
        "chk_r_ip": [
          null,
          0.0
        ],
        "chk_r_oop": [
          null,
          0.0
        ],
        "fold_cal": [
          null,
          0
        ],
        "id_k": [
          null,
          30
        ],
        "ident": [
          null,
          0
        ],
        "raise_lam": [
          null,
          [
            0.15,
            0.3,
            1.0,
            2.5
          ]
        ],
        "raise_x": [
          null,
          3.5
        ],
        "real_sb": [
          null,
          0.92
        ],
        "rm_street": [
          null,
          [
            0.0,
            0.0,
            0.0
          ]
        ],
        "sd_cal": [
          null,
          0
        ],
        "sd_k": [
          null,
          6
        ],
        "sd_prior": [
          null,
          0.42
        ],
        "size_read": [
          null,
          0.0
        ],
        "tb_open_max": [
          null,
          4.5
        ],
        "tb_pct": [
          null,
          0.0
        ],
        "vs3_pct": [
          null,
          1.0
        ],
        "vs4_pct": [
          null,
          1.0
        ]
      }
    },
    "tools/independent_pablo/pokerbot/strategy.py": {
      "params": {
        "open_ep": 0.13,
        "open_mp": 0.18,
        "open_co": 0.27,
        "open_btn": 0.42,
        "open_sb": 0.36,
        "open_size": 2.5,
        "iso_tighten": 0.8,
        "threebet_value": 0.035,
        "threebet_bluff": 0.03,
        "threebet_size": 3.2,
        "call_open": 0.11,
        "bb_defend": 0.22,
        "fourbet_value": 0.02,
        "call_3bet": 0.05,
        "jam_call": 0.03,
        "value_flop": 0.64,
        "value_turn": 0.68,
        "value_river": 0.72,
        "raise_eq": 0.82,
        "call_margin": 0.02,
        "draw_discount": 0.04,
        "commit_penalty": 0.1,
        "bet_value": 0.66,
        "bet_bluff": 0.55,
        "cbet_freq": 0.55,
        "bluff_freq": 0.3,
        "semibluff_eq": 0.38,
        "agg_tighten": 0.55,
        "exploit": 0.7,
        "mc_iters": 260,
        "mc_ms": 6.0,
        "jam_equity": 0,
        "exploit_ramp": 0,
        "portfolio": 0,
        "river_overbet": 0.0,
        "ev_mode": 0,
        "real_ip": 0.85,
        "real_oop": 0.7,
        "size_k": 0.5,
        "tag_counter": 0,
        "sd_read": 0.0,
        "explore": 0.0
      },
      "config_diff_vs_G": {
        "3b_ip": [
          3.0,
          null
        ],
        "3b_oop": [
          3.6,
          null
        ],
        "agg_tighten": [
          null,
          0.55
        ],
        "bb_defend": [
          null,
          0.22
        ],
        "bb_raise": [
          0.08,
          null
        ],
        "bet_bluff": [
          null,
          0.55
        ],
        "bet_margin": [
          -0.08,
          null
        ],
        "bet_sizes": [
          [
            0.33,
            0.6,
            1.0
          ],
          null
        ],
        "bet_value": [
          null,
          0.66
        ],
        "bluff_af": [
          1.2,
          null
        ],
        "bluff_base": [
          0.15,
          null
        ],
        "bluff_freq": [
          null,
          0.3
        ],
        "c_air": [
          0.15,
          null
        ],
        "c_mid": [
          1,
          null
        ],
        "c_weak": [
          0.55,
          null
        ],
        "call_3bet": [
          null,
          0.05
        ],
        "call_lo": [
          0.6,
          null
        ],
        "call_margin": [
          null,
          0.02
        ],
        "call_open": [
          null,
          0.11
        ],
        "call_tax": [
          0.0,
          null
        ],
        "cbet_freq": [
          null,
          0.55
        ],
        "chk_ip": [
          0.8,
          null
        ],
        "chk_oop": [
          0.7,
          null
        ],
        "commit_penalty": [
          null,
          0.1
        ],
        "draw_discount": [
          null,
          0.04
        ],
        "eq_3b": [
          0.52,
          null
        ],
        "eq_4b": [
          0.56,
          null
        ],
        "ev_mode": [
          null,
          0
        ],
        "exploit": [
          null,
          0.7
        ],
        "exploit_ramp": [
          null,
          0
        ],
        "explore": [
          null,
          0.0
        ],
        "fold_vs_raise": [
          1.0,
          null
        ],
        "fourbet_value": [
          null,
          0.02
        ],
        "hard_ms": [
          3.0,
          null
        ],
        "iso_mult": [
          0.9,
          null
        ],
        "iso_tighten": [
          null,
          0.8
        ],
        "jam_call": [
          null,
          0.03
        ],
        "jam_equity": [
          null,
          0
        ],
        "loose_add": [
          1.0,
          null
        ],
        "max_ms": [
          1.2,
          null
        ],
        "max_sims": [
          1500,
          null
        ],
        "mc_iters": [
          null,
          260
        ],
        "mc_ms": [
          null,
          6.0
        ],
        "multi_exp": [
          0.75,
          null
        ],
        "o_btn": [
          0.7,
          null
        ],
        "o_co": [
          0.45,
          null
        ],
        "o_ep": [
          0.22,
          null
        ],
        "o_hj": [
          0.36,
          null
        ],
        "o_mp": [
          0.28,
          null
        ],
        "o_sb": [
          0.487,
          null
        ],
        "open_btn": [
          null,
          0.42
        ],
        "open_co": [
          null,
          0.27
        ],
        "open_ep": [
          null,
          0.13
        ],
        "open_mp": [
          null,
          0.18
        ],
        "open_sb": [
          null,
          0.36
        ],
        "open_size": [
          3.5,
          2.5
        ],
        "overlimp": [
          0.3,
          null
        ],
        "pf_call_margin": [
          0.0,
          null
        ],
        "portfolio": [
          null,
          0
        ],
        "pri_ftb": [
          0.6,
          null
        ],
        "pri_pfr": [
          0.17,
          null
        ],
        "pri_vpip": [
          0.28,
          null
        ],
        "q_3bet": [
          0,
          null
        ],
        "q_3bet_ftr": [
          0.8,
          null
        ],
        "q_3bet_range": [
          0.35,
          null
        ],
        "q_min_obs": [
          8,
          null
        ],
        "q_river_extra": [
          [
            1.75,
            3.0
          ],
          null
        ],
        "q_small_extra": [
          [
            0.15
          ],
          null
        ],
        "q_steal": [
          0,
          null
        ],
        "q_steal_f": [
          0.75,
          null
        ],
        "q_steal_ftr": [
          0.8,
          null
        ],
        "q_trap": [
          1,
          null
        ],
        "q_trap_af": [
          0.45,
          null
        ],
        "q_trap_eq": [
          0.8,
          null
        ],
        "r3_mult": [
          0.35,
          null
        ],
        "raise_eq": [
          null,
          0.82
        ],
        "raise_margin": [
          -0.04,
          null
        ],
        "raise_sizes": [
          [
            1.0,
            2.0
          ],
          null
        ],
        "real_ip": [
          1.05,
          0.85
        ],
        "real_oop": [
          0.92,
          0.7
        ],
        "river_overbet": [
          null,
          0.0
        ],
        "sb_limp": [
          0.0,
          null
        ],
        "sd_read": [
          null,
          0.0
        ],
        "semibluff_eq": [
          null,
          0.38
        ],
        "shove_spr": [
          5,
          null
        ],
        "size_exp": [
          1.0,
          null
        ],
        "size_k": [
          null,
          0.5
        ],
        "steal_k": [
          1.5,
          null
        ],
        "tag_counter": [
          null,
          0
        ],
        "threebet_bluff": [
          null,
          0.03
        ],
        "threebet_size": [
          null,
          3.2
        ],
        "threebet_value": [
          null,
          0.035
        ],
        "value_flop": [
          null,
          0.64
        ],
        "value_river": [
          null,
          0.72
        ],
        "value_turn": [
          null,
          0.68
        ],
        "w_b_mid": [
          0.85,
          null
        ],
        "w_b_weak": [
          0.55,
          null
        ],
        "w_r_air": [
          0.5,
          null
        ],
        "w_r_mid": [
          0.6,
          null
        ],
        "w_r_weak": [
          0.25,
          null
        ]
      }
    },
    "tools/independent_pablo/candidate/engine.py": {
      "params": {
        "pri_vpip": 0.28,
        "pri_pfr": 0.17,
        "pri_ftb": 0.6,
        "r3_mult": 0.35,
        "call_lo": 0.6,
        "bb_raise": 0.08,
        "open_size": 3.5,
        "loose_add": 1.0,
        "o_btn": 0.42,
        "o_sb": 0.34,
        "o_co": 0.3,
        "o_hj": 0.24,
        "o_mp": 0.19,
        "o_ep": 0.15,
        "steal_k": 0.75,
        "iso_mult": 0.9,
        "overlimp": 0.3,
        "sb_limp": 0.0,
        "multi_exp": 0.75,
        "real_ip": 1.05,
        "real_oop": 0.92,
        "eq_3b": 0.48,
        "eq_4b": 0.56,
        "3b_ip": 3.0,
        "3b_oop": 3.6,
        "pf_call_margin": 0.0,
        "bluff_base": 0.15,
        "bluff_af": 1.2,
        "w_r_air": 0.5,
        "w_r_weak": 0.25,
        "w_r_mid": 0.6,
        "w_b_weak": 0.55,
        "w_b_mid": 0.85,
        "c_air": 0.15,
        "c_weak": 0.55,
        "c_mid": 0.88,
        "size_exp": 1.0,
        "max_sims": 1500,
        "max_ms": 1.2,
        "bet_sizes": [
          0.33,
          0.6,
          1.0
        ],
        "raise_sizes": [
          1.0,
          2.0
        ],
        "shove_spr": 5,
        "chk_ip": 1.0,
        "chk_oop": 0.9,
        "bet_margin": 0.02,
        "call_tax": 0.0,
        "fold_vs_raise": 1.0,
        "raise_margin": 0.02,
        "hard_ms": 3.0,
        "q_steal": 0,
        "q_steal_ftr": 0.8,
        "q_steal_f": 0.75,
        "q_3bet": 0,
        "q_3bet_range": 0.35,
        "q_3bet_ftr": 0.8,
        "q_river_extra": [
          1.75,
          3.0
        ],
        "q_small_extra": [
          0.15
        ],
        "q_trap": 1,
        "q_trap_eq": 0.8,
        "q_trap_af": 0.45,
        "q_min_obs": 8,
        "sd_cal": 0,
        "sd_prior": 0.42,
        "sd_k": 6,
        "real_sb": 0.92,
        "size_read": 0.0,
        "fold_cal": 0,
        "ident": 0,
        "id_k": 30
      },
      "config_diff_vs_G": {
        "bet_margin": [
          -0.08,
          0.02
        ],
        "c_mid": [
          1,
          0.88
        ],
        "chk_ip": [
          0.8,
          1.0
        ],
        "chk_oop": [
          0.7,
          0.9
        ],
        "eq_3b": [
          0.52,
          0.48
        ],
        "fold_cal": [
          null,
          0
        ],
        "id_k": [
          null,
          30
        ],
        "ident": [
          null,
          0
        ],
        "o_btn": [
          0.7,
          0.42
        ],
        "o_co": [
          0.45,
          0.3
        ],
        "o_ep": [
          0.22,
          0.15
        ],
        "o_hj": [
          0.36,
          0.24
        ],
        "o_mp": [
          0.28,
          0.19
        ],
        "o_sb": [
          0.487,
          0.34
        ],
        "raise_margin": [
          -0.04,
          0.02
        ],
        "real_sb": [
          null,
          0.92
        ],
        "sd_cal": [
          null,
          0
        ],
        "sd_k": [
          null,
          6
        ],
        "sd_prior": [
          null,
          0.42
        ],
        "size_read": [
          null,
          0.0
        ],
        "steal_k": [
          1.5,
          0.75
        ]
      }
    }
  },
  "A_v_A": {
    "submissions/G_v7_final/bot.py": {
      "full_trajectory_and_result_match": true,
      "result_log_sha256": "430753218bed87f5500fc94e8d69853a64bf29766d998283724d4ca5889f4dd2"
    },
    "tools/independent_pablo/bot.py": {
      "full_trajectory_and_result_match": true,
      "result_log_sha256": "a07bd8a804ee127a314899f27940abf332ba427ec4861f476b4ecb68fb255197"
    }
  },
  "official_subprocess_smoke": {
    "hands": 20,
    "hero_chips": 1900,
    "stats": {
      "decisions": 25,
      "timeouts": 0,
      "errors": 0,
      "error_samples": [],
      "max_ms": 4.65,
      "avg_ms": 0.696,
      "bank_out": 0
    }
  },
  "effects": {
    "1-50": {
      "pablo_bb100": 135.51999999999998,
      "G_bb100": 295.92,
      "diff_bb100": -160.40000000000003,
      "paired_se": 112.88313868775974,
      "pair_diffs": [
        132.29999999999995,
        -328.0,
        98.69999999999999,
        -361.20000000000005,
        -343.8
      ]
    },
    "51-200": {
      "pablo_bb100": 83.02666666666667,
      "G_bb100": 21.779999999999998,
      "diff_bb100": 61.24666666666668,
      "paired_se": 19.35916837056799,
      "pair_diffs": [
        80.16666666666671,
        74.63333333333333,
        115.43333333333334,
        29.866666666666674,
        6.133333333333333
      ]
    },
    "201-1000": {
      "pablo_bb100": 71.42875,
      "G_bb100": 70.07625,
      "diff_bb100": 1.3524999999999943,
      "paired_se": 29.55194668926228,
      "pair_diffs": [
        -5.974999999999998,
        114.61249999999998,
        -15.900000000000006,
        -29.66250000000001,
        -56.3125
      ]
    },
    "all": {
      "pablo_bb100": 76.373,
      "G_bb100": 74.12400000000001,
      "diff_bb100": 2.2489999999999966,
      "paired_se": 25.386476931626415,
      "pair_diffs": [
        13.859999999999992,
        86.48500000000001,
        9.529999999999987,
        -37.30999999999999,
        -61.32000000000002
      ]
    }
  },
  "rows": [
    {
      "seed": 87100000,
      "hero_seat": 0,
      "pablo_v4": {
        "chips": 15373,
        "window_chips": {
          "1-50": 3499,
          "51-200": 8511,
          "201-1000": 3363
        },
        "actions": {
          "1-50|preflop|fold": 43,
          "1-50|preflop|raise": 6,
          "1-50|flop|fold": 3,
          "1-50|flop|raise": 3,
          "1-50|preflop|call": 4,
          "1-50|flop|check": 1,
          "51-200|preflop|fold": 133,
          "51-200|preflop|raise": 12,
          "51-200|flop|check": 3,
          "51-200|turn|check": 1,
          "51-200|river|fold": 1,
          "51-200|preflop|call": 11,
          "51-200|flop|raise": 11,
          "51-200|preflop|check": 1,
          "51-200|turn|raise": 3,
          "51-200|river|check": 1,
          "51-200|flop|call": 2,
          "51-200|flop|fold": 2,
          "51-200|turn|fold": 1,
          "51-200|river|raise": 1,
          "201-1000|preflop|fold": 680,
          "201-1000|preflop|raise": 104,
          "201-1000|preflop|call": 61,
          "201-1000|flop|check": 11,
          "201-1000|flop|fold": 24,
          "201-1000|flop|call": 23,
          "201-1000|turn|raise": 17,
          "201-1000|flop|raise": 35,
          "201-1000|turn|check": 9,
          "201-1000|turn|fold": 6,
          "201-1000|river|check": 4,
          "201-1000|river|raise": 2,
          "201-1000|river|fold": 2,
          "201-1000|preflop|check": 1,
          "201-1000|turn|call": 2,
          "201-1000|river|call": 1
        },
        "all_seat_errors": 0,
        "hero_error_samples": []
      },
      "G": {
        "chips": 12601,
        "window_chips": {
          "1-50": 2176,
          "51-200": 6106,
          "201-1000": 4319
        },
        "actions": {
          "1-50|preflop|fold": 40,
          "1-50|preflop|raise": 8,
          "1-50|flop|fold": 3,
          "1-50|flop|raise": 5,
          "1-50|preflop|call": 6,
          "51-200|preflop|fold": 128,
          "51-200|preflop|call": 20,
          "51-200|flop|raise": 17,
          "51-200|preflop|raise": 14,
          "51-200|preflop|check": 1,
          "51-200|flop|check": 4,
          "51-200|flop|call": 3,
          "51-200|turn|raise": 1,
          "51-200|turn|fold": 1,
          "51-200|flop|fold": 1,
          "51-200|turn|check": 2,
          "51-200|turn|call": 1,
          "51-200|river|raise": 2,
          "201-1000|preflop|fold": 633,
          "201-1000|preflop|raise": 128,
          "201-1000|preflop|call": 109,
          "201-1000|flop|raise": 99,
          "201-1000|turn|raise": 26,
          "201-1000|river|raise": 15,
          "201-1000|flop|call": 10,
          "201-1000|turn|fold": 4,
          "201-1000|turn|call": 2,
          "201-1000|river|fold": 2,
          "201-1000|flop|fold": 26,
          "201-1000|river|check": 4,
          "201-1000|turn|check": 3,
          "201-1000|preflop|check": 1,
          "201-1000|flop|check": 2,
          "201-1000|river|call": 1
        },
        "all_seat_errors": 0,
        "hero_error_samples": []
      }
    },
    {
      "seed": 87100001,
      "hero_seat": 1,
      "pablo_v4": {
        "chips": 37533,
        "window_chips": {
          "1-50": -1435,
          "51-200": -7966,
          "201-1000": 46934
        },
        "actions": {
          "1-50|preflop|fold": 46,
          "1-50|preflop|call": 6,
          "1-50|flop|fold": 2,
          "1-50|preflop|raise": 3,
          "1-50|flop|raise": 1,
          "1-50|turn|raise": 1,
          "1-50|river|raise": 1,
          "51-200|preflop|fold": 122,
          "51-200|preflop|call": 19,
          "51-200|flop|raise": 12,
          "51-200|preflop|raise": 25,
          "51-200|flop|call": 4,
          "51-200|turn|raise": 3,
          "51-200|river|check": 1,
          "51-200|flop|fold": 4,
          "51-200|turn|fold": 1,
          "51-200|flop|check": 2,
          "51-200|turn|check": 1,
          "51-200|river|fold": 1,
          "201-1000|preflop|fold": 655,
          "201-1000|preflop|raise": 96,
          "201-1000|flop|call": 17,
          "201-1000|turn|raise": 11,
          "201-1000|preflop|call": 87,
          "201-1000|flop|raise": 53,
          "201-1000|flop|check": 15,
          "201-1000|flop|fold": 28,
          "201-1000|turn|call": 3,
          "201-1000|river|check": 4,
          "201-1000|turn|check": 5,
          "201-1000|river|call": 1,
          "201-1000|turn|fold": 5,
          "201-1000|river|raise": 2,
          "201-1000|preflop|check": 1
        },
        "all_seat_errors": 0,
        "hero_error_samples": []
      },
      "G": {
        "chips": 20236,
        "window_chips": {
          "1-50": 1845,
          "51-200": -10205,
          "201-1000": 28596
        },
        "actions": {
          "1-50|preflop|fold": 40,
          "1-50|preflop|call": 11,
          "1-50|flop|fold": 2,
          "1-50|preflop|raise": 4,
          "1-50|flop|raise": 6,
          "1-50|turn|raise": 4,
          "1-50|river|check": 2,
          "1-50|river|fold": 1,
          "1-50|river|raise": 1,
          "51-200|preflop|fold": 111,
          "51-200|preflop|call": 30,
          "51-200|flop|raise": 26,
          "51-200|preflop|raise": 28,
          "51-200|flop|fold": 3,
          "51-200|flop|call": 6,
          "51-200|turn|fold": 1,
          "51-200|turn|raise": 2,
          "51-200|river|raise": 1,
          "201-1000|preflop|fold": 621,
          "201-1000|preflop|raise": 118,
          "201-1000|flop|fold": 29,
          "201-1000|flop|raise": 83,
          "201-1000|preflop|call": 113,
          "201-1000|flop|call": 16,
          "201-1000|turn|raise": 21,
          "201-1000|turn|call": 6,
          "201-1000|river|raise": 13,
          "201-1000|turn|check": 3,
          "201-1000|river|check": 3,
          "201-1000|turn|fold": 4,
          "201-1000|river|fold": 3,
          "201-1000|flop|check": 3,
          "201-1000|river|call": 1,
          "201-1000|preflop|check": 1
        },
        "all_seat_errors": 0,
        "hero_error_samples": []
      }
    },
    {
      "seed": 87100002,
      "hero_seat": 2,
      "pablo_v4": {
        "chips": -9337,
        "window_chips": {
          "1-50": 3903,
          "51-200": 2739,
          "201-1000": -15979
        },
        "actions": {
          "1-50|preflop|raise": 7,
          "1-50|flop|call": 2,
          "1-50|turn|raise": 2,
          "1-50|preflop|fold": 44,
          "1-50|preflop|call": 2,
          "1-50|flop|raise": 2,
          "1-50|river|raise": 1,
          "1-50|turn|call": 1,
          "1-50|river|call": 1,
          "51-200|preflop|fold": 129,
          "51-200|preflop|raise": 19,
          "51-200|flop|raise": 13,
          "51-200|turn|raise": 4,
          "51-200|river|check": 2,
          "51-200|turn|fold": 3,
          "51-200|preflop|call": 8,
          "51-200|turn|check": 3,
          "51-200|flop|fold": 3,
          "51-200|flop|call": 1,
          "51-200|preflop|check": 1,
          "201-1000|preflop|fold": 671,
          "201-1000|preflop|raise": 111,
          "201-1000|flop|fold": 23,
          "201-1000|preflop|call": 68,
          "201-1000|flop|check": 10,
          "201-1000|flop|raise": 45,
          "201-1000|turn|raise": 13,
          "201-1000|turn|check": 5,
          "201-1000|river|raise": 4,
          "201-1000|flop|call": 15,
          "201-1000|river|check": 3,
          "201-1000|turn|fold": 7,
          "201-1000|river|fold": 1,
          "201-1000|turn|call": 2,
          "201-1000|river|call": 1,
          "201-1000|preflop|check": 1
        },
        "all_seat_errors": 0,
        "hero_error_samples": []
      },
      "G": {
        "chips": -11243,
        "window_chips": {
          "1-50": 2916,
          "51-200": -724,
          "201-1000": -13435
        },
        "actions": {
          "1-50|preflop|raise": 9,
          "1-50|flop|raise": 7,
          "1-50|preflop|fold": 40,
          "1-50|preflop|call": 6,
          "1-50|turn|raise": 2,
          "1-50|river|raise": 1,
          "1-50|turn|check": 1,
          "1-50|turn|fold": 1,
          "1-50|flop|fold": 1,
          "51-200|preflop|fold": 123,
          "51-200|preflop|raise": 19,
          "51-200|flop|raise": 18,
          "51-200|turn|raise": 7,
          "51-200|river|raise": 5,
          "51-200|preflop|call": 18,
          "51-200|turn|call": 3,
          "51-200|river|fold": 1,
          "51-200|flop|check": 1,
          "51-200|flop|fold": 3,
          "51-200|flop|call": 3,
          "51-200|river|call": 2,
          "51-200|river|check": 1,
          "51-200|preflop|check": 1,
          "201-1000|preflop|fold": 640,
          "201-1000|preflop|call": 105,
          "201-1000|flop|raise": 81,
          "201-1000|preflop|raise": 120,
          "201-1000|flop|fold": 21,
          "201-1000|turn|raise": 27,
          "201-1000|turn|fold": 2,
          "201-1000|river|raise": 15,
          "201-1000|flop|call": 15,
          "201-1000|flop|check": 4,
          "201-1000|turn|call": 5,
          "201-1000|river|check": 5,
          "201-1000|river|fold": 5,
          "201-1000|river|call": 2,
          "201-1000|turn|check": 2,
          "201-1000|preflop|check": 1
        },
        "all_seat_errors": 0,
        "hero_error_samples": []
      }
    },
    {
      "seed": 87100003,
      "hero_seat": 3,
      "pablo_v4": {
        "chips": 15100,
        "window_chips": {
          "1-50": -2878,
          "51-200": 7522,
          "201-1000": 10456
        },
        "actions": {
          "1-50|preflop|fold": 41,
          "1-50|preflop|call": 8,
          "1-50|flop|fold": 5,
          "1-50|preflop|raise": 7,
          "1-50|flop|check": 3,
          "1-50|flop|raise": 3,
          "1-50|turn|check": 3,
          "1-50|turn|call": 1,
          "1-50|river|raise": 1,
          "1-50|turn|fold": 1,
          "1-50|river|fold": 1,
          "51-200|preflop|raise": 26,
          "51-200|flop|fold": 4,
          "51-200|preflop|fold": 129,
          "51-200|flop|raise": 6,
          "51-200|preflop|call": 6,
          "51-200|turn|call": 1,
          "51-200|flop|check": 4,
          "51-200|flop|call": 1,
          "51-200|turn|check": 1,
          "51-200|river|raise": 1,
          "51-200|turn|raise": 1,
          "201-1000|preflop|fold": 675,
          "201-1000|preflop|raise": 131,
          "201-1000|preflop|call": 68,
          "201-1000|flop|raise": 55,
          "201-1000|flop|call": 19,
          "201-1000|turn|raise": 12,
          "201-1000|flop|check": 8,
          "201-1000|flop|fold": 16,
          "201-1000|turn|check": 3,
          "201-1000|turn|fold": 6,
          "201-1000|river|check": 3,
          "201-1000|river|call": 4,
          "201-1000|preflop|check": 2,
          "201-1000|turn|call": 3,
          "201-1000|river|raise": 2,
          "201-1000|river|fold": 1
        },
        "all_seat_errors": 0,
        "hero_error_samples": []
      },
      "G": {
        "chips": 22562,
        "window_chips": {
          "1-50": 734,
          "51-200": 6626,
          "201-1000": 15202
        },
        "actions": {
          "1-50|preflop|fold": 38,
          "1-50|preflop|call": 12,
          "1-50|flop|fold": 2,
          "1-50|preflop|raise": 7,
          "1-50|flop|raise": 10,
          "1-50|turn|raise": 2,
          "1-50|river|raise": 1,
          "1-50|river|check": 1,
          "1-50|river|fold": 1,
          "51-200|preflop|fold": 118,
          "51-200|preflop|raise": 30,
          "51-200|preflop|call": 21,
          "51-200|flop|check": 4,
          "51-200|flop|raise": 17,
          "51-200|turn|raise": 3,
          "51-200|river|raise": 2,
          "51-200|flop|fold": 4,
          "51-200|flop|call": 1,
          "201-1000|preflop|fold": 634,
          "201-1000|preflop|raise": 137,
          "201-1000|preflop|call": 123,
          "201-1000|flop|raise": 92,
          "201-1000|turn|raise": 27,
          "201-1000|river|raise": 19,
          "201-1000|flop|call": 14,
          "201-1000|turn|fold": 10,
          "201-1000|flop|fold": 27,
          "201-1000|flop|check": 4,
          "201-1000|river|check": 3,
          "201-1000|river|fold": 2,
          "201-1000|turn|check": 2,
          "201-1000|turn|call": 5,
          "201-1000|preflop|check": 2,
          "201-1000|river|call": 3
        },
        "all_seat_errors": 0,
        "hero_error_samples": []
      }
    },
    {
      "seed": 87100004,
      "hero_seat": 4,
      "pablo_v4": {
        "chips": 17704,
        "window_chips": {
          "1-50": 3687,
          "51-200": 1648,
          "201-1000": 12369
        },
        "actions": {
          "1-50|preflop|fold": 41,
          "1-50|preflop|raise": 12,
          "1-50|flop|raise": 4,
          "1-50|preflop|call": 2,
          "1-50|flop|check": 1,
          "1-50|turn|check": 1,
          "1-50|river|check": 1,
          "1-50|turn|raise": 1,
          "1-50|river|raise": 1,
          "51-200|preflop|fold": 127,
          "51-200|preflop|raise": 21,
          "51-200|flop|raise": 9,
          "51-200|turn|call": 1,
          "51-200|river|fold": 1,
          "51-200|preflop|call": 11,
          "51-200|flop|check": 6,
          "51-200|turn|raise": 1,
          "51-200|river|raise": 1,
          "51-200|flop|call": 1,
          "51-200|turn|fold": 1,
          "51-200|flop|fold": 7,
          "51-200|turn|check": 1,
          "51-200|river|check": 1,
          "201-1000|preflop|fold": 693,
          "201-1000|preflop|raise": 118,
          "201-1000|preflop|call": 56,
          "201-1000|flop|raise": 44,
          "201-1000|flop|call": 13,
          "201-1000|turn|check": 6,
          "201-1000|turn|call": 4,
          "201-1000|river|raise": 3,
          "201-1000|flop|check": 9,
          "201-1000|flop|fold": 18,
          "201-1000|preflop|check": 1,
          "201-1000|turn|raise": 12,
          "201-1000|river|check": 8,
          "201-1000|turn|fold": 4,
          "201-1000|river|fold": 2,
          "201-1000|river|call": 2
        },
        "all_seat_errors": 0,
        "hero_error_samples": []
      },
      "G": {
        "chips": 29968,
        "window_chips": {
          "1-50": 7125,
          "51-200": 1464,
          "201-1000": 21379
        },
        "actions": {
          "1-50|preflop|fold": 39,
          "1-50|preflop|raise": 13,
          "1-50|flop|raise": 7,
          "1-50|turn|raise": 3,
          "1-50|river|raise": 1,
          "1-50|preflop|call": 6,
          "1-50|river|check": 1,
          "1-50|river|fold": 1,
          "51-200|preflop|fold": 119,
          "51-200|preflop|raise": 24,
          "51-200|preflop|call": 21,
          "51-200|flop|raise": 20,
          "51-200|turn|fold": 2,
          "51-200|turn|raise": 2,
          "51-200|river|raise": 2,
          "51-200|flop|call": 1,
          "51-200|flop|fold": 7,
          "201-1000|preflop|fold": 659,
          "201-1000|preflop|call": 106,
          "201-1000|flop|raise": 85,
          "201-1000|preflop|raise": 118,
          "201-1000|flop|fold": 20,
          "201-1000|preflop|check": 1,
          "201-1000|flop|call": 8,
          "201-1000|turn|raise": 20,
          "201-1000|river|raise": 10,
          "201-1000|turn|call": 3,
          "201-1000|river|fold": 3,
          "201-1000|river|check": 1,
          "201-1000|river|call": 1,
          "201-1000|flop|check": 2,
          "201-1000|turn|check": 1,
          "201-1000|turn|fold": 4
        },
        "all_seat_errors": 0,
        "hero_error_samples": []
      }
    }
  ]
}
```

## Algorithms, lineage and what is actually new

The current export is the same broad weighted-range EV/Monte Carlo engine family as G/I/N, substantially extended rather than an unrelated poker algorithm. Its source still uses familiar G structures: preflop ranked ranges, per-seat Bayesian public-action estimates, weighted opponent hands, candidate bet EV and side-pot accounting. It is not a CFR blueprint or neural policy merely because the project includes RL/literature plans.

Meaningful v4 extensions visible in the export:
- Behavior-based opponent fingerprinting (`idll`, posterior identity mixture and `id_k`) supplies empirical priors without receiving opponent names.
- Embedded population/bot profile tables adjust observed bet-size/range-strength relationships and answer probabilities. `_size_weights` uses bet size to narrow strength classes.
- `ans_cal` models both fold and raise responses by bet size, blended between responses historically made against high-aggression own bots and others using hero's observed betting frequency. Raised-pot/value risks are therefore modeled differently from G's continue-only estimate.
- Winner-style configuration tightens early opens, uses a top14% heads-up3-bet threshold where applicable, changes3-bet/4-bet continuation ranges, removes G's8%-pot betting bonus, and changes check realization/bet-size choices.

These are bundled configuration/model/logic changes. A small pilot cannot attribute any net difference to one algorithm. The embedded empirical targets may suffer showdown selection bias; behavior-identification priors may lag opponents' overnight versions. Both deserve controlled ablations rather than treating fitted own-field scores as confirmation.

The exact exported MODEL, source and effective configurations are preserved in the isolated files and hash inventory. G/I/N comparisons use their exact named frozen files, not inferred website labels. v4 runs max_ms4/hard_ms8/max_sims6000/bank7s; G1.2/3/1500/8.5s. The fixed32-work strategy screen intentionally removes that compute imbalance. A subsequent real-runtime comparison must restore each exact export and measure the tournament subprocess protocol separately.

## Independent result and decision

The current named v4 export versus frozen G is +2.249bb/100, paired-table SE25.386 across five1000-hand pairs. Both positive and negative large effects occur. An approximate t95% interval is[-68.23,+72.73]. This is inconclusive and does not support replacing G or calling Pablo's export strongest. Window51-200 is positive in this sample, but selecting that window after viewing several windows would not validate early adaptation. No I/N extension is warranted until a credible G improvement is established.

Both full-trajectory A-v-A controls passed before screening. Zero diagnostic LocalPlayer errors were reported with internal exception propagation enabled. This is a more visible sandbox check than the original production act(), which silently falls back on exceptions. The20hand exact-export subprocess smoke passed25decisions with no timeout/error/bankout, maximum4.65ms and average0.696ms at25ms cap. This establishes small protocol compatibility only; it does not validate a1000hand bank or worst-case runtime.

Next: ask author to identify the intended strongest exact exported artifact and provide frozen-input/seed holdout evidence; repair candidate/export's missing committed prerequisites if that candidate is intended; use controlled module/config ablations and updated independent fields before further promotion. Keep G online per existing decision. No autonomous lab, exporter, credential fetch, workers or network service were started.

### Agent-method AST comparison

```json
{
  "G": {
    "identical_methods": [
      "on_table_start",
      "S",
      "on_hand_end",
      "blindfold",
      "legalise",
      "decide",
      "r"
    ],
    "changed_shared_methods": [
      "__init__",
      "_learn",
      "vpip",
      "pfr",
      "bigrate",
      "fold3",
      "ftr",
      "ftb",
      "af",
      "budget",
      "act",
      "pf_range",
      "preflop",
      "opp_models",
      "simulate",
      "postflop"
    ],
    "added_methods": [
      "_id_learn",
      "pri",
      "sdmult",
      "_id_obs",
      "_id_post",
      "_last_aggr",
      "_size_weights"
    ]
  },
  "I": {
    "identical_methods": [
      "on_table_start",
      "S",
      "on_hand_end",
      "blindfold",
      "legalise",
      "decide",
      "r"
    ],
    "changed_shared_methods": [
      "__init__",
      "_learn",
      "vpip",
      "pfr",
      "bigrate",
      "fold3",
      "ftr",
      "ftb",
      "af",
      "budget",
      "act",
      "pf_range",
      "preflop",
      "opp_models",
      "simulate",
      "postflop"
    ],
    "added_methods": [
      "_id_learn",
      "pri",
      "sdmult",
      "_id_obs",
      "_id_post",
      "_last_aggr",
      "_size_weights"
    ]
  },
  "N": {
    "identical_methods": [
      "on_table_start",
      "S",
      "on_hand_end",
      "blindfold",
      "legalise",
      "decide",
      "r"
    ],
    "changed_shared_methods": [
      "__init__",
      "_learn",
      "vpip",
      "pfr",
      "bigrate",
      "fold3",
      "ftr",
      "ftb",
      "af",
      "budget",
      "act",
      "pf_range",
      "preflop",
      "opp_models",
      "simulate",
      "postflop"
    ],
    "added_methods": [
      "_id_learn",
      "pri",
      "sdmult",
      "_id_obs",
      "_id_post",
      "_last_aggr",
      "_size_weights"
    ]
  }
}
```
