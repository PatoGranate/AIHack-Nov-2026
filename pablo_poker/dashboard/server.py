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
    return {"now": now, "total_hands": max_id, "hands_per_sec": recent / 30.0, "batches": batches,
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
    return {"trials": trials, "promotions": promos, "cycles": cycles}


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
        if path in ("/api/live", "/api/rsi"):
            if not os.path.exists(DB_PATH):
                return self._send(200, json.dumps({"empty": True}), "application/json")
            try:
                db = sqlite3.connect("file:%s?mode=ro" % DB_PATH, uri=True, timeout=10)
                db.row_factory = sqlite3.Row
                try:
                    body = live(db) if path == "/api/live" else rsi(db)
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
