"""Round-aligned data pipeline for the v2/v3 engine (no old lab, which would overwrite bot.py):

  every round (+95 s): fetch our hands + WBot/Red feeds + public standings/uploads
  whenever new hands land: rebuild data/v3_model.json (recency-weighted field model:
  size->strength tables, fold curves, per-bot profiles and fingerprints) and
  re-export bot.py with it, so the uploadable bot always carries the freshest model

    python run_fetch.py
"""
import glob
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from rsi.lab import Lab  # noqa: E402
from storage import db as store  # noqa: E402


def hands_signature():
    fs = glob.glob(os.path.join(ROOT, "hands", "*.json")) + glob.glob(os.path.join(ROOT, "hands", "external", "**", "*.json"),
                                                                     recursive=True)
    return len(fs), max([os.path.getmtime(f) for f in fs] or [0])


def refresh():
    from export_v2 import PARAMS_FILE, export
    from tools.build_v3_model import OUT, build
    m = build()
    tmp = OUT + ".tmp"
    json.dump(m, open(tmp, "w"), indent=0, sort_keys=True)
    os.replace(tmp, OUT)
    params = json.load(open(PARAMS_FILE)) if os.path.exists(PARAMS_FILE) else {}
    out, size = export(params)
    print("[model %s] rebuilt from rounds up to %s (%d bots) -> bot.py re-exported (%d KB)" % (
        time.strftime("%H:%M:%S"), m["latest_round"], len(m["bots"]), size // 1024), flush=True)


if __name__ == "__main__":
    lab = Lab(store.connect(), {}, cleanup=False)
    print(lab.task_fetch()[0], flush=True)
    lab.start_round_fetcher()
    sig = None
    while True:
        s = hands_signature()
        if s != sig:
            time.sleep(5)            # let the fetch finish writing
            try:
                refresh()
            except Exception as e:  # never let a bad file stop the pipeline
                print("[model] rebuild failed: %r" % (e,), flush=True)
            sig = hands_signature()
        time.sleep(20)
