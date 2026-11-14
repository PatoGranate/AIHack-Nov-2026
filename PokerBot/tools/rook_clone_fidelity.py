"""Rook: Sunday clone-fidelity audit and isolated recalibration.

Usage (from PokerBot/):
    python tools/rook_clone_fidelity.py <DATA_ROOT> [--write]

<DATA_ROOT> is a PokerBot/ folder holding Hand_data/ and
ExternalAnalysis/SaturdayFieldPostmortem/data/leaderboard_history_r13_r48.csv
(PR #7 head f7fbac4 was used).

Read-only unless --write. With --write it creates NEW clones in tools/opponents/sunday_v2/ plus MANIFEST.json.
It never touches tools/opponents/real/: tools/make_clones.py deletes r_*.py there, so it is NOT reused.
The PARAMS mapping is copied verbatim from tools/make_clones.py so that old and new clones are comparable.
"""
import collections, csv, glob, hashlib, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze

ROOT = sys.argv[1]
WRITE = "--write" in sys.argv
SUNDAY = {"Poke": "Poke", "Resonance Qt": "ResonanceQt", "Anker Batteries": "AnkerBatteries",
          "Chinese people can fly": "Chinesepeoplecanfly", "GamesGone": "GamesGone", "Anton": "Anton",
          "YSL_TWIZZY": "YSLTWIZZY"}
OLD_DIR = "tools/opponents/real"
NEW_DIR = "tools/opponents/sunday_v2"

# ---- deduplicated, counted Saturday tables (same rule as PR #7: ref + ordered players; skip practice) ----
files = sorted(glob.glob(ROOT + "/Hand_data/SaturdayRealRounds/*.json") +
               glob.glob(ROOT + "/Hand_data/ExternalTeamData/*/SaturdayRealRounds/*.json"))
seen, tables = set(), []
for f in files:
    d = json.loads(open(f, "rb").read().decode("utf-8-sig"))
    k = (d["ref"], tuple(d["players"]))
    if "practice" in d["ref"] or k in seen:
        continue
    seen.add(k)
    tables.append((int(d["ref"].split("/")[-1][1:]), f, d))

# ---- each team's displayed version per round, from the public leaderboard history (r13-r48) ----
ver = collections.defaultdict(dict)
for r in csv.DictReader(open(ROOT + "/ExternalAnalysis/SaturdayFieldPostmortem/data/leaderboard_history_r13_r48.csv",
                             encoding="utf-8-sig")):
    ver[r["team"]][int(r["played"])] = int(r["displayed_version"])


def version_window(team):
    """Rounds played under the team's latest observed version (displayed_version at played=48, i.e. after r48).

    The leaderboard row at played=p shows the version after round p, so the version used in round p is
    uncertain at a switch. We use rounds p+1 where the version at p and at p+1 both equal the latest version.
    Rounds 49-54 are included only as an assumption (no per-round version data), and are flagged.
    """
    v = ver.get(team, {})
    if 48 not in v:
        return None, set()
    last = v[48]
    rounds = {p + 1 for p in range(13, 48) if v.get(p) == last and v.get(p + 1) == last}
    return last, rounds


def stats_for(team, rounds=None):
    import tempfile
    sel = [f for (rn, f, d) in tables if team in d["players"] and (rounds is None or rn in rounds)]
    if not sel:
        return None, 0
    S, *_ = analyze.analyse(sel)
    return S.get(analyze.fixname(team)) or S.get(team), len(sel)


def summarise(o):
    H = o["hands"]
    q = dict(hands=H, vpip=o["vpip"] / H, pfr=o["pfr"] / H, threebet=o["3b"] / max(1, o["f_raise"]),
             limp=o["limp"] / max(1, o["unopened"]),
             af=o["pbet"] / max(1, o["pbet"] + o["pcall"] + o["pcheck"]),
             ftb=o["ffold"] / max(1, o["faced"]), n_f_raise=o["f_raise"], n_unopened=o["unopened"],
             n_faced=o["faced"], n_post=o["pbet"] + o["pcall"] + o["pcheck"])
    se = lambda p, n: math.sqrt(max(p * (1 - p), 1e-9) / max(n, 1))
    q["se"] = dict(vpip=se(q["vpip"], H), pfr=se(q["pfr"], H), threebet=se(q["threebet"], o["f_raise"]),
                   limp=se(q["limp"], o["unopened"]), af=se(q["af"], q["n_post"]), ftb=se(q["ftb"], o["faced"]))
    return q


def params_from(o):
    """Verbatim copy of the PARAMS mapping in tools/make_clones.py."""
    H = o["hands"]; vpip = o["vpip"] / H; pfr = o["pfr"] / H; tb = o["3b"] / max(1, o["f_raise"]); shv = o["shove"] / H
    limp = o["limp"] / max(1, o["unopened"]); af = o["pbet"] / max(1, o["pbet"] + o["pcall"] + o["pcheck"])
    ftb = o["ffold"] / max(1, o["faced"]); cb = o["cb"] / max(1, o["cb_ch"]); frse = o["fold_raise"] / max(1, o["f_raise"])
    opsz = o["open_sz"] / max(1, o["open_n"])
    call = min(0.95, max(pfr * 1.2, (1 - frse) + tb))
    p = dict(open=round(min(0.9, pfr * 1.25), 3), threebet=round(min(0.5, tb * 1.1 + 0.01), 3),
             call=round(call * (0.55 if call < 0.5 else 0.7), 3), call_cap=0.15 if frse > 0.8 else 0.3,
             open_size=round(min(6, max(2, opsz if opsz < 10 else 3)), 1),
             limp=round(min(0.95, vpip * 1.1), 3) if limp > 0.25 else 0.0,
             cbet=round(cb, 2), bluff=round(max(0.0, (af - 0.2) * 0.9), 2),
             bet_min=1 if af > 0.45 else (2 if af > 0.25 else 3),
             call_min=1 if ftb < 0.3 else (2 if ftb < 0.52 else 3),
             raise_min=3 if af > 0.5 else 4, bet_frac=0.7, semibluff=round(min(0.8, af), 2))
    if ftb < 0.25:
        p["air_call"] = 0.55
    if shv > 0.04:
        p["shove_mix"] = round(shv * 1.1, 3)
    return p


def old_clone(fn):
    src = open(fn, encoding="utf-8").read()
    import ast, re
    m = re.search(r"# clone of .*?: vpip ([\d.]+) pfr ([\d.]+) 3b ([\d.]+) af ([\d.]+) ftb ([\d.]+) \((\d+) hands\)", src)
    P = ast.literal_eval(re.search(r"PARAMS = (\{.*\})", src).group(1))
    return dict(vpip=float(m[1]), pfr=float(m[2]), threebet=float(m[3]), af=float(m[4]), ftb=float(m[5]),
                hands=int(m[6])), P, hashlib.sha256(open(fn, "rb").read()).hexdigest()


report = {"data_root": os.path.abspath(ROOT), "tables_used": len(tables), "teams": {}}
print("tables used (dedup, counted):", len(tables))
for team, fn in SUNDAY.items():
    oldtgt, oldP, oldsha = old_clone("%s/r_%s.py" % (OLD_DIR, fn))
    allo, nt_all = stats_for(team)
    lastv, rounds = version_window(team)
    rounds_ext = rounds | set(range(49, 55)) if rounds else rounds
    lato, nt_lat = stats_for(team, rounds_ext) if rounds else (None, 0)
    A = summarise(allo); L = summarise(lato) if lato else None
    rec = dict(old=dict(path="%s/r_%s.py" % (OLD_DIR, fn), sha256=oldsha, target=oldtgt, params=oldP),
               all_saturday=dict(tables=nt_all, **A), latest_version=None)
    if L:
        rec["latest_version"] = dict(version=lastv, rounds=sorted(rounds_ext), tables=nt_lat,
                                     note="r49-54 included by assumption: version unchanged after r48", **L)
    report["teams"][team] = rec
    print("\n== %s  old clone %s… target from %d hands" % (team, oldsha[:12], oldtgt["hands"]))
    print("   %-9s %7s %16s %16s" % ("stat", "old", "all-Saturday", "latest v%s" % lastv))
    for k in ("vpip", "pfr", "threebet", "limp", "af", "ftb"):
        o = oldtgt.get(k)
        a = "%.3f±%.3f" % (A[k], A["se"][k])
        l = "%.3f±%.3f" % (L[k], L["se"][k]) if L else "-"
        flag = ""
        if o is not None and abs(A[k] - o) > 3 * A["se"][k] and abs(A[k] - o) > 0.03:
            flag = "  <-- old vs all >3SE"
        print("   %-9s %7s %16s %16s%s" % (k, "%.2f" % o if o is not None else "n/a", a, l, flag))
    print("   hands: all %d (%d tables); latest-version %s" % (A["hands"], nt_all,
          "%d (%d tables, rounds %d-%d)" % (L["hands"], nt_lat, min(rounds_ext), max(rounds_ext)) if L else "-"))
    if WRITE:
        src_o, label = (lato, "latest v%d (rounds %s)" % (lastv, ",".join(map(str, sorted(rounds_ext))))) \
            if (L and L["hands"] >= 4000) else (allo, "all Saturday tables")
        rec["new"] = dict(calibration=label, params=params_from(src_o), hands=src_o["hands"])
        os.makedirs(NEW_DIR, exist_ok=True)
        q = summarise(src_o)
        path = "%s/r_%s.py" % (NEW_DIR, fn)
        open(path, "w", encoding="utf-8", newline="\n").write('''import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # sunday_v2 clone of %s: vpip %.2f pfr %.2f 3b %.2f limp %.2f af %.2f ftb %.2f (%d hands; %s)
    PARAMS = %r
''' % (team, q["vpip"], q["pfr"], q["threebet"], q["limp"], q["af"], q["ftb"], src_o["hands"], label, rec["new"]["params"]))
        rec["new"]["path"] = path
        rec["new"]["sha256"] = hashlib.sha256(open(path, "rb").read()).hexdigest()
if WRITE:
    man = {"field": "sunday_v2", "generator": "tools/rook_clone_fidelity.py",
           "generator_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
           "mapping": "verbatim copy of tools/make_clones.py PARAMS mapping",
           "data_root_note": "PR #7 head f7fbac4 Hand_data (159 files, 135 dedup tables) + leaderboard_history_r13_r48.csv",
           "old_field": OLD_DIR + " (unchanged)",
           "files": {t: report["teams"][t]["new"]["sha256"] for t in SUNDAY},
           "calibration": {t: report["teams"][t]["new"]["calibration"] for t in SUNDAY}}
    json.dump(man, open(NEW_DIR + "/MANIFEST.json", "w", encoding="utf-8", newline="\n"), indent=1)
json.dump(report, open("ExternalAnalysis/AgentReports/rook_clone_fidelity_data.json", "w", encoding="utf-8", newline="\n"), indent=1, default=str)
