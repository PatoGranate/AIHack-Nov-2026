"""Build tools/review/data.json for hand_review.html.

python tools/review/build_review_data.py

Reads every hand-history JSON under Hand_data (except Hand_data/_fetched): our
PracticeRounds (rNvM = sample N of version M), SaturdayRealRounds (G), and other
teams' downloads (ExternalData_OtherBots, ExternalTeamData/**). Each file is kept
as a source record (team, practice/live, ref, seat, file sha256, public-history
sha256). Tables are deduplicated by (ref, ordered players, public-history hash);
extra viewpoints only contribute showdown hole cards.
Stats logic follows tools/analyze.py (copied so files are read as UTF-8).
"""
import os, sys, json, glob, re, hashlib
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import preflop_tables as PT  # noqa: E402

ME = "WBot"
BB = 20
STACK = 2000
VNAMES = {1: "A: first upload (chart + simulation)", 2: "C: very aggressive",
          3: "E: balanced + timeout fix", 4: "D: max aggressive", 5: "G: v7 corrected model, current upload"}
RANKS = "23456789TJQKA"
PCT = {}
_c = 0
for c in PT.RANK:
    _c += 6 if len(c) == 2 else (4 if c[2] == "s" else 12)
    PCT[c] = _c / 1326.0


def key(h):
    a, b = RANKS.index(h[0][0]), RANKS.index(h[1][0])
    if a < b:
        a, b = b, a
    if a == b:
        return RANKS[a] * 2
    return RANKS[a] + RANKS[b] + ("s" if h[0][1] == h[1][1] else "o")


def hclass(h):
    p = PCT[key(h)]
    return "prem" if p <= .05 else "good" if p <= .15 else "mid" if p <= .35 else "weak"


# ---------------------------------------------------------------- loading
def load(path):
    with open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))  # strict: raises on bad bytes


def fix_name(n):
    """Repair UTF-8 text that was mis-decoded as latin-1 (e.g. 'cr\u00c3\u00aapes' -> 'cr\u00eapes')."""
    try:
        return n.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return n


def rnd(ref):
    return ref.split("/")[-1]


HD = os.path.join(ROOT, "Hand_data")


def pub_hash(d):
    """sha256 of the public history: per hand n, button, stacks, events, results (no hole cards)."""
    pub = [[h["n"], h["button"], h["start_stacks"], h["events"], h["results"]] for h in d["hands"]]
    return hashlib.sha256(json.dumps(pub, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


# every hand-history file under Hand_data except the _fetched duplicates folder
paths = []
for p in sorted(glob.glob(os.path.join(HD, "**", "*.json"), recursive=True)):
    rel = os.path.relpath(p, HD).replace("\\", "/")
    if rel.split("/")[0] == "_fetched":
        continue
    paths.append((rel, p))

repaired = {}
recs = []
for rel, p in paths:
    with open(p, "rb") as f:
        raw = f.read()
    d = json.loads(raw.decode("utf-8"))  # strict UTF-8
    if not isinstance(d, dict) or "hands" not in d or "seat" not in d:
        continue
    new = [fix_name(n) for n in d["players"]]
    for x, y in zip(d["players"], new):
        if x != y: repaired[x] = y
    d["players"] = new
    m = re.match(r"r(\d+)v(\d+)\.json$", os.path.basename(p))
    recs.append(dict(d=d, rel=rel, sha=hashlib.sha256(raw).hexdigest(), pub=pub_hash(d),
                     team=d["players"][d["seat"]], typ="practice" if "practice" in d["ref"] else "live",
                     ver=int(m.group(2)) if m else None, lab=("r%sv%s" % (m.group(1), m.group(2))) if m else None))

# version of our files: rNvM name, else same table as an rNvM file, else live Saturday round = G (5)
# website version for WBot tables without an rNvM file (from the results API "version" field)
REF_VER = {"saturday/practice/r014": 2}
ver_by_pub = {r["pub"]: (r["ver"], r["lab"]) for r in recs if r["ver"]}
for r in recs:
    if r["team"] == ME and r["ver"] is None:
        if r["pub"] in ver_by_pub:
            r["ver"], r["lab"] = ver_by_pub[r["pub"]]
        elif r["typ"] == "live":
            r["ver"] = 5
        elif r["d"]["ref"] in REF_VER:
            r["ver"] = REF_VER[r["d"]["ref"]]

# group viewpoints into distinct tables: canonical identity (ref + ordered players) + public-history hash
groups = {}
for r in recs:
    groups.setdefault((r["d"]["ref"], tuple(r["d"]["players"]), r["pub"]), []).append(r)

tables = []
for ti, (k, rs) in enumerate(sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1]))):
    rs.sort(key=lambda r: (r["team"] != ME, r["ver"] is None, r["rel"]))
    prim = rs[0]; d = prim["d"]
    ours_t = prim["team"] == ME
    rr = rnd(d["ref"])
    # merge other viewpoints' hole cards, only for seats that reached showdown
    for other in rs[1:]:
        for h, h2 in zip(d["hands"], other["d"]["hands"]):
            sd = dict(h2.get("showdown") or {}); sd.update(h.get("showdown") or {})
            h["showdown"] = sd
            hole = h.setdefault("hole", {})
            for s, c in (h2.get("hole") or {}).items():
                if s not in hole and s in sd:
                    hole[s] = c
    d["_src"] = "ours" if ours_t else "ext"
    d["_ver"] = prim["ver"] if ours_t else 0
    d["_typ"] = prim["typ"]
    if ours_t:
        d["_lab"] = prim["lab"] or ("live " + rr if prim["typ"] == "live" else "prac " + rr)
    else:
        d["_lab"] = ("other live " if prim["typ"] == "live" else "other prac ") + rr
    d["_views"] = rs
    tables.append(d)

sources = []
for ti, d in enumerate(tables):
    for r in d["_views"]:
        sources.append(dict(team=r["team"], typ=r["typ"], ref=r["d"]["ref"], seat=r["d"]["seat"], file=r["rel"],
                            sha=r["sha"], pub=r["pub"], t=ti))


# ---------------------------------------------------------------- per hand facts
def facts(h, n):
    """Replay one hand: contributions, folds, streets, aggression facts."""
    contrib = [0] * n
    street_in = [0] * n
    folded = [False] * n
    street = "preflop"
    cur = h["bb"]; pf_raises = 0
    last_act = {}  # (seat, street) -> action
    river_shove = False; pf_allin = False; post_allin = False
    post_raise = defaultdict(int)
    saw_flop = None
    end_street = "preflop"
    for e in h["events"]:
        t = e[0]
        if t == "post":
            contrib[e[1]] += e[2]; street_in[e[1]] += e[2]
        elif t == "board":
            street = e[1]; cur = 0; street_in = [0] * n; end_street = street
            if street == "flop":
                saw_flop = sum(1 for f in folded if not f)
        elif t == "refund":
            contrib[e[1]] -= e[2]
        elif t == "act":
            _, s, a, amt = e
            last_act[(s, street)] = a
            if a == "fold":
                folded[s] = True
            elif a in ("call", "raise"):
                if a == "call":
                    contrib[s] += amt; street_in[s] += amt
                else:
                    contrib[s] += amt - street_in[s]; street_in[s] = amt; cur = amt
                    if street == "preflop": pf_raises += 1
                    else: post_raise[s] += 1
                if contrib[s] >= STACK:
                    if street == "preflop": pf_allin = True
                    else: post_allin = True
                    if street == "river": river_shove = True
    alive = [i for i in range(n) if not folded[i]]
    return dict(contrib=contrib, folded=folded, pf_raises=pf_raises, last_act=last_act,
                river_shove=river_shove, pf_allin=pf_allin, post_allin=post_allin, post_raise=post_raise,
                saw_flop=saw_flop or 0, end_street=end_street, alive=alive,
                showdown=len(alive) > 1)


# ---------------------------------------------------------------- stats (analyze.py logic)
def new_stats():
    return defaultdict(float)


def table_stats(d):
    names = d["players"]; n = len(names)
    S = defaultdict(new_stats)
    for h in d["hands"]:
        street = "preflop"; cur = h["bb"]; nraise = 0; first_raiser = None; last_raiser = None
        vol = set(); op_done = False
        for i in range(n):
            S[names[i]]["hands"] += 1
            S[names[i]]["chips"] += h["results"][i]
        for e in h["events"]:
            if e[0] == "board":
                street = e[1]; cur = 0; nraise = 0; continue
            if e[0] != "act":
                continue
            _, s, a, amt = e
            o = S[names[s]]
            if street == "preflop":
                # (a) cold decision: no voluntary chips yet, facing exactly one raise, not the opener
                if nraise == 1 and s not in vol and s != first_raiser:
                    o["cold_n"] += 1
                    if a == "fold": o["cold_f"] += 1
                # (b) opener's first decision after its open is re-raised, facing exactly a 3-bet
                if s == first_raiser and nraise >= 2 and not op_done:
                    op_done = True
                    if nraise == 2:
                        o["op_n"] += 1
                        if a == "fold": o["op_f"] += 1
                if a in ("call", "raise"): vol.add(s)
                if a in ("call", "raise"): o["_vp"] = 1
                if a == "raise":
                    o["_pr"] = 1
                    if nraise == 0: first_raiser = s
                    last_raiser = s
                    if nraise >= 1: o["3b"] += 1
                    if amt >= 600: o["shove"] += 1
                if nraise >= 1 and a in ("fold", "call", "raise"):
                    o["f_raise"] += 1
                    if a == "fold": o["fold_raise"] += 1
                if nraise == 0 and a == "call": o["limp"] += 1
                if nraise == 0 and a in ("fold", "call", "raise"): o["unopened"] += 1
            else:
                if a == "raise": o["pbet"] += 1
                elif a == "call": o["pcall"] += 1
                elif a == "check": o["pcheck"] += 1
                if cur > 0 and a in ("fold", "call", "raise"):
                    o["faced"] += 1
                    if a == "fold": o["ffold"] += 1
                if street == "flop" and s == last_raiser and cur == 0:
                    o["cb_ch"] += 1
                    if a == "raise": o["cb"] += 1
            if a == "raise":
                cur = amt; nraise += 1
        for i in range(n):
            o = S[names[i]]
            o["vpip"] += o.pop("_vp", 0); o["pfr"] += o.pop("_pr", 0)
    return S


def summarize(o):
    H = max(1, o["hands"])
    r = lambda a, b: round(a / max(1, b), 3)
    return dict(h=int(o["hands"]), bb100=round(o["chips"] / BB / H * 100, 1),
                vpip=r(o["vpip"], H), pfr=r(o["pfr"], H), tb=r(o["3b"], o["f_raise"]),
                af=r(o["pbet"], o["pbet"] + o["pcall"] + o["pcheck"]), ftb=r(o["ffold"], o["faced"]),
                cb=r(o["cb"], o["cb_ch"]),
                cf=[int(o["cold_f"]), int(o["cold_n"])], of=[int(o["op_f"]), int(o["op_n"])],
                limp=r(o["limp"], o["unopened"]), shv=r(o["shove"], H))


TS = [table_stats(d) for d in tables]


def merged(names_filter, idxs):
    out = defaultdict(new_stats)
    for i in idxs:
        for nm, o in TS[i].items():
            if names_filter and nm not in names_filter: continue
            for k, v in o.items(): out[nm][k] += v
    return out


# ---------------------------------------------------------------- table index for page
T = []
for i, d in enumerate(tables):
    T.append(dict(ref=d["ref"], r=rnd(d["ref"]), p=d["players"], src=d["_src"], v=d["_ver"],
                  lab=d["_lab"], o=d["seat"], typ=d["_typ"]))

# ---------------------------------------------------------------- versions
versions = []
for v in sorted(VNAMES):
    idxs = [i for i, d in enumerate(tables) if d["_src"] == "ours" and d["_ver"] == v]
    st = merged({ME}, idxs)[ME]
    s = summarize(st)
    rounds = []
    cls = defaultdict(lambda: [0.0, 0]); end = defaultdict(lambda: [0.0, 0])
    big_w = big_l = 0
    for i in idxs:
        d = tables[i]; me = d["seat"]; n = len(d["players"])
        tot = 0
        for h in d["hands"]:
            res = h["results"][me]; tot += res
            if res >= 800: big_w += 1
            if res <= -800: big_l += 1
            c = cls[hclass(h["hole"][str(me)])]; c[0] += res / BB; c[1] += 1
            F = facts(h, n)
            SK = {"preflop": "pf", "flop": "fl", "turn": "tu", "river": "rv"}
            if F["showdown"] and not F["folded"][me]:
                k = "sd"
            elif F["folded"][me]:
                k = next(SK[x] for x in SK if F["last_act"].get((me, x)) == "fold")
            else:
                k = SK[F["end_street"]]
            e = end[k]; e[0] += res / BB; e[1] += 1
        rounds.append(dict(r=rnd(d["ref"]), lab=T[i]["lab"], h=len(d["hands"]),
                           bb100=round(tot / BB / len(d["hands"]) * 100, 1)))
    versions.append(dict(v=v, name=VNAMES[v], rounds=sorted(rounds, key=lambda x: x["r"]), h=s["h"],
                         bb100=s["bb100"], vpip=s["vpip"], pfr=s["pfr"], af=s["af"], ftb=s["ftb"],
                         bw=big_w, bl=big_l,
                         cls={k: [round(a, 1), b] for k, (a, b) in cls.items()},
                         end={k: [round(a, 1), b] for k, (a, b) in end.items()}))

# ---------------------------------------------------------------- bots
allS = merged(None, range(len(tables)))
appear = defaultdict(list)
for i, d in enumerate(tables):
    for nm in d["players"]:
        appear[nm].append(i)


def style(s):
    v, p, af, ftb, limp = s["vpip"], s["pfr"], s["af"], s["ftb"], s["limp"]
    ratio = p / v if v else 0
    if v < .12: return "nit"
    if v > .45 and p > .28: return "maniac"
    if s["shv"] >= .06: return "loose shover" if v > .3 else "tight shover"
    if ftb < .3: return "calling station" if v >= .25 else "tight calling station"
    if limp > .3: return "loose-passive limper" if v > .3 else "passive limper"
    tight = v <= .26
    aggr = ratio >= .55 or af >= .45
    return ("tight" if tight else "loose") + "-" + ("aggressive" if aggr else "passive")


def note(nm, s, lab):
    out = []
    v, p, ftb, cb, af = s["vpip"], s["pfr"], s["ftb"], s["cb"], s["af"]
    of_f, of_n = s["of"]
    out.append("Plays %d%% of hands, raises %d%% preflop; folds to %d%% of postflop bets." % (
        round(v * 100), round(p * 100), round(ftb * 100)))
    tips = []
    if lab == "nit" or v < .16:
        tips.append("Steal its blinds often and give up when it fights back: its ranges are strong.")
    if "station" in lab or ftb < .3:
        tips.append("Do not bluff it; value-bet thinner and bigger, it pays off with weak pairs.")
    elif ftb > .55:
        tips.append("Bet when it checks: it folds to aggression too often, so small c-bets print.")
    if lab in ("maniac", "loose shover", "tight shover") or s["shv"] >= .05:
        tips.append("Tighten up and call its shoves with strong pairs and big aces; let it bluff into you.")
    if "limper" in lab or s["limp"] > .3:
        tips.append("Isolate its limps with a raise in position; it rarely re-raises.")
    if of_n < 15:
        tips.append("3-bet read: sample too small (its open was re-raised only %d times)." % of_n)
    elif of_f / of_n >= .6:
        tips.append("When its open is 3-bet it folds %d/%d: 3-bet its opens lighter." % (of_f, of_n))
    elif of_f / of_n <= .35:
        tips.append("When its open is 3-bet it folds only %d/%d: 3-bet it for value, not as a bluff." % (of_f, of_n))
    else:
        tips.append("When its open is 3-bet it folds %d/%d: no strong 3-bet edge either way." % (of_f, of_n))
    if cb > .7:
        tips.append("It c-bets %d%% of flops: float or check-raise its continuation bets." % round(cb * 100))
    if af > .55 and ftb >= .3:
        tips.append("Very aggressive after the flop: trap with strong hands and let it bet.")
    if lab == "loose-aggressive":
        tips.append("Loose-aggressive and winning: avoid marginal spots out of position and call its bets lighter with top pair.")
    if lab == "tight-aggressive" and not tips:
        tips.append("Tight-aggressive: respect its raises, steal when it folds the blinds, and avoid paying off big river bets.")
    if lab == "tight-passive" or lab == "loose-passive":
        tips.append("Passive: bet for value relentlessly and fold when it suddenly raises.")
    if not tips:
        tips.append("Solid, balanced stats: play standard and avoid big bluffs without a read.")
    return out[0] + " " + " ".join(tips[:4])


bots = []
for nm, o in allS.items():
    if nm == ME: continue
    s = summarize(o)
    lab = style(s)
    s.update(n=nm, sty=lab, t=sorted(set(appear[nm])), note=note(nm, s, lab))
    bots.append(s)
bots.sort(key=lambda b: -b["bb100"])

# ---------------------------------------------------------------- hand tags / curation
def tags(h, n, focus, names):
    """Factual descriptors only (no EV judgement)."""
    F = facts(h, n); out = []
    r = h["results"][focus]
    if r <= -800: out.append("large losing pot")
    if r >= 800: out.append("large winning pot")
    if F["pf_raises"] >= 3: out.append("4-bet+ pot")
    elif F["pf_raises"] == 2: out.append("3-bet pot")
    if F["pf_allin"]: out.append("all-in preflop")
    if F["post_allin"]: out.append("all-in postflop")
    if F["river_shove"]: out.append("river all-in")
    if F["saw_flop"] >= 3: out.append("multiway")
    if F["showdown"]:
        out.append("showdown")
        if focus in F["alive"] and r < 0: out.append("lost at showdown")
    elif r > 0:
        out.append("won without showdown")
    if sum(F["contrib"]) >= 3000: out.append("big pot")
    return list(dict.fromkeys(out))


def pack_hand(ti, h, focus):
    d = tables[ti]; n = len(d["players"])
    ev = []
    for e in h["events"]:
        t = e[0]
        if t == "post": ev.append(["p", e[1], e[2]])
        elif t == "act": ev.append([e[1], {"fold": "f", "check": "k", "call": "c", "raise": "r"}.get(e[2], e[2]), e[3]])
        elif t == "board": ev.append(["b", e[1][0], "".join(e[2])])
        elif t == "refund": ev.append(["u", e[1], e[2]])
        elif t == "win": ev.append(["w", e[1], e[2], e[3] or ""])
    return dict(t=ti, n=h["n"], bt=h["button"], f=focus,
                ho={k: "".join(v) for k, v in (h.get("hole") or {}).items()},
                sd=h.get("showdown") or {}, bd="".join(h["board"]), ev=ev, r=h["results"],
                g=tags(h, n, focus, d["players"]))


picked = []
used = set()


def add(ti, h, focus):
    k = (ti, h["n"])
    if k in used: return False
    used.add(k); picked.append(pack_hand(ti, h, focus)); return True


for v in sorted(VNAMES):
    pool = []
    for ti, d in enumerate(tables):
        if d["_src"] == "ours" and d["_ver"] == v:
            pool += [(ti, h, d["seat"]) for h in d["hands"]]
    pool.sort(key=lambda x: x[1]["results"][x[2]])
    for ti, h, s in pool[:8]: add(ti, h, s)
    for ti, h, s in pool[::-1][:5]: add(ti, h, s)
    # 3 more teaching hands: biggest pots with a notable tag
    extra = []
    for ti, h, s in pool:
        if (ti, h["n"]) in used: continue
        g = tags(h, len(tables[ti]["players"]), s, tables[ti]["players"])
        if {"river all-in", "all-in postflop", "lost at showdown"} & set(g):
            extra.append((abs(h["results"][s]), ti, h, s))
    extra.sort(key=lambda x: -x[0])
    for _, ti, h, s in extra[:3]: add(ti, h, s)

ext_idx = [i for i, d in enumerate(tables) if d["_src"] == "ext"]
in_ext = {nm for i in ext_idx for nm in tables[i]["players"]} - {ME}
cand = [b for b in bots if b["n"] in in_ext and b["h"] >= 1000]
stars = [b["n"] for b in cand[:2]] + [b["n"] for b in cand[::-1][:2]]
for nm in stars:
    pool = []
    for ti in ext_idx:
        d = tables[ti]
        if nm not in d["players"]: continue
        s = d["players"].index(nm)
        for h in d["hands"]:
            sc = abs(h["results"][s]) + (600 if str(s) in (h.get("showdown") or {}) else 0)
            g = tags(h, len(d["players"]), s, d["players"])
            if "river all-in" in g: sc += 500
            if "all-in postflop" in g: sc += 300
            pool.append((sc, ti, h, s))
    pool.sort(key=lambda x: -x[0])
    k = 0
    for _, ti, h, s in pool:
        if k >= 6: break
        if add(ti, h, s): k += 1

# ---------------------------------------------------------------- sim panel + write
SIM = dict(
    note="Paired duplicate A/B tests, bb/100: G (v7, current upload) vs F and vs E, each over four opponent fields (held-out, real clones, strong, archive field).",
    rows=[["G vs F", 22.4, 31.4, 26.9, 15.8], ["G vs E", 26.7, 25.6, 36.1, 17.8]],
    cols=["held-out", "real clones", "strong", "archive field"],
    )

# every WBot round (practice + live), including tables without a version label
ROUNDS = []
for i, d in enumerate(tables):
    if d["_src"] != "ours": continue
    me = d["seat"]
    tot = sum(h["results"][me] for h in d["hands"])
    ROUNDS.append(dict(r=rnd(d["ref"]), typ=d["_typ"], v=d["_ver"], lab=d["_lab"],
                       h=len(d["hands"]), bb100=round(tot / BB / len(d["hands"]) * 100, 1)))
ROUNDS.sort(key=lambda x: (x["typ"] != "practice", x["r"]))

out = dict(me=ME, bb=BB, T=T, V=versions, B=bots, H=picked, sim=SIM, R=ROUNDS, S=sources)
path = os.path.join(HERE, "data.json")
raw = json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
with open(path, "wb") as f:
    f.write(raw)
with open(path, "rb") as f:
    assert json.loads(f.read().decode("utf-8")) == out, "data.json failed strict UTF-8 round-trip"
if repaired:
    print("repaired names:", ascii(repaired))
print("files %d, distinct tables %d (ours %d, other %d), bots %d, hands %d, size %.1f KB" % (
    len(sources), len(tables), sum(d["_src"] == "ours" for d in tables), sum(d["_src"] == "ext" for d in tables),
    len(bots), len(picked), os.path.getsize(path) / 1024))
for r in ROUNDS:
    if r["v"] is None: print(" unversioned WBot round:", r["typ"], r["r"], r["bb100"])
for v in versions:
    print(" v%d %s bb/100 %+.1f rounds %s" % (v["v"], v["name"], v["bb100"], [(r["r"], r["bb100"]) for r in v["rounds"]]))
print(" stars:", stars)
