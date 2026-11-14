"""Observe and diagnose (adapted from lab/diagnose.py): read the hand database,
never write it, and say where a strategy wins and loses chips.

  - headline: hands, bb/100 with a 95% interval, VPIP, PFR, WTSD, W$SD
  - by position, by the street the hand ended on, by preflop action
  - leaks: rules that map a symptom to the parameters that could fix it

`prioritize` turns the leaks into an ORDER for the RSI proposal budget. Like
the lab's version it never approves anything: only the gate does.
"""
import math

BB = 20

# symptom -> parameters worth trying first (direction hint: +1 raise, -1 lower)
LEAK_RULES = [
    ("loses_when_folding_preflop_from_blinds", [("bb_defend", +1), ("open_sb", +1)]),
    ("loses_at_showdown", [("call_margin", +1), ("value_river", +1), ("commit_penalty", +1)]),
    ("wins_little_without_showdown", [("bluff_freq", +1), ("cbet_freq", +1), ("bet_bluff", -1)]),
    ("too_tight_preflop", [("open_btn", +1), ("open_co", +1), ("call_open", +1), ("open_mp", +1)]),
    ("too_loose_preflop", [("open_ep", -1), ("open_mp", -1), ("call_open", -1)]),
    ("passive_postflop", [("value_flop", -1), ("value_turn", -1), ("raise_eq", -1)]),
    ("big_pot_losses", [("jam_call", -1), ("call_3bet", -1), ("raise_eq", +1)]),
]


def _interval(values):
    n = len(values)
    if n < 2:
        return 0.0, 0.0, 0.0
    mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    half = 1.96 * sd / math.sqrt(n)
    return mean, mean - half, mean + half


def _bb100(deltas):
    m, lo, hi = _interval(deltas)
    return round(m / BB * 100, 1), round(lo / BB * 100, 1), round(hi / BB * 100, 1)


def diagnose(db, strategy_id, batch_ids=None, limit=200000):
    q = "SELECT position, delta, vpip, pfr, saw_flop, showdown, won, end_street, actions FROM hands WHERE strategy_id=?"
    args = [strategy_id]
    if batch_ids:
        q += " AND batch_id IN (%s)" % ",".join("?" * len(batch_ids))
        args += list(batch_ids)
    q += " ORDER BY id DESC LIMIT ?"
    args.append(limit)
    rows = db.execute(q, args).fetchall()
    if not rows:
        return {"strategy_id": strategy_id, "hands": 0, "leaks": []}
    n = len(rows)
    deltas = [r["delta"] for r in rows]
    flop = [r for r in rows if r["saw_flop"]]
    sd = [r for r in rows if r["showdown"]]
    out = {
        "strategy_id": strategy_id, "hands": n,
        "bb100": _bb100(deltas),
        "vpip": round(sum(r["vpip"] for r in rows) / n, 3),
        "pfr": round(sum(r["pfr"] for r in rows) / n, 3),
        "wtsd": round(len(sd) / max(1, len(flop)), 3),
        "wsd": round(sum(r["won"] for r in sd) / max(1, len(sd)), 3),
    }
    groups = {}
    for key, fn in (("position", lambda r: r["position"]), ("end", lambda r: r["end_street"]),
                    ("preflop", lambda r: "raised" if r["pfr"] else "called" if r["vpip"] else "folded/checked")):
        g = {}
        for r in rows:
            g.setdefault(fn(r), []).append(r["delta"])
        groups[key] = {k: {"hands": len(v), "bb100": _bb100(v)[0], "chips": sum(v)} for k, v in sorted(g.items())}
    out["by"] = groups

    # ---- symptoms
    leaks = []
    pos = groups["position"]
    blinds = [pos[p] for p in ("SB", "BB") if p in pos]
    if blinds and sum(b["chips"] for b in blinds) / max(1, sum(b["hands"] for b in blinds)) < -0.9 * BB:
        leaks.append("loses_when_folding_preflop_from_blinds")
    if out["wsd"] < 0.5 and len(sd) > 50:
        leaks.append("loses_at_showdown")
    nosd = [r["delta"] for r in flop if not r["showdown"]]
    if nosd and sum(nosd) < 0:
        leaks.append("wins_little_without_showdown")
    if out["vpip"] < 0.17:
        leaks.append("too_tight_preflop")
    if out["vpip"] > 0.40:
        leaks.append("too_loose_preflop")
    aggr = sum(r["actions"].count("fR") + r["actions"].count("tR") + r["actions"].count("rR") for r in flop)
    calls = sum(r["actions"].count("fC") + r["actions"].count("tC") + r["actions"].count("rC") for r in flop)
    out["postflop_af"] = round(aggr / max(1, calls), 2)
    if out["postflop_af"] < 1.0:
        leaks.append("passive_postflop")
    big = [d for d in deltas if d <= -50 * BB]
    if len(big) / n > 0.03:
        leaks.append("big_pot_losses")
    out["leaks"] = leaks
    return out


def prioritize(report, params):
    """Order (param, direction) pairs: diagnosed leaks first, then everything else."""
    seen, order = set(), []
    for leak in report.get("leaks", []):
        for rule, hints in LEAK_RULES:
            if rule == leak:
                for name, d in hints:
                    if (name, d) not in seen and name in params:
                        seen.add((name, d))
                        order.append((name, d))
    return order


def format_report(rep):
    if not rep.get("hands"):
        return "no hands recorded for %s" % rep.get("strategy_id")
    lines = ["%s: %d hands, %+.1f bb/100 (95%% CI %+.1f..%+.1f)" % ((rep["strategy_id"], rep["hands"]) + tuple(rep["bb100"])),
             "VPIP %.1f%%  PFR %.1f%%  WTSD %.1f%%  W$SD %.1f%%  postflop AF %.2f" % (
                 rep["vpip"] * 100, rep["pfr"] * 100, rep["wtsd"] * 100, rep["wsd"] * 100, rep["postflop_af"])]
    for key, g in rep["by"].items():
        lines.append("  by %-8s " % key + "  ".join("%s %+.0f (%d)" % (k, v["bb100"], v["hands"]) for k, v in g.items()))
    lines.append("  leaks: " + (", ".join(rep["leaks"]) or "none"))
    return "\n".join(lines)
