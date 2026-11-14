"""Self-play hill climbing over bot parameters.

    python tools/tune.py --iters 40

Keeps tools/params_best.json (+ tools/cands/best.py). Each iteration mutates
1-2 params, builds tools/cands/try.py, plays duplicate A/B vs best in a field
that includes previous bests (a growing league of our own versions), and accepts
only if the combined z-score over two independent seeds clears the bar.
"""
import sys, os, json, random, subprocess, re, shutil, argparse, time, math

T = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(T)
sys.path.insert(0, T)
from build import build  # noqa

BEST_JSON = os.path.join(T, "params_best.json")
LOG = os.path.join(T, "tune_log.txt")

NUM = {  # param: (lo, hi)
    "o_btn": (0.2, 0.7), "o_sb": (0.15, 0.6), "o_co": (0.15, 0.6), "o_hj": (0.1, 0.5), "o_mp": (0.08, 0.4),
    "o_ep": (0.06, 0.32), "steal_k": (0, 4), "iso_mult": (0.4, 1.2), "overlimp": (0, 0.5), "bb_raise": (0.03, 0.2),
    "open_size": (2.0, 4.0), "loose_add": (0, 2.0), "multi_exp": (0.2, 1.2), "real_ip": (0.7, 1.35),
    "real_oop": (0.6, 1.25), "eq_3b": (0.5, 0.72), "eq_4b": (0.52, 0.75), "pri_ftb": (0.2, 0.7),
    "bluff_base": (0.02, 0.5), "bluff_af": (0, 3), "w_r_air": (0.1, 1), "w_r_weak": (0.05, 0.7),
    "w_r_mid": (0.2, 1), "w_b_weak": (0.2, 1), "w_b_mid": (0.4, 1), "c_air": (0.02, 0.5), "c_weak": (0.2, 0.9),
    "c_mid": (0.5, 1), "size_exp": (0.3, 2.0), "chk_ip": (0.8, 1.15), "chk_oop": (0.7, 1.05),
    "bet_margin": (-0.05, 0.1), "call_tax": (-0.05, 0.1), "fold_vs_raise": (0.3, 1.2), "raise_margin": (-0.05, 0.15),
    "pf_call_margin": (-1, 2), "r3_mult": (0.15, 0.7), "call_lo": (0, 1), "shove_spr": (1, 8), "sb_limp": (0, 0.4),
    "pri_vpip": (0.15, 0.5), "pri_pfr": (0.06, 0.3),
}
LISTS = {
    "bet_sizes": [[0.33, 0.6, 1.0], [0.25, 0.5, 0.8, 1.2], [0.5, 1.0], [0.33, 0.66, 1.0, 1.5], [0.4, 0.75], [0.3, 0.6, 1.0, 2.0]],
    "raise_sizes": [[0.7, 1.1], [0.6, 1.0, 1.5], [0.8], [0.5, 1.0], [1.0, 2.0]],
}


def load_best():
    if os.path.exists(BEST_JSON):
        return json.load(open(BEST_JSON))
    import importlib.util
    sp = importlib.util.spec_from_file_location("pb", os.path.join(T, "params_base.py"))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return dict(m.PARAMS)


def mutate(p, rng):
    q = dict(p)
    keys = list(NUM) + list(LISTS)
    k = rng.choice([1, 1, 2])
    changed = []
    for key in rng.sample(keys, k):
        if key in LISTS:
            opts = [o for o in LISTS[key] if o != q.get(key)]
            q[key] = rng.choice(opts)
        else:
            lo, hi = NUM[key]
            v = q[key]
            step = (hi - lo) * rng.choice([-0.25, -0.15, -0.08, 0.08, 0.15, 0.25])
            q[key] = round(min(hi, max(lo, v + step)), 3)
        changed.append("%s:%r->%r" % (key, p.get(key), q[key]))
    return q, changed


def arena(cand, base, tables, seed, field, extra):
    cmd = [sys.executable, os.path.join(T, "arena.py"), cand, base, "--tables", str(tables), "--hands", "300",
           "--seed", str(seed), "--field", field]
    if extra:
        cmd += ["--extra"] + extra
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    out = r.stdout
    m = re.search(r"DIFF\s+([+-][\d.]+) bb/100 \(se ([\d.]+)\)", out)
    if r.returncode != 0 or not m or "invalid" in out or "ERR" in out:
        with open(os.path.join(T, "tune_failures.txt"), "a") as fh:
            fh.write("=== %s rc=%s\nSTDOUT:\n%s\nSTDERR:\n%s\n" % (" ".join(cmd), r.returncode, out[-3000:], r.stderr[-3000:]))
        raise RuntimeError("INVALID arena run (rc=%s); see tools/tune_failures.txt" % r.returncode)
    return float(m.group(1)), float(m.group(2))


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    open(LOG, "a").write(line + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=30)
    ap.add_argument("--tables", type=int, default=96)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--z", type=float, default=2.0)
    ap.add_argument("--fields", default="real,realself,real,mix")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    best = load_best()
    os.makedirs(os.path.join(T, "cands"), exist_ok=True)
    best_path = "tools/cands/best.py"
    build(os.path.join(ROOT, best_path), best)
    league = sorted("tools/cands/" + f for f in os.listdir(os.path.join(T, "cands")) if f.startswith("gen"))
    gen = len(league)
    fields = a.fields.split(",")
    s0 = rng.randrange(10 ** 6)
    for it in range(a.iters):
        q, changed = mutate(best, rng)
        build(os.path.join(ROOT, "tools/cands/try.py"), q)
        extra = league[-3:]
        f1 = fields[it % len(fields)]
        try:
            d1, se1 = arena("tools/cands/try.py", best_path, a.tables, s0 + it * 2, f1, extra)
        except RuntimeError as ex:
            log("it%d INVALID %s -- stopping search" % (it, ex))
            break
        z1 = d1 / se1
        msg = "it%d %s [%s] d=%+.1f se=%.1f z=%.2f" % (it, " ".join(changed), f1, d1, se1, z1)
        if z1 > 1.0:
            f2 = fields[(it + 1) % len(fields)]
            try:
                d2, se2 = arena("tools/cands/try.py", best_path, a.tables, s0 + it * 2 + 1, f2, extra)
            except RuntimeError as ex:
                log("it%d INVALID confirm %s -- stopping search" % (it, ex))
                break
            d = (d1 + d2) / 2
            se = math.sqrt(se1 ** 2 + se2 ** 2) / 2
            msg += " | confirm [%s] d=%+.1f se=%.1f -> comb z=%.2f" % (f2, d2, se2, d / se)
            if d / se > a.z and d2 > 0:
                best = q
                json.dump(best, open(BEST_JSON, "w"), indent=1)
                gen += 1
                gp = "tools/cands/gen%02d.py" % gen
                shutil.copy(os.path.join(ROOT, "tools/cands/try.py"), os.path.join(ROOT, gp))
                shutil.copy(os.path.join(ROOT, "tools/cands/try.py"), os.path.join(ROOT, best_path))
                league.append(gp)
                msg += "  ACCEPT -> " + gp
        log(msg)


if __name__ == "__main__":
    main()
