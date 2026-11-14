"""Parallel arena: run 100+ tables across every CPU core and stream every hand
into the real-time database.

Bots run in-process (no subprocess per seat) with a fixed amount of Monte
Carlo work per decision, so results are repeatable and ~50x faster than the
tournament harness. Use local_sim.py for the exact tournament timing checks.

    jobs = [make_job(...), ...]
    results = run_batch(jobs, db, workers=8, kind="practice")
"""
import multiprocessing as mp
import os
import sys
import threading
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

    def __init__(self, agent, record=False, strategy_id=None, sink=None, ctx=None, dsink=None):
        self.agent = agent
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
               int(delta > 0), end, " ".join(h["acts"]) if h else "", time.time())
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


def run_table(job, queue=None):
    """Play one table. Streams hand rows to `queue` (if given) and returns the result."""
    try:
        return _run_table(job, queue)
    except Exception:
        return {"table_id": job["table_id"], "error": traceback.format_exc(limit=8)}


def _run_table(job, queue):
    n = len(job["opponents"]) + 1
    hs = job["hero_seat"]
    specs = list(job["opponents"])
    specs.insert(hs, job["hero"])
    buf = []
    ctx = {"batch_id": job["batch_id"], "table_id": job["table_id"]}

    def flush():
        if queue is not None and buf:
            queue.put({"type": "hands", "rows": list(buf)})
            buf.clear()

    def sink(row):
        buf.append(row)
        if len(buf) >= FLUSH_EVERY:
            flush()

    dbuf = []

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
        if i == hs:
            agent = opponents.make(spec, seat_seed, fixed_iters=job["fixed_iters"])
        else:
            agent = opponents.make(spec, seat_seed, fixed_iters=job["opp_iters"])
        is_hero = i == hs
        players.append(SeatPlayer(agent, record=is_hero and job["record"],
                                  strategy_id=spec.get("strategy_id") or opponents.label(spec),
                                  sink=sink, ctx=ctx, dsink=dsink if is_hero and job.get("decisions") else None))
    labels = [opponents.label(s) for s in specs]
    if queue is not None:
        queue.put({"type": "table_start", "table_id": job["table_id"], "batch_id": job["batch_id"],
                   "seed": job["seed"], "n_seats": n, "hands": job["hands"], "hero_seat": hs, "lineup": labels})
    res = FixedHandsTable(players, hands=job["hands"], config=job["config"], seed=job["seed"]).play()
    flush()
    dflush()
    seats = [(job["table_id"], i, labels[i], specs[i].get("strategy_id") or labels[i], res["chips"][i], res["hands"],
              round(players[i].max_ms, 3), players[i].errors) for i in range(n)]
    if queue is not None:
        queue.put({"type": "table_end", "table_id": job["table_id"], "seats": seats})
    return {"table_id": job["table_id"], "seed": job["seed"], "hero_seat": hs, "chips": res["chips"],
            "hero_chips": res["chips"][hs], "hands": res["hands"], "labels": labels,
            "hero_errors": players[hs].errors, "hero_max_ms": players[hs].max_ms}


# -------------------------------------------------------------- batches
def _init_worker(root):
    if root not in sys.path:
        sys.path.insert(0, root)


def _work(args):
    job, queue = args
    return run_table(job, queue)


def run_batch(jobs, db=None, workers=None, progress=None):
    """Run jobs on a process pool. With `db`, every hand streams into it live."""
    from storage.db import write_message
    workers = workers or max(1, (os.cpu_count() or 2))
    results = []
    if workers == 1 and db is None:
        for i, job in enumerate(jobs):
            results.append(run_table(job))
            if progress:
                progress(i + 1, len(jobs), results[-1])
        return results
    mgr = mp.Manager()
    queue = mgr.Queue() if db is not None else None
    writer = None
    if db is not None:
        def drain():
            while True:
                msg = queue.get()
                if msg is None:
                    break
                try:
                    write_message(db, msg)
                except Exception:
                    traceback.print_exc()
        writer = threading.Thread(target=drain, daemon=True)
        writer.start()
    try:
        with mp.Pool(workers, initializer=_init_worker, initargs=(ROOT,)) as pool:
            for i, res in enumerate(pool.imap_unordered(_work, [(j, queue) for j in jobs])):
                if res.get("error"):
                    print("\n[arena] table %s failed:\n%s" % (res["table_id"], res["error"]))
                results.append(res)
                if progress:
                    progress(i + 1, len(jobs), res)
    finally:
        if writer is not None:
            queue.put(None)
            writer.join()
        mgr.shutdown()
    return results
