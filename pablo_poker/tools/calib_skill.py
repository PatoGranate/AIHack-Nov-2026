"""Fit each clone's hand-reading skill (data/field_skill.json) to the real bot's showdown win rate.

    python tools/calib_skill.py SIMDIR [gain]

Clones reproduce every bot's frequencies, but frequencies alone make every clone equally skilled
(real showdown win rates 40-65%, clones 47-56%). Skill > 0 makes a clone read the bettor's range from
the bet size; skill < 0 adds noise to its hand strength. One pass: skill += gain * (real wsd - sim wsd).
"""
import glob
import json
import os
import sys
import argparse
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "field_skill.json")


def wsd(docs):
    C = defaultdict(lambda: [0, 0])
    for d in docs:
        pl = [p.split(":", 1)[1] if p.startswith(("fb:", "clone:")) else p for p in d["players"]]
        for h in d["hands"]:
            sd = h.get("showdown") or {}
            if len(sd) < 2:
                continue
            for k in sd:
                c = C[pl[int(k)]]
                c[0] += 1
                c[1] += h["results"][int(k)] > 0
    return C


def real_docs(lo=38,before=None):
    seen = set()
    pats = ["hands/saturday_r0*.json", "hands/external/WBot/saturday_r0*.json", "hands/external/Red/saturday_r0*.json"]
    for pat in pats:
        for f in sorted(glob.glob(os.path.join(ROOT, pat))):
            if int(f[-8:-5]) < lo:
                continue
            d = json.load(open(f, encoding="utf-8"))
            if before is not None and d.get('round',{}).get('slot','') >= before:
                continue
            k = (d["round"].get("slot"), tuple(d["players"]))
            if k not in seen:
                seen.add(k)
                yield d


if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument('simdir');ap.add_argument('gain',type=float,nargs='?',default=5.)
    ap.add_argument('--before',required=True,help='exclusive ISO training cutoff; never fit on held-out rounds')
    ap.add_argument('--out',default=os.path.join(ROOT,'sunday','field_skill_candidate.json'))
    a=ap.parse_args();gain=a.gain
    R = wsd(real_docs(before=a.before))
    S = wsd(json.load(open(f, encoding="utf-8")) for f in glob.glob(os.path.join(a.simdir, "*.json")))
    sk = json.load(open(a.out)) if os.path.exists(a.out) else {}
    rows = []
    for name in sorted(set(R) & set(S)):
        if name == "kaiserbot" or R[name][0] < 120 or S[name][0] < 120:
            continue
        r, s = R[name][1] / R[name][0], S[name][1] / S[name][0]
        old = sk.get(name, 0.0)
        sk[name] = round(max(-1.0, min(3.0, old + gain * (r - s))), 3)
        rows.append((name, r, s, old, sk[name]))
    json.dump(sk, open(a.out, "w"), indent=1, sort_keys=True)
    json.dump({'training_before':a.before,'simdir':os.path.abspath(a.simdir),
               'status':'fit_only_requires_independent_validation','gain':gain},open(a.out+'.manifest.json','w'),indent=2)
    err = sum(abs(r - s) for _, r, s, _, _ in rows) / max(1, len(rows))
    print("mean |real - sim| showdown win rate: %.3f over %d bots" % (err, len(rows)))
    for name, r, s, o, nw in sorted(rows, key=lambda x: -x[1]):
        print("  %-26s real %.2f sim %.2f  skill %+.2f -> %+.2f" % (name[:26], r, s, o, nw))
