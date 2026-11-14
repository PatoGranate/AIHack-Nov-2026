"""Input manifest: every hand file the scripts read, its SHA-256, account, round, dedup key, and whether it was used.

A table seen by two of our accounts appears twice. The first file in sorted path order is used and the other is
marked as a duplicate. All scripts apply the same rule (dedup key = round ref + ordered seat names).
Writes data/input_manifest.csv and prints a summary.
"""
import csv, hashlib, json, os, platform, sys
import numpy as np
from common import DATA, POKER, hand_files

rows, seen = [], {}
for f in hand_files():
    b = open(f, "rb").read()
    d = json.loads(b.decode("utf-8-sig"))
    key = d["ref"] + " | " + " / ".join(d["players"])
    counted = "practice" not in d["ref"]
    used = counted and key not in seen
    if used:
        seen[key] = f
    rows.append(dict(path=os.path.relpath(f, os.path.dirname(POKER)).replace("\\", "/"), sha256=hashlib.sha256(b).hexdigest(),
                     account=d["players"][d["seat"]], ref=d["ref"], hands=len(d["hands"]),
                     status="used" if used else ("duplicate_of " + os.path.relpath(seen[key], os.path.dirname(POKER)).replace("\\", "/") if counted else "practice_skipped"),
                     dedup_key=key))
with open(os.path.join(DATA, "input_manifest.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
used = [r for r in rows if r["status"] == "used"]
print("python %s, numpy %s, %s" % (platform.python_version(), np.__version__, platform.platform()))
print("hand files read: %d; used (unique counted tables): %d; duplicates: %d; hands used: %d" % (
    len(rows), len(used), sum(r["status"].startswith("duplicate") for r in rows), sum(r["hands"] for r in used)))
by = {}
for r in used:
    by[r["account"]] = by.get(r["account"], 0) + 1
print("used tables by observing account:", by)
