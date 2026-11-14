"""Proposals: each candidate is the champion with exactly ONE parameter moved.

Order of the proposal budget:
  1. what the diagnosis points at (rsi/diagnose.py leak rules), then
  2. a UCB1 bandit over (parameter, direction) arms, scored on every past
     selection-stage result: knobs that keep paying are tried again (with a
     bigger step), knobs that never help fade out. This is the part of the
     loop that learns *how to improve itself*.
"""
import json
import math

from pokerbot.strategy import PARAM_SPACE


def move(params, name, direction, steps=1):
    lo, hi, step = PARAM_SPACE[name]
    v = params[name] + direction * step * steps
    v = round(max(lo, min(hi, v)), 4)
    if abs(v - params[name]) < 1e-9:
        return None
    out = dict(params)
    out[name] = v
    return out


def arm_history(db):
    """(param, direction) -> list of selection-stage mean diffs (bb/100)."""
    hist = {}
    for r in db.execute("SELECT changed, detail, mean_bb100 FROM trials WHERE stage='selection'"):
        try:
            d = json.loads(r["detail"] or "{}")
        except ValueError:
            continue
        key = (r["changed"], d.get("direction"))
        if key[0] and key[1] in (-1, 1) and r["mean_bb100"] is not None:
            hist.setdefault(key, []).append(r["mean_bb100"])
    return hist


def propose(champ_params, priority, db, k=6, c=12.0):
    hist = arm_history(db)
    total = sum(len(v) for v in hist.values()) + 1
    arms = [(n, d) for n in PARAM_SPACE for d in (1, -1)]

    def ucb(arm):
        h = hist.get(arm)
        if not h:
            return float("inf")
        return sum(h) / len(h) + c * math.sqrt(math.log(total) / len(h))

    # a diagnosed arm keeps its priority only until the evidence says it does not pay
    def still_promising(arm):
        h = hist.get(arm)
        return not h or len(h) < 2 or sum(h) / len(h) > 0
    ordered = [a for a in priority if still_promising(a)][: max(1, k // 2)]
    for arm in sorted(arms, key=lambda a: (-ucb(a), a)):
        if arm not in ordered:
            ordered.append(arm)
    out = []
    for name, d in ordered:
        h = hist.get((name, d))
        steps = 2 if h and sum(h) / len(h) > 5 else 1
        cand = move(champ_params, name, d, steps)
        if cand is None:
            continue
        out.append({"params": cand, "changed": name, "direction": d, "steps": steps,
                    "hypothesis": "%s %s by %d step(s) (%s)" % (name, "up" if d > 0 else "down", steps,
                                                                "diagnosis" if (name, d) in priority else "bandit")})
        if len(out) >= k:
            break
    return out
