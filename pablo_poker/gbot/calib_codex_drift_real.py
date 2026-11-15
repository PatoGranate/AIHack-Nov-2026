"""False-alarm rate of Codex's BehaviorProfile change detector (pokerbot/behavior_profile.py)
on REAL Saturday rounds: a seat 'ever flagged' inside a round is a false alarm (code cannot change mid-round)."""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from pokerbot.behavior_profile import BehaviorProfile
from pokerbot.opponent_evidence import hand_counts
files, seen, docs = [], set(), []
for pat in ("hands/saturday_r0*.json", "hands/external/WBot/saturday_r0*.json", "hands/external/Red/saturday_r0*.json"):
    files += sorted(glob.glob(os.path.join(ROOT, pat)))
for f in files:
    d = json.load(open(f, encoding="utf-8")); k = (d["round"].get("slot"), tuple(d["players"]))
    if k not in seen and len(d["hands"]) >= 900:
        seen.add(k); docs.append(d)
seats = flagged = fails = 0
for d in docs:
    labels = ["WBot" if s == d["seat"] else "seat:%d" % s for s in range(len(d["players"]))]
    prof = {s: BehaviorProfile() for s in range(len(labels)) if s != d["seat"]}
    ever = set()
    for h in d["hands"]:
        try:
            c = hand_counts(h, labels)
        except Exception:
            fails += 1; continue
        for s, p in prof.items():
            p.update(c[labels[s]])
            if p.changed:
                ever.add(s)
    seats += len(prof); flagged += len(ever)
print("rounds %d: %d of %d real opponent-rounds ever flagged as changed (%.1f%% false alarms); parse failures %d" % (
    len(docs), flagged, seats, 100.0 * flagged / seats, fails))
json.dump({"rounds": len(docs), "flagged": flagged, "seats": seats}, open(os.path.join(HERE, "codex_drift_calibration.json"), "w"))
