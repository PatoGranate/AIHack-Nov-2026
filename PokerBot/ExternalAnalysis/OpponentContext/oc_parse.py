"""Opponent-context audit: input loading and decision extraction (public actions only; no hidden cards are used).

Inputs: the same committed hand archives as the Saturday post-mortem (SaturdayRealRounds of our three accounts).
Counted rounds only (refs without "practice"). Tables seen by more than one account are de-duplicated by
(round ref, ordered seat names); the first file in sorted path order is used. `load_tables()` checks the result
against the post-mortem manifest (`SaturdayFieldPostmortem/data/input_manifest.csv`) and fails if they differ.

Event semantics (checked per hand by `_replay`): "raise" amounts are the street total the actor raises TO,
"call" amounts are the chips added, "refund" returns an uncalled excess. Every hand must satisfy
results[s] == wins[s] - (contributions[s] - refunds[s]).
"""
import csv
import glob
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
POKER = os.path.dirname(os.path.dirname(HERE))  # PokerBot/
GLOBS = [
    os.path.join(POKER, "Hand_data", "SaturdayRealRounds", "*.json"),
    os.path.join(POKER, "Hand_data", "ExternalTeamData", "*", "SaturdayRealRounds", "*.json"),
]
PM_MANIFEST = os.path.join(os.path.dirname(HERE), "SaturdayFieldPostmortem", "data", "input_manifest.csv")

TABLE4 = ["Resonance Qt", "Anker Batteries", "Chinese people can fly", "GamesGone", "Poke", "Anton", "YSL_TWIZZY"]
STRONG = ["Gherkers", "Attention Is All In", "AAST"]
HERO = "WBot"

# Bet-size buckets: aggressor's added chips / pot before the action (the bot's own size definition).
SIZE_EDGES = [0.0, 0.40, 0.75, 1.10, 1e9]
SIZE_LABELS = ["<40%", "40-75%", "75-110%", ">110%"]
# Preflop first-in open size, in big blinds (raise-to amount).
OPEN_EDGES = [0.0, 2.6, 3.1, 4.1, 1e9]
OPEN_LABELS = ["<=2.5bb", "2.6-3.0bb", "3.1-4.0bb", ">4bb"]


def bucket(x, edges, labels):
    for i in range(len(labels)):
        if edges[i] <= x < edges[i + 1]:
            return labels[i]
    return labels[-1]


def position(seat, button, n):
    """Seat label relative to the button: BTN, SB, BB, EP (first 1-2 after BB), MP/HJ, CO."""
    p = (seat - button) % n
    if p == 0:
        return "BTN"
    if p == 1:
        return "SB"
    if p == 2:
        return "BB"
    if p == n - 1:
        return "CO"
    if p == n - 2:
        return "HJ"
    return "EP"


def load_tables():
    """Return [(path, sha256, dict)] for unique counted tables, sorted by path; verified against the PM manifest."""
    files = sorted(f for g in GLOBS for f in glob.glob(g))
    seen, out = set(), []
    for f in files:
        with open(f, "rb") as fh:
            b = fh.read()
        d = json.loads(b.decode("utf-8-sig"))
        if "practice" in d["ref"]:
            continue
        key = d["ref"] + " | " + " / ".join(d["players"])
        if key in seen:
            continue
        seen.add(key)
        out.append((os.path.relpath(f, os.path.dirname(POKER)).replace("\\", "/"), hashlib.sha256(b).hexdigest(), d))
    if not os.path.isfile(PM_MANIFEST):
        raise SystemExit("required post-mortem input manifest is missing: " + PM_MANIFEST)
    with open(PM_MANIFEST, encoding="utf-8-sig", newline="") as fh:
        used = [r for r in csv.DictReader(fh) if r["status"] == "used"]
    pm = {r["path"]: r["sha256"].lower() for r in used}
    if len(pm) != len(used):
        raise SystemExit("duplicate used paths in the post-mortem input manifest")
    mine = {p: digest for p, digest, _ in out}
    if pm.keys() != mine.keys():
        raise SystemExit("input set differs from the post-mortem manifest: %d vs %d files" % (len(mine), len(pm)))
    mismatches = [p for p in mine if mine[p] != pm[p]]
    if mismatches:
        raise SystemExit("input SHA256 differs from the post-mortem manifest: " + ", ".join(sorted(mismatches)))
    return out


def _replay(h, n):
    """Walk one hand. Yields (event, state) for every 'act' event; validates chip conservation at the end."""
    bets = [0] * n
    contrib = [0] * n
    folded = [False] * n
    street = "preflop"
    cur = 0
    nraise = 0
    acted = set()  # seats that acted on the current bet level
    for e in h["events"]:
        k = e[0]
        if k == "post":
            bets[e[1]] += e[2]
            contrib[e[1]] += e[2]
            cur = max(cur, bets[e[1]])
        elif k == "board":
            street = e[1]
            bets = [0] * n
            cur = 0
            nraise = 0
            acted = set()
        elif k == "refund":
            contrib[e[1]] -= e[2]
            bets[e[1]] -= e[2]
        elif k == "act":
            yield e, dict(street=street, bets=list(bets), contrib=list(contrib), folded=list(folded),
                          cur=cur, nraise=nraise, pot=sum(contrib))
            s, a, amt = e[1], e[2], e[3]
            if a == "call":
                bets[s] += amt
                contrib[s] += amt
            elif a == "raise":
                contrib[s] += amt - bets[s]
                bets[s] = amt
                cur = amt
                nraise += 1
            elif a == "fold":
                folded[s] = True
    wins = [0] * n
    for e in h["events"]:
        if e[0] == "win":
            wins[e[1]] += e[2]
    if any(h["results"][s] != wins[s] - contrib[s] for s in range(n)):
        raise ValueError("chip conservation failed in hand %s" % h["n"])


def extract(tables):
    """Return (postflop, preflop, botstat) decision lists.

    postflop: one record per postflop decision with chips to call (fold/call/raise), with context.
    preflop: one record per first response to a first-in open (non-opener) and per opener's response to a 3-bet.
    botstat: per (table, seat) the G/N bot's own `faced`/`ffold` counters, replicated from its _learn().
    """
    post, pre, bot = [], [], []
    for ti, (path, _sha, d) in enumerate(tables):
        names = d["players"]
        n = len(names)
        rnd = int(d["ref"].split("/r")[-1])
        bcount = {s: [0, 0] for s in range(n)}
        for h in d["hands"]:
            bb = h["bb"]
            btn = h["button"]
            start = h["start_stacks"]
            order = {s: (s - btn - 1) % n for s in range(n)}  # postflop acting order
            # per-street trackers
            street = None
            agg = None          # (seat, size, nraise) of the last aggressor on this street
            responded = set()   # seats that already responded to the current street's first bet
            callers = 0         # calls of the current bet level
            pf_opener = None
            pf_open_bb = None
            pf_limpers = 0
            pf_resp = set()
            pf_cold = 0
            pf_3b = None
            pf_opener_resp = False
            pf_last = None      # last preflop raiser (the preflop aggressor)
            for e, st in _replay(h, n):
                s, a, amt = e[1], e[2], e[3]
                if st["street"] != street:
                    street = st["street"]
                    agg, responded, callers = None, set(), 0
                to_call = st["cur"] - st["bets"][s]
                stack_left = start[s] - st["contrib"][s]
                live = sum(1 for x in range(n) if not st["folded"][x])
                if street == "preflop":
                    pos = position(s, btn, n)
                    if st["nraise"] == 1 and s != pf_opener and s not in pf_resp and to_call > 0 and a != "check":
                        pre.append(dict(t=ti, rnd=rnd, n=n, name=names[s], kind="vs_open", pos=pos,
                                        opener_pos=position(pf_opener, btn, n), opener=names[pf_opener],
                                        open_bb=pf_open_bb, size=bucket(pf_open_bb, OPEN_EDGES, OPEN_LABELS),
                                        limped=pf_limpers > 0, cold=min(pf_cold, 2), action=a))
                        pf_resp.add(s)
                        if a == "call":
                            pf_cold += 1
                    if st["nraise"] == 2 and s == pf_opener and not pf_opener_resp and to_call > 0:
                        pre.append(dict(t=ti, rnd=rnd, n=n, name=names[s], kind="open_vs_3bet", pos=pos,
                                        three_by=names[pf_3b], ip=order[s] > order[pf_3b], action=a))
                        pf_opener_resp = True
                    if a == "raise":
                        pf_last = s
                        if st["nraise"] == 0:
                            pf_opener, pf_open_bb = s, amt / float(bb)
                        elif st["nraise"] == 1:
                            pf_3b = s
                    elif a == "call" and st["nraise"] == 0:
                        pf_limpers += 1
                else:
                    # bot's own counter: every postflop fold/call/raise while a bet is outstanding (cur > 0)
                    if st["cur"] > 0 and a in ("fold", "call", "raise"):
                        bcount[s][0] += 1
                        bcount[s][1] += a == "fold"
                    if to_call > 0 and a in ("fold", "call", "raise") and agg is not None:
                        aseat, asize, araise = agg
                        post.append(dict(
                            t=ti, rnd=rnd, n=n, hand=h["n"], name=names[s], street=street,
                            facing="bet" if araise == 1 else "raise",
                            first=s not in responded,
                            size=bucket(asize, SIZE_EDGES, SIZE_LABELS), size_x=asize,
                            hu=live == 2, live=live, callers=min(callers, 2),
                            ip=order[s] > order[aseat], bettor=names[aseat],
                            pfr=("resp" if s == pf_last else "bettor" if aseat == pf_last else "none"),
                            allin=to_call >= stack_left, action=a))
                        if araise == 1:
                            responded.add(s)
                    if a == "raise":
                        agg = (s, (amt - st["bets"][s]) / float(max(1, st["pot"])), st["nraise"] + 1)
                        callers = 0
                    elif a == "call":
                        callers += 1
        for s in range(n):
            bot.append(dict(t=ti, rnd=rnd, name=names[s], faced=bcount[s][0], ffold=bcount[s][1]))
    return post, pre, bot
