"""Pre-registered check of the Saturday findings on Sunday's live rounds (written 2026-11-15 before any Sunday data).

Usage (from this folder):  python 06_sunday_check.py <hand-json files or globs> [...]
Self-test on Saturday:     python 06_sunday_check.py --selftest

Inputs: counted (non-practice) WBot tables only, de-duplicated by (round ref, ordered seat names); every file's
SHA256 is printed, and every hand must pass chip conservation (oc_parse.extract). Public actions only.

Pre-registered questions and reading rules (fixed before seeing Sunday data):
A. The WBot-bettor gap. Saturday: opponents folded 12.3 pts less to WBot's first bets than to other bettors' first
   bets at the same tables, stratified by size x street x HU/MW x IP/OOP x preflop-aggressor role
   (01 section 5; table-4 opponents -13.2). FORGE's v2 hero term (logit -0.32) assumes it persists.
   - 90% table-bootstrap CI entirely below 0: the gap persists for the live policy; keep a static hero term.
   - CI includes 0: not shown for the live policy; re-estimate the term from live rounds (FORGE's caveat).
   - CI entirely above -5: materially smaller than Saturday; the Saturday-fitted term over-corrects.
   Fewer than 5 Sunday tables: report only, no reading (one table's SE is several points).
B. Table-4 opponent levels (first-bet fold rate overall, vs others' bets, vs WBot's bets, HU, MW, facing a raise),
   Sunday vs Saturday WBot tables (same composition), with table-bootstrap CIs. Descriptive: a level outside Saturday's CI flags a possible version change;
   it says nothing about profitability.
Writes data/out_06_sunday_check.txt (the self-test writes data/out_06_selftest_saturday.txt).
"""
import glob
import hashlib
import json
import os
import sys

import numpy as np

import oc_parse as P
import oc_stats as S

selftest = sys.argv[1:] == ["--selftest"]
sys.stdout = S.Tee(S.out_path("out_06_selftest_saturday.txt" if selftest else "out_06_sunday_check.txt"))
rng = np.random.default_rng(S.SEED + 8)
HERO = P.HERO
paths = P.GLOBS if selftest else sys.argv[1:]
if not paths:
    raise SystemExit(__doc__)
files = sorted({os.path.abspath(f) for g in paths for f in (glob.glob(g) or [g])})
seen, tables = set(), []
for f in files:
    with open(f, "rb") as fh:
        b = fh.read()
    d = json.loads(b.decode("utf-8-sig"))
    key = d["ref"] + " | " + " / ".join(d["players"])
    if "practice" in d["ref"] or HERO not in d["players"] or key in seen:
        continue
    seen.add(key)
    tables.append((os.path.relpath(f).replace("\\", "/"), hashlib.sha256(b).hexdigest(), d))
print("Pre-registered Sunday check%s (exploratory, public actions only)" % (" - SELF-TEST ON SATURDAY" if selftest else ""))
print("python %s, numpy %s; seed %d; %d table resamples" % (sys.version.split()[0], np.__version__, S.SEED + 8, S.B))
print("%d unique counted WBot tables, %d hands" % (len(tables), sum(len(d["hands"]) for _, _, d in tables)))
for p, h, d in tables:
    print("  %s  %s  %s" % (h[:16], d["ref"], p))
if not tables:
    raise SystemExit("no counted WBot tables in the inputs")
post, _pre, _bot = P.extract(tables)  # validates chip conservation per hand
fb = [r for r in post if r["facing"] == "bet" and r["first"] and r["name"] != HERO]
with open(S.out_path("postflop_context_summary.json"), encoding="utf-8") as fh:
    sat = json.load(fh)

# ---------------------------------------------------------------- A. stratified gap
cell = lambda r: "%s|%s|%s|%s|%s" % (r["size"], r["street"], r["hu"], r["ip"], r["pfr"])
print("\n== A. Fold rate vs WBot's first bets minus vs other bettors' (stratified MH, 90% table-bootstrap CI) ==")
res = {}
for scope, names in (("all opponents", None), ("table-4 opponents", set(P.TABLE4))):
    recs = [dict(r, name="X") for r in fb if names is None or r["name"] in names]
    if not recs:
        print("%-18s no decisions" % scope)
        continue
    cells = sorted({cell(r) for r in recs})
    labs = [c + w for c in cells for w in ("#W", "#O")]
    ts, K, N = S.counts(recs, labs, lambda r: cell(r) + ("#W" if r["bettor"] == HERO else "#O"),
                        lambda r: r["action"] == "fold")["X"]
    allw = np.vstack([np.ones((1, K.shape[0])), S.weights(K.shape[0], S.B, rng)])
    k, n = allw @ K, allw @ N
    kw, nw, ko, no = k[:, 0::2], n[:, 0::2], k[:, 1::2], n[:, 1::2]
    with np.errstate(invalid="ignore", divide="ignore"):
        wmh = nw * no / (nw + no)
        diff = np.nansum(wmh * (kw / nw - ko / no), axis=1) / np.nansum(np.where(nw * no > 0, wmh, 0), axis=1)
    lo, hi = S.ci(diff[1:])
    ref = sat["vs_wbot_stratified"][scope]
    T = len(ts)
    if T < 5:
        verdict = "fewer than 5 tables: report only"
    elif hi < 0:
        verdict = "CI below 0: gap persists" + ("; CI above -5: smaller than Saturday" if lo > -0.05 else "")
    else:
        verdict = "CI includes 0: not shown for this policy; re-estimate from live rounds"
    res[scope] = dict(diff=float(diff[0]), lo=float(lo), hi=float(hi), tables=T, n_wbot=int(N[:, 0::2].sum()),
                      n_others=int(N[:, 1::2].sum()), verdict=verdict)
    print("%-18s %+5.1f [%+5.1f,%+5.1f]  tables=%d  n vs WBot=%d, vs others=%d  | Saturday %+5.1f [%+5.1f,%+5.1f]"
          % (scope, 100 * diff[0], 100 * lo, 100 * hi, T, N[:, 0::2].sum(), N[:, 1::2].sum(),
             100 * ref["diff"], 100 * ref["lo"], 100 * ref["hi"]))
    print("%-18s reading: %s" % ("", verdict))
    if selftest:
        assert abs(diff[0] - ref["diff"]) < 1e-12, "self-test: point estimate differs from 01 section 5"

# ---------------------------------------------------------------- B. table-4 levels
# Reference = Saturday WBot tables only (same table composition as Sunday, where every table has WBot): all-table
# Saturday levels mix in fewer WBot bets, which draw fewer folds, and would flag spurious changes.
print("\n== B. Table-4 opponents: fold rates, this input vs Saturday WBot tables (90% table-bootstrap CI) ==")
print("'vs others' bets' is the cleanest version-change signal: 'all' and 'vs WBot' also move with WBot's own policy.")
BUCKETS = [("all first-bet", lambda r: r["facing"] == "bet" and r["first"]),
           ("vs others' bets", lambda r: r["facing"] == "bet" and r["first"] and r["bettor"] != HERO),
           ("vs WBot's bets", lambda r: r["facing"] == "bet" and r["first"] and r["bettor"] == HERO),
           ("HU", lambda r: r["facing"] == "bet" and r["first"] and r["hu"]),
           ("MW", lambda r: r["facing"] == "bet" and r["first"] and not r["hu"]),
           ("facing a raise", lambda r: r["facing"] == "raise")]


def levels(recs_all):
    out = {}
    for nm in P.TABLE4:
        recs = [r for r in recs_all if r["name"] == nm]
        for lab, keep in BUCKETS:
            g = S.counts([r for r in recs if keep(r)], ["x"], lambda r: "x", lambda r: r["action"] == "fold")
            if nm in g:
                ts, K, N = g[nm]
                pt, draws, _ = S.boot_rates(K, N, rng)
                lo, hi = S.ci(draws)
                out.setdefault(nm, {})[lab] = dict(rate=float(pt[0]), lo=float(lo[0]), hi=float(hi[0]),
                                                   n=int(N.sum()), tables=len(ts))
    return out


sat_tables = [t for t in P.load_tables() if HERO in t[2]["players"]]
sat_post = P.extract(sat_tables)[0]
ref_lv, lv = levels(sat_post), levels(post)
fr = lambda x: "-" if not x else "%2.0f%% [%2.0f,%2.0f] n=%d t=%d" % (100 * x["rate"], 100 * x["lo"], 100 * x["hi"],
                                                                     x["n"], x["tables"])
for nm in P.TABLE4:
    if nm not in lv:
        print("%-24s not seen" % nm)
        continue
    for lab, _ in BUCKETS:
        x, y = lv[nm].get(lab), ref_lv.get(nm, {}).get(lab)
        flag = "  <- outside Saturday CI" if (x and y and x["tables"] >= 3 and not y["lo"] <= x["rate"] <= y["hi"]) else ""
        print("%-24s %-16s %-28s | Saturday %s%s" % (nm, lab, fr(x), fr(y), flag))
        if selftest and x:
            assert x["n"] == y["n"] and abs(x["rate"] - y["rate"]) < 1e-12, (nm, lab)
if not selftest:
    with open(S.out_path("sunday_check_summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dict(inputs=[[p, h] for p, h, _ in tables], gap=res, table4_levels=lv,
                       saturday_wbot_table_levels=ref_lv), fh, indent=1, ensure_ascii=False)
    print("\nwrote data/sunday_check_summary.json")
