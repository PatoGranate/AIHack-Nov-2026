"""FORGE context model, step 1: extract every post-flop response-to-a-bet event from real rounds.

One row per (table, hand, responder) decision where the responder faced a post-flop bet or raise
(to_call > 0) and folded, called or raised. Context is reconstructed from the public action log
only (what the bot sees in on_hand_end), using the engine's semantics:
  raise amount = raise-to total for the street; call amount = chips added.

Usage:
  python extract_events.py --root <dir containing PokerBot/> --manifest <input_manifest.csv> --out events.csv
Rows with manifest status != "used" (duplicates) are skipped.
"""
import argparse
import csv
import json
import os

STREET_OF_BOARD = {3: "flop", 4: "turn", 5: "river"}


def table_events(path):
    d = json.load(open(path, encoding="utf-8"))
    names = d["players"]
    ref = d.get("ref") or d["round"]["ref"]
    rnd = int(ref.split("/r")[-1])
    n = len(names)
    rows = []
    for hi, h in enumerate(sorted(d["hands"], key=lambda x: x["n"])):
        button = h["button"]
        stacks = list(h["start_stacks"])
        contrib = [0] * n
        bets = [0] * n
        folded = [False] * n
        street = "preflop"
        cur = 0
        naggr = 0
        aggr_seat = None
        aggr_add_ratio = 0.0
        for ev in h["events"]:
            t = ev[0]
            if t == "post":
                s, a = ev[1], ev[2]
                contrib[s] += a
                bets[s] += a
                stacks[s] -= a
                cur = max(cur, bets[s])
            elif t == "board":
                street = STREET_OF_BOARD.get(len(ev[2]), ev[1])
                bets = [0] * n
                cur = 0
                naggr = 0
                aggr_seat = None
            elif t == "act":
                s, a, amt = ev[1], ev[2], ev[3]
                to_call = cur - bets[s]
                if street != "preflop" and to_call > 0 and a in ("fold", "call", "raise"):
                    live_others = sum(1 for j in range(n) if not folded[j] and j != s)
                    order = lambda x: (x - button - 1) % n
                    rows.append({
                        "round": rnd, "table": ref + "|" + "/".join(names), "hand": hi,
                        "seat": s, "name": names[s], "street": street,
                        "kind": "bet" if naggr == 1 else "raise",
                        "size": round(aggr_add_ratio, 4),
                        "mw": 1 if live_others >= 2 else 0,
                        "ip": 1 if order(s) > order(aggr_seat) else 0,
                        "bettor": names[aggr_seat],
                        "allin_call": 1 if to_call >= stacks[s] else 0,
                        "fold": 1 if a == "fold" else 0,
                    })
                if a == "raise":
                    pot_before = sum(contrib)
                    add = amt - bets[s]
                    aggr_add_ratio = add / float(max(1, pot_before))
                    contrib[s] += add
                    stacks[s] -= add
                    bets[s] = amt
                    cur = max(cur, amt)
                    naggr += 1
                    aggr_seat = s
                elif a == "call":
                    contrib[s] += amt
                    stacks[s] -= amt
                    bets[s] += amt
                elif a == "fold":
                    folded[s] = True
            elif t == "refund":
                s, a = ev[1], ev[2]
                contrib[s] -= a
                bets[s] -= a
                stacks[s] += a
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = []
    ntab = 0
    with open(args.manifest, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["status"] != "used":
                continue
            ntab += 1
            out.extend(table_events(os.path.join(args.root, r["path"])))
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print("tables", ntab, "events", len(out))


if __name__ == "__main__":
    main()
