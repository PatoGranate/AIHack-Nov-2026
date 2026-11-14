"""How each real bot evolves from round to round, and where it is heading.

Teams re-upload all day (some are on version 11), so an all-time average
describes a bot that no longer exists. For every bot and every round we
measure its style (VPIP, PFR, steal, 3-bet, c-bet, aggression, fold to
steal / 3-bet / c-bet, river bluffs) and then, per metric:

  trend      least-squares slope per round
  stability  standard deviation across rounds (after removing sampling noise)
  verdict    "changing" when the drift over the observed rounds is large,
             otherwise "stable"
  shift      rounds where the style jumps (likely a new upload)
  forecast   next round's value: recency-weighted level + damped trend

The forecast profiles are what the lab's frequency clones play, so tuning
targets where opponents are going, not where they were.

    python -m rsi.evolution                    every bot with >= 3 rounds
    python -m rsi.evolution "Attention Is All In" Gherkers
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

METRICS = ["vpip", "pfr", "steal", "threebet", "cbet", "agg", "fold_to_steal", "fold_to_3bet", "fold_to_cbet"]
CHANGE_LIMIT = {"vpip": 0.04, "pfr": 0.04, "steal": 0.08, "threebet": 0.03, "cbet": 0.10, "agg": 0.06,
                "fold_to_steal": 0.08, "fold_to_3bet": 0.12, "fold_to_cbet": 0.10}


def round_no(ref):
    """Counted Saturday round number of a round ref, or None (practice rounds have no public versions)."""
    m = re.search(r"saturday/r(\d+)$", str(ref))
    return int(m.group(1)) if m else None


def _public_versions():
    """({name: {round: version}}, {name: current version}) from the standings snapshots (rsi/standings.py)."""
    try:
        from storage import db as store
        from rsi.standings import version_by_round
        d = store.connect()
        cur = {n: v for n, v in d.execute("SELECT name, version FROM standings s WHERE id = "
                                          "(SELECT MAX(id) FROM standings WHERE name = s.name)")}
        return version_by_round(d), cur
    except Exception:
        return {}, {}


def round_key(ref):
    m = re.search(r"r(\d+)$", str(ref))
    return (0 if "practice" in str(ref) else 1, int(m.group(1)) if m else 0, str(ref))


def series(hands_dir=None, min_hands=300):
    """{bot: [(ref, profile, hands, bb100), ...] in round order}."""
    from rsi.field import HANDS_DIR
    from tools.real_report import collect, profile
    st = collect(hands_dir or HANDS_DIR, by_round=True)
    out = {}
    for (name, ref), c in st.items():
        if c["hands"] >= min_hands:
            out.setdefault(name, []).append((ref, profile(c), c["hands"], c["chips"] / 20.0 / c["hands"] * 100))
    for v in out.values():
        v.sort(key=lambda x: round_key(x[0]))
    return out


def _slope(ys):
    n = len(ys)
    if n < 2:
        return 0.0
    xm, ym = (n - 1) / 2.0, sum(ys) / n
    den = sum((i - xm) ** 2 for i in range(n))
    return sum((i - xm) * (y - ym) for i, y in enumerate(ys)) / den if den else 0.0


def analyse(rounds, versions=None, current=None):
    """Per-metric trend, stability, verdict, shifts and forecast for one bot's rounds.

    versions: {round_number: version} from the public standings. When known, the
    forecast uses only the rounds played by the bot's latest version (a confirmed
    upload resets what we know), and the result says if a newer version is not
    seen at our tables yet."""
    vers = [(versions or {}).get(round_no(r[0])) for r in rounds]
    seg = len(rounds)
    if vers and vers[-1] is not None:
        seg = 0
        for v in reversed(vers):
            if v != vers[-1]:
                break
            seg += 1
    out = {"_versions": vers, "_segment": seg,
           "_changes": [(rounds[i][0], vers[i - 1], vers[i]) for i in range(1, len(vers))
                        if vers[i] is not None and vers[i - 1] is not None and vers[i] != vers[i - 1]],
           "_unseen": bool(current is not None and vers and vers[-1] is not None and current != vers[-1])}
    for m in METRICS:
        ys = [p[m] for _, p, _, _ in rounds]
        n = len(ys)
        mean = sum(ys) / n
        sd = (sum((y - mean) ** 2 for y in ys) / (n - 1)) ** 0.5 if n > 1 else 0.0
        slope = _slope(ys)
        drift = abs(slope) * max(1, n - 1)
        shifts = [rounds[i][0] for i in range(1, n) if abs(ys[i] - ys[i - 1]) > 1.5 * CHANGE_LIMIT[m]]
        cur = ys[-seg:] if seg else ys                  # only the latest confirmed version's rounds
        w = [0.6 ** (len(cur) - 1 - i) for i in range(len(cur))]
        level = sum(wi * y for wi, y in zip(w, cur)) / sum(w)
        trend = _slope(cur) if len(cur) >= 3 else (slope if seg == n else 0.0)
        forecast = min(1.0, max(0.0, level + 0.5 * trend))
        out[m] = {"first": ys[0], "last": ys[-1], "slope": slope, "sd": sd, "forecast": forecast, "shifts": shifts,
                  "verdict": "changing" if drift > CHANGE_LIMIT[m] or sd > CHANGE_LIMIT[m] else "stable"}
    return out


def forecasts(min_rounds=2, hands_dir=None):
    """{bot: forecast profile} for every bot seen in >= min_rounds rounds."""
    out = {}
    vby, cur = _public_versions()
    for name, rounds in series(hands_dir).items():
        if len(rounds) >= min_rounds:
            a = analyse(rounds, vby.get(name), cur.get(name))
            prof = dict(rounds[-1][1])
            prof.update({m: a[m]["forecast"] for m in METRICS})
            out[name] = prof
    return out


def report(names=None, min_rounds=3):
    ser = series()
    vby, curv = _public_versions()
    names = names or [n for n, r in sorted(ser.items(), key=lambda kv: -len(kv[1])) if len(r) >= min_rounds]
    for name in names:
        rounds = ser.get(name)
        if not rounds:
            continue
        a = analyse(rounds, vby.get(name), curv.get(name))
        changing = [m for m in METRICS if a[m]["verdict"] == "changing"]
        print("\n%s  (%d rounds; bb/100 by round: %s)" % (name, len(rounds), " ".join("%+.0f" % r[3] for r in rounds)))
        vtxt = " ".join("v%s" % v if v is not None else "?" for v in a["_versions"])
        print("   versions by round: %s | now v%s%s | forecast uses the last %d round(s)%s" % (
            vtxt, curv.get(name, "?"), " (NEW, not seen at our tables yet)" if a["_unseen"] else "", a["_segment"],
            ("; confirmed uploads at " + ", ".join("%s (v%s->v%s)" % c for c in a["_changes"])) if a["_changes"] else ""))
        print("   %-14s %6s %6s %8s %6s %8s  %s" % ("metric", "first", "last", "slope/rd", "sd", "next", "verdict"))
        for m in METRICS:
            x = a[m]
            print("   %-14s %6.2f %6.2f %+8.3f %6.3f %8.2f  %s%s" % (m, x["first"], x["last"], x["slope"], x["sd"], x["forecast"],
                                                               x["verdict"], (" (jumps at " + ", ".join(x["shifts"]) + ")") if x["shifts"] else ""))
        print("   -> conserving: %s | changing: %s" % (", ".join(m for m in METRICS if m not in changing) or "-",
                                                     ", ".join(changing) or "-"))


if __name__ == "__main__":
    report(sys.argv[1:] or None)
