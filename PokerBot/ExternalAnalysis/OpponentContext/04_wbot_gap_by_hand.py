"""Does the 'opponents fold less to WBot's bets' gap grow during a round? (exploratory)

Bots receive no seat names, so any opponent adaptation to WBot must be learned within the 1,000-hand round. If the gap
is caused by adaptation it should be small early and grow; if it is already full-size in the first hands, it more
likely comes from where/what WBot bets (spot selection) or from fixed opponent logic. Public actions only.
Same stratified Mantel-Haenszel difference as 01 section 5, by hand-number quarter. Writes data/out_04_wbot_gap_by_hand.txt.
"""
import sys

import numpy as np

import oc_parse as P
import oc_stats as S

sys.stdout = S.Tee(S.out_path("out_04_wbot_gap_by_hand.txt"))
rng = np.random.default_rng(S.SEED + 4)
tables = P.load_tables()
post, _pre, _bot = P.extract(tables)
HERO = P.HERO
hero_tables = {ti for ti, (_, _, d) in enumerate(tables) if HERO in d["players"]}
fb = [r for r in post if r["facing"] == "bet" and r["first"] and r["t"] in hero_tables and r["name"] != HERO]
QUART = [(1, 250), (251, 500), (501, 750), (751, 1000)]
print("Opponents' fold rate vs WBot's bets minus vs other bettors' bets, by hand-number quarter (54 WBot tables)")
print("stratified by size x street x HU/MW x IP/OOP x preflop-aggressor role; 90% table-bootstrap CI\n")
cell = lambda r: "%s|%s|%s|%s|%s" % (r["size"], r["street"], r["hu"], r["ip"], r["pfr"])
for scope, names in (("all opponents", None), ("table-4 opponents", set(P.TABLE4))):
    print(scope)
    for lo_h, hi_h in QUART:
        recs = [dict(r, name="X") for r in fb if lo_h <= r["hand"] <= hi_h and (names is None or r["name"] in names)]
        cells = sorted({cell(r) for r in recs})
        labs = [c + w for c in cells for w in ("#W", "#O")]
        _, K, N = S.counts(recs, labs, lambda r: cell(r) + ("#W" if r["bettor"] == HERO else "#O"),
                           lambda r: r["action"] == "fold")["X"]
        allw = np.vstack([np.ones((1, K.shape[0])), S.weights(K.shape[0], S.B, rng)])
        k, n = allw @ K, allw @ N
        kw, nw, ko, no = k[:, 0::2], n[:, 0::2], k[:, 1::2], n[:, 1::2]
        with np.errstate(invalid="ignore", divide="ignore"):
            wmh = nw * no / (nw + no)
            diff = np.nansum(wmh * (kw / nw - ko / no), axis=1) / np.nansum(np.where(nw * no > 0, wmh, 0), axis=1)
            rw = K[:, 0::2].sum() / N[:, 0::2].sum()
            ro = K[:, 1::2].sum() / N[:, 1::2].sum()
        dlo, dhi = S.ci(diff[1:])
        print("  hands %4d-%4d: vs WBot %2.0f%% (n=%d), vs others %2.0f%% (n=%d), stratified diff %+5.1f [%+5.1f,%+5.1f]"
              % (lo_h, hi_h, 100 * rw, N[:, 0::2].sum(), 100 * ro, N[:, 1::2].sum(), 100 * diff[0], 100 * dlo, 100 * dhi))
    print()
