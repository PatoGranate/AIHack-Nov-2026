"""The RSI loop (adapted from lab/research.py):

  observe -> diagnose -> propose -> select -> pre-register -> holdout ->
  challenger -> gate -> promote (old champion joins the league) -> repeat

  - A proposal is DATA: the champion with one parameter moved. Nothing proposed
    is ever executed as code.
  - Selection uses its own fresh seeds. The holdout uses different fresh seeds,
    looked at once, for the single selected contender; the look is recorded.
  - Every table is played twice with the same seed (duplicate poker): once
    with the champion, once with the candidate. The per-table chip difference
    is the evidence, which removes most of the card luck.
  - Only the deterministic gate (rsi/gate.py) can promote.
  - After a promotion the old champion becomes an opponent, so each new
    champion has to beat every former version of itself: recursive
    self-improvement through self-play.
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
    "selection_tables": 48, "selection_hands": 300,
    "holdout_tables": 160, "holdout_hands": 500,
    "challenger_tables": 48, "challenger_hands": 400,
    "workers": None,
    "hero_iters": 120, "opp_iters": 60,
    "table_config": {"betting": "no_limit", "raise_cap": 0},
}

# The challenger never sees the self-play league: a candidate that only learned
# to beat its own ancestors is caught here.
CHALLENGER_MIX = [
    (3, {"kind": "house", "name": "tag"}), (2, {"kind": "house", "name": "station"}),
    (2, {"kind": "house", "name": "random"}), (6, {"kind": "starter"}),
    (2, {"kind": "arch", "name": "nit"}), (1, {"kind": "arch", "name": "maniac"}),
    (2, {"kind": "arch", "name": "lag"}),
]


def _bb100(chips, hands):
    return chips / BB / max(1, hands) * 100


def _paired_jobs(db, kind, seeds, hands, heroes, league, mix, cfg, record_first=True, note=""):
    bid = store.new_batch(db, kind, len(seeds) * len(heroes), hands, note)
    jobs = []
    for seed in seeds:
        opps = opponents.lineup(seed, 7, league=league if mix is None else (), mix=mix)
        for i, h in enumerate(heroes):
            jobs.append(arena.make_job("%s-%d-b%d-%s" % (kind, seed, bid, h["strategy_id"]), bid, seed, hands, h, opps,
                                       record=record_first and i == 0, config=cfg["table_config"],
                                       fixed_iters=cfg["hero_iters"], opp_iters=cfg["opp_iters"]))
    return bid, jobs


def _run(db, jobs, cfg, label):
    t0 = time.time()

    def prog(i, n, _):
        print("\r  [%s] %d/%d tables  %.0fs" % (label, i, n, time.time() - t0), end="", flush=True)
    res = arena.run_batch(jobs, db, workers=cfg["workers"], progress=prog)
    print()
    return res


def _diffs(results, base_id, cand_id):
    """Per-seed chip difference candidate - champion, as ints (seed -> diff)."""
    by = {}
    for r in results:
        if r.get("error"):
            continue
        sid = r["table_id"].rsplit("-", 1)[-1]
        by.setdefault(r["seed"], {})[sid] = r
    out, hands, errors = {}, None, 0
    for seed, d in by.items():
        if base_id.split("-")[-1] in d and cand_id.split("-")[-1] in d:
            b, c = d[base_id.split("-")[-1]], d[cand_id.split("-")[-1]]
            out[seed] = c["hero_chips"] - b["hero_chips"]
            hands = c["hands"]
            errors += c["hero_errors"]
    return out, hands or 1, errors


def run_cycle(db, cycle, cfg=None, log=print):
    cfg = dict(DEFAULTS, **(cfg or {}))
    champ = registry.champion(db)
    base = registry.spec(champ)
    league = registry.league(db)
    log("\n=== RSI cycle %d | champion %s (gen %d) | league %d former champions" % (
        cycle, champ["id"], champ["generation"], len(league)))

    # 1-2. observe + diagnose: champion hands from practice/selection only (never holdout)
    train = [r["id"] for r in db.execute("SELECT id FROM batches WHERE kind IN ('practice','selection')")]
    rep = diagnose(db, champ["id"], batch_ids=train) if train else {"leaks": []}
    if rep.get("hands"):
        log(format_report(rep))
    priority = prioritize(rep, champ["params"])

    # 3. propose
    cands = propose.propose(champ["params"], priority, db, k=cfg["candidates"])
    for c in cands:
        c["id"] = registry.strategy_id(c["params"])
        store.save_strategy(db, c["id"], c["params"], champ["id"], champ["generation"] + 1, c["hypothesis"], "candidate")
        c["spec"] = {"kind": "strategy", "params": c["params"], "strategy_id": c["id"]}
    log("  proposals: " + "; ".join(c["hypothesis"] for c in cands))

    # 4. selection on fresh seeds
    seeds = registry.fresh_seeds(db, cfg["selection_tables"])
    bid, jobs = _paired_jobs(db, "selection", seeds, cfg["selection_hands"], [base] + [c["spec"] for c in cands],
                             league, None, cfg, note="cycle %d" % cycle)
    res = _run(db, jobs, cfg, "selection")
    store.finish_batch(db, bid)
    scored = []
    for c in cands:
        d, hands, errs = _diffs(res, champ["id"], c["id"])
        vals = [_bb100(v, hands) for v in d.values()]
        mean = sum(vals) / len(vals) if vals else -999
        sd = sample_sd(vals) if len(vals) > 1 else 0
        se = sd / max(1, len(vals)) ** 0.5
        db.execute("INSERT INTO trials(cycle, parent_id, candidate_id, changed, stage, n, mean_bb100, ci_low, ci_high, status, detail, created) "
                   "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                   (cycle, champ["id"], c["id"], c["changed"], "selection", len(vals), mean, mean - 1.96 * se, mean + 1.96 * se,
                    "scored", json.dumps({"direction": c["direction"], "steps": c["steps"], "errors": errs}), time.time()))
        scored.append((mean, se, c))
        log("    %-34s %+7.1f bb/100 (se %.1f)" % (c["hypothesis"][:34], mean, se))
    db.commit()
    scored.sort(key=lambda x: -x[0])
    best_mean, best_se, best = scored[0]
    if best_mean <= 0:
        log("  no contender beat the champion in selection; cycle ends")
        return {"cycle": cycle, "promoted": False, "reason": "NO_CONTENDER"}

    # 5. pre-register the single contender and its holdout BEFORE looking
    hold = registry.fresh_seeds(db, cfg["holdout_tables"])
    fresh = registry.seeds_unused(db, hold)
    prereg = {"candidate_sha256": gate.sha(best["params"]), "parent_sha256": gate.sha(champ["params"]),
              "changed": gate.changed_parameters(champ["params"], best["params"]),
              "holdout_sha256": gate.sha(hold), "lab_sha256": gate.LAB_SHA}
    cur = db.execute("INSERT INTO trials(cycle, parent_id, candidate_id, changed, stage, n, status, detail, created) "
                     "VALUES (?,?,?,?,?,?,?,?,?)",
                     (cycle, champ["id"], best["id"], best["changed"], "prereg", len(hold), "registered", json.dumps(prereg), time.time()))
    db.commit()
    trial_id = cur.lastrowid

    # 6. holdout (once)
    bid, jobs = _paired_jobs(db, "holdout", hold, cfg["holdout_hands"], [base, best["spec"]], league, None, cfg,
                             record_first=False, note="cycle %d trial %d" % (cycle, trial_id))
    res = _run(db, jobs, cfg, "holdout")
    store.finish_batch(db, bid)
    d, hands, errs = _diffs(res, champ["id"], best["id"])
    ordered = [d[s] for s in hold if s in d]
    looks = db.execute("SELECT COUNT(*) FROM trials WHERE parent_id=? AND stage='holdout'", (champ["id"],)).fetchone()[0] + 1
    alpha = adjusted_alpha(Fraction(gate.LAB["alpha"]).limit_denominator(1000), looks)
    lo, hi = bootstrap_mean_interval(ordered, alpha=alpha, resamples=gate.LAB["bootstrap_resamples"],
                                     seed="holdout-%d-%s" % (trial_id, best["id"]))
    vals = [_bb100(v, hands) for v in ordered]
    mean = sum(vals) / len(vals)
    mde = minimum_detectable_effect(sd=sample_sd(vals), n=len(vals), alpha=alpha,
                                    power=Fraction(gate.LAB["power"]).limit_denominator(100))
    k = gate.LAB["folds"]
    folds = [round(sum(vals[i::k]) / max(1, len(vals[i::k])), 1) for i in range(k)]

    # 7. challenger: different opponents, fresh seeds
    ch_seeds = registry.fresh_seeds(db, cfg["challenger_tables"])
    bid, jobs = _paired_jobs(db, "challenger", ch_seeds, cfg["challenger_hands"], [base, best["spec"]], (), CHALLENGER_MIX, cfg,
                             record_first=False, note="cycle %d trial %d" % (cycle, trial_id))
    res = _run(db, jobs, cfg, "challenger")
    store.finish_batch(db, bid)
    cd, ch_hands, ch_errs = _diffs(res, champ["id"], best["id"])
    ch_mean = sum(_bb100(v, ch_hands) for v in cd.values()) / max(1, len(cd))

    evidence = {"holdout_seeds": hold, "tables": len(vals), "mean_bb100": round(mean, 2),
                "ci_low_bb100": round(_bb100(float(lo), hands), 2), "ci_high_bb100": round(_bb100(float(hi), hands), 2),
                "alpha_adjusted": float(alpha), "trials_counted": looks, "mde_bb100": round(mde, 2),
                "detectable": mean >= mde, "folds": folds, "challenger_bb100": round(ch_mean, 2),
                "candidate_errors": errs + ch_errs}
    context = {"holdout_fresh": fresh, "trials_used": len(cands)}
    decision = gate.decide(best["params"], champ["params"], prereg, evidence, context)
    db.execute("INSERT INTO trials(cycle, parent_id, candidate_id, changed, stage, n, mean_bb100, ci_low, ci_high, status, detail, created) "
               "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
               (cycle, champ["id"], best["id"], best["changed"], "holdout", len(vals), evidence["mean_bb100"],
                evidence["ci_low_bb100"], evidence["ci_high_bb100"], "approved" if decision["approved"] else "rejected",
                json.dumps({"evidence": {k2: v for k2, v in evidence.items() if k2 != "holdout_seeds"}, "gate": decision}),
                time.time()))
    db.commit()
    log("  holdout: %+.1f bb/100, CI [%+.1f, %+.1f] at alpha %.4f, MDE %.1f, folds %s, challenger %+.1f" % (
        mean, evidence["ci_low_bb100"], evidence["ci_high_bb100"], float(alpha), mde, folds, ch_mean))
    if decision["approved"]:
        new = store.load_strategy(db, best["id"])
        registry.promote(db, cycle, champ, new, decision)
        log("  PROMOTED %s -> %s (%s)" % (champ["id"], new["id"], best["hypothesis"]))
        return {"cycle": cycle, "promoted": True, "champion": new["id"], "evidence": evidence}
    log("  gate refused: " + ", ".join(decision["reasons"]))
    db.execute("UPDATE strategies SET status='rejected' WHERE id=? AND status='candidate'", (best["id"],))
    db.commit()
    return {"cycle": cycle, "promoted": False, "reason": decision["reasons"]}


def research_loop(db, cycles=None, hours=None, cfg=None, log=print):
    start = time.time()
    first = (db.execute("SELECT MAX(cycle) FROM trials").fetchone()[0] or 0) + 1
    out = []
    c = first
    while True:
        if cycles is not None and c - first >= cycles:
            break
        if hours is not None and time.time() - start > hours * 3600:
            break
        out.append(run_cycle(db, c, cfg, log))
        c += 1
    return out
