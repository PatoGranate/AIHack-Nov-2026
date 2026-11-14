"""Play a table of real-opponent clones and print their stats in the same format as analyze.py."""
import sys, os, json, glob, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import FixedHandsTable
from engine.players import LocalPlayer
import importlib.util, analyze
logs = []
class Obs:
    def act(self, s): return {"action": "check"} if s["to_call"] == 0 else {"action": "fold"}
    def on_hand_end(self, sm): logs.append(sm)
files = sorted(glob.glob("tools/opponents/real/r_*.py"))
def ld(p):
    sp = importlib.util.spec_from_file_location(os.path.basename(p)[:-3], p); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m.Agent
hands = []
names_all = []
rng = random.Random(1)
for t in range(6):
    pick = rng.sample(files, 6)
    logs.clear()
    pl = [LocalPlayer(Obs)] + [LocalPlayer(ld(f)) for f in pick]
    FixedHandsTable(pl, hands=600, seed=t).play()
    names = ["WBot"] + [os.path.basename(f)[2:-3] for f in pick]
    hs = []
    for sm in logs:
        ev = []; st = "preflop"
        for h in sm["history"]:
            if h["street"] != st: st = h["street"]; ev.append(["board", st, []])
            if h["action"] in ("small_blind", "big_blind"): continue
            ev.append(["act", h["seat"], h["action"], h["amount"]])
        hs.append({"n": sm["hand_number"], "button": 0, "bb": 20, "hole": {"0": ["2c", "7d"]}, "showdown": {}, "board": sm["board"], "events": ev, "results": [0] * 7})
    json.dump({"players": names, "hands": hs}, open("tools/cands/_clone%d.json" % t, "w"))
S, *_ = analyze.analyse(glob.glob("tools/cands/_clone*.json"))
for nm, o in sorted(S.items()):
    H = o["hands"]; af = o["pbet"] / max(1, o["pbet"] + o["pcall"] + o["pcheck"])
    print("%-20s vpip %.2f pfr %.2f 3b %.2f af %.2f ftb %.2f cbet %.2f frse %.2f" % (nm, o["vpip"]/H, o["pfr"]/H, o["3b"]/max(1,o["f_raise"]), af, o["ffold"]/max(1,o["faced"]), o["cb"]/max(1,o["cb_ch"]), o["fold_raise"]/max(1,o["f_raise"])))
