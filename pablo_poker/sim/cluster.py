"""Cluster arena: 100+ tables in play at once, on this machine and any other.

    lab / practice process  =  job server (queues over TCP) + DB writer thread
    worker processes        =  each pulls up to `slots` tables and plays them
                               interleaved, one hand at a time (8 procs x 16
                               slots = 128 tables in play simultaneously)
    remote workers          =  teammates' laptops:  python worker.py --connect HOST:50555 --key SECRET

Throughput scales with total CPU cores across machines; "in flight" scales
with slots. Workers are persistent (no process start-up per batch), check
that their code matches the server's (same strategy, same engine), and a job
whose worker disappears is re-queued after a stall timeout.
"""
import hashlib
import os
import queue
import secrets
import sys
import threading
import time
import traceback
import uuid
from multiprocessing import get_context
from multiprocessing.managers import BaseManager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CODE_FILES = ["pokerbot/strategy.py", "sim/arena.py", "sim/opponents.py", "sim/extremes.py", "sim/statbot.py", "engine/game.py",
              "hands/external/WBot/bot.py", "hands/external/Red/bot.py",
              "engine/cards.py", "examples/starter_bot.py", "examples/random_bot.py", "examples/tight_aggressive.py",
              "examples/calling_station.py"]


def code_sha():
    h = hashlib.sha256()
    for rel in CODE_FILES:
        with open(os.path.join(ROOT, rel), "rb") as f:
            h.update(f.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]


# ------------------------------------------------------------ server side
_JOBS, _RESULTS, _MSGS = queue.Queue(), queue.Queue(), queue.Queue()


def _jobs():
    return _JOBS


def _results():
    return _RESULTS


def _msgs():
    return _MSGS


class _ServerManager(BaseManager):
    pass


_ServerManager.register("jobs", callable=_jobs)
_ServerManager.register("results", callable=_results)
_ServerManager.register("msgs", callable=_msgs)


class _ClientManager(BaseManager):
    pass


_ClientManager.register("jobs")
_ClientManager.register("results")
_ClientManager.register("msgs")


# ------------------------------------------------------------ worker side
def worker_main(address, authkey, slots=16, quiet=True):
    """Pull tables, play them interleaved, push results. Runs until the server goes away."""
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from sim import arena
    mine = code_sha()
    fails = 0
    while True:
        try:
            m = _ClientManager(address=tuple(address), authkey=authkey)
            m.connect()
            jobs, results, msgs = m.jobs(), m.results(), m.msgs()
            fails = 0
        except (OSError, EOFError):
            fails += 1
            if fails > 60:
                return
            time.sleep(2)
            continue
        active = []
        try:
            while True:
                while len(active) < slots:
                    try:
                        item = jobs.get(timeout=1.0) if not active else jobs.get_nowait()
                    except queue.Empty:
                        break
                    tag, job = item
                    if job.get("code") and job["code"] != mine:
                        results.put((tag, {"table_id": job["table_id"], "error":
                                           "code version mismatch (worker %s, server %s): pull the same commit" % (mine, job["code"])}))
                        continue
                    active.append([tag, job, arena.table_steps(job, msgs)])
                for entry in list(active):
                    tag, job, gen = entry
                    try:
                        next(gen)
                    except StopIteration as stop:
                        results.put((tag, stop.value))
                        active.remove(entry)
                    except Exception:
                        results.put((tag, {"table_id": job["table_id"], "error": traceback.format_exc(limit=8)}))
                        active.remove(entry)
        except (OSError, EOFError, ConnectionError):
            time.sleep(2)            # server restarted or gone: reconnect (in-flight tables are re-queued by the server)


# ---------------------------------------------------------------- cluster
class Cluster:
    def __init__(self, db_path=None, workers=None, slots=16, listen=None, authkey=None):
        """listen: None (this machine only) or "0.0.0.0:50555" to accept remote workers."""
        if listen:
            host, port = listen.rsplit(":", 1)
            address = (host, int(port))
            if not authkey:
                raise ValueError("remote workers need a shared key (--key)")
        else:
            address = ("127.0.0.1", 0)
        self.authkey = (authkey or secrets.token_hex(16)).encode() if isinstance(authkey or "", str) else authkey
        self.manager = _ServerManager(address=address, authkey=self.authkey)
        self.server = self.manager.get_server()
        self.address = self.server.address
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.code = code_sha()
        self.db_path = db_path
        self.writer = threading.Thread(target=self._drain, daemon=True)
        self.writer.start()
        n = workers or os.cpu_count() or 2
        ctx = get_context("spawn")
        local_addr = ("127.0.0.1", self.address[1])
        self.procs = [ctx.Process(target=worker_main, args=(local_addr, self.authkey, slots), daemon=True) for _ in range(n)]
        for p in self.procs:
            p.start()
        self.slots = slots

    def _drain(self):
        db = None
        while True:
            msg = _MSGS.get()
            if isinstance(msg, tuple) and msg and msg[0] == "flush":
                msg[1].set()
                continue
            if self.db_path is None:
                continue
            try:
                if db is None:
                    from storage.db import connect
                    db = connect(self.db_path)
                from storage.db import write_message
                write_message(db, msg)
            except Exception:
                traceback.print_exc()

    def run(self, jobs, progress=None, stall_timeout=900):
        # drop anything left over from an abandoned batch
        while True:
            try:
                _JOBS.get_nowait()
            except queue.Empty:
                break
        tag = uuid.uuid4().hex
        pending = {}
        for j in jobs:
            j["code"] = self.code
            pending[j["table_id"]] = j
            _JOBS.put((tag, j))
        results, last = [], time.time()
        while pending:
            try:
                t, res = _RESULTS.get(timeout=1.0)
            except queue.Empty:
                if time.time() - last > stall_timeout:
                    for j in pending.values():          # a worker vanished: give its tables to someone else
                        _JOBS.put((tag, j))
                    last = time.time()
                continue
            if t != tag or res.get("table_id") not in pending:
                continue
            pending.pop(res["table_id"])
            results.append(res)
            last = time.time()
            if res.get("error"):
                print("\n[cluster] table %s failed:\n%s" % (res["table_id"], res["error"][-1500:]))
            if progress:
                progress(len(results), len(jobs), res)
        ev = threading.Event()
        _MSGS.put(("flush", ev))                         # every hand of this batch is in the DB before we return
        ev.wait(120)
        return results


_CLUSTER = None


def get_cluster(db_path=None, workers=None, slots=None, listen=None, authkey=None):
    global _CLUSTER
    if _CLUSTER is None:
        _CLUSTER = Cluster(db_path, workers, slots or int(os.environ.get("POKER_SLOTS", 16)),
                           listen or os.environ.get("POKER_LISTEN"), authkey or os.environ.get("POKER_KEY"))
    elif db_path:
        _CLUSTER.db_path = db_path
    return _CLUSTER
