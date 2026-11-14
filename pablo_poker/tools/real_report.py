"""Who wins on the real tables, and how: per-bot style and where the chips come from.

    python tools/real_report.py                 # every bot with >= 2,000 hands
    python tools/real_report.py --bots kaiserbot "Attention Is All In" Gherkers

Reads hands/ and hands/external/ (de-duplicated). Columns:
  VPIP / PFR / 3B      preflop: plays a hand / raises / re-raises when facing one raise
  STEAL                opens from CO/BTN/SB when folded to
  CBET                 bets the flop as preflop aggressor (when it gets the chance)
  AGG                  postflop bets+raises / all postflop actions
  WTSD / W$SD          goes to showdown after seeing a flop / wins when it does
  noSD / SD            bb/100 from hands that ended without / at showdown
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from rsi.field import HANDS_DIR, _files  # noqa: E402


def profile(c):
    """Frequency profile for sim/statbot.StatBot from one bot's collected counts."""
    r = lambda a, b, d: (c[a] / c[b]) if c[b] >= 30 else d      # noqa: E731
    H = max(1, c["hands"])
    return {"vpip": c["vpip"] / H, "pfr": c["pfr"] / H, "threebet": r("tb", "tb_opp", 0.04), "steal": r("st", "st_opp", 0.4),
            "cbet": r("cb", "cb_opp", 0.65), "agg": r("agg", "pacts", 0.3), "fold_to_steal": r("fst", "fst_opp", 0.7),
            "fold_to_3bet": r("f3", "f3_opp", 0.5), "fold_to_cbet": r("fcb", "fcb_opp", 0.55),
            "river_bluff": r("rb", "rb_sd", 0.05)}


def collect(hands_dir=HANDS_DIR, by_round=False):
    """Counts per bot (or per (bot, round ref) with by_round=True)."""
    stats, seen = {}, set()
    for f, _own in _files(hands_dir):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        players = d.get("players") or []
        rnd = d.get("round") or {}
        ref, table = d.get("ref") or rnd.get("ref") or f, rnd.get("table")
        n = len(players)
        for h in d.get("hands", []):
            key = (ref, table, h.get("n"))
            if key in seen:
                continue
            seen.add(key)
            button = h.get("button", 0)
            street, acts = "preflop", {"preflop": [], "flop": [], "turn": [], "river": []}
            for e in h.get("events", []):
                if e[0] == "board":
                    street = e[1]
                elif e[0] == "act":
                    acts[street].append((e[1], e[2]))
            pf = acts["preflop"]
            raises = [i for i, a in enumerate(pf) if a[1] == "raise"]
            first_vol = next((i for i, a in enumerate(pf) if a[1] in ("call", "raise")), None)
            aggressor = pf[raises[-1]][0] if raises else None
            sd = h.get("showdown") or {}
            res = h.get("results") or [0] * n
            flop_seen = {s for s, _ in acts["flop"]} | {s for s, _ in acts["turn"]} | {int(k) for k in sd}
            for s, name in enumerate(players):
                c = stats.setdefault((name, ref) if by_round else name, dict(hands=0, vpip=0, pfr=0, tb_opp=0, tb=0, st_opp=0, st=0, cb_opp=0, cb=0,
                                                agg=0, pacts=0, flops=0, sd=0, sdwin=0, nosd_chips=0, sd_chips=0, chips=0,
                                                fst_opp=0, fst=0, f3_opp=0, f3=0, fcb_opp=0, fcb=0, rb=0, rb_sd=0))
                c["hands"] += 1
                c["chips"] += res[s]
                mine = [a for (x, a) in pf if x == s]
                c["vpip"] += any(a in ("call", "raise") for a in mine)
                c["pfr"] += "raise" in mine
                # 3-bet opportunity: facing exactly one raise when it acts
                for i, (x, a) in enumerate(pf):
                    if x == s and a in ("fold", "call", "raise"):
                        before = sum(1 for (_, b) in pf[:i] if b == "raise")
                        if before == 1:
                            c["tb_opp"] += 1
                            c["tb"] += a == "raise"
                            break
                # steal opportunity: folded to it in CO/BTN/SB
                off = (s - button) % n
                if off in (0, 1, n - 1):
                    idx = next((i for i, (x, _) in enumerate(pf) if x == s), None)
                    if idx is not None and (first_vol is None or first_vol >= idx):
                        c["st_opp"] += 1
                        c["st"] += pf[idx][1] == "raise"
                # c-bet opportunity: preflop aggressor, first to have the chance to bet the flop
                if aggressor == s and acts["flop"]:
                    fl = acts["flop"]
                    idx = next((i for i, (x, _) in enumerate(fl) if x == s), None)
                    if idx is not None and not any(a == "raise" for (_, a) in fl[:idx]):
                        c["cb_opp"] += 1
                        c["cb"] += fl[idx][1] == "raise"
                # fold to a late-position steal (first raise from CO/BTN/SB with nobody in before it)
                if raises and first_vol == raises[0]:
                    opener = pf[raises[0]][0]
                    if (opener - button) % n in (0, 1, n - 1) and s != opener:
                        r = next((a for (x, a) in pf[raises[0] + 1:] if x == s), None)
                        if r in ("fold", "call", "raise"):
                            c["fst_opp"] += 1
                            c["fst"] += r == "fold"
                    if len(raises) > 1 and s == opener:
                        r = next((a for (x, a) in pf[raises[1] + 1:] if x == s), None)
                        if r in ("fold", "call", "raise"):
                            c["f3_opp"] += 1
                            c["f3"] += r == "fold"
                # fold to the preflop aggressor's flop bet
                if aggressor is not None and s != aggressor:
                    fl = acts["flop"]
                    fb = next((i for i, (x, a) in enumerate(fl) if a == "raise"), None)
                    if fb is not None and fl[fb][0] == aggressor:
                        r = next((a for (x, a) in fl[fb + 1:] if x == s), None)
                        if r in ("fold", "call", "raise"):
                            c["fcb_opp"] += 1
                            c["fcb"] += r == "fold"
                # river bets that reached showdown: bluff (high card) share
                if str(s) in sd and any(x == s and a == "raise" for (x, a) in acts["river"]):
                    shown = (h.get("hole") or {}).get(str(s))
                    if shown and len(h.get("board") or []) == 5:
                        from pokerbot.strategy import card_int, evaluate
                        c["rb_sd"] += 1
                        c["rb"] += (evaluate([card_int(x) for x in shown + h["board"]]) >> 20) == 0
                for st_ in ("flop", "turn", "river"):
                    for x, a in acts[st_]:
                        if x == s:
                            c["pacts"] += 1
                            c["agg"] += a == "raise"
                if s in flop_seen:
                    c["flops"] += 1
                if str(s) in sd:
                    c["sd"] += 1
                    c["sdwin"] += res[s] > 0
                    c["sd_chips"] += res[s]
                else:
                    c["nosd_chips"] += res[s]
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bots", nargs="*")
    ap.add_argument("--min-hands", type=int, default=2000)
    a = ap.parse_args()
    stats = collect()
    names = a.bots or [k for k, v in sorted(stats.items(), key=lambda kv: -kv[1]["chips"] / max(1, kv[1]["hands"]))
                       if v["hands"] >= a.min_hands]
    pct = lambda x, y: "%5.1f" % (100.0 * x / y) if y else "   - "      # noqa: E731
    print("%-24s %6s %8s %5s %5s %5s %5s %5s %5s %5s %5s %8s %8s" % (
        "bot", "hands", "bb/100", "VPIP", "PFR", "3B", "STEAL", "CBET", "AGG", "WTSD", "W$SD", "noSD", "SD"))
    for nm in names:
        c = stats.get(nm)
        if not c:
            continue
        H = c["hands"]
        print("%-24s %6d %+8.1f %s %s %s %s %s %s %s %s %+8.1f %+8.1f" % (
            nm[:24], H, c["chips"] / 20 / H * 100, pct(c["vpip"], H), pct(c["pfr"], H), pct(c["tb"], c["tb_opp"]),
            pct(c["st"], c["st_opp"]), pct(c["cb"], c["cb_opp"]), pct(c["agg"], c["pacts"]), pct(c["sd"], c["flops"]),
            pct(c["sdwin"], c["sd"]), c["nosd_chips"] / 20 / H * 100, c["sd_chips"] / 20 / H * 100))


if __name__ == "__main__":
    main()
