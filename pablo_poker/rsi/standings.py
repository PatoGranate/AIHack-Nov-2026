"""Public standings -> confirmed uploads and per-round results for EVERY team.

The tournament site's standings page polls a public endpoint
(poker.imperialaihack.com/pokerbots/api/public) that lists each team's
current bot version, chips, hands, rounds and timeouts. The lab snapshots it
on every fetch:

  - a change of a team's version number is a confirmed new upload (the only
    sure proof that a bot changed); it is stored as an upload event and lets
    rsi/evolution.py split each bot's history into versions
  - differences between snapshots give every team's result per round, even
    for teams we never sat with

    python -m rsi.standings            take a snapshot now and print recent uploads
"""
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

URL = "https://poker.imperialaihack.com/pokerbots/api/public"

SCHEMA = """
CREATE TABLE IF NOT EXISTS standings (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, phase TEXT, played INTEGER,
  name TEXT, version INTEGER, rounds INTEGER, hands INTEGER, chips INTEGER, bb100 REAL, timeouts INTEGER);
CREATE INDEX IF NOT EXISTS standings_name ON standings(name, played);
CREATE TABLE IF NOT EXISTS uploads (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, name TEXT, from_version INTEGER,
  to_version INTEGER, after_round INTEGER);
"""


def fetch_public(timeout=20):
    req = urllib.request.Request(URL, headers={"User-Agent": "pokerbots-kit/1.0", "Cache-Control": "no-store"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def snapshot(db, data=None):
    """Store one snapshot (only rows that changed). Returns the list of new upload events."""
    db.executescript(SCHEMA)
    data = data or fetch_public()
    sat = data.get("saturday") or {}
    phase, played = data.get("phase"), int(sat.get("played") or 0)
    rows = sat.get("standings") or []
    now = time.time()
    events = []
    for r in rows:
        name, ver = r.get("name"), int(r.get("version") or 0)
        last = db.execute("SELECT played, version, rounds FROM standings WHERE name=? ORDER BY id DESC LIMIT 1", (name,)).fetchone()
        if last is not None and last[1] != ver:
            db.execute("INSERT INTO uploads(ts, name, from_version, to_version, after_round) VALUES (?,?,?,?,?)",
                       (now, name, last[1], ver, played))
            events.append({"name": name, "from": last[1], "to": ver, "after_round": played})
        if last is None or last[0] != played or last[1] != ver or last[2] != r.get("rounds"):
            db.execute("INSERT INTO standings(ts, phase, played, name, version, rounds, hands, chips, bb100, timeouts) "
                       "VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (now, phase, played, name, ver, r.get("rounds"), r.get("hands"), r.get("chips"), r.get("bb100"),
                        r.get("timeouts")))
    db.commit()
    return events


def version_by_round(db):
    """{name: {round_number: version that played it}} from the snapshots.

    An upload plays from the next round, so round N is credited to the version
    seen in the last snapshot taken before round N was played (played < N);
    with no such snapshot, the first one after it."""
    db.executescript(SCHEMA)
    out = {}
    snaps = {}
    for name, played, ver in db.execute("SELECT name, played, version FROM standings ORDER BY id"):
        snaps.setdefault(name, []).append((played, ver))
    for name, ss in snaps.items():
        top = max(p for p, _ in ss)
        first = min(p for p, _ in ss)          # before our first snapshot the version is unknown
        m = {}
        for n in range(max(1, first), top + 1):
            before = [v for p, v in ss if p < n]
            after = [v for p, v in ss if p >= n]
            m[n] = before[-1] if before else after[0]
        out[name] = m
    return out


def round_results(db):
    """{name: {round_number: bb/100 in that round}} from consecutive snapshots (only gaps of one round)."""
    db.executescript(SCHEMA)
    out = {}
    prev = {}
    for name, played, chips, hands in db.execute("SELECT name, played, chips, hands FROM standings ORDER BY id"):
        p = prev.get(name)
        if p and played == p[0] + 1 and hands > p[2]:
            out.setdefault(name, {})[played] = (chips - p[1]) / 20.0 / (hands - p[2]) * 100
        prev[name] = (played, chips, hands)
    return out


def recent_uploads(db, limit=30):
    db.executescript(SCHEMA)
    return [dict(zip(("ts", "name", "from", "to", "after_round"), r)) for r in
            db.execute("SELECT ts, name, from_version, to_version, after_round FROM uploads ORDER BY id DESC LIMIT ?", (limit,))]


if __name__ == "__main__":
    from storage import db as store
    db = store.connect()
    ev = snapshot(db)
    print("snapshot stored; %d new upload(s) since the last snapshot" % len(ev))
    for e in recent_uploads(db, 15):
        print("  %s  %-26s v%s -> v%s (after round %s)" % (time.strftime("%H:%M", time.localtime(e["ts"])), e["name"],
                                                          e["from"], e["to"], e["after_round"]))
