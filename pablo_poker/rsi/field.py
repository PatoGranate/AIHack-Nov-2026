"""Field model: learn the REAL opponents from downloaded tournament hands.

    python fetch_hands.py --token ...       (or let the lab do it: data/token.txt or $POKER_TOKEN)
    python -m rsi.field                     print every opponent's profile

Where the data lives
  hands/*.json             our own rounds (fetch_hands.py with our token); these define who "we" are
  hands/external/**.json   anything else in the same format: teammates' or other teams'
                           downloads, any subfolders. Hands seen twice (two teams at one table)
                           are counted once (key: round ref + table + hand number).
  data/self_names.txt      optional, one bot name per line: extra names to treat as ours

From those files it measures, per opponent bot: VPIP, PFR, preflop shove
rate, postflop aggression frequency and result. Each opponent then gets a
*clone*: our own strategy with parameters scaled until its tendencies match,
plus a push/fold component for frequent shovers. The lab uses the clones as
the main opponent pool, so tuning targets the tables we actually play.
"""
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDS_DIR = os.path.join(ROOT, "hands")
TOKEN_FILE = os.path.join(ROOT, "data", "token.txt")
SELF_NAMES = set()   # filled from each file's own seat


def _files(hands_dir):
    own = sorted(glob.glob(os.path.join(hands_dir, "*.json")))
    ext = sorted(glob.glob(os.path.join(hands_dir, "external", "**", "*.json"), recursive=True))
    return [(f, True) for f in own] + [(f, False) for f in ext]


def self_names(hands_dir=HANDS_DIR):
    names = set()
    for f, own in _files(hands_dir):
        if not own:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        players, me = d.get("players") or [], d.get("seat")
        if isinstance(me, int) and me < len(players):
            names.add(players[me])
    try:
        names |= {x.strip() for x in open(os.path.join(ROOT, "data", "self_names.txt"), encoding="utf-8") if x.strip()}
    except OSError:
        pass
    return names


def profiles(hands_dir=HANDS_DIR):
    prof = {}
    SELF_NAMES.clear()
    SELF_NAMES.update(self_names(hands_dir))
    seen_hands = set()
    for f, own in _files(hands_dir):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        players = d.get("players") or []
        rnd = d.get("round") or {}
        ref = d.get("ref") or rnd.get("ref") or f
        table = rnd.get("table", d.get("table"))
        for h in d.get("hands", []):
            key = (ref, table, h.get("n"))
            if h.get("n") is not None and key in seen_hands:
                continue
            seen_hands.add(key)
            vp, pr, jam = set(), set(), set()
            pf = {}
            street = "preflop"
            for e in h.get("events", []):
                if e[0] == "board":
                    street = e[1]
                elif e[0] == "act":
                    s, a, amt = e[1], e[2], e[3]
                    if street == "preflop":
                        if a in ("call", "raise"):
                            vp.add(s)
                        if a == "raise":
                            pr.add(s)
                            if amt >= 900:
                                jam.add(s)
                    else:
                        c = pf.setdefault(s, [0, 0])
                        c[0] += a == "raise"
                        c[1] += 1
            for s, name in enumerate(players):
                p = prof.setdefault(name, {"name": name, "hands": 0, "vpip": 0, "pfr": 0, "jam": 0, "pf_aggr": 0,
                                           "pf_acts": 0, "chips": 0})
                p["hands"] += 1
                p["vpip"] += s in vp
                p["pfr"] += s in pr
                p["jam"] += s in jam
                if s in pf:
                    p["pf_aggr"] += pf[s][0]
                    p["pf_acts"] += pf[s][1]
                res = h.get("results") or []
                if s < len(res):
                    p["chips"] += res[s]
    out = []
    for p in prof.values():
        n = max(1, p["hands"])
        out.append({"name": p["name"], "hands": p["hands"], "vpip": p["vpip"] / n, "pfr": p["pfr"] / n,
                    "jam": p["jam"] / n, "agg_freq": p["pf_aggr"] / max(1, p["pf_acts"]),
                    "bb100": p["chips"] / 20.0 / n * 100, "self": p["name"] in SELF_NAMES})
    return sorted(out, key=lambda x: -x["hands"])


def clone_params(pr):
    """Scale our strategy so its tendencies resemble this profile (rough, monotone mapping)."""
    from pokerbot.strategy import DEFAULT_PARAMS, PARAM_SPACE

    def clamp(k, v):
        lo, hi, _ = PARAM_SPACE[k]
        return round(max(lo, min(hi, v)), 4)
    d = DEFAULT_PARAMS
    kr = max(0.3, min(4.0, pr["pfr"] / 0.10))                    # our baseline PFR is ~10%
    kv = max(0.3, min(5.0, max(0.01, pr["vpip"] - pr["pfr"]) / 0.08))
    out = {k: clamp(k, d[k] * kr) for k in ("open_ep", "open_mp", "open_co", "open_btn", "open_sb", "threebet_value")}
    out["call_open"] = clamp("call_open", d["call_open"] * kv)
    out["bb_defend"] = clamp("bb_defend", d["bb_defend"] * kv)
    agg = pr["agg_freq"]
    out["bluff_freq"] = clamp("bluff_freq", 0.1 + 1.6 * max(0.0, agg - 0.15))
    out["cbet_freq"] = clamp("cbet_freq", 0.3 + 1.5 * max(0.0, agg - 0.15))
    if pr["vpip"] > 0.5:                                          # loose-passive spewers call too wide postflop
        out["call_margin"] = clamp("call_margin", -0.06)
    out["exploit"] = 0.3
    return out


def field_mix(min_hands=200, weight_total=24):
    """Opponent mix built from the real field: [(weight, spec), ...] or [] without data."""
    prs = [p for p in profiles() if not p["self"] and p["hands"] >= min_hands]
    if not prs:
        return []
    tot = sum(p["hands"] for p in prs)
    mix = []
    for p in prs:
        w = max(1, round(weight_total * p["hands"] / tot))
        mix.append((w, {"kind": "strategy", "params": clone_params(p), "strategy_id": "clone:" + p["name"][:24]}))
        if p["jam"] >= 0.04:                                      # frequent shovers: add a push/fold component
            mix.append((max(1, round(w * min(1.0, p["jam"] * 5))), {"kind": "extreme", "name": "pushfold"}))
    return mix


def read_token():
    tok = os.environ.get("POKER_TOKEN")
    if tok:
        return tok.strip()
    try:
        return open(TOKEN_FILE, encoding="utf-8").read().strip() or None
    except OSError:
        return None


def fetch(timeout=120):
    """Run fetch_hands.py with the stored token. Returns (ok, last output line)."""
    tok = read_token()
    if not tok:
        return False, "no token (set $POKER_TOKEN or write data/token.txt)"
    try:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "fetch_hands.py"), "--token", tok, "--out", HANDS_DIR],
                           capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return False, "fetch timed out"
    lines = (r.stdout + r.stderr).strip().splitlines()
    return r.returncode == 0, lines[-1] if lines else ""


if __name__ == "__main__":
    sys.path.insert(0, ROOT)
    for p in profiles():
        print("%-28s %s hands %5d  VPIP %4.0f%%  PFR %4.0f%%  shove %4.1f%%  postflop agg %4.0f%%  %+7.1f bb/100" % (
            p["name"][:28], "*" if p["self"] else " ", p["hands"], 100 * p["vpip"], 100 * p["pfr"], 100 * p["jam"],
            100 * p["agg_freq"], p["bb100"]))


EXTERNAL_TOKENS = os.path.join(ROOT, "data", "external_tokens.txt")
EXTERNAL_TEAMS = os.path.join(ROOT, "data", "external_teams.json")


def fetch_external(timeout=180):
    """Fetch every token in data/external_tokens.txt into hands/external/<team>/. Returns [(team, line)]."""
    import hashlib
    import re as _re
    import shutil
    try:
        tokens = [t.strip() for t in open(EXTERNAL_TOKENS, encoding="utf-8") if t.strip()]
    except OSError:
        return []
    try:
        teams = json.load(open(EXTERNAL_TEAMS, encoding="utf-8"))
    except (OSError, ValueError):
        teams = {}
    out = []
    for tok in dict.fromkeys(tokens):
        key = hashlib.sha256(tok.encode()).hexdigest()[:12]          # never store the token itself in the mapping
        team = teams.get(key)
        dest = os.path.join(HANDS_DIR, "external", team) if team else os.path.join(HANDS_DIR, "external", "_new_" + key)
        try:
            r = subprocess.run([sys.executable, os.path.join(ROOT, "fetch_hands.py"), "--token", tok, "--out", dest],
                               capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        except subprocess.TimeoutExpired:
            out.append((team or key, "timed out"))
            continue
        lines = (r.stdout + r.stderr).strip().splitlines()
        last = lines[-1] if lines else ""
        if not team and r.returncode == 0 and ":" in last:
            team = _re.sub(r"[^A-Za-z0-9_-]", "_", last.split(":", 1)[0]) or key
            final = os.path.join(HANDS_DIR, "external", team)
            os.makedirs(final, exist_ok=True)
            for f in glob.glob(os.path.join(dest, "*.json")):
                shutil.move(f, os.path.join(final, os.path.basename(f)))
            shutil.rmtree(dest, ignore_errors=True)
            teams[key] = team
            json.dump(teams, open(EXTERNAL_TEAMS, "w", encoding="utf-8"), indent=1)
        out.append((team or key, last))
    return out
