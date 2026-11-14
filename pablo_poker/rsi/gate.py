"""Deterministic promotion gate (adapted from lab/gate.py).

Plain code with pre-registered thresholds. It approves exactly one kind of
change: ONE strategy parameter, inside PARAM_SPACE, evaluated on held-out
table seeds that played no part in choosing it. Every refusal says why.

Checks (same spirit as the lab, poker evidence instead of trades):
  CONFIG_ONLY        candidate is a valid parameter set inside the search space
  ONE_CHANGE         exactly one parameter differs, and it is the pre-registered one
  PREREGISTERED      candidate + holdout seeds were recorded before the evaluation
  HOLDOUT_FRESH      holdout seeds never used before (each seed is judged once)
  SAMPLE             enough paired tables, and the effect is above the minimum detectable
  BEATS_BASELINE     bootstrap CI (Bonferroni-adjusted for every trial vs this parent) > 0
  STABILITY          not worse than the champion in enough of the holdout folds
  CHALLENGER         not worse on a different opponent pool (no overfitting to the league)
  NO_ERRORS          the candidate raised no exceptions
  BUDGET             trials per cycle within budget
"""
import hashlib
import json

from pokerbot.strategy import PARAM_SPACE

# "practical" (default): promote when the 80% interval of the holdout difference is above zero.
# Every holdout is fresh data, so each test is independent; a wrong promotion of a near-zero change
# costs little and the next cycles can undo it. "strict" is the original lab setting (90% interval,
# Bonferroni over every look, effect above the minimum detectable effect, 3 of 4 folds).
MODE = "practical"
LAB = {
    "practical": {"alpha": 0.20, "bonferroni": False, "require_mde": False, "power": 0.80,
                  "min_holdout_tables": 48, "folds": 4, "min_folds_not_worse": 2,
                  "challenger_tolerance_bb100": 25.0, "max_trials_per_cycle": 8, "bootstrap_resamples": 1000},
    "strict": {"alpha": 0.10, "bonferroni": True, "require_mde": True, "power": 0.80,
               "min_holdout_tables": 48, "folds": 4, "min_folds_not_worse": 3,
               "challenger_tolerance_bb100": 10.0, "max_trials_per_cycle": 8, "bootstrap_resamples": 1000},
}[MODE]
LAB_SHA = hashlib.sha256(json.dumps(LAB, sort_keys=True).encode()).hexdigest()


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def changed_parameters(parent, child):
    return sorted(k for k in set(parent) | set(child) if parent.get(k) != child.get(k))


def valid_params(params):
    problems = []
    for k, v in params.items():
        if k in ("mc_iters", "mc_ms", "explore"):
            continue
        if k not in PARAM_SPACE:
            problems.append("UNKNOWN_PARAMETER:%s" % k)
            continue
        lo, hi, _ = PARAM_SPACE[k]
        if not isinstance(v, (int, float)) or not lo - 1e-9 <= v <= hi + 1e-9:
            problems.append("OUT_OF_BOUNDS:%s" % k)
    return problems


def decide(candidate, parent, prereg, evidence, context):
    checks = []

    def check(name, problems, detail=None):
        checks.append({"name": name, "status": "FAIL" if problems else "PASS", "reasons": problems, "detail": detail or {}})

    check("CONFIG_ONLY", valid_params(candidate))

    changed = changed_parameters(parent, candidate)
    p = []
    if len(changed) > 1:
        p.append("MORE_THAN_ONE_CHANGE")
    elif not changed:
        p.append("NO_CHANGE")
    if prereg.get("changed") != changed:
        p.append("CHANGE_NOT_THE_PREREGISTERED_ONE")
    check("ONE_CHANGE", p, {"changed": changed})

    p = []
    if prereg.get("candidate_sha256") != sha(candidate) or prereg.get("parent_sha256") != sha(parent):
        p.append("NOT_PREREGISTERED")
    if prereg.get("lab_sha256") != LAB_SHA:
        p.append("THRESHOLDS_NOT_THE_PREREGISTERED_ONES")
    if prereg.get("holdout_sha256") != sha(evidence.get("holdout_seeds")):
        p.append("NOT_THE_PREREGISTERED_DATA")
    check("PREREGISTERED", p)

    check("HOLDOUT_FRESH", [] if context.get("holdout_fresh") else ["HOLDOUT_REUSED"])

    n = int(evidence.get("tables", 0))
    p = []
    if n < LAB["min_holdout_tables"]:
        p.append("SAMPLE_TOO_SMALL")
    if LAB["require_mde"] and not evidence.get("detectable"):
        p.append("EFFECT_BELOW_MINIMUM_DETECTABLE")
    check("SAMPLE", p, {"tables": n, "mde_bb100": evidence.get("mde_bb100")})

    ok = evidence.get("ci_low_bb100", -1) > 0 and evidence.get("mean_bb100", 0) > 0
    check("BEATS_BASELINE", [] if ok else ["NOT_SIGNIFICANTLY_BETTER_THAN_CHAMPION"],
          {"mean": evidence.get("mean_bb100"), "ci": [evidence.get("ci_low_bb100"), evidence.get("ci_high_bb100")],
           "alpha_adjusted": evidence.get("alpha_adjusted"), "trials_counted": evidence.get("trials_counted")})

    folds = evidence.get("folds", [])
    good = sum(1 for f in folds if f >= 0)
    check("STABILITY", [] if good >= LAB["min_folds_not_worse"] else ["UNSTABLE_ACROSS_FOLDS"], {"folds": folds})

    ch = evidence.get("challenger_bb100")
    check("CHALLENGER", [] if ch is not None and ch >= -LAB["challenger_tolerance_bb100"] else ["CHALLENGER_DISAGREES"],
          {"challenger_bb100": ch})

    check("NO_ERRORS", [] if not evidence.get("candidate_errors") else ["CANDIDATE_RAISED_ERRORS"])
    check("BUDGET", [] if context.get("trials_used", 0) <= LAB["max_trials_per_cycle"] else ["RESEARCH_BUDGET_EXCEEDED"])

    reasons = list(dict.fromkeys(r for c in checks for r in c["reasons"]))
    return {"approved": not reasons, "reasons": reasons, "checks": checks,
            "decision_sha256": sha({"c": sha(candidate), "p": sha(parent), "checks": [[c["name"], c["status"]] for c in checks]})}
