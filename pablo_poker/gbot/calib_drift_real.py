"""False-alarm rate of the G profiling change detector on REAL Saturday rounds.

    python gbot/calib_drift_real.py [z ...]

An opponent's code cannot change inside one 1,000-hand round, so every seat the detector
flags inside a real round is a false alarm. Replays public histories only (no hole cards).
"""
import glob
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load():
    spec = importlib.util.spec_from_file_location("gp_cal", os.path.join(HERE, "G_profile.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def summaries(d):
    for h in d["hands"]:
        hist, street = [], "preflop"
        for e in h["events"]:
            if e[0] == "post":
                hist.append({"seat": e[1], "action": "small_blind" if not hist else "big_blind", "amount": e[2], "street": "preflop"})
            elif e[0] == "board":
                street = e[1]
            elif e[0] == "act":
                hist.append({"seat": e[1], "action": e[2], "amount": e[3], "street": street})
        yield {"history": hist, "shown": h.get("showdown") or {}}


if __name__ == "__main__":
    m = load()
    files, seen = [], set()
    for pat in ("hands/saturday_r0*.json", "hands/external/WBot/saturday_r0*.json", "hands/external/Red/saturday_r0*.json"):
        files += sorted(glob.glob(os.path.join(ROOT, pat)))
    docs = []
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        k = (d["round"].get("slot"), tuple(d["players"]))
        if k not in seen and len(d["hands"]) >= 900:
            seen.add(k)
            docs.append(d)
    out = {}
    for z in [float(x) for x in sys.argv[1:]] or [2.5, 3.0, 3.5, 4.0]:
        m.GP_Z = z
        seats = flags = 0
        for d in docs:
            a = m.Agent()
            for s in summaries(d):
                a.on_hand_end(s)
            n = len(d["players"]) - 1
            seats += n
            flags += sum(1 for s in a.gp_changed if s != d["seat"])
        out[z] = (flags, seats)
        print("z=%.1f: %d of %d real opponent-rounds flagged (%.1f%% false alarms)" % (z, flags, seats, 100.0 * flags / seats))
    json.dump({"rounds": len(docs), "results": {str(k): v for k, v in out.items()}}, open(os.path.join(HERE, "drift_calibration.json"), "w"), indent=1)
