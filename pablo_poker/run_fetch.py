"""Only the round-aligned fetcher (real hands + public standings/uploads), without the RSI lab.
Use while bot.py is the v2 engine, so the lab's export step cannot overwrite it.

    python run_fetch.py
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from rsi.lab import Lab  # noqa: E402
from storage import db as store  # noqa: E402

if __name__ == "__main__":
    lab = Lab(store.connect(), {}, cleanup=False)
    print(lab.task_fetch()[0], flush=True)
    lab.start_round_fetcher()
    while True:
        time.sleep(60)
