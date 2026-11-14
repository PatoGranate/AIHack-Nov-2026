"""Real-time SQLite database for every game, hand, strategy and RSI decision.

One file (data/poker.db), WAL mode: the arena's single writer thread inserts
while the dashboard, the RSI loop and your own notebooks read concurrently.

Tables
  batches     one launch of N tables (practice, rsi-selection, rsi-holdout, challenger)
  tables      one table = one seed, one lineup, H hands
  seats       final chips per seat (every bot, ours and opponents)
  hands       one row per hand per OUR seat (position, cards, result, flags)
  decisions   optional: one row per decision of OUR seat (state -> action), for RL
  strategies  every parameter set ever created, with lineage (parent, generation)
  trials      every RSI evaluation (selection and holdout), kept forever
  promotions  every champion change and the gate record that allowed it
  state       key/value: champion pointer, holdout seed counter, ...
"""
import json
import os
import sqlite3
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "data", "poker.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS batches (
  id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, note TEXT, started REAL, finished REAL,
  n_tables INTEGER, hands_per_table INTEGER, status TEXT);
CREATE TABLE IF NOT EXISTS tables (
  id TEXT PRIMARY KEY, batch_id INTEGER, seed INTEGER, n_seats INTEGER, hands INTEGER,
  hero_seat INTEGER, lineup TEXT, started REAL, finished REAL, status TEXT);
CREATE TABLE IF NOT EXISTS seats (
  table_id TEXT, seat INTEGER, label TEXT, strategy_id TEXT, chips INTEGER, hands INTEGER,
  max_ms REAL, errors INTEGER, PRIMARY KEY (table_id, seat));
CREATE TABLE IF NOT EXISTS hands (
  id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id INTEGER, table_id TEXT, hand_no INTEGER,
  seat INTEGER, strategy_id TEXT, position TEXT, hole TEXT, board TEXT, delta INTEGER,
  vpip INTEGER, pfr INTEGER, saw_flop INTEGER, showdown INTEGER, won INTEGER,
  end_street TEXT, actions TEXT, ts REAL);
CREATE INDEX IF NOT EXISTS hands_strategy ON hands(strategy_id);
CREATE INDEX IF NOT EXISTS hands_batch ON hands(batch_id);
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id INTEGER, table_id TEXT, hand_no INTEGER, seat INTEGER,
  strategy_id TEXT, street TEXT, position TEXT, hole TEXT, board TEXT, pot INTEGER, to_call INTEGER,
  stack INTEGER, n_live INTEGER, raises INTEGER, action TEXT, amount INTEGER);
CREATE INDEX IF NOT EXISTS decisions_hand ON decisions(table_id, hand_no, seat);
CREATE TABLE IF NOT EXISTS strategies (
  id TEXT PRIMARY KEY, params TEXT, parent_id TEXT, generation INTEGER, created REAL,
  hypothesis TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS trials (
  id INTEGER PRIMARY KEY AUTOINCREMENT, cycle INTEGER, parent_id TEXT, candidate_id TEXT,
  changed TEXT, stage TEXT, n INTEGER, mean_bb100 REAL, ci_low REAL, ci_high REAL,
  status TEXT, detail TEXT, created REAL);
CREATE TABLE IF NOT EXISTS promotions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL, cycle INTEGER, from_id TEXT, to_id TEXT, gate TEXT);
CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT);
"""


def connect(path=None, readonly=False):
    path = path or DEFAULT_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if readonly:
        db = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30, check_same_thread=False)
    else:
        db = sqlite3.connect(path, timeout=30, check_same_thread=False)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=NORMAL")
        db.executescript(SCHEMA)
        db.commit()
    db.row_factory = sqlite3.Row
    return db


# ------------------------------------------------------------------ state
def get_state(db, key, default=None):
    row = db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else default


def set_state(db, key, value):
    db.execute("INSERT INTO state(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
               (key, json.dumps(value)))
    db.commit()


# ------------------------------------------------------------- batches
def new_batch(db, kind, n_tables, hands, note=""):
    cur = db.execute("INSERT INTO batches(kind, note, started, n_tables, hands_per_table, status) VALUES (?,?,?,?,?,?)",
                     (kind, note, time.time(), n_tables, hands, "running"))
    db.commit()
    return cur.lastrowid


def finish_batch(db, batch_id, status="done"):
    db.execute("UPDATE batches SET finished=?, status=? WHERE id=?", (time.time(), status, batch_id))
    db.commit()


# ------------------------------------------------------------- writing
def write_message(db, msg):
    """Apply one message from an arena worker (see sim/arena.py)."""
    kind = msg["type"]
    if kind == "table_start":
        db.execute("INSERT OR REPLACE INTO tables(id, batch_id, seed, n_seats, hands, hero_seat, lineup, started, status) "
                   "VALUES (?,?,?,?,?,?,?,?,?)",
                   (msg["table_id"], msg["batch_id"], msg["seed"], msg["n_seats"], msg["hands"],
                    msg.get("hero_seat"), json.dumps(msg["lineup"]), time.time(), "running"))
    elif kind == "hands":
        db.executemany(
            "INSERT INTO hands(batch_id, table_id, hand_no, seat, strategy_id, position, hole, board, delta, vpip, pfr, "
            "saw_flop, showdown, won, end_street, actions, ts) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            msg["rows"])
    elif kind == "decisions":
        db.executemany(
            "INSERT INTO decisions(batch_id, table_id, hand_no, seat, strategy_id, street, position, hole, board, pot, "
            "to_call, stack, n_live, raises, action, amount) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", msg["rows"])
    elif kind == "table_end":
        db.execute("UPDATE tables SET finished=?, status='done' WHERE id=?", (time.time(), msg["table_id"]))
        db.executemany("INSERT OR REPLACE INTO seats(table_id, seat, label, strategy_id, chips, hands, max_ms, errors) "
                       "VALUES (?,?,?,?,?,?,?,?)", msg["seats"])
    db.commit()


# ---------------------------------------------------------- strategies
def save_strategy(db, sid, params, parent_id=None, generation=0, hypothesis="", status="candidate"):
    db.execute("INSERT OR IGNORE INTO strategies(id, params, parent_id, generation, created, hypothesis, status) "
               "VALUES (?,?,?,?,?,?,?)",
               (sid, json.dumps(params, sort_keys=True), parent_id, generation, time.time(), hypothesis, status))
    db.commit()


def load_strategy(db, sid):
    row = db.execute("SELECT * FROM strategies WHERE id=?", (sid,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["params"] = json.loads(d["params"])
    return d
