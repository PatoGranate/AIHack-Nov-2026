"""Bounded behaviour check: the 7 Sunday clones from one field at one table with a passive observer
(check/fold). Measures realised stats with analyze.analyse. Usage (from PokerBot/):
    python tools/rook_clone_behaviour_check.py <field_dir> <out_dir> [tables=1] [hands=1000]
Same caveats as tools/clone_check.py: observer seat always check/folds, so the table is effectively
7-handed. The button is recorded as 0, so positional stats are not meaningful; VPIP/PFR/3b/AF/FTB are.
"""
import sys, os, json, glob, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kit")); sys.path.insert(0, HERE)
from engine import FixedHandsTable
from engine.players import LocalPlayer
import analyze
field, out = sys.argv[1], sys.argv[2]
T = int(sys.argv[3]) if len(sys.argv) > 3 else 1; N = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
NAMES = ["Poke", "ResonanceQt", "AnkerBatteries", "Chinesepeoplecanfly", "GamesGone", "Anton", "YSLTWIZZY"]
logs = []
class Obs:
    def act(self, s): return {"action": "check"} if s["to_call"] == 0 else {"action": "fold"}
    def on_hand_end(self, sm): logs.append(sm)
def ld(p):
    sp = importlib.util.spec_from_file_location("c_" + os.path.basename(p)[:-3], p); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m.Agent
os.makedirs(out, exist_ok=True)
outs = []
for t in range(T):
    logs.clear()
    pl = [LocalPlayer(Obs)] + [LocalPlayer(ld(os.path.join(field, "r_%s.py" % n))) for n in NAMES]
    FixedHandsTable(pl, hands=N, seed=1000 + t).play()
    hs = []
    for sm in logs:
        ev = []; st = "preflop"
        for h in sm["history"]:
            if h["street"] != st: st = h["street"]; ev.append(["board", st, []])
            if h["action"] in ("small_blind", "big_blind"): continue
            ev.append(["act", h["seat"], h["action"], h["amount"]])
        hs.append({"n": sm["hand_number"], "button": 0, "bb": 20, "hole": {}, "showdown": {}, "board": sm["board"], "events": ev, "results": [0] * 8})
    fn = os.path.join(out, "_bc%d.json" % t); json.dump({"players": ["OBS"] + NAMES, "hands": hs}, open(fn, "w")); outs.append(fn)
S, *_ = analyze.analyse(outs)
for nm in NAMES:
    o = S[nm]; H = o["hands"]
    print("%-20s hands %d vpip %.3f pfr %.3f 3b %.3f limp %.3f af %.3f ftb %.3f" % (nm, H, o["vpip"]/H, o["pfr"]/H, o["3b"]/max(1,o["f_raise"]), o["limp"]/max(1,o["unopened"]), o["pbet"]/max(1,o["pbet"]+o["pcall"]+o["pcheck"]), o["ffold"]/max(1,o["faced"])))
