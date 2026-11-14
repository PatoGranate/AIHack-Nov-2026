"""Autonomous tuner for the v2 engine (pokerbot/v2.py): the RSI loop on the new bot.

Each cycle:
  1. propose ~6 candidates around the champion (single-knob steps from a bandit
     over knobs, plus one random 3-knob package)
  2. selection: paired duplicate tables vs the champion on two realistic fields
     (real WBot/Red code + equity clones of every real bot; real code only)
  3. the best candidate goes to a holdout on fresh seeds (twice the tables)
  4. promote if the holdout gain is positive at 80% one-sided confidence and the
     selection agreed; then write data/v2_params.json, export bot.py, timing-check it

    python -m rsi.v2_tuner            # until data/STOP_V2 exists
"""
import json
import math
import os
import random
import statistics as st
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PARAMS_FILE = os.path.join(ROOT, "data", "v2_params.json")
HISTORY_FILE = os.path.join(ROOT, "data", "v2_history.json")
STOP_FILE = os.path.join(ROOT, "data", "STOP_V2")

# knob: (lo, hi, step)   lists are handled as fixed choices
SPACE = {
    "o_ep": (0.12, 0.30, 0.02), "o_mp": (0.16, 0.36, 0.02), "o_hj": (0.22, 0.44, 0.03), "o_co": (0.33, 0.60, 0.03),
    "o_btn": (0.40, 0.80, 0.05), "o_sb": (0.30, 0.60, 0.04), "open_size": (2.5, 4.0, 0.25), "loose_add": (0.0, 1.0, 0.5),
    "steal_k": (0.5, 2.5, 0.5), "eq_3b": (0.44, 0.58, 0.02), "eq_4b": (0.50, 0.62, 0.02),
    "3b_ip": (2.6, 3.8, 0.2), "3b_oop": (3.0, 4.2, 0.2), "real_ip": (0.90, 1.15, 0.05), "real_oop": (0.78, 1.0, 0.04),
    "real_sb": (0.70, 0.96, 0.04), "bluff_base": (0.05, 0.30, 0.05), "bluff_af": (0.4, 2.0, 0.4),
    "c_air": (0.05, 0.30, 0.05), "c_weak": (0.40, 0.75, 0.05), "chk_ip": (0.70, 0.95, 0.05), "chk_oop": (0.60, 0.85, 0.05),
    "bet_margin": (-0.12, 0.04, 0.02), "raise_margin": (-0.08, 0.04, 0.02), "call_tax": (0.0, 0.06, 0.02),
    "fold_vs_raise": (0.8, 1.3, 0.1), "size_exp": (0.7, 1.4, 0.1), "multi_exp": (0.5, 1.0, 0.1),
    "w_b_weak": (0.35, 0.75, 0.1), "w_b_mid": (0.65, 1.0, 0.05), "sd_cal": (0, 1, 1), "q_trap": (0, 1, 1),
}
BASE = {"max_ms": 6.0, "hard_ms": 12.0, "max_sims": 6000}
SEL_TABLES, HOLD_TABLES, HANDS = 128, 288, 300


def load_champion():
    try:
        return json.load(open(PARAMS_FILE))
    except (OSError, ValueError):
        return dict(BASE)


def load_history():
    try:
        return json.load(open(HISTORY_FILE))
    except (OSError, ValueError):
        return {"cycles": [], "arms": {}, "seed_cursor": 900000}


def save_history(h):
    json.dump(h, open(HISTORY_FILE, "w"), indent=1)


def current(params, k):
    from pokerbot.v2 import P
    return params.get(k, P[k])


def step(params, k, d):
    lo, hi, s = SPACE[k]
    v = current(params, k) + d * s
    v = max(lo, min(hi, v))
    return int(round(v)) if s == 1 else round(v, 4)


def propose(champ, hist, rng, n=5):
    """UCB over (knob, direction) arms, skipping no-op steps."""
    arms = hist["arms"]
    total = sum(a["n"] for a in arms.values()) + 1
    scored = []
    for k in SPACE:
        for d in (-1, 1):
            nv = step(champ, k, d)
            if nv == current(champ, k):
                continue
            a = arms.get("%s%+d" % (k, d), {"n": 0, "sum": 0.0})
            mean = a["sum"] / a["n"] if a["n"] else 3.0
            ucb = mean + 6.0 * math.sqrt(math.log(total + 1) / (a["n"] + 1))
            scored.append((ucb + rng.random() * 0.5, k, d, nv))
    scored.sort(reverse=True)
    cands, used = [], set()
    for _, k, d, nv in scored:
        if k in used:
            continue
        used.add(k)
        cands.append(("%s%+d" % (k, d), {k: nv}, [(k, d)]))
        if len(cands) >= n:
            break
    # one random package of 3 knobs
    ks = rng.sample(list(SPACE), 3)
    pkg, arms_used = {}, []
    for k in ks:
        d = rng.choice((-1, 1))
        nv = step(champ, k, d)
        if nv != current(champ, k):
            pkg[k] = nv
            arms_used.append((k, d))
    if pkg:
        cands.append(("pkg:" + ",".join("%s%+d" % a for a in arms_used), pkg, arms_used))
    return cands


def evaluate(heroes, tables, seed0):
    """heroes: {name: params}; the first is the reference. Returns {name: (mean diff, se, n)}."""
    from rsi.field import _equity_clone_mix
    from sim import arena, opponents
    real = opponents.real_bot_specs()
    fields = [[(6, s) for s in real] + _equity_clone_mix(), [(1, s) for s in real]]
    names = list(heroes)
    jobs = []
    for fi, mix in enumerate(fields):
        for s in range(tables):
            seed = seed0 + fi * 100000 + s
            opps = opponents.lineup(seed, 6, mix=mix)
            for hi, n in enumerate(names):
                jobs.append(arena.make_job("%d|%d|%d" % (fi, seed, hi), 0, seed, HANDS,
                                           {"kind": "v2", "params": heroes[n], "strategy_id": n}, opps,
                                           record=False, fixed_iters=64, opp_iters=40))
    res = arena.run_batch(jobs)
    by = {}
    for r in res:
        if r.get("error"):
            continue
        fi, seed, hi = r["table_id"].split("|")
        by.setdefault((fi, seed), {})[int(hi)] = r["hero_ev_chips"] / 20 / r["hands"] * 100
    out = {}
    for hi, n in enumerate(names):
        d = [v[hi] - v[0] for v in by.values() if hi in v and 0 in v]
        out[n] = (st.mean(d) if d else 0.0, (st.stdev(d) / len(d) ** 0.5) if len(d) > 1 else 99.0, len(d))
    return out


def export_and_check(params):
    sys.path.insert(0, ROOT)
    from export_v2 import export
    from rsi.lab import timing_check
    tmp = os.path.join(ROOT, "data", "v2_candidate_bot.py")
    export(params, tmp)
    ok, info = timing_check(tmp, hands=400, timeout_ms=25.0)
    if ok:
        export(params, os.path.join(ROOT, "bot.py"))
    return ok, info


def main():
    rng = random.Random()
    hist = load_history()
    while not os.path.exists(STOP_FILE):
        champ = load_champion()
        t0 = time.time()
        cands = propose(champ, hist, rng)
        heroes = {"champion": champ}
        for name, change, _ in cands:
            heroes[name] = dict(champ, **change)
        seed0 = hist["seed_cursor"]
        hist["seed_cursor"] += 1000
        print("\n[v2 %s] cycle %d: %s" % (time.strftime("%H:%M:%S"), len(hist["cycles"]) + 1,
                                           ", ".join(n for n, _, _ in cands)), flush=True)
        sel = evaluate(heroes, SEL_TABLES, seed0)
        for name, change, arms_used in cands:
            m, se, n = sel[name]
            print("   %-46s %+6.1f bb/100 (se %.1f)" % (name, m, se), flush=True)
            for k, d in arms_used:
                a = hist["arms"].setdefault("%s%+d" % (k, d), {"n": 0, "sum": 0.0})
                a["n"] += 1
                a["sum"] += m / max(1, len(arms_used))
        best = max(cands, key=lambda c: sel[c[0]][0] - 0.5 * sel[c[0]][1])
        bm, bse, _ = sel[best[0]]
        rec = {"ts": time.time(), "candidates": {n: sel[n][:2] for n, _, _ in cands}, "best": best[0],
               "promoted": False}
        if bm > 1.0 and bm > bse:
            seed1 = hist["seed_cursor"]
            hist["seed_cursor"] += 1000
            hold = evaluate({"champion": champ, best[0]: dict(champ, **best[1])}, HOLD_TABLES, seed1)
            hm, hse, hn = hold[best[0]]
            rec["holdout"] = [hm, hse, hn]
            print("   holdout %s: %+.1f bb/100 (se %.1f, %d tables)" % (best[0], hm, hse, hn), flush=True)
            if hm > 0.84 * hse:
                newp = dict(champ, **best[1])
                ok, info = export_and_check(newp)
                if ok:
                    json.dump(newp, open(PARAMS_FILE, "w"), indent=1, sort_keys=True)
                    rec["promoted"] = True
                    rec["params"] = newp
                    print("   PROMOTED %s -> bot.py exported, timing ok %s" % (best[0], info), flush=True)
                else:
                    print("   timing check failed, not promoted: %s" % info, flush=True)
            else:
                print("   holdout not convincing: kept champion", flush=True)
        else:
            print("   no candidate worth a holdout", flush=True)
        rec["seconds"] = time.time() - t0
        hist["cycles"].append(rec)
        save_history(hist)
    os.remove(STOP_FILE)
    print("[v2] STOP_V2 found; exiting")


if __name__ == "__main__":
    main()
