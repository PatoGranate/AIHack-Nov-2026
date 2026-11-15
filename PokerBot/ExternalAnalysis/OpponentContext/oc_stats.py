"""Table-bootstrap rates and between-opponent heterogeneity, shared by the audit scripts (numpy only).

Rate intervals resample whole tables (1,000-hand rounds). The heterogeneity null is independent-binomial
conditional on observed counts; unit_tau uses binomial variances and a heuristic variance decomposition.
Those components do not preserve shared-table dependence or table overdispersion and are exploratory.
"""
import os
import sys

import numpy as np

SEED = 20261115  # bootstrap seed (not an arena seed)
B = 2000
SIM = 300        # null simulations for heterogeneity calibration
SIM_B = 200      # bootstrap draws inside each null simulation


class Tee:
    """Mirror stdout into a file so every committed output is exactly what the script printed."""

    def __init__(self, path):
        self.f = open(path, "w", encoding="utf-8", newline="\n")
        self.o = sys.stdout

    def write(self, s):
        self.f.write(s)
        self.o.write(s)

    def flush(self):
        self.f.flush()
        self.o.flush()


def counts(recs, labels, key, event, min_tables=1):
    """Per name: (table ids, K[T, L], N[T, L]) for the records' buckets. key(r) -> label or None."""
    lab = {l: i for i, l in enumerate(labels)}
    acc = {}
    for r in recs:
        b = key(r)
        if b is None:
            continue
        d = acc.setdefault(r["name"], {})
        row = d.setdefault(r["t"], [[0] * len(labels), [0] * len(labels)])
        row[1][lab[b]] += 1
        row[0][lab[b]] += event(r)
    out = {}
    for nm, d in acc.items():
        if len(d) < min_tables:
            continue
        ts = sorted(d)
        out[nm] = (np.array(ts), np.array([d[t][0] for t in ts], float), np.array([d[t][1] for t in ts], float))
    return out


def weights(T, b, rng):
    """b x T matrix of table-resample multiplicities."""
    idx = rng.integers(0, T, size=(b, T))
    W = np.zeros((b, T))
    np.add.at(W, (np.repeat(np.arange(b), T), idx.ravel()), 1)
    return W


def boot_rates(K, N, rng, b=B):
    """Point rate, bootstrap draws (b x L) of the pooled rate per bucket (nan where a draw has no decisions)."""
    W = weights(K.shape[0], b, rng)
    k, n = W @ K, W @ N
    with np.errstate(invalid="ignore", divide="ignore"):
        draws = k / n
    tot_n = N.sum(0)
    with np.errstate(invalid="ignore", divide="ignore"):
        point = K.sum(0) / tot_n
    return point, draws, W


def ci(draws, lo=5, hi=95):
    """90% percentile interval over bootstrap draws (ignoring nan)."""
    return np.nanpercentile(draws, lo, axis=0), np.nanpercentile(draws, hi, axis=0)


def logit(k, n):
    p = (k + 0.5) / (n + 1.0)
    return np.log(p / (1 - p))


def dl_tau2(y, v):
    """DerSimonian-Laird between-unit variance, Q statistic and random-effects mean (weights 1/(v + tau^2))."""
    w = 1.0 / v
    mu = np.sum(w * y) / np.sum(w)
    q = float(np.sum(w * (y - mu) ** 2))
    k = len(y)
    c = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    t2 = max(0.0, (q - (k - 1)) / c)
    wr = 1.0 / (v + t2)
    return t2, q, float(np.sum(wr * y) / np.sum(wr))


def _effect_stats(K, N, a, b, w):
    """Per-opponent effect (bucket a minus bucket b) on probability and logit scales for weight matrix w."""
    ka, na, kb, nb = w @ K[:, a], w @ N[:, a], w @ K[:, b], w @ N[:, b]
    with np.errstate(invalid="ignore", divide="ignore"):
        dp = ka / na - kb / nb
    dl = logit(ka, na) - logit(kb, nb)
    return dp, dl


def heterogeneity(groups, a, b=None, min_n=30, min_tables=5, rng=None, null="binomial"):
    """Between-opponent SD of a level (b is None: bucket a) or of a context effect (bucket a minus bucket b).

    Each opponent's estimate and variance come from its own table bootstrap. tau is DerSimonian-Laird. The Q
    statistic is calibrated by simulation: null = every opponent shares the level (or effect), each table keeps
    its real decision counts, outcomes are binomial; the same bootstrap/Q pipeline is re-run on each simulation.
    null="perm" instead shuffles team labels across the real opponent-table rows (each team keeps its number of
    rows of each non-empty-bucket pattern), so every null table keeps its observed overdispersion; teams are
    exchangeable under that null, so for effects it also equalises levels. Returns dict or None when fewer than 4 opponents qualify.
    """
    rng = rng or np.random.default_rng(SEED)
    rows = []
    for nm, (ts, K, N) in groups.items():
        if len(ts) < min_tables or N[:, a].sum() < min_n or (b is not None and N[:, b].sum() < min_n):
            continue
        rows.append((nm, K, N))
    if len(rows) < 4:
        return None

    # Variance floor: binomial variance at the FIELD rate for the opponent's decision count, so a degenerate team
    # (e.g. one that never folds in a bucket, bootstrap variance ~0) cannot take all the weight.
    pf = {j: sum(K[:, j].sum() for _, K, N in rows) / sum(N[:, j].sum() for _, K, N in rows)
          for j in ([a] if b is None else [a, b])}

    def floors(N):
        fp = sum(pf[j] * (1 - pf[j]) / N[:, j].sum() for j in pf)
        fl = sum(1.0 / (N[:, j].sum() * pf[j] * (1 - pf[j])) for j in pf)
        return fp, fl

    def stats(rows_kn, bb):
        yp, vp, yl, vl = [], [], [], []
        for K, N in rows_kn:
            fp, fl = floors(N)
            W = weights(K.shape[0], bb, rng)
            if b is None:
                k, n = W @ K[:, a], W @ N[:, a]
                with np.errstate(invalid="ignore", divide="ignore"):
                    dp = k / n
                dl = logit(k, n)
                pt_p = K[:, a].sum() / N[:, a].sum()
                pt_l = logit(K[:, a].sum(), N[:, a].sum())
            else:
                dp, dl = _effect_stats(K, N, a, b, W)
                one = np.ones((1, K.shape[0]))
                pp, ll = _effect_stats(K, N, a, b, one)
                pt_p, pt_l = pp[0], ll[0]
            yp.append(pt_p)
            vp.append(max(np.nanvar(dp), fp))
            yl.append(pt_l)
            vl.append(max(np.nanvar(dl), fl))
        tp = dl_tau2(np.array(yp), np.array(vp))
        tl = dl_tau2(np.array(yl), np.array(vl))
        return tp, tl, np.array(yp), np.array(vp), np.array(vl)

    (tau2p, qp, mup), (tau2l, ql, mul), yp, vp, vl = stats([(K, N) for _, K, N in rows], B)
    if null == "perm":
        allK = np.concatenate([K for _, K, _ in rows])
        allN = np.concatenate([N for _, _, N in rows])
        owner = np.concatenate([np.full(K.shape[0], i) for i, (_, K, _) in enumerate(rows)])
        used = [a] if b is None else [a, b]
        # permute within strata of rows sharing the same non-empty pattern over the used buckets, so a team never
        # receives only empty rows (e.g. "open by WBot" exists only at WBot tables)
        pattern = (allN[:, used] > 0) @ (2 ** np.arange(len(used)))
        null_q = []
        for _ in range(SIM):
            perm = np.arange(len(owner))
            for s in np.unique(pattern):
                ix = np.flatnonzero(pattern == s)
                perm[ix] = rng.permutation(ix)
            sim = [(allK[perm[owner == i]], allN[perm[owner == i]]) for i in range(len(rows))]
            (_, q, _), (_, q2, _), _, _, _ = stats(sim, SIM_B)
            null_q.append((q, q2))
        null_q = np.array(null_q)
        cw = lambda v: float(np.sum(1.0 / v) - np.sum(1.0 / v ** 2) / np.sum(1.0 / v))  # DL denominator
        return dict(k=len(rows), mean=mup, tau=float(np.sqrt(tau2p)), q=qp, c=cw(vp),
                    p_sim=float((1 + np.sum(null_q[:, 0] >= qp)) / (1 + len(null_q))),
                    q_null_med=float(np.median(null_q[:, 0])),
                    mean_logit=mul, tau_logit=float(np.sqrt(tau2l)), q_logit=ql,
                    c_logit=cw(vl),
                    p_sim_logit=float((1 + np.sum(null_q[:, 1] >= ql)) / (1 + len(null_q))),
                    q_null_med_logit=float(np.median(null_q[:, 1])),
                    names=[r[0] for r in rows], y=yp, se=np.sqrt(vp))
    # Null simulations. Level: one shared rate. Effect: each opponent keeps its own midpoint and the effect is
    # shared, on the probability scale for Q and on the logit scale for Q_logit (two separate null sets).
    sig = lambda x: 1.0 / (1.0 + np.exp(-x))
    null_q = []
    for _ in range(SIM):
        qs = []
        for scale in ("p", "logit") if b is not None else ("p",):
            sim = []
            for nm, K, N in rows:
                Ks = np.zeros_like(K)
                if b is None:
                    Ks[:, a] = rng.binomial(N[:, a].astype(int), mup)
                else:
                    ra, rb = K[:, a].sum() / N[:, a].sum(), K[:, b].sum() / N[:, b].sum()
                    if scale == "p":
                        c = (ra + rb) / 2.0
                        pa, pb = c + mup / 2.0, c - mup / 2.0
                    else:
                        c = (logit(K[:, a].sum(), N[:, a].sum()) + logit(K[:, b].sum(), N[:, b].sum())) / 2.0
                        pa, pb = sig(c + mul / 2.0), sig(c - mul / 2.0)
                    Ks[:, a] = rng.binomial(N[:, a].astype(int), min(max(pa, 0.005), 0.995))
                    Ks[:, b] = rng.binomial(N[:, b].astype(int), min(max(pb, 0.005), 0.995))
                sim.append((Ks, N))
            (_, q, _), (_, q2, _), _, _, _ = stats(sim, SIM_B)
            qs.append(q if scale == "p" else q2)
        null_q.append((qs[0], qs[-1] if b is not None else q2))
    null_q = np.array(null_q)
    return dict(k=len(rows), mean=mup, tau=float(np.sqrt(tau2p)), q=qp,
                p_sim=float((1 + np.sum(null_q[:, 0] >= qp)) / (1 + len(null_q))),
                q_null_med=float(np.median(null_q[:, 0])),
                mean_logit=mul, tau_logit=float(np.sqrt(tau2l)), q_logit=ql,
                p_sim_logit=float((1 + np.sum(null_q[:, 1] >= ql)) / (1 + len(null_q))),
                names=[r[0] for r in rows], y=yp, se=np.sqrt(vp))


def unit_tau(groups, a, min_n=10, rng=None):
    """Between-unit SD where a unit is one opponent at one table (= what an in-round estimate must learn).

    Returns total tau over opponent-table units, and its split into between-team and within-team (table-to-table)
    components, from binomial variances and variance subtraction (not a fitted hierarchical model).
    Calibrated against a binomial null with real per-unit counts; kstar is an approximate prior concentration
    (the exact beta concentration subtracts 1), not an optimized learning parameter.
    """
    rng = rng or np.random.default_rng(SEED)
    k, n, team = [], [], []
    for ti, (nm, (ts, K, N)) in enumerate(groups.items()):
        for t in range(len(ts)):
            if N[t, a] >= min_n:
                k.append(K[t, a])
                n.append(N[t, a])
                team.append(ti)
    k, n, team = np.array(k), np.array(n), np.array(team)
    if len(k) < 20:
        return None
    p = k.sum() / n.sum()

    def tau_total(kk):
        y = kk / n
        v = np.maximum(y * (1 - y), p * (1 - p) * 0.25) / n
        t2, q, mu = dl_tau2(y, v)
        return t2, q

    t2, q = tau_total(k)
    null = np.array([tau_total(rng.binomial(n.astype(int), p))[1] for _ in range(1000)])
    # within-team component: deviations of each unit from its own team's pooled rate
    pt = np.array([k[team == g].sum() / n[team == g].sum() for g in team])
    y = k / n
    v = np.maximum(y * (1 - y), p * (1 - p) * 0.25) / n
    w = 1 / v
    teams = np.unique(team)
    q_w = float(np.sum(w * (y - pt) ** 2))
    df_w = len(y) - len(teams)
    c_w = sum(np.sum(w[team == g]) - np.sum(w[team == g] ** 2) / np.sum(w[team == g]) for g in teams)
    t2_w = max(0.0, (q_w - df_w) / c_w)
    return dict(units=len(k), mean=float(p), median_n=float(np.median(n)), tau=float(np.sqrt(t2)),
                tau_within=float(np.sqrt(t2_w)), tau_between=float(np.sqrt(max(0.0, t2 - t2_w))),
                p_sim=float((1 + np.sum(null >= q)) / (1 + len(null))),
                kstar=float(p * (1 - p) / t2) if t2 > 0 else None)


def fmt_rate(point, lo, hi, n):
    if n == 0 or np.isnan(point):
        return "%-22s" % ("- (n=0)")
    return "%-22s" % ("%2.0f%% [%2.0f,%2.0f] n=%d" % (100 * point, 100 * lo, 100 * hi, n))


def out_path(name):
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)
