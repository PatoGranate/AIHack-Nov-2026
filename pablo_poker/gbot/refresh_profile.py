"""Refresh the Table D opponent profile from the latest fetched round(s) and write a NEW G_profile_td file.

    python gbot/refresh_profile.py hands/external/WBot/sunday_r001.json [more round files ...]
    python gbot/refresh_profile.py --dir hands/external/WBot --pattern "sunday*" --last 1

Plan agreed by the team: round 1 runs G_profile_td (Saturday-pooled Table D profile). After every round, the fetched
hand log shows what the other bots actually did; this tool recomputes the pooled opponent profile from it and writes
gbot/G_profile_td_<ref>.py for the next upload. Nothing is ever overwritten (Pablo's rule); the previous file stays.

- Bots get no names or fixed seats, so the profile is pooled across every opponent at the table (our seat excluded).
- Statistics come from replaying the round through frozen G's own counter (`_learn`), so they mean exactly what G
  measures in play: vpip, pfr, big, f3 (own open folded to a 3-bet), ftr, ftb, af.
- New value = (previous profile x K + this round's counts) / (K + this round's opportunities): fresh evidence
  dominates, a thin statistic (e.g. f3, ~150 decisions) moves less than a dense one (vpip, ~7,000 hands).
"""
import argparse
import ast
import glob
import hashlib
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from gbot.calib_drift_real import summaries  # noqa: E402

PROFILE_DIR = os.path.join(HERE, "profiles")
K = {"vpip": 2000, "pfr": 2000, "big": 2000, "f3": 100, "ftr": 400, "ftb": 400, "af": 600}


def load_g():
    spec = importlib.util.spec_from_file_location("g_refresh", os.path.join(HERE, "G_frozen.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def round_counts(path, G):
    d = json.load(open(path, encoding="utf-8"))
    a = G.Agent()
    a.seat = d["seat"]
    for s in summaries(d):
        a.on_hand_end(s)
    tot = {k: 0 for k in ("hands", "vpip", "pfr", "big", "o3", "o3fold", "f3", "f3fold", "faced", "ffold", "pbet", "pcall", "pcheck")}
    for seat, st in a.st.items():
        if seat == d["seat"]:
            continue
        for k in tot:
            tot[k] += getattr(st, k)
    ref = (d.get("round") or {}).get("ref") or os.path.basename(path)[:-5]
    return ref, tot, [p for i, p in enumerate(d["players"]) if i != d["seat"]]


def current_prior():
    files = sorted(glob.glob(os.path.join(PROFILE_DIR, "td_prior_*.json")), key=os.path.getmtime)
    if files:
        return json.load(open(files[-1]))["prior"], os.path.basename(files[-1])
    src = open(os.path.join(HERE, "g_profile_adapter.py"), encoding="utf-8").read()
    m = re.search(r"GP_ROSTER = (\{.*?\})", src, re.S)
    return ast.literal_eval(m.group(1)), "Saturday pooled (g_profile_adapter.py)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--dir")
    ap.add_argument("--pattern", default="*")
    ap.add_argument("--last", type=int, default=1)
    a = ap.parse_args()
    files = list(a.files)
    if a.dir:
        files += sorted(glob.glob(os.path.join(a.dir, a.pattern + ".json")))[-a.last:]
    if not files:
        sys.exit("no round files given")
    G = load_g()
    prior, prior_src = current_prior()
    tot, refs, opps = None, [], set()
    for f in files:
        ref, c, players = round_counts(f, G)
        refs.append(ref)
        opps.update(players)
        tot = c if tot is None else {k: tot[k] + c[k] for k in tot}
    num_den = {"vpip": ("vpip", "hands"), "pfr": ("pfr", "hands"), "big": ("big", "hands"), "f3": ("o3fold", "o3"),
               "ftr": ("f3fold", "f3"), "ftb": ("ffold", "faced")}
    new, obs = {}, {}
    for key, (num, den) in num_den.items():
        n = tot[den]
        obs[key] = (tot[num] / n if n else None, n)
        new[key] = round((prior[key] * K[key] + tot[num]) / (K[key] + n), 4)
    acts = tot["pbet"] + tot["pcall"] + tot["pcheck"]
    obs["af"] = (tot["pbet"] / acts if acts else None, acts)
    new["af"] = round((prior["af"] * K["af"] + tot["pbet"]) / (K["af"] + acts), 4)
    tag = re.sub(r"[^A-Za-z0-9]+", "_", refs[-1]).strip("_")
    os.makedirs(PROFILE_DIR, exist_ok=True)
    jpath = os.path.join(PROFILE_DIR, "td_prior_%s.json" % tag)
    out = os.path.join(HERE, "G_profile_td_%s.py" % tag)
    if os.path.exists(out) or os.path.exists(jpath):
        sys.exit("refusing to overwrite %s (never replace a version)" % out)
    base = open(os.path.join(HERE, "G_profile_td.py"), encoding="utf-8").read()
    pat = r"GP_ROSTER = \{.*?\}"
    assert re.search(pat, base, re.S), "GP_ROSTER not found in G_profile_td.py"
    src = re.sub(pat, "GP_ROSTER = " + json.dumps(new, sort_keys=True), base, count=1, flags=re.S)
    src = src.replace("# pooled Table D tendencies (data/v3_model.json, Saturday rounds, recency-weighted)",
                      "# pooled Table D tendencies refreshed from %s (gbot/refresh_profile.py)" % ", ".join(refs))
    ast.parse(src)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    sha = hashlib.sha256(open(out, "rb").read()).hexdigest()
    rec = {"rounds": refs, "opponents": sorted(opps), "previous": prior_src, "prior": new,
           "observed": {k: {"rate": (round(v[0], 4) if v[0] is not None else None), "n": v[1]} for k, v in obs.items()},
           "bot_file": os.path.basename(out), "sha256": sha}
    json.dump(rec, open(jpath, "w"), indent=1)
    print("rounds %s, opponents %s" % (refs, sorted(opps)))
    print("%-5s %8s %8s %8s %7s" % ("stat", "previous", "observed", "new", "n"))
    for k in ("vpip", "pfr", "big", "f3", "ftr", "ftb", "af"):
        o = obs[k][0]
        print("%-5s %8.3f %8s %8.3f %7d" % (k, prior[k], "%.3f" % o if o is not None else "-", new[k], obs[k][1]))
    print("wrote %s (sha256 %s...) and %s" % (os.path.relpath(out, ROOT), sha[:12], os.path.relpath(jpath, ROOT)))


if __name__ == "__main__":
    main()
