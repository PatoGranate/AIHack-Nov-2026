"""Paired benchmark of v2-engine parameter sets on the data-driven fields, with the hero's playing style.

    python tools/bench2.py VARIANTS.json [tables] [hands]          env: FIELDS=A,B  SEED0=...

Fields (sim/fieldbot.py clones of every real bot, absolute hand-strength selection):
  A  no adaptation: the clones answer every bettor alike (folds a bit too much vs a 95% bettor)
  B  adaptation calibrated on the real answers to our bots (tools/calib_adapt.py) plus trapping
Reality sat between the two for the live bot, so a change must hold up in both.
Style columns: bet when checked to (flop/turn/river), first-in open %, 3-bet %, won at showdown %,
bb/100 from showdown pots / pots won without showdown / hands ending preflop, stack showdowns per 1000 hands.
"""
import json
import multiprocessing as mp
import os
import statistics as st
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_FIELD = [None]


def style(log, hs, n):
    S = dict(fb=[0, 0], tb=[0, 0], rb=[0, 0], rfi=[0, 0], tb3=[0, 0], wsd=[0, 0], fr=[0, 0], sd=0.0, nsd=0.0, pf=0.0, big=0)
    for h in log:
        res = h["end"][hs] - h["stacks"][hs]
        street, bets, nraise, opened, pfagg, alive, inv = "preflop", [0] * n, 0, False, None, set(range(n)), 0
        saw = False
        for e in h["events"]:
            if e[0] == "post":
                bets[e[1]] = e[2]
                if e[1] == hs:
                    inv += e[2]
            elif e[0] == "board":
                street, bets = e[1], [0] * n
                if hs in alive:
                    saw = True
            elif e[0] == "act":
                _, s, a, amt = e
                cur = max(bets)
                add = amt - bets[s] if a == "raise" else (amt if a == "call" else 0)
                if s == hs:
                    inv += add
                    if street == "preflop":
                        if nraise == 0 and not opened and a in ("fold", "call", "raise"):
                            S["rfi"][0] += 1
                            S["rfi"][1] += a == "raise"
                        if nraise == 1 and s != pfagg and a in ("fold", "call", "raise"):
                            S["tb3"][0] += 1
                            S["tb3"][1] += a == "raise"
                    elif cur == 0 and a in ("check", "raise"):
                        k = street[0] + "b"
                        S[k][0] += 1
                        S[k][1] += a == "raise"
                    elif street == "flop" and a in ("fold", "call", "raise"):
                        S["fr"][0] += 1
                        S["fr"][1] += a == "raise"
                if street == "preflop":
                    if a == "raise":
                        nraise += 1
                        pfagg = s
                        opened = True
                    elif a == "call":
                        opened = True
                if a == "fold":
                    alive.discard(s)
                if a == "raise":
                    bets[s] = amt
                else:
                    bets[s] += add
        sd = h.get("showdown") or {}
        if not saw:
            S["pf"] += res
        elif str(hs) in sd and len(sd) > 1 or (hs in sd and len(sd) > 1):
            S["sd"] += res
            S["wsd"][0] += 1
            S["wsd"][1] += res > 0
            S["big"] += inv >= 1000
        else:
            S["nsd"] += res
    return S


def one(job):
    field, seed, name, params, hands = job
    import sim.fieldbot as fb
    os.environ["FB_ADAPT"] = "off" if field == "A" else os.path.join(ROOT, "data", "field_adapt.json")
    fb.reset_state()
    fb.model()
    _FIELD[0] = field
    from sim import arena, opponents
    from engine import FixedHandsTable
    opps = opponents.lineup(seed, 7, mix=fb.mix("recent"))
    hs = seed % 8
    specs = list(opps)
    specs.insert(hs, {"kind": "v2", "params": dict(params, max_sims=500, max_ms=500.0, hard_ms=2000.0, bank_s=1e9)})
    players = []
    for i, spec in enumerate(specs):
        agent = opponents.make(spec, seed * 31 + i * 1009 + 7)
        players.append(arena.SeatPlayer(agent, record=False, strategy_id="x"))
    res = FixedHandsTable(players, hands=hands, config={"betting": "no_limit", "raise_cap": 0}, seed=seed, record=True).play()
    return field, seed, name, res["chips"][hs] / 20.0 / hands * 100, style(res["log"], hs, len(specs))


def fmt(S, H):
    p = lambda k: 100.0 * S[k][1] / max(1, S[k][0])   # noqa: E731
    b = lambda k: S[k] / 20.0 / H * 100                # noqa: E731
    return "bet %2.0f/%2.0f/%2.0f fR %2.0f open %2.0f 3b %4.1f wsd %2.0f | sd %+5.1f nsd %+5.1f pf %+5.1f | big %4.1f" % (
        p("fb"), p("tb"), p("rb"), p("fr"), p("rfi"), p("tb3"), p("wsd"), b("sd"), b("nsd"), b("pf"), S["big"] * 1000.0 / H)


if __name__ == "__main__":
    variants = json.load(open(sys.argv[1]))
    T = int(sys.argv[2]) if len(sys.argv) > 2 else 48
    H = int(sys.argv[3]) if len(sys.argv) > 3 else 600
    fields = os.environ.get("FIELDS", "A,B").split(",")
    seed0 = int(os.environ.get("SEED0", 910000))
    jobs = [(f, seed0 + s, n, p, H) for f in fields for s in range(T) for n, p in variants.items()]
    out, sty = {}, {}
    with mp.Pool(max(2, mp.cpu_count() - 1)) as pool:
        for f, seed, n, bb, S in pool.imap_unordered(one, jobs, chunksize=1):
            out.setdefault((f, seed), {})[n] = bb
            agg = sty.setdefault((f, n), None)
            if agg is None:
                sty[(f, n)] = S
            else:
                for k, v in S.items():
                    if isinstance(v, list):
                        agg[k][0] += v[0]
                        agg[k][1] += v[1]
                    else:
                        agg[k] += v
    names = list(variants)
    for f in fields:
        rows = [v for (ff, _), v in out.items() if ff == f and len(v) == len(names)]
        print("\nfield %s: %d paired tables x %d hands" % (f, len(rows), H))
        for n in names:
            x = [r[n] for r in rows]
            d = [r[n] - r[names[0]] for r in rows]
            print("  %-16s %+6.1f  d %+5.1f (se %.1f) | %s" % (n[:16], st.mean(x), st.mean(d),
                  st.stdev(d) / len(d) ** 0.5 if len(d) > 1 else 0, fmt(sty[(f, n)], H * len(rows))))
    print("\nreal live bot (r038-053): bet 97/92/80 open 35 3b 4.6 wsd 45 | sd -1.3 nsd +19.0 pf -6.8 | big 18.6 (+10.9)")
    print("real winners           : bet 59/56/44 fR 12 open 24 3b 12.3 wsd 57 | sd +29.7 nsd -1.6 pf -1.5 | big ~10-13 (+26.5)")
