"""Bring everything up to date: python tools/refresh_data.py   (token from env POKER_TOKEN, optional)
1) fetch our new rounds (live -> SaturdayRealRounds, practice -> PracticeRounds)
2) pick one file per unique table (ref + roster) across ALL folders
3) refit real clones, 'late' clones (our 8 newest live rounds), held-out field, manifest."""
import os, sys, glob, json, subprocess, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
tok = os.environ.get("POKER_TOKEN")
if tok:
    tmp = "Hand_data/_tmp_fetch"; os.makedirs(tmp, exist_ok=True)
    for f in glob.glob("Hand_data/SaturdayRealRounds/*.json") + glob.glob("Hand_data/PracticeRounds/saturday_practice_*.json"):
        open(os.path.join(tmp, os.path.basename(f)), "w").close()      # mark as already fetched
    subprocess.run([sys.executable, "kit/fetch_hands.py", "--token", tok, "--out", tmp], check=False)
    for f in glob.glob(tmp + "/*.json"):
        if os.path.getsize(f) > 0:
            dst = "Hand_data/PracticeRounds" if "practice" in os.path.basename(f) else "Hand_data/SaturdayRealRounds"
            shutil.move(f, os.path.join(dst, os.path.basename(f))); print("new:", os.path.basename(f))
    shutil.rmtree(tmp, ignore_errors=True)
seen = {}; 
for f in sorted(glob.glob("Hand_data/**/*.json", recursive=True)):
    try:
        d = json.load(open(f, encoding="utf-8"))
        key = (d["ref"], tuple(d["players"]))
    except Exception:
        continue
    seen.setdefault(key, f)
uniq = sorted(seen.values())
live_mine = sorted(glob.glob("Hand_data/SaturdayRealRounds/saturday_r0*.json"))
print("unique tables:", len(uniq), "| our live rounds:", len(live_mine))
subprocess.run([sys.executable, "tools/make_clones.py"] + uniq, check=True, stdout=subprocess.DEVNULL)
# late field: clones fit only on our newest 8 live rounds
sys.path.insert(0, "tools")
from analyze import analyse
S, *_ = analyse(live_mine[-8:])
src = open("tools/make_clones.py", encoding="utf-8").read()
body = src[src.index("for nm, o in S.items():"):src.index('open("tools/opponents/real/weights.txt"')].replace("tools/opponents/real/r_", "tools/opponents/late/l_")
os.makedirs("tools/opponents/late", exist_ok=True)
for f in glob.glob("tools/opponents/late/l_*.py"): os.remove(f)
lines = []
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()): exec(body)
open("tools/opponents/late/list.txt", "w", encoding="utf-8").write("\n".join(x[0] for x in lines))
print("late clones:", len(lines), "from", [os.path.basename(f)[9:13] for f in live_mine[-8:]])
subprocess.run([sys.executable, "tools/build_fields.py"], check=True)
