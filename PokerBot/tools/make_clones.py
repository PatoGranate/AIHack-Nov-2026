"""Fit a ParamBot clone per real opponent from downloaded hands: python tools/make_clones.py kit/hands/*.json"""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import analyse
files = [f for f in sys.argv[1:] if not os.path.basename(f).startswith("_")] or glob.glob("kit/hands/saturday*.json")
S, *_ = analyse(files)
os.makedirs("tools/opponents/real", exist_ok=True)
for f in glob.glob("tools/opponents/real/r_*.py"):
    os.remove(f)
lines = []
for nm, o in S.items():
    if nm == "WBot":
        continue
    H = o["hands"]; vpip = o["vpip"] / H; pfr = o["pfr"] / H; tb = o["3b"] / max(1, o["f_raise"]); shv = o["shove"] / H
    limp = o["limp"] / max(1, o["unopened"]); af = o["pbet"] / max(1, o["pbet"] + o["pcall"] + o["pcheck"])
    ftb = o["ffold"] / max(1, o["faced"]); cb = o["cb"] / max(1, o["cb_ch"]); frse = o["fold_raise"] / max(1, o["f_raise"])
    opsz = o["open_sz"] / max(1, o["open_n"])
    call = min(0.95, max(pfr * 1.2, (1 - frse) + tb))
    p = dict(open=round(min(0.9, pfr * 1.25), 3), threebet=round(min(0.5, tb * 1.1 + 0.01), 3),
             call=round(call * (0.55 if call < 0.5 else 0.7), 3), call_cap=0.15 if frse > 0.8 else 0.3,
             open_size=round(min(6, max(2, opsz if opsz < 10 else 3)), 1),
             limp=round(min(0.95, vpip * 1.1), 3) if limp > 0.25 else 0.0,
             cbet=round(cb, 2), bluff=round(max(0.0, (af - 0.2) * 0.9), 2),
             bet_min=1 if af > 0.45 else (2 if af > 0.25 else 3),
             call_min=1 if ftb < 0.3 else (2 if ftb < 0.52 else 3),
             raise_min=3 if af > 0.5 else 4, bet_frac=0.7, semibluff=round(min(0.8, af), 2))
    if ftb < 0.25:
        p["air_call"] = 0.55
    if shv > 0.04:
        p["shove_mix"] = round(shv * 1.1, 3)
    fn = "tools/opponents/real/r_%s.py" % "".join(ch for ch in nm if ch.isascii() and ch.isalnum())
    open(fn, "w", encoding="utf-8").write('''import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of %s: vpip %.2f pfr %.2f 3b %.2f af %.2f ftb %.2f (%d hands)
    PARAMS = %r
''' % (nm, vpip, pfr, tb, af, ftb, H, p))
    lines.append((fn, H, round(o["chips"] / 20 / H * 100, 1)))
    print("%-22s %5d vpip %.2f pfr %.2f af %.2f ftb %.2f bb/100 %+.0f" % (nm, H, vpip, pfr, af, ftb, o["chips"] / 20 / H * 100))
open("tools/opponents/real/weights.txt", "w", encoding="utf-8").write("\n".join("%s %d %s" % x for x in lines))
