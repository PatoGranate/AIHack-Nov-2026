"""The RSI loop (adapted from lab/research.py):

  observe -> diagnose -> propose -> select -> pre-register -> holdout ->
  challenger -> gate -> promote (old champion joins the league) -> repeat

  - A proposal is DATA: the champion with one parameter moved. Nothing proposed
    is ever executed as code.
  - Selection uses its own fresh seeds. The holdout uses different fresh seeds,
    looked at once, for the single selected contender; the look is recorded.
  - Every table is played twice with the same seed (duplicate poker), and the
    evidence is the per-table difference in all-in-EV-adjusted chips (the
    chance-node part of AIVAT): ~3x less variance than raw chips.
  - Training opponents = clones of the REAL field (rsi/field.py, from
    downloaded hands) + the synthetic pool + former champions. The challenger
    uses a different pool (house bots, starter, archetypes, extremes) and no
    self-play, so a candidate that only beats its ancestors is caught.
  - Only the deterministic gate (rsi/gate.py) can promote.
  - `judge` is also how the autonomous lab tests ideas from the literature
    (rsi/lab.py): same pre-registration, holdout, challenger and gate.
"""
import json
import time
from fractions import Fraction

from rsi import gate, propose, registry
from rsi.diagnose import diagnose, format_report, prioritize
from rsi.stats import adjusted_alpha, bootstrap_mean_interval, minimum_detectable_effect, sample_sd
from sim import arena, opponents
from storage import db as store

BB = 20

DEFAULTS = {
    "candidates": 6,
    "selection_tables": 96, "selection_hands": 300,
    "holdout_tables": 192, "holdout_hands": 400,
    "challenger_tables": 96, "challenger_hands": 300,
    "workers": None,
    # 64 Monte Carlo trials ~ what the live bot gets in its 1 ms budget; ~5x faster than 120/50
    "hero_iters": 64, "opp_iters": 24,
    "table_config": {"betting": "no_limit", "raise_cap": 0},
    "field_share": 0.7,          # share of opponents drawn from real-field clones when hands/ has data
}

CHALLENGER_MIX = [
    (3, {"kind": "house", "name": "tag"}), (2, {"kind": "house", "name": "station"}),
    (2, {"kind": "house", "name": "random"}), (5, {"kind": "starter"}),
    (2, {"kind": "arch", "name": "nit"}), (1, {"kind": "arch", "name": "maniac"}),
    (2, {"kind": "arch", "name": "lag"}),
    (1, {"kind": "extreme", "name": "jammer"}), (1, {"kind": "extreme", "name": "checkraiser"}),
    (1, {"kind": "extreme", "name": "randomsizer"}), (1, {"kind": "extreme", "name": "overbettor"}),
]


def training_mix(share=0.7):
    """Real-field clones (if any hands were downloaded) blended with the synthetic pool."""
    from rsi.field import field_mix
    fm = field_mix()
    real = opponents.real_bot_specs()             # the actual WBot / Red code: the most realistic opponents we have
    if real:
        fm = fm + [(max(1.0, sum(w for w, _ in fm) * 0.15 / len(real)), s) for s in real]
    if not fm:
        return list(opponents.DEFAULT_MIX)
    f_tot = sum(w for w, _ in fm)
    d_tot = sum(w for w, _ in opponents.DEFAULT_MIX)
    scale = f_tot * (1 - share) / share / d_tot
    return fm + [(w * scale, s) for w, s in opponents.DEFAULT_MIX]


def _bb100(chips, hands):
    return chips / BB / max(1, hands) * 100


def _paired_jobs(db, kind, seeds, hands, heroes, league, mix, cfg, record_first=True, note=""):
    bid = store.new_batch(db, kind, len(seeds) * len(heroes), hands, note)
    jobs = []
    for seed in seeds:
        opps = opponents.lineup(seed, 7, league=league, mix=mix)
        for i, h in enumerate(heroes):
            jobs.append(arena.make_job("%s-%d-b%d-%s" % (kind, seed, bid, h["strategy_id"]), bid, seed, hands, h, opps,
                                       record=record_first and i == 0, config=cfg["table_config"],
                                       fixed_iters=cfg["hero_iters"], opp_iters=cfg["opp_iters"]))
    return bid, jobs


def _run(db, jobs, cfg, label, log=print):
    t0 = time.time()

    def prog(i, n, _):
        if i == n or i % 16 == 0:
            print("\r  [%s] %d/%d tables  %.0fs" % (label, i, n, time.time() - t0), end="", flush=True)
    res = arena.run_batch(jobs, db, workers=cfg["workers"], progress=prog)
    print()
    return res


def _diffs(results, base_id, cand_id):
    """Per-seed difference candidate - champion in all-in-EV chips (seed -> diff)."""
    b_key, c_key = base_id.split("-")[-1], cand_id.split("-")[-1]
    by = {}
    for r in results:
        if r.get("error"):
            continue
        by.setdefault(r["seed"], {})[r["table_id"].rsplit("-", 1)[-1]] = r
    out, hands, errors = {}, None, 0
    for seed, d in by.items():
        if b_key in d and c_key in d:
            b, c = d[b_key], d[c_key]
            out[seed] = c.get("hero_ev_chips", c["hero_chips"]) - b.get("hero_ev_chips", b["hero_chips"])
            hands = c["hands"]
            errors += c["hero_errors"]
    return out, hands or 1, errors


def _record_trial(db, cycle, parent, cand_id, changed, stage, n, mean, lo, hi, status, detail):
    cur = db.execute("INSERT INTO trials(cycle, parent_id, candidate_id, changed, stage, n, mean_bb100, ci_low, ci_high, status, "
                     "detail, created) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                     (cycle, parent, cand_id, changed, stage, n, mean, lo, hi, status, json.dumps(detail, default=str), time.time()))
    db.commit()
    return cur.lastrowid


def judge(db, cycle, champ, cand, cfg, log=print, trials_used=1, source="rsi"):
    """Pre-register -> holdout (once) -> challenger -> gate -> promote. cand: {id, params, changed, hypothesis, spec}."""
    base = registry.spec(champ)
    league = registry.league(db)
    mix = training_mix(cfg["field_share"])
    hold = registry.fresh_seeds(db, cfg["holdout_tables"])
    fresh = registry.seeds_unused(db, hold)
    prereg = {"candidate_sha256": gate.sha(cand["params"]), "parent_sha256": gate.sha(champ["params"]),
              "changed": gate.changed_parameters(champ["params"], cand["params"]),
              "holdout_sha256": gate.sha(hold), "lab_sha256": gate.LAB_SHA, "source": source,
              "package": bool(cand.get("package"))}
    trial_id = _record_trial(db, cycle, champ["id"], cand["id"], cand["changed"], "prereg", len(hold), None, None, None,
                             "registered", prereg)

    bid, jobs = _paired_jobs(db, "holdout", hold, cfg["holdout_hands"], [base, cand["spec"]], league, mix, cfg,
                             record_first=False, note="cycle %d trial %d" % (cycle, trial_id))
    res = _run(db, jobs, cfg, "holdout")
    store.finish_batch(db, bid)
    d, hands, errs = _diffs(res, champ["id"], cand["id"])
    ordered = [d[s] for s in hold if s in d]
    looks = db.execute("SELECT COUNT(*) FROM trials WHERE parent_id=? AND stage='holdout'", (champ["id"],)).fetchone()[0] + 1
    alpha = adjusted_alpha(Fraction(gate.LAB["alpha"]).limit_denominator(1000), looks if gate.LAB["bonferroni"] else 1)
    lo, hi = bootstrap_mean_interval(ordered, alpha=alpha, resamples=gate.LAB["bootstrap_resamples"],
                                     seed="holdout-%d-%s" % (trial_id, cand["id"]))
    vals = [_bb100(v, hands) for v in ordered]
    mean = sum(vals) / len(vals)
    mde = minimum_detectable_effect(sd=sample_sd(vals), n=len(vals), alpha=alpha,
                                    power=Fraction(gate.LAB["power"]).limit_denominator(100))
    k = gate.LAB["folds"]
    folds = [round(sum(vals[i::k]) / max(1, len(vals[i::k])), 1) for i in range(k)]

    ch_seeds = registry.fresh_seeds(db, cfg["challenger_tables"])
    from rsi.field import recent_stat_mix
    recent = recent_stat_mix()
    ch_mix = (recent + [(w * 0.25, s) for w, s in CHALLENGER_MIX if s["kind"] == "extreme"]) if recent else CHALLENGER_MIX
    real = opponents.real_bot_specs()
    if real:
        ch_mix = ch_mix + [(sum(w for w, _ in ch_mix) * 0.15 / len(real), s) for s in real]
    bid, jobs = _paired_jobs(db, "challenger", ch_seeds, cfg["challenger_hands"], [base, cand["spec"]], (), ch_mix, cfg,
                             record_first=False, note="cycle %d trial %d" % (cycle, trial_id))
    res = _run(db, jobs, cfg, "challenger")
    store.finish_batch(db, bid)
    cd, ch_hands, ch_errs = _diffs(res, champ["id"], cand["id"])
    ch_mean = sum(_bb100(v, ch_hands) for v in cd.values()) / max(1, len(cd))

    evidence = {"holdout_seeds": hold, "tables": len(vals), "mean_bb100": round(mean, 2),
                "ci_low_bb100": round(_bb100(float(lo), hands), 2), "ci_high_bb100": round(_bb100(float(hi), hands), 2),
                "alpha_adjusted": float(alpha), "trials_counted": looks, "mde_bb100": round(mde, 2),
                "detectable": mean >= mde, "folds": folds, "challenger_bb100": round(ch_mean, 2),
                "candidate_errors": errs + ch_errs, "metric": "all-in EV adjusted chips"}
    decision = gate.decide(cand["params"], champ["params"], prereg, evidence,
                           {"holdout_fresh": fresh, "trials_used": trials_used})
    _record_trial(db, cycle, champ["id"], cand["id"], cand["changed"], "holdout", len(vals), evidence["mean_bb100"],
                  evidence["ci_low_bb100"], evidence["ci_high_bb100"], "approved" if decision["approved"] else "rejected",
                  {"evidence": {k2: v for k2, v in evidence.items() if k2 != "holdout_seeds"}, "gate": decision, "source": source})
    log("  holdout: %+.1f bb/100, CI [%+.1f, %+.1f] at alpha %.4f, MDE %.1f, folds %s, challenger %+.1f" % (
        mean, evidence["ci_low_bb100"], evidence["ci_high_bb100"], float(alpha), mde, folds, ch_mean))
    if decision["approved"]:
        new = store.load_strategy(db, cand["id"])
        registry.promote(db, cycle, champ, new, decision)
        log("  PROMOTED %s -> %s (%s)" % (champ["id"], new["id"], cand["hypothesis"]))
        return {"cycle": cycle, "promoted": True, "champion": new["id"], "evidence": evidence}
    log("  gate refused: " + ", ".join(decision["reasons"]))
    db.execute("UPDATE strategies SET status='rejected' WHERE id=? AND status='candidate'", (cand["id"],))
    db.commit()
    return {"cycle": cycle, "promoted": False, "reason": decision["reasons"], "evidence": evidence}


def make_candidate(db, champ, params, changed, hypothesis, direction=0, steps=1, package=False):
    cid = registry.strategy_id(params)
    store.save_strategy(db, cid, params, champ["id"], champ["generation"] + 1, hypothesis, "candidate")
    return {"id": cid, "params": params, "changed": changed, "hypothesis": hypothesis, "direction": direction,
            "steps": steps, "spec": {"kind": "strategy", "params": params, "strategy_id": cid}, "package": package}


def run_cycle(db, cycle, cfg=None, log=print, extra_priority=()):
    cfg = dict(DEFAULTS, **(cfg or {}))
    champ = registry.champion(db)
    base = registry.spec(champ)
    league = registry.league(db)
    log("\n=== RSI cycle %d | champion %s (gen %d) | league %d former champions" % (
        cycle, champ["id"], champ["generation"], len(league)))

    train = [r["id"] for r in db.execute("SELECT id FROM batches WHERE kind IN ('practice','selection')")]
    rep = diagnose(db, champ["id"], batch_ids=train) if train else {"leaks": []}
    if rep.get("hands"):
        log(format_report(rep))
    priority = list(extra_priority) + [a for a in prioritize(rep, champ["params"]) if a not in extra_priority]

    cands = []
    for c in propose.propose(champ["params"], priority, db, k=cfg["candidates"]):
        cands.append(make_candidate(db, champ, c["params"], c["changed"], c["hypothesis"], c["direction"], c["steps"]))
    log("  proposals: " + "; ".join(c["hypothesis"] for c in cands))

    seeds = registry.fresh_seeds(db, cfg["selection_tables"])
    mix = training_mix(cfg["field_share"])
    bid, jobs = _paired_jobs(db, "selection", seeds, cfg["selection_hands"], [base] + [c["spec"] for c in cands],
                             league, mix, cfg, note="cycle %d" % cycle)
    res = _run(db, jobs, cfg, "selection")
    store.finish_batch(db, bid)
    scored = []
    for c in cands:
        d, hands, errs = _diffs(res, champ["id"], c["id"])
        vals = [_bb100(v, hands) for v in d.values()]
        mean = sum(vals) / len(vals) if vals else -999
        se = (sample_sd(vals) if len(vals) > 1 else 0) / max(1, len(vals)) ** 0.5
        _record_trial(db, cycle, champ["id"], c["id"], c["changed"], "selection", len(vals), mean, mean - 1.96 * se,
                      mean + 1.96 * se, "scored", {"direction": c["direction"], "steps": c["steps"], "errors": errs})
        scored.append((mean, se, c))
        log("    %-38s %+7.1f bb/100 (se %.1f)" % (c["hypothesis"][:38], mean, se))
    scored.sort(key=lambda x: -x[0])
    best_mean, _, best = scored[0]
    if best_mean <= 0:
        log("  no contender beat the champion in selection; cycle ends")
        return {"cycle": cycle, "promoted": False, "reason": "NO_CONTENDER"}
    return judge(db, cycle, champ, best, cfg, log, trials_used=len(cands))


def next_cycle(db):
    return (db.execute("SELECT MAX(cycle) FROM trials").fetchone()[0] or 0) + 1


def research_loop(db, cycles=None, hours=None, cfg=None, log=print):
    start = time.time()
    out = []
    done = 0
    while True:
        if cycles is not None and done >= cycles:
            break
        if hours is not None and time.time() - start > hours * 3600:
            break
        out.append(run_cycle(db, next_cycle(db), cfg, log))
        done += 1
    return out
