"""The autonomous lab: keeps researching while it runs, records what it finds,
and turns findings into the next experiments.

Each iteration the scheduler picks ONE task:

  fetch     download new tournament rounds (data/token.txt or $POKER_TOKEN) and
            rebuild the real-field clones the lab trains against
  stress    champion vs tables full of each extreme strategy (always all-in,
            always fold, min-raise, overbet, check-raise, random sizing,
            push/fold). A losing matchup is a finding and queues the knobs that
            counter it (sim/extremes.COUNTER_PARAMS)
  probe     play each extreme strategy as the HERO against the training field:
            if e.g. a shover out-earns the champion, the field folds too much,
            so aggression knobs get priority
  idea      test the next untested idea from research/ideas.json (literature-
            derived features; the file is re-read every iteration, so new ideas
            can be added while the lab runs) through the full gate
  practice  a fresh practice batch so the diagnosis has new champion hands
  rsi       a normal RSI cycle (diagnosis + bandit + stress/probe priorities)
  export    after a promotion: write bot.py, run a tournament-timing check, and
            roll back if it times out or errors

Everything is logged to the database (lab_log, findings, state) and shown on
the dashboard. Stop it cleanly by creating data/STOP.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback

from pokerbot.strategy import PARAM_SPACE
from rsi import loop, registry
from rsi.field import EXTERNAL_TOKENS, fetch, fetch_external, read_token
from sim import arena, opponents
from sim.extremes import COUNTER_PARAMS, EXTREMES
from storage import db as store

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDEAS_FILE = os.path.join(ROOT, "research", "ideas.json")
STOP_FILE = os.path.join(ROOT, "data", "STOP")

LAB_SCHEMA = """
CREATE TABLE IF NOT EXISTS lab_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, iteration INTEGER, task TEXT,
  status TEXT, seconds REAL, summary TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS findings (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, champion TEXT, kind TEXT,
  subject TEXT, value REAL, verdict TEXT, detail TEXT);
"""

# probe hero that out-earns the champion -> what the field is giving away -> knobs to try
PROBE_HINTS = {
    "jammer": [("bluff_freq", 1), ("open_btn", 1), ("threebet_bluff", 1)],
    "pushfold": [("open_co", 1), ("open_btn", 1), ("threebet_value", 1)],
    "minraiser": [("open_size", -1), ("threebet_size", -1)],
    "overbettor": [("bet_value", 1), ("value_river", -1)],
    "checkraiser": [("raise_eq", -1), ("semibluff_eq", -1)],
    "randomsizer": [("bluff_freq", 1)],
    "folder": [("open_ep", -1), ("call_open", -1)],
}

QUICK = {"selection_tables": 24, "selection_hands": 200, "holdout_tables": 64, "holdout_hands": 250,
         "challenger_tables": 24, "challenger_hands": 200, "candidates": 4}


class Lab:
    def __init__(self, db, cfg=None, log=print, fetch_minutes=4, stress_tables=16, stress_hands=300,
                 probe_tables=24, probe_hands=300, practice_tables=128, practice_hands=400, cleanup=True):
        self.db = db
        self.fetch_thread = None
        db.executescript(LAB_SCHEMA)
        if not cleanup:
            self.cfg = dict(loop.DEFAULTS, **(cfg or {}))
            self.log = log
            self.it = 0
            return
        # batches left "running" by a previous lab process that was stopped mid-task
        db.execute("UPDATE tables SET status='abandoned' WHERE status='running' AND batch_id IN "
                   "(SELECT id FROM batches WHERE status='running')")
        db.execute("UPDATE batches SET status='abandoned', finished=? WHERE status='running'", (time.time(),))
        db.commit()
        self.cfg = dict(loop.DEFAULTS, **(cfg or {}))
        self.log = log
        self.fetch_minutes = fetch_minutes
        self.sizes = dict(stress=(stress_tables, stress_hands), probe=(probe_tables, probe_hands),
                          practice=(practice_tables, practice_hands))
        self.it = store.get_state(db, "lab_iteration", 0)

    # ------------------------------------------------------------- helpers
    def state(self, key, default=None):
        return store.get_state(self.db, key, default)

    def set_state(self, key, value):
        store.set_state(self.db, key, value)

    def finding(self, kind, subject, value, verdict, detail=None):
        champ = store.get_state(self.db, "champion_id")
        self.db.execute("INSERT INTO findings(ts, champion, kind, subject, value, verdict, detail) VALUES (?,?,?,?,?,?,?)",
                        (time.time(), champ, kind, subject, value, verdict, json.dumps(detail or {}, default=str)))
        self.db.commit()

    def ideas(self):
        try:
            raw = json.load(open(IDEAS_FILE, encoding="utf-8"))
        except (OSError, ValueError) as e:
            self.log("  [lab] cannot read ideas.json: %s" % e)
            return []
        out = []
        # data-driven ideas first: tendencies mined from the real hands (rsi/insights.py), relative to the champion
        from rsi.propose import move
        champ = registry.champion(self.db)
        for i in self.state("auto_ideas", []):
            if i.get("param") in PARAM_SPACE:
                cand = move(champ["params"], i["param"], i["direction"], i.get("steps", 1))
                if cand is not None:
                    out.append(dict(i, value=cand[i["param"]], id="%s@%s" % (i["id"], champ["id"])))
        for i in raw:
            if not isinstance(i, dict) or not i.get("id"):
                continue
            if isinstance(i.get("params"), dict) and all(k in PARAM_SPACE for k in i["params"]):
                out.append(dict(i, package=True, param="+".join(sorted(i["params"])), value=i["params"]))
            elif i.get("param") in PARAM_SPACE and "value" in i:
                out.append(i)
        # packages first (they survived the temporal overfitting test), then data-driven, then the rest
        out.sort(key=lambda i: 0 if i.get("package") else 1 if i.get("auto") else 2)
        return out

    def pending_idea(self):
        champ = registry.champion(self.db)
        tested = self.state("ideas_tested", {})
        for idea in self.ideas():
            rec = tested.get(idea["id"], {})
            if idea.get("package"):
                if all(champ["params"].get(k) == v for k, v in idea["value"].items()):
                    continue
            elif champ["params"].get(idea["param"]) == idea["value"]:
                continue                                  # already part of the champion
            if rec.get("champion") == champ["id"] or rec.get("attempts", 0) >= 3:
                continue                                  # judged against this champion / given up
            return idea
        return None

    def priorities(self):
        """Knobs suggested by the latest stress and probe findings for this champion."""
        champ = store.get_state(self.db, "champion_id")
        out = []
        for row in self.db.execute("SELECT kind, subject FROM findings WHERE champion=? AND verdict='leak' "
                                   "ORDER BY id DESC LIMIT 20", (champ,)):
            hints = COUNTER_PARAMS.get(row["subject"], []) if row["kind"] == "stress" else PROBE_HINTS.get(row["subject"], [])
            for h in hints:
                if h not in out and h[0] in PARAM_SPACE:
                    out.append(h)
        return out

    # ------------------------------------------------------------ scheduler
    def near_misses(self):
        """Candidates of the current champion that won their holdout on average but were refused: re-test once."""
        champ = registry.champion(self.db)
        done = self.state("lab_retested", {})
        out = []
        for r in self.db.execute("SELECT candidate_id, changed, mean_bb100 FROM trials WHERE stage='holdout' AND "
                                 "parent_id=? AND status='rejected' AND mean_bb100 > 0 ORDER BY mean_bb100 DESC",
                                 (champ["id"],)):
            if done.get(r["candidate_id"], 0) >= 1:
                continue
            cand = store.load_strategy(self.db, r["candidate_id"])
            if cand is None:
                continue
            params = dict(champ["params"], **cand["params"])
            if len([k for k in params if params[k] != champ["params"].get(k)]) != 1:
                continue
            out.append((r["candidate_id"], r["changed"], r["mean_bb100"], params))
        return out

    def choose(self):
        champ = store.get_state(self.db, "champion_id")
        if self.state("lab_export_needed", False):
            return "export"
        last_fetch = self.state("lab_last_fetch", 0)
        thread_alive = self.fetch_thread is not None and self.fetch_thread.is_alive()
        if not thread_alive and (read_token() or os.path.exists(EXTERNAL_TOKENS)) and                 time.time() - last_fetch > self.fetch_minutes * 60:
            return "fetch"
        idea0 = self.pending_idea()
        if idea0 and idea0.get("package"):
            return "idea"                         # whole-style packages first: big jumps escape the local optimum
        if self.near_misses():
            return "retest"
        if self.state("lab_stressed", None) != champ:
            return "stress"
        if self.state("lab_probed", None) != champ:
            return "probe"
        gen = (registry.champion(self.db) or {}).get("generation", 0)
        if gen > 0 and self.state("lab_benchmarked", None) != champ:
            return "benchmark"
        if self.it % 8 == 7:
            return "practice"
        idea = self.pending_idea()
        if idea and (idea.get("auto") or idea.get("package") or self.it % 2 == 1):
            return "idea"
        return "rsi"

    def start_round_fetcher(self, offset=95, retry=150, period=300):
        """Background thread: fetch exactly `offset` s after every round (rounds every `period` s on the clock),
        retrying at `retry` s if our new round is not published yet. Uses its own DB connection."""
        import threading
        db_path = self.db.execute("PRAGMA database_list").fetchone()[2]

        def loop_():
            mine = Lab(store.connect(db_path), self.cfg, self.log, cleanup=False)
            while True:
                now = time.time()
                slot = now - (now % period)
                fire = slot + offset if now < slot + offset else slot + period + offset
                time.sleep(max(1.0, fire - time.time()))
                for attempt in (0, 1):
                    t0 = time.time()
                    try:
                        summary, _ = mine.task_fetch()
                        status = "ok"
                    except Exception:
                        summary, status = traceback.format_exc(limit=4), "error"
                    mine.db.execute("INSERT INTO lab_log(ts, iteration, task, status, seconds, summary, detail) VALUES (?,?,?,?,?,?,?)",
                                    (time.time(), -1, "fetch", status, time.time() - t0, summary, "{}"))
                    mine.db.commit()
                    self.log("[fetch %s] %s" % (time.strftime("%H:%M:%S"), summary))
                    if attempt == 0 and status == "ok" and re.search(r"kaiserbot: 0 new round", summary or "") and read_token():
                        time.sleep(max(1.0, fire - offset + retry - time.time()))
                        continue
                    break

        self.fetch_thread = threading.Thread(target=loop_, daemon=True)
        self.fetch_thread.start()

    def run(self, hours=None, max_iterations=None):
        start = time.time()
        if read_token() or os.path.exists(EXTERNAL_TOKENS):
            self.start_round_fetcher()
        n = 0
        while True:
            if os.path.exists(STOP_FILE):
                self.log("[lab] STOP file found; exiting")
                os.remove(STOP_FILE)
                break
            if hours is not None and time.time() - start > hours * 3600:
                break
            if max_iterations is not None and n >= max_iterations:
                break
            task = self.choose()
            self.set_state("lab_status", {"task": task, "since": time.time(), "iteration": self.it, "pid": os.getpid()})
            t0 = time.time()
            try:
                summary, detail = getattr(self, "task_" + task)()
                status = "ok"
            except Exception:
                summary, detail, status = "crashed", {"traceback": traceback.format_exc(limit=10)}, "error"
                self.log(detail["traceback"])
            dt = time.time() - t0
            self.db.execute("INSERT INTO lab_log(ts, iteration, task, status, seconds, summary, detail) VALUES (?,?,?,?,?,?,?)",
                            (time.time(), self.it, task, status, dt, summary, json.dumps(detail or {}, default=str)))
            self.db.commit()
            self.log("[lab] #%d %s (%s, %.0fs): %s" % (self.it, task, status, dt, summary))
            self.it += 1
            n += 1
            self.set_state("lab_iteration", self.it)
            if status == "error":
                time.sleep(5)
        self.set_state("lab_status", {"task": "stopped", "since": time.time(), "iteration": self.it})

    # ---------------------------------------------------------------- tasks
    def task_fetch(self):
        ok, line = fetch() if read_token() else (False, "no own token")
        ext = fetch_external()
        self.set_state("lab_last_fetch", time.time())
        # public standings: every team's bot version -> confirmed uploads (rsi/standings.py)
        uploads = []
        try:
            from rsi import standings
            uploads = standings.snapshot(self.db)
            for u in uploads:
                self.finding("upload", u["name"], u["to"], "info", u)
        except Exception as e:
            self.log("  [lab] standings snapshot failed: %s" % e)
        from rsi.field import profiles
        from rsi import insights
        prs = [p for p in profiles() if not p["self"]]
        new = [l for l in [line] + [e[1] for e in ext] if re.search(r": [1-9]\d* new round", l or "")]
        if new:
            self.finding("field", "update", len(prs), "info", {"lines": new})
        # re-mine the field's tendencies and refresh the data-driven ideas
        tend = insights.tendencies()
        for k, v in tend.items():
            if v["rate"] is not None:
                self.finding("tendency", k, round(100 * v["rate"], 1), "info", {"n": v["n"]})
        auto = insights.ideas(tend)
        self.set_state("auto_ideas", auto)
        # ground truth: our REAL results per uploaded version (the sim can be optimistic; this is what counts)
        import glob as _glob
        per = {}
        for f in _glob.glob(os.path.join(ROOT, "hands", "*.json")):
            try:
                r = json.load(open(f, encoding="utf-8")).get("round") or {}
            except (OSError, ValueError):
                continue
            if "version" in r and "bb100" in r:
                per.setdefault(r["version"], []).append(r["bb100"])
        for v, xs in sorted(per.items()):
            self.finding("real", "upload v%s" % v, round(sum(xs) / len(xs), 1), "ok" if sum(xs) > 0 else "leak",
                         {"rounds": len(xs), "per_round": [round(x, 1) for x in xs]})
        ext_txt = "; ".join("%s: %s" % (t, l.split(";")[0].split(":")[-1].strip()) for t, l in ext)
        up_txt = ", ".join("%s v%s->v%s" % (u["name"], u["from"], u["to"]) for u in uploads)
        return "%s | external: %s | %d bots profiled | %d data-driven ideas | uploads: %s" % (
            line.split(";")[0], ext_txt or "none", len(prs), len(auto), up_txt or "none"), {"ok": ok, "tendencies": tend,
                                                                                         "uploads": uploads}

    def _table_jobs(self, kind, hero, specs_for_seed, seeds, hands, note):
        bid = store.new_batch(self.db, kind, len(seeds), hands, note)
        jobs = [arena.make_job("%s-%d-b%d-%s" % (kind, s, bid, hero["strategy_id"]), bid, s, hands, hero,
                               specs_for_seed(s), record=False, config=self.cfg["table_config"],
                               fixed_iters=self.cfg["hero_iters"], opp_iters=self.cfg["opp_iters"]) for s in seeds]
        return bid, jobs

    def _bb100(self, results):
        ok = [r for r in results if not r.get("error")]
        chips = sum(r.get("hero_ev_chips", r["hero_chips"]) for r in ok)
        hands = sum(r["hands"] for r in ok)
        return chips / 20.0 / max(1, hands) * 100

    def task_stress(self):
        champ = registry.champion(self.db)
        hero = registry.spec(champ)
        tables, hands = self.sizes["stress"]
        jobs, groups = [], {}
        for name in EXTREMES:
            seeds = registry.fresh_seeds(self.db, tables)
            bid, js = self._table_jobs("stress", dict(hero, strategy_id=champ["id"]),
                                       lambda s, n=name: [{"kind": "extreme", "name": n}] * 7, seeds, hands, "vs %s" % name)
            groups[name] = (bid, {j["table_id"] for j in js})
            jobs += js
        res = arena.run_batch(jobs, self.db, workers=self.cfg["workers"])
        out, leaks = {}, []
        for name, (bid, ids) in groups.items():
            store.finish_batch(self.db, bid)
            v = self._bb100([r for r in res if r.get("table_id") in ids])
            out[name] = round(v, 1)
            verdict = "leak" if v < 0 else "ok"
            if verdict == "leak":
                leaks.append(name)
            self.finding("stress", name, round(v, 1), verdict, {"tables": tables, "hands": hands})
        self.set_state("lab_stressed", champ["id"])
        return ("leaks vs " + ", ".join(leaks) if leaks else "beats every extreme") + " | " + \
            ", ".join("%s %+.0f" % kv for kv in out.items()), out

    def task_probe(self):
        champ = registry.champion(self.db)
        tables, hands = self.sizes["probe"]
        seeds = registry.fresh_seeds(self.db, tables)
        mix = loop.training_mix(self.cfg["field_share"])
        league = registry.league(self.db)
        heroes = [dict(registry.spec(champ), strategy_id=champ["id"])] + \
                 [{"kind": "extreme", "name": n, "strategy_id": "probe-" + n} for n in EXTREMES]
        bid = store.new_batch(self.db, "probe", len(seeds) * len(heroes), hands, "extreme heroes vs field")
        jobs = []
        for s in seeds:
            opps = opponents.lineup(s, 7, league=league, mix=mix)
            for h in heroes:
                jobs.append(arena.make_job("probe-%d-b%d-%s" % (s, bid, h["strategy_id"]), bid, s, hands, h, opps,
                                           record=False, config=self.cfg["table_config"],
                                           fixed_iters=self.cfg["hero_iters"], opp_iters=self.cfg["opp_iters"]))
        res = arena.run_batch(jobs, self.db, workers=self.cfg["workers"])
        store.finish_batch(self.db, bid)
        by = {}
        for r in res:
            if not r.get("error"):
                by.setdefault(r["table_id"].rsplit("-b%d-" % bid, 1)[-1], []).append(r)
        base = self._bb100(by.get(champ["id"], []))
        out = {"champion": round(base, 1)}
        better = []
        for n in EXTREMES:
            v = self._bb100(by.get("probe-" + n, []))
            out[n] = round(v, 1)
            verdict = "leak" if v > base else "ok"   # an extreme beating the champion vs this field = untapped edge
            if verdict == "leak":
                better.append(n)
            self.finding("probe", n, round(v, 1), verdict, {"champion_bb100": round(base, 1)})
        self.set_state("lab_probed", champ["id"])
        return ("field is exploitable like: " + ", ".join(better) if better else "no extreme beats the champion") + \
            " | champion %+.0f" % base, out

    def task_benchmark(self):
        """Champion vs the generation-0 baseline on fresh paired tables: the real cumulative gain."""
        champ = registry.champion(self.db)
        base_row = self.db.execute("SELECT id FROM strategies WHERE generation=0 ORDER BY created LIMIT 1").fetchone()
        base = registry.spec(dict(store.load_strategy(self.db, base_row["id"]), params=dict(
            registry.champion(self.db)["params"], **store.load_strategy(self.db, base_row["id"])["params"])))
        tables, hands = self.cfg["holdout_tables"], self.cfg["holdout_hands"]
        seeds = registry.fresh_seeds(self.db, tables)
        bid, jobs = loop._paired_jobs(self.db, "benchmark", seeds, hands, [base, registry.spec(champ)],
                                      registry.league(self.db), loop.training_mix(self.cfg["field_share"]), self.cfg,
                                      record_first=False, note="gen %d vs gen 0" % champ["generation"])
        res = arena.run_batch(jobs, self.db, workers=self.cfg["workers"])
        store.finish_batch(self.db, bid)
        d, h, _ = loop._diffs(res, base_row["id"], champ["id"])
        vals = [v / 20.0 / h * 100 for v in d.values()]
        mean = sum(vals) / max(1, len(vals))
        from rsi.stats import sample_sd
        se = sample_sd(vals) / max(1, len(vals)) ** 0.5 if len(vals) > 1 else 0.0
        self.finding("benchmark", "gen%d_vs_gen0" % champ["generation"], round(mean, 1), "ok" if mean > 0 else "leak",
                     {"se": round(se, 1), "tables": len(vals), "champion": champ["id"]})
        self.set_state("lab_benchmarked", champ["id"])
        return "generation %d vs generation 0: %+.1f bb/100 (se %.1f, %d paired tables)" % (
            champ["generation"], mean, se, len(vals)), {"mean": mean, "se": se}

    def task_idea(self):
        idea = self.pending_idea()
        if not idea:
            return "no pending idea", {}
        champ = registry.champion(self.db)
        params = dict(champ["params"])
        if idea.get("package"):
            params.update(idea["value"])
        else:
            params[idea["param"]] = idea["value"]
        cand = loop.make_candidate(self.db, champ, params, idea["param"],
                                   "idea %s: %s=%s (%s)" % (idea["id"], idea["param"], idea["value"], idea.get("source", "")),
                                   package=bool(idea.get("package")))
        self.log("\n=== idea %s | %s" % (idea["id"], cand["hypothesis"]))
        r = loop.judge(self.db, loop.next_cycle(self.db), champ, cand, self.cfg, self.log, source="idea:" + idea["id"])
        tested = self.state("ideas_tested", {})
        rec = tested.get(idea["id"], {})
        tested[idea["id"]] = {"champion": champ["id"], "attempts": rec.get("attempts", 0) + 1,
                              "result": "promoted" if r["promoted"] else "refused",
                              "mean_bb100": r.get("evidence", {}).get("mean_bb100"), "ts": time.time()}
        self.set_state("ideas_tested", tested)
        self.finding("idea", idea["id"], r.get("evidence", {}).get("mean_bb100") or 0,
                     "promoted" if r["promoted"] else "refused", {"reasons": r.get("reason")})
        if r["promoted"]:
            self.set_state("lab_export_needed", True)
        return "%s -> %s" % (idea["id"], "PROMOTED" if r["promoted"] else "refused (%s)" % ", ".join(r.get("reason") or [])), r

    def task_retest(self):
        cid, changed, mean, params = self.near_misses()[0]
        done = self.state("lab_retested", {})
        done[cid] = done.get(cid, 0) + 1
        self.set_state("lab_retested", done)
        champ = registry.champion(self.db)
        cand = loop.make_candidate(self.db, champ, params, changed,
                                   "re-test %s (holdout %+.1f bb/100 before)" % (changed, mean))
        self.log("=== re-test near-miss %s | %s" % (cid, cand["hypothesis"]))
        r = loop.judge(self.db, loop.next_cycle(self.db), champ, cand, self.cfg, self.log, source="retest")
        if r["promoted"]:
            self.set_state("lab_export_needed", True)
        return "%s -> %s" % (changed, "PROMOTED" if r["promoted"] else "refused (%s)" % ", ".join(r.get("reason") or [])), r

    def task_practice(self):
        champ = registry.champion(self.db)
        tables, hands = self.sizes["practice"]
        seeds = registry.fresh_seeds(self.db, tables)
        mix = loop.training_mix(self.cfg["field_share"])
        league = registry.league(self.db)
        bid = store.new_batch(self.db, "practice", tables, hands, "lab practice, hero %s" % champ["id"])
        jobs = [arena.make_job("practice-%d-b%d" % (s, bid), bid, s, hands, registry.spec(champ),
                               opponents.lineup(s, 7, league=league, mix=mix), config=self.cfg["table_config"],
                               fixed_iters=self.cfg["hero_iters"], opp_iters=self.cfg["opp_iters"]) for s in seeds]
        res = arena.run_batch(jobs, self.db, workers=self.cfg["workers"])
        store.finish_batch(self.db, bid)
        v = self._bb100(res)
        return "champion %+.1f bb/100 (EV-adjusted) over %d tables x %d hands vs the training field" % (v, tables, hands), {}

    def task_rsi(self):
        pri = self.priorities()
        r = loop.run_cycle(self.db, loop.next_cycle(self.db), self.cfg, self.log, extra_priority=pri)
        if r.get("promoted"):
            self.set_state("lab_export_needed", True)
            return "PROMOTED %s" % r["champion"], r
        reason = r.get("reason")
        return "no promotion (%s)" % (", ".join(reason) if isinstance(reason, list) else reason), r

    def task_export(self):
        from export_bot import export
        bot = os.path.join(ROOT, "bot.py")
        backup = os.path.join(ROOT, "data", "bot.previous.py")
        if os.path.exists(bot):
            shutil.copy(bot, backup)
        champ = registry.champion(self.db)
        export(self.db)
        archive = os.path.join(ROOT, "data", "champions")
        os.makedirs(archive, exist_ok=True)
        shutil.copy(bot, os.path.join(archive, "%s_gen%d.py" % (champ["id"], champ["generation"])))
        ok, info = timing_check(bot)
        self.set_state("lab_export_needed", False)
        if not ok:
            if os.path.exists(backup):
                shutil.copy(backup, bot)
            self.finding("timing", champ["id"], 0, "leak", info)
            return "timing check FAILED, bot.py rolled back: %s" % info, info
        self.finding("export", champ["id"], champ["generation"], "ok", info)
        return "bot.py = %s (gen %d); timing ok: %s" % (champ["id"], champ["generation"], info), info


def timing_check(bot_path, hands=300, timeout_ms=25.0):
    # runs while the lab's workers saturate every core, so it checks at the real limit (25 ms)
    """Tournament harness (separate process, real clock) at HALF the real per-decision limit."""
    cmd = [sys.executable, os.path.join(ROOT, "local_sim.py"), bot_path, "--rounds", "1", "--hands", str(hands),
           "--timeout", str(timeout_ms), "--seed", "1"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return False, {"error": "local_sim timed out"}
    for line in r.stdout.splitlines():
        if line.split() and os.path.basename(line.split()[0].replace("\\", "/")) == os.path.basename(bot_path):
            parts = line.split()
            try:
                timeouts, errors = int(parts[3]), int(parts[4])
            except (IndexError, ValueError):
                break
            return timeouts <= 1 and errors == 0, {"timeouts": timeouts, "errors": errors, "limit_ms": timeout_ms}
    return False, {"error": "could not parse local_sim output", "tail": r.stdout[-400:] + r.stderr[-400:]}
