"""Replay our REAL rounds through an engine variant and judge its big decisions against the cards
the opponents actually held. No simulator involved: this is the test a soft simulator cannot fake.

    python tools/replay_decisions.py                                   # live engine + live params
    python tools/replay_decisions.py --params '{"size_read": 1.0}'      # a variant
    python tools/replay_decisions.py --engine candidate/engine.py --rounds 45-53

The variant sits in our seat, sees every hand exactly as we did (same history, same learning
between hands) and is asked what it would do at each of our real decision points. Then:

  big calls we made      luck-free value of each (equity vs the real cards x final pot - call);
                         a variant that folds the losing ones and keeps the winning ones is better
  big bets we made       value of each vs checking; shows what a variant gives up or saves
  new commitments        spots where the variant puts in 300+ chips and we did not (unknown value)

Only our last chip action of a hand is judged (after it nothing else of ours changes the result).
"""
import argparse
import glob
import importlib.util
import itertools
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BIG = 300


def load_engine(path):
    spec = importlib.util.spec_from_file_location("replay_engine_%d" % abs(hash(path)), os.path.join(ROOT, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def equity(ev, hero, opps, bd, rng):
    dead = set(hero + bd + [c for o in opps for c in o])
    deck = [c for c in range(52) if c not in dead]
    need = 5 - len(bd)
    if need == 0:
        runs = [()]
    elif need <= 2:
        runs = list(itertools.combinations(deck, need))
    else:
        runs = [rng.sample(deck, need) for _ in range(1200)]
    tot = 0.0
    for r in runs:
        b = bd + list(r)
        hv = ev(b + hero)
        ov = [ev(b + o) for o in opps]
        m = max(ov)
        if hv > m:
            tot += 1
        elif hv == m:
            tot += 1.0 / (1 + ov.count(m))
    return tot / len(runs)


def replay(path, mod, params, model=None, sims=1200):
    d = json.load(open(path, encoding="utf-8"))
    me, n = d["seat"], len(d["players"])
    if model is not None:
        mod.MODEL.clear()
        mod.MODEL.update(model)
        if hasattr(mod, "_MODEL_SRC"):
            mod._MODEL_SRC[0] = None
    p = dict(params or {})
    p.update({"max_sims": sims, "max_ms": 500.0, "hard_ms": 2000.0, "bank_s": 1e9})
    a = mod.Agent(params=p, seed=12345)
    a.on_table_start({"seat": me, "num_players": n, "hands": len(d["hands"]), "starting_stack": 2000})
    rng = random.Random(5)
    rows = []
    for h in d["hands"]:
        start = h.get("start_stacks") or [2000] * n
        stacks = list(start)
        bets = [0] * n
        contrib = [0] * n
        folded = [False] * n
        hist, board, street, posts = [], [], "preflop", 0
        bb = h.get("bb", 20)
        min_inc = bb
        hole = h["hole"].get(str(me))
        mine = []                       # our decisions this hand
        for e in h["events"]:
            if e[0] == "post":
                s, amt = e[1], e[2]
                stacks[s] -= amt
                bets[s] += amt
                contrib[s] += amt
                hist.append({"seat": s, "street": "preflop", "action": "small_blind" if posts == 0 else "big_blind",
                             "amount": amt})
                posts += 1
            elif e[0] == "board":
                street, board = e[1], list(e[2])
                bets = [0] * n
                min_inc = bb
            elif e[0] == "act":
                _, s, act, amt = e
                cur = max(bets)
                if s == me and hole:
                    tc = min(cur - bets[s], stacks[s])
                    max_to = bets[s] + stacks[s]
                    others = any(j != s and not folded[j] and stacks[j] > 0 for j in range(n))
                    can_raise = max_to > cur and others
                    state = {"hand_number": h["n"], "street": street, "seat": me, "button": h["button"],
                             "hole_cards": list(hole), "board": list(board), "small_blind": h.get("sb", 10),
                             "big_blind": bb, "pot": sum(contrib), "stacks": list(stacks), "bets": list(bets),
                             "folded": list(folded), "to_call": tc,
                             "min_raise_to": min(cur + min_inc, max_to) if can_raise else None,
                             "max_raise_to": max_to if can_raise else None,
                             "legal_actions": (["fold", "call"] if tc > 0 else ["check"]) + (["raise"] if can_raise else []),
                             "betting": "no_limit", "history": list(hist)}
                    out = a.act(state) or {}
                    va = out.get("action")
                    vadd = 0
                    if va == "raise":
                        vadd = int(out.get("amount", 0)) - bets[s]
                    elif va == "call":
                        vadd = tc
                    add = (amt - bets[s]) if act == "raise" else (amt if act == "call" else 0)
                    mine.append({"street": street, "act": act, "add": add, "pot": sum(contrib), "tc": tc,
                                 "board": list(board), "vact": va, "vadd": vadd, "inv": contrib[s],
                                 "e": getattr(a, "last_e", None)})
                add = 0
                if act == "raise":
                    add = amt - bets[s]
                    if amt - cur >= min_inc:
                        min_inc = amt - cur
                    bets[s] = amt
                elif act == "call":
                    add = amt
                    bets[s] += amt
                elif act == "fold":
                    folded[s] = True
                stacks[s] -= add
                contrib[s] += add
                hist.append({"seat": s, "street": street, "action": act, "amount": amt})
        sd = h.get("showdown") or {}
        shown = {k: v for k, v in h.get("hole", {}).items() if k in sd}
        a._learn({"history": hist, "board": h.get("board") or [], "shown": shown})
        if not mine:
            continue
        res = h["results"][me]
        potfinal = sum(e[2] for e in h["events"] if e[0] == "win")
        opps = [[mod.to_int(c) for c in v] for k, v in shown.items() if k != str(me)]
        hi = [mod.to_int(c) for c in hole]
        last_chip = max((i for i, m in enumerate(mine) if m["add"] > 0), default=None)
        for i, m in enumerate(mine):
            m.update({"n": h["n"], "hole": hole, "res": res, "last": i == last_chip, "eq": None, "ev": None,
                      "lvl": mod.level_street(hi[0], hi[1], [mod.to_int(c) for c in m["board"]]) if m["board"] else -1})
            if i == last_chip and opps and str(me) in sd:
                bd = [mod.to_int(c) for c in m["board"]]
                m["eq"] = equity(mod.evaluate, hi, opps, bd, rng)
                # value of the action from that point: what we get back minus what we add
                m["ev"] = m["eq"] * potfinal - m["add"]
                m["ev_passive"] = m["eq"] * (potfinal - 2 * m["add"]) if m["act"] == "raise" else 0.0
            elif i == last_chip:
                m["ev"] = res + m["inv"]                        # everyone folded to it: we took the pot
                m["ev_passive"] = None
            rows.append(m)
    return d, rows


def summarise(all_rows, hands, label):
    out = {"label": label, "hands": hands}
    same = sum(1 for m in all_rows if m["act"] == m["vact"] or (m["act"] == "check" and m["vact"] in (None, "check")))
    out["agree"] = same / float(max(1, len(all_rows)))
    post = [m for m in all_rows if m["street"] != "preflop"]
    for st in ("flop", "turn", "river"):
        x = [m for m in post if m["street"] == st and m["tc"] == 0]
        out["bet_%s" % st] = (sum(m["act"] == "raise" for m in x) / float(max(1, len(x))),
                              sum(m["vact"] == "raise" for m in x) / float(max(1, len(x))))
    calls = [m for m in all_rows if m["last"] and m["act"] == "call" and m["add"] >= BIG and m["eq"] is not None]
    kept = [m for m in calls if m["vact"] in ("call", "raise")]
    dropped = [m for m in calls if m["vact"] == "fold"]
    out["calls"] = (len(calls), sum(m["ev"] for m in calls), len(dropped), sum(m["ev"] for m in dropped),
                    sum(m["eq"] for m in dropped) / max(1, len(dropped)), sum(m["eq"] for m in kept) / max(1, len(kept)))
    bets = [m for m in all_rows if m["last"] and m["act"] == "raise" and m["add"] >= BIG and m["street"] != "preflop"]
    called = [m for m in bets if m["eq"] is not None]
    won = [m for m in bets if m["eq"] is None]
    dc = [m for m in called if m["vact"] != "raise"]
    dw = [m for m in won if m["vact"] != "raise"]
    # called bets the variant would not make: gain = passive value - actual value
    gain_c = sum((m["ev_passive"] if m["tc"] == 0 else (m["eq"] * (m["pot"] + m["tc"]) - m["tc"] if m["vact"] == "call" else 0.0))
                 - m["ev"] for m in dc)
    # fold-winning bets the variant would not make: loses the share of the pot it would not win at showdown
    loss_w = sum(m["pot"] * (1.0 - (m["e"] if m["e"] is not None else 0.5)) for m in dw)
    out["bets"] = (len(bets), len(called), sum(m["eq"] for m in called) / max(1, len(called)), len(dc), gain_c,
                   sum(m["eq"] for m in dc) / max(1, len(dc)), len(dw), loss_w)
    new = [m for m in all_rows if m["vadd"] >= BIG and m["add"] < BIG]
    out["new_big"] = (len(new), sum(m["vact"] == "call" for m in new), sum(m["vact"] == "raise" for m in new))
    pf = [m for m in all_rows if m["street"] == "preflop"]
    out["pf_raise"] = (sum(m["act"] == "raise" for m in pf) / float(max(1, len(pf))),
                       sum(m["vact"] == "raise" for m in pf) / float(max(1, len(pf))))
    return out


def show(o):
    k = 100.0 / 20.0 / max(1, o["hands"])          # chips -> bb/100
    print("\n== %s  (%d hands; agrees with what we actually did on %.0f%% of decisions)" % (o["label"], o["hands"], 100 * o["agree"]))
    print("   bets when checked to (actual -> variant): flop %.0f%% -> %.0f%%, turn %.0f%% -> %.0f%%, river %.0f%% -> %.0f%%;"
          "  preflop raises %.1f%% -> %.1f%%" % tuple(100 * x for x in o["bet_flop"] + o["bet_turn"] + o["bet_river"] + o["pf_raise"]))
    n, ev, nd, evd, eqd, eqk = o["calls"]
    print("   big calls we made: %d worth %+.1f bb/100 in total. Variant folds %d of them (equity %.2f, worth %+.1f bb/100) "
          "-> gain %+.1f bb/100; keeps equity %.2f" % (n, ev * k, nd, eqd, evd * k, -evd * k, eqk))
    nb, nc, eqc, ndc, gain, eqdc, ndw, loss = o["bets"]
    print("   big bets we made: %d (%d called, equity %.2f). Variant skips %d called ones (equity %.2f) -> gain %+.1f bb/100; "
          "skips %d that won the pot outright -> est. loss %.1f bb/100" % (nb, nc, eqc, ndc, eqdc, gain * k, ndw, loss * k))
    print("   net on judged spots: %+.1f bb/100;  new 300+ chip commitments the variant adds: %d (%d calls, %d bets/raises)"
          % ((-evd + gain - loss) * k, o["new_big"][0], o["new_big"][1], o["new_big"][2]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="pokerbot/v2.py")
    ap.add_argument("--params")
    ap.add_argument("--rounds", default="38-53")
    ap.add_argument("--model", default=os.path.join(ROOT, "data", "v3_model.json"))
    ap.add_argument("--sims", type=int, default=1200)
    ap.add_argument("--label")
    ap.add_argument("--save")
    a = ap.parse_args()
    lo, hi = [int(x) for x in a.rounds.split("-")]
    files = [f for f in sorted(glob.glob(os.path.join(ROOT, "hands", "saturday_r*.json"))) if lo <= int(f[-8:-5]) <= hi]
    mod = load_engine(a.engine)
    if a.params:
        params = json.loads(a.params)
    else:
        params = json.load(open(os.path.join(ROOT, "data", "v2_params.json")))
    if a.params and a.params.startswith("+"):
        pass
    model = json.load(open(a.model)) if a.model and os.path.exists(a.model) else None
    t0 = time.time()
    rows, hands = [], 0
    for f in files:
        d, r = replay(f, mod, params, model, a.sims)
        rows += r
        hands += len(d["hands"])
    o = summarise(rows, hands, a.label or ("%s %s" % (a.engine, json.dumps(params, sort_keys=True))))
    show(o)
    print("   (%.0f s)" % (time.time() - t0))
    if a.save:
        json.dump(rows, open(a.save, "w"))
