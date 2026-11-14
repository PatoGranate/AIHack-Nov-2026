"""Strategy registry (adapted from lab/registry.py): the champion pointer, the
lineage of every parameter set, the self-play league and fresh seeds.

All of it lives in the same SQLite database as the hands, so the dashboard and
the RSI loop see one consistent picture.
"""
import json
import time

from rsi.gate import sha
from pokerbot.strategy import DEFAULT_PARAMS
from storage import db as store

SEED_BASE = 1_000_000


def strategy_id(params):
    return "s-" + sha(params)[:10]


def ensure_champion(db, params=None):
    cid = store.get_state(db, "champion_id")
    if cid and store.load_strategy(db, cid):
        return cid
    params = dict(params or DEFAULT_PARAMS)
    cid = strategy_id(params)
    store.save_strategy(db, cid, params, None, 0, "game-theory baseline (pokerbot/strategy.py defaults)", "champion")
    db.execute("UPDATE strategies SET status='champion' WHERE id=?", (cid,))
    db.commit()
    store.set_state(db, "champion_id", cid)
    return cid


def champion(db):
    """The champion, with any parameter added to the bot since it was saved filled in with its default."""
    s = store.load_strategy(db, ensure_champion(db))
    s["params"] = dict(DEFAULT_PARAMS, **s["params"])
    for k in ("explore", "mc_iters", "mc_ms"):          # compute settings live in DEFAULT_PARAMS, not in strategies
        s["params"][k] = DEFAULT_PARAMS[k]
    s["params"].pop("explore", None)
    return s


def spec(strategy):
    return {"kind": "strategy", "params": strategy["params"], "strategy_id": strategy["id"]}


def league(db, k=6):
    """Most recent retired champions: the bot's former selves, used as opponents."""
    rows = db.execute("SELECT id FROM strategies WHERE status='retired' ORDER BY created DESC LIMIT ?", (k,)).fetchall()
    return [spec(store.load_strategy(db, r["id"])) for r in reversed(rows)]


def promote(db, cycle, old, new, gate_record):
    db.execute("UPDATE strategies SET status='retired' WHERE id=?", (old["id"],))
    db.execute("UPDATE strategies SET status='champion' WHERE id=?", (new["id"],))
    db.execute("INSERT INTO promotions(at, cycle, from_id, to_id, gate) VALUES (?,?,?,?,?)",
               (time.time(), cycle, old["id"], new["id"], json.dumps(gate_record)))
    db.commit()
    store.set_state(db, "champion_id", new["id"])


def fresh_seeds(db, n):
    """Seeds that no table has ever used: each holdout is judged on new deals."""
    start = store.get_state(db, "seed_counter", SEED_BASE)
    store.set_state(db, "seed_counter", start + n)
    return list(range(start, start + n))


def seeds_unused(db, seeds):
    q = "SELECT COUNT(*) FROM tables WHERE seed IN (%s)" % ",".join("?" * len(seeds))
    return db.execute(q, seeds).fetchone()[0] == 0
