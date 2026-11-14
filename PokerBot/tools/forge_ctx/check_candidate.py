"""FORGE check: the candidate's in-bot counters (_learn_ctx) must equal the offline extractor + field model.

Replays real tables through Agent.on_hand_end with the public history the engine would send, then
compares per-seat (folds, responses, expected folds) against extract_events.py + field_coef.json.
Usage: python check_candidate.py --root <dir containing PokerBot/> --tables <path.json> [...]
"""
import argparse
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import extract_events  # noqa: E402


def load_cand():
    p = os.path.join(HERE, "..", "cands", "forge_ctx_v1.py")
    spec = importlib.util.spec_from_file_location("forge_ctx_v1", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def summaries(path):
    d = json.load(open(path, encoding="utf-8"))
    names = {"flop", "turn", "river"}
    for h in sorted(d["hands"], key=lambda x: x["n"]):
        hist = []
        street = "preflop"
        posted = 0
        for ev in h["events"]:
            if ev[0] == "post":
                hist.append({"seat": ev[1], "street": "preflop",
                             "action": "small_blind" if posted == 0 else "big_blind", "amount": ev[2]})
                posted += 1
            elif ev[0] == "board":
                street = {3: "flop", 4: "turn", 5: "river"}[len(ev[2])]
                assert street in names
            elif ev[0] == "act":
                hist.append({"seat": ev[1], "street": street, "action": ev[2], "amount": ev[3]})
        yield {"history": hist, "shown": {}, "board": h.get("board", [])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", nargs="+", required=True)
    args = ap.parse_args()
    coef = json.load(open(os.path.join(HERE, "field_coef.json")))
    cw = dict(zip(coef["columns"], coef["coef"]))
    cand = load_cand()
    worst = 0.0
    for path in args.tables:
        ag = cand.Agent()
        npl = len(json.load(open(path, encoding="utf-8"))["players"])
        ag.on_table_start({"seat": 0, "num_players": npl, "hands": 1000, "starting_stack": 2000})
        for s in summaries(path):
            ag.on_hand_end(s)
        exp = {}
        for r in extract_events.table_events(path):
            sb = sum(1 for e in coef["size_edges"] if r["size"] >= e)
            x = cw["const"] + (cw["sz%d" % sb] if sb else 0.0) + cw["raise"] * (r["kind"] == "raise") \
                + cw["mw"] * r["mw"] + cw["turn"] * (r["street"] == "turn") + cw["river"] * (r["street"] == "river") \
                + cw["ip"] * r["ip"] + cw["allin"] * r["allin_call"] + cw["mw_ip"] * r["mw"] * r["ip"]
            a = exp.setdefault(r["seat"], [0, 0, 0.0])
            a[0] += r["fold"]; a[1] += 1; a[2] += 1 / (1 + math.exp(-x))
        for seat, (f, n, e) in sorted(exp.items()):
            o = ag.S(seat)
            ok = o.xf == f and o.xn == n and abs(o.xe - e) < 0.05
            worst = max(worst, abs(o.xe - e))
            print("%s seat %d  bot (%d, %d, %.2f)  offline (%d, %d, %.2f)  %s" % (
                os.path.basename(path), seat, o.xf, o.xn, o.xe, f, n, e, "OK" if ok else "MISMATCH"))
    print("max |xe diff| =", round(worst, 4))


if __name__ == "__main__":
    main()
