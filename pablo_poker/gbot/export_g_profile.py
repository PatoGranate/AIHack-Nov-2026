"""Build standalone G profiling candidates. Never touches G itself or any live bot.

    python gbot/export_g_profile.py

G_frozen.py      verbatim PokerBot/submissions/G_v7_final/bot.py (sha256 checked)
G_profile.py     G + rolling window and policy-change detection (generic priors)
G_profile_td.py  same + pooled Table D priors for unseen seats
G_profile_tdf.py Table D priors + whole-round evidence; only a detected policy change drops old hands
"""
import ast
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
G_SHA = "1ee577f0e4fed6aef7fef55d1c6f2684e5f3a2a8ce777983bb9ace9ba55ffe12"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


if __name__ == "__main__":
    g = os.path.join(HERE, "G_frozen.py")
    assert sha(g) == G_SHA, "G_frozen.py is not frozen G"
    base = open(g, encoding="utf-8").read()
    adapter = open(os.path.join(HERE, "g_profile_adapter.py"), encoding="utf-8").read()
    out = {"G_frozen.py": G_SHA}
    for name, roster, window in (("G_profile.py", False, 400), ("G_profile_td.py", True, 400),
                                 ("G_profile_tdf.py", True, 1000)):
        src = base + "\n" + adapter.replace("GP_ROSTER_PRIOR = False", "GP_ROSTER_PRIOR = %s" % roster).replace(
            "GP_WINDOW = 400", "GP_WINDOW = %d" % window)
        ast.parse(src)
        p = os.path.join(HERE, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        out[name] = sha(p)
    out["g_profile_adapter.py"] = sha(os.path.join(HERE, "g_profile_adapter.py"))
    json.dump(out, open(os.path.join(HERE, "manifest.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
