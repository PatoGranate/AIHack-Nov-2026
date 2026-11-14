"""Live dashboard over the real-time database (standard library only).

    python dashboard/server.py            # http://localhost:8765
    python dashboard/server.py --port 9000 --db data/poker.db

Reads the SQLite file read-only on every request (WAL lets it run while the
arena and the RSI loop write). The page refreshes every 2 seconds.
"""
import argparse
import json
import os
import sqlite3
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
BB = 20
DB_PATH = os.path.join(ROOT, "data", "poker.db")


def q(db, sql, args=()):
    return [dict(r) for r in db.execute(sql, args).fetchall()]


def live(db):
    now = time.time()
    max_id = db.execute("SELECT COALESCE(MAX(id), 0) FROM hands").fetchone()[0]
    recent = db.execute("SELECT COUNT(*) FROM hands WHERE id > ? AND ts > ?", (max_id - 300000, now - 30)).fetchone()[0]
    batches = q(db, "SELECT b.id, b.kind, b.note, b.started, b.finished, b.n_tables, b.hands_per_table, b.status, "
                    "(SELECT COUNT(*) FROM tables t WHERE t.batch_id=b.id AND t.status='done') AS done, "
                    "(SELECT COUNT(*) FROM tables t WHERE t.batch_id=b.id AND t.status='running') AS running "
                    "FROM batches b ORDER BY b.id DESC LIMIT 12")
    champ_id = None
    row = db.execute("SELECT value FROM state WHERE key='champion_id'").fetchone()
    if row:
        champ_id = json.loads(row[0])
    champ = q(db, "SELECT id, generation, params, hypothesis FROM strategies WHERE id=?", (champ_id,))
    strategies = q(db, "SELECT strategy_id, COUNT(*) AS hands, SUM(delta) AS chips, AVG(vpip) AS vpip, AVG(pfr) AS pfr "
                       "FROM (SELECT * FROM hands ORDER BY id DESC LIMIT 200000) GROUP BY strategy_id ORDER BY hands DESC LIMIT 10")
    for s in strategies:
        s["bb100"] = s["chips"] / BB / max(1, s["hands"]) * 100
    positions = []
    if champ_id:
        positions = q(db, "SELECT position, COUNT(*) AS hands, SUM(delta) AS chips FROM "
                          "(SELECT * FROM hands WHERE strategy_id=? ORDER BY id DESC LIMIT 100000) GROUP BY position", (champ_id,))
        for p in positions:
            p["bb100"] = p["chips"] / BB / max(1, p["hands"]) * 100
    # cumulative result of the latest batch that recorded hands
    curve = []
    last = db.execute("SELECT batch_id FROM hands ORDER BY id DESC LIMIT 1").fetchone()
    if last:
        rows = db.execute("SELECT delta FROM hands WHERE batch_id=? ORDER BY id", (last[0],)).fetchall()
        step = max(1, len(rows) // 300)
        cum = 0
        for i, (d,) in enumerate(rows):
            cum += d
            if i % step == 0 or i == len(rows) - 1:
                curve.append([i + 1, round(cum / BB, 1)])
    lineup = q(db, "SELECT label, COUNT(*) AS seats, SUM(chips) AS chips, SUM(hands) AS hands FROM seats "
                   "WHERE table_id IN (SELECT id FROM tables ORDER BY rowid DESC LIMIT 400) GROUP BY label ORDER BY chips DESC")
    for l in lineup:
        l["bb100"] = l["chips"] / BB / max(1, l["hands"]) * 100
    played = db.execute("SELECT COALESCE(SUM(hands), 0) FROM tables WHERE status='done'").fetchone()[0]
    last5 = db.execute("SELECT COALESCE(SUM(hands), 0) FROM tables WHERE status='done' AND finished > ?",
                       (now - 300,)).fetchone()[0]
    in_play = db.execute("SELECT COUNT(*) FROM tables t JOIN batches b ON b.id=t.batch_id "
                         "WHERE t.status='running' AND b.status='running'").fetchone()[0]
    return {"now": now, "total_hands": max_id, "hands_per_sec": recent / 30.0, "batches": batches,
            "hands_played": played, "table_hands_per_sec": last5 / 300.0, "tables_in_play": in_play,
            "champion": champ[0] if champ else None, "strategies": strategies, "positions": positions,
            "curve": curve, "curve_batch": last[0] if last else None, "lineup": lineup}


def rsi(db):
    trials = q(db, "SELECT id, cycle, candidate_id, changed, stage, n, mean_bb100, ci_low, ci_high, status, detail, created "
                   "FROM trials WHERE stage IN ('selection','holdout') ORDER BY id DESC LIMIT 60")
    for t in trials:
        d = json.loads(t.pop("detail") or "{}")
        if t["stage"] == "holdout":
            t["reasons"] = d.get("gate", {}).get("reasons", [])
            t["challenger"] = d.get("evidence", {}).get("challenger_bb100")
    promos = q(db, "SELECT p.id, p.at, p.cycle, p.from_id, p.to_id, s.hypothesis, s.generation FROM promotions p "
                   "LEFT JOIN strategies s ON s.id=p.to_id ORDER BY p.id DESC LIMIT 30")
    cycles = db.execute("SELECT COALESCE(MAX(cycle), 0) FROM trials").fetchone()[0]
    for t in trials:
        t["source"] = "selection" if t["stage"] == "selection" else "rsi"
    srcs = {}
    for (detail, status) in db.execute("SELECT detail, status FROM trials WHERE stage='holdout'"):
        src = (json.loads(detail or "{}").get("source") or "rsi")
        src = "idea" if src.startswith("idea") else src
        srcs.setdefault(src, {"tested": 0, "promoted": 0})
        srcs[src]["tested"] += 1
        srcs[src]["promoted"] += status == "approved"
    # per-trial source for the table
    src_by_id = {r[0]: (json.loads(r[1] or "{}").get("source") or "rsi")
                 for r in db.execute("SELECT id, detail FROM trials WHERE stage='holdout' ORDER BY id DESC LIMIT 60")}
    for t in trials:
        if t["stage"] == "holdout":
            t["source"] = src_by_id.get(t["id"], "rsi")
    funnel = {
        "scored": db.execute("SELECT COUNT(*) FROM trials WHERE stage='selection'").fetchone()[0],
        "holdout": db.execute("SELECT COUNT(*) FROM trials WHERE stage='holdout'").fetchone()[0],
        "promoted": db.execute("SELECT COUNT(*) FROM promotions").fetchone()[0],
    }
    # generation history: baseline + every promotion with the parameter that changed and its evidence
    gens = []
    first = db.execute("SELECT id, created FROM strategies WHERE generation=0 ORDER BY created LIMIT 1").fetchone()
    if first:
        gens.append({"generation": 0, "id": first[0], "at": first[1], "change": "game-theory baseline", "evidence": None})
    for p in db.execute("SELECT p.at, p.from_id, p.to_id, s.generation, s.params, f.params FROM promotions p "
                        "JOIN strategies s ON s.id=p.to_id JOIN strategies f ON f.id=p.from_id ORDER BY p.id").fetchall():
        new, old = json.loads(p[4]), json.loads(p[5])
        changed = [k for k in new if new.get(k) != old.get(k, new.get(k)) and k not in ("explore",)]
        change = ", ".join("%s %s -> %s" % (k, old.get(k, "default"), new[k]) for k in changed) or "parameters filled"
        ev = db.execute("SELECT mean_bb100, ci_low, ci_high, n FROM trials WHERE stage='holdout' AND status='approved' "
                        "AND candidate_id=? ORDER BY id DESC LIMIT 1", (p[2],)).fetchone()
        gens.append({"generation": p[3], "id": p[2], "at": p[0], "change": change,
                     "evidence": {"mean": ev[0], "ci": [ev[1], ev[2]], "tables": ev[3]} if ev else None})
    return {"trials": trials, "promotions": promos, "cycles": cycles, "funnel": funnel, "sources": srcs,
            "generations": gens}


def lab(db):
    def has(t):
        return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None
    st = db.execute("SELECT value FROM state WHERE key='lab_status'").fetchone()
    tested = db.execute("SELECT value FROM state WHERE key='ideas_tested'").fetchone()
    out = {"status": json.loads(st[0]) if st else None, "log": [], "findings": [],
           "ideas_tested": json.loads(tested[0]) if tested else {}}
    if has("lab_log"):
        out["log"] = q(db, "SELECT ts, iteration, task, status, seconds, summary FROM lab_log ORDER BY id DESC LIMIT 25")
    if has("findings"):
        out["findings"] = q(db, "SELECT f.ts, f.kind, f.subject, f.value, f.verdict, f.champion FROM findings f "
                                "JOIN (SELECT kind, subject, MAX(id) AS mid FROM findings GROUP BY kind, subject) g "
                                "ON f.id = g.mid ORDER BY f.kind, f.subject")
    if has("uploads"):
        out["uploads"] = q(db, "SELECT ts, name, from_version, to_version, after_round FROM uploads ORDER BY id DESC LIMIT 25")
        out["upload_counts"] = q(db, "SELECT name, COUNT(*) AS n, MAX(to_version) AS v FROM uploads GROUP BY name ORDER BY n DESC")
    try:
        out["ideas"] = json.load(open(os.path.join(ROOT, "research", "ideas.json"), encoding="utf-8"))
    except (OSError, ValueError):
        out["ideas"] = []
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if path in ("/api/live", "/api/rsi", "/api/lab"):
            if not os.path.exists(DB_PATH):
                return self._send(200, json.dumps({"empty": True}), "application/json")
            try:
                db = sqlite3.connect("file:%s?mode=ro" % DB_PATH, uri=True, timeout=10)
                db.row_factory = sqlite3.Row
                try:
                    body = {"/api/live": live, "/api/rsi": rsi, "/api/lab": lab}[path](db)
                finally:
                    db.close()
                return self._send(200, json.dumps(body, default=str), "application/json")
            except sqlite3.Error as e:
                return self._send(500, json.dumps({"error": str(e)}), "application/json")
        self._send(404, "not found", "text/plain")


def main():
    global DB_PATH
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--db", default=DB_PATH)
    a = ap.parse_args()
    DB_PATH = os.path.abspath(a.db)
    print("dashboard on http://localhost:%d  (db: %s)" % (a.port, DB_PATH))
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
