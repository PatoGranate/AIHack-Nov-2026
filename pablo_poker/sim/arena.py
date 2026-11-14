"""Arena: one table = one seed, one lineup, H hands, bots in-process.

Bots run in-process (no subprocess per seat) with a fixed amount of Monte
Carlo work per decision, so results are repeatable and ~50x faster than the
tournament harness. Use local_sim.py for the exact tournament timing checks.

`table_steps` plays a table as a generator (one hand per step), so a worker
can keep many tables in play at once (sim/cluster.py). Each result carries
the raw chips AND the all-in-EV-adjusted chips (the chance-node part of
AIVAT, Burch et al. 2018): when betting is over before the board is
complete, the hero's result is replaced by its exact expected share over the
remaining cards. Unbiased, and much less noisy.

    jobs = [make_job(...), ...]
    results = run_batch(jobs, db)       # runs on the cluster, streams into the DB
"""
import itertools
import os
import random
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine import FixedHandsTable  # noqa: E402
from sim import opponents  # noqa: E402

START_STACK = 2000
BB = 20
FLUSH_EVERY = 100


def position_name(seat, button, n):
    off = (seat - button) % n
    if off == 0:
        return "BTN"
    if off == 1:
        return "SB"
    if off == 2:
        return "BB"
    from_end = n - off          # 1 = CO, 2 = HJ, 3 = MP
    return {1: "CO", 2: "HJ", 3: "MP"}.get(from_end, "EP")


class SeatPlayer:
    """Engine seat adapter: error-safe, timed, optionally records hero hands."""

    def __init__(self, agent, record=False, strategy_id=None, sink=None, ctx=None, dsink=None, table=None):
        self.agent = agent
        self.table = table          # set for the hero: lets hand_end read the engine's hand record (all hole cards)
        self.ev_chips = 0
        self.record = record
        self.dsink = dsink
        self.strategy_id = strategy_id
        self.sink = sink
        self.ctx = ctx or {}
        self.errors = 0
        self.max_ms = 0.0
        self.seat = None
        self._hand = None

    def start_table(self, seat, info):
        self.seat = seat
        if hasattr(self.agent, "on_table_start"):
            try:
                self.agent.on_table_start(info)
            except Exception:
                self.errors += 1

    def act(self, state):
        t0 = time.perf_counter()
        try:
            out = self.agent.act(state)
        except Exception:
            self.errors += 1
            out = None
        ms = (time.perf_counter() - t0) * 1000
        self.max_ms = max(self.max_ms, ms)
        if self.record:
            h = self._hand
            if h is None or h["n"] != state["hand_number"]:
                h = self._hand = {"n": state["hand_number"], "hole": "".join(state["hole_cards"]),
                                  "pos": position_name(state["seat"], state["button"], len(state["stacks"])),
                                  "acts": []}
            a = (out or {}).get("action") if isinstance(out, dict) else None
            h["acts"].append(state["street"][0] + str(a or "x")[0].upper())
            if self.dsink is not None:
                me = state["seat"]
                amt = out.get("amount") if isinstance(out, dict) else None
                self.dsink((self.ctx.get("batch_id"), self.ctx.get("table_id"), state["hand_number"], me, self.strategy_id,
                            state["street"], h["pos"], h["hole"], "".join(state["board"]), state["pot"], state["to_call"],
                            state["stacks"][me] + state["bets"][me], sum(1 for f in state["folded"] if not f),
                            state["raises_this_street"], str(a), int(amt) if isinstance(amt, (int, float)) else None))
        if isinstance(out, dict):
            return {"action": out.get("action"), "amount": out.get("amount")}
        return out

    def hand_end(self, summary):
        if hasattr(self.agent, "on_hand_end"):
            try:
                self.agent.on_hand_end(summary)
            except Exception:
                pass
        ev = None
        if self.table is not None:
            log = self.table.log
            rec = log[-1] if log and log[-1]["n"] == summary["hand_number"] else None
            if rec is not None:
                try:
                    ev = allin_ev(rec, self.seat, random.Random(summary["hand_number"]))
                except Exception:
                    ev = None
            log.clear()
            raw = summary["stacks"][self.seat] - START_STACK
            self.ev_chips += raw if ev is None else ev
        if not self.record:
            return
        seat = self.seat
        h = self._hand if self._hand and self._hand["n"] == summary["hand_number"] else None
        hist = summary.get("history") or []
        mine = [x for x in hist if x["seat"] == seat and x["action"] not in ("small_blind", "big_blind")]
        vpip = int(any(x["street"] == "preflop" and x["action"] in ("call", "raise") for x in mine))
        pfr = int(any(x["street"] == "preflop" and x["action"] == "raise" for x in mine))
        fold = next((x["street"] for x in mine if x["action"] == "fold"), None)
        showdown = int(str(seat) in (summary.get("shown") or {}))
        board = summary.get("board") or []
        saw_flop = int(len(board) >= 3 and fold != "preflop")
        end = fold or ("showdown" if showdown else ["preflop", "preflop", "preflop", "flop", "turn", "river"][len(board)])
        delta = summary["stacks"][seat] - START_STACK
        pos = h["pos"] if h else ("BB" if any(x["seat"] == seat and x["action"] == "big_blind" for x in hist) else "?")
        row = (self.ctx.get("batch_id"), self.ctx.get("table_id"), summary["hand_number"], seat, self.strategy_id,
               pos, h["hole"] if h else "", "".join(board), delta, vpip, pfr, saw_flop, showdown,
               int(delta > 0), end, " ".join(h["acts"]) if h else "", time.time(), delta if ev is None else ev)
        self.sink(row)


def make_job(table_id, batch_id, seed, hands, hero, opponent_specs, hero_seat=None, record=True,
             config=None, fixed_iters=120, opp_iters=60, decisions=False):
    n = len(opponent_specs) + 1
    if hero_seat is None:
        hero_seat = seed % n
    return {"table_id": table_id, "batch_id": batch_id, "seed": seed, "hands": hands, "hero": hero,
            "opponents": opponent_specs, "hero_seat": hero_seat, "record": record,
            "config": config or {"betting": "no_limit", "raise_cap": 0},
            "fixed_iters": fixed_iters, "opp_iters": opp_iters, "decisions": decisions}


def allin_ev(rec, seat, rng, samples=400):
    """Hero's expected result when the betting ended before the board was complete, else None."""
    sd = rec.get("showdown") or {}
    if str(seat) not in sd or len(sd) < 2:
        return None
    ev = rec["events"]
    last = max(i for i, e in enumerate(ev) if e[0] in ("act", "post"))
    known = 0
    for e in ev[:last + 1]:
        if e[0] == "board":
            known = len(e[2])
    if known >= 5:
        return None
    from pokerbot.strategy import card_int, evaluate
    n = len(rec["stacks"])
    won = [0] * n
    for e in ev:
        if e[0] == "win":
            won[e[1]] += e[2]
    contrib = [rec["stacks"][i] - rec["end"][i] + won[i] for i in range(n)]
    live = [int(s) for s in sd]
    holes = {int(k): [card_int(c) for c in v] for k, v in rec["hole"].items()}
    board = [card_int(c) for c in rec["board"][:known]]
    dead = set(board)
    for v in holes.values():
        dead.update(v)
    deck = [c for c in range(52) if c not in dead]
    need = 5 - known
    if need <= 2:
        runouts = list(itertools.combinations(deck, need))
    else:
        runouts = [rng.sample(deck, need) for _ in range(samples)]
    levels = sorted(set(c for c in contrib if c > 0))
    total = 0.0
    for extra in runouts:
        full = board + list(extra)
        scores = {i: evaluate(holes[i] + full) for i in live}
        prev, mine = 0, 0.0
        for lvl in levels:
            portion = sum(min(c, lvl) - min(c, prev) for c in contrib)
            elig = [i for i in live if contrib[i] >= lvl] or live
            best = max(scores[i] for i in elig)
            ws = [i for i in elig if scores[i] == best]
            if seat in ws:
                mine += portion / len(ws)
            prev = lvl
        total += mine
    return int(round(total / len(runouts) - contrib[seat]))


def table_steps(job, queue=None):
    """Generator: plays one hand per step; its return value is the table result."""
    n = len(job["opponents"]) + 1
    hs = job["hero_seat"]
    specs = list(job["opponents"])
    specs.insert(hs, job["hero"])
    buf, dbuf = [], []
    ctx = {"batch_id": job["batch_id"], "table_id": job["table_id"]}

    def flush():
        if queue is not None and buf:
            queue.put({"type": "hands", "rows": list(buf)})
            buf.clear()

    def sink(row):
        buf.append(row)
        if len(buf) >= FLUSH_EVERY:
            flush()

    def dflush():
        if queue is not None and dbuf:
            queue.put({"type": "decisions", "rows": list(dbuf)})
            dbuf.clear()

    def dsink(row):
        dbuf.append(row)
        if len(dbuf) >= FLUSH_EVERY * 2:
            dflush()

    players = []
    for i, spec in enumerate(specs):
        seat_seed = job["seed"] * 31 + i * 1009 + 7
        agent = opponents.make(spec, seat_seed, fixed_iters=job["fixed_iters"] if i == hs else job["opp_iters"])
        is_hero = i == hs
        players.append(SeatPlayer(agent, record=is_hero and job["record"],
                                  strategy_id=spec.get("strategy_id") or opponents.label(spec),
                                  sink=sink, ctx=ctx, dsink=dsink if is_hero and job.get("decisions") else None))
    labels = [opponents.label(s) for s in specs]
    if queue is not None:
        queue.put({"type": "table_start", "table_id": job["table_id"], "batch_id": job["batch_id"],
                   "seed": job["seed"], "n_seats": n, "hands": job["hands"], "hero_seat": hs, "lineup": labels})
    table = FixedHandsTable(players, hands=job["hands"], config=job["config"], seed=job["seed"], record=True)
    players[hs].table = table
    # --- same sequence as FixedHandsTable.play(), one hand per step
    start = table.cfg["starting_stack"]
    from engine.game import effective_raise_cap
    for seat, p in enumerate(players):
        p.start_table(seat, {"seat": seat, "num_players": n, "format": "fixed_hands", "hands": job["hands"],
                             "starting_stack": start, "stacks_reset_each_hand": True,
                             "small_blind": table.cfg["blinds"][0][0], "big_blind": table.cfg["blinds"][0][1],
                             "betting": table.cfg["betting"], "raise_cap": effective_raise_cap(table.cfg) or None})
    chips = [0] * n
    button = table.rng.randrange(n)
    for hand_no in range(1, job["hands"] + 1):
        table.stacks = [start] * n
        button = (button + 1) % n
        table._play_hand(hand_no, button)
        for i in range(n):
            chips[i] += table.stacks[i] - start
        table.log.clear()
        yield hand_no
    flush()
    dflush()
    seats = [(job["table_id"], i, labels[i], specs[i].get("strategy_id") or labels[i], chips[i], job["hands"],
              round(players[i].max_ms, 3), players[i].errors) for i in range(n)]
    if queue is not None:
        queue.put({"type": "table_end", "table_id": job["table_id"], "seats": seats})
    return {"table_id": job["table_id"], "seed": job["seed"], "hero_seat": hs, "chips": chips,
            "hero_chips": chips[hs], "hero_ev_chips": players[hs].ev_chips, "hands": job["hands"], "labels": labels,
            "hero_errors": players[hs].errors, "hero_max_ms": players[hs].max_ms}


def run_table(job, queue=None):
    """Play one table to the end in this process."""
    try:
        gen = table_steps(job, queue)
        while True:
            next(gen)
    except StopIteration as stop:
        return stop.value
    except Exception:
        return {"table_id": job["table_id"], "error": traceback.format_exc(limit=8)}


def db_path_of(db):
    row = db.execute("PRAGMA database_list").fetchone()
    return row[2] if row else None


def run_batch(jobs, db=None, workers=None, progress=None):
    """Run jobs on the cluster (persistent workers, many tables in flight). With `db`, hands stream into it live."""
    from sim.cluster import get_cluster
    cluster = get_cluster(db_path_of(db) if db is not None else None, workers)
    return cluster.run(jobs, progress=progress)
