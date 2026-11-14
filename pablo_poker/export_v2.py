"""Write bot.py (the file to upload) from the v2 engine with a chosen parameter set.

    python export_v2.py                      # pokerbot/v2.py defaults + data/v2_params.json if present
    python export_v2.py --params '{"sd_cal": 1}'
"""
import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
PARAMS_FILE = os.path.join(ROOT, "data", "v2_params.json")


def export(params, out=os.path.join(ROOT, "bot.py")):
    src = open(os.path.join(ROOT, "pokerbot", "v2.py"), encoding="utf-8").read()
    marker = "\n# ---------------------------------------------------------------- tables\n"
    assert marker in src
    baked = "\nP.update(%s)\n" % json.dumps(params, sort_keys=True) if params else ""
    src = src.replace(marker, baked + marker, 1)
    src = re.sub(r"^DEBUG = True", "DEBUG = False", src, flags=re.M)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    return out, len(src.encode("utf-8"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--params")
    ap.add_argument("--out", default=os.path.join(ROOT, "bot.py"))
    a = ap.parse_args()
    if a.params:
        params = json.loads(a.params)
    elif os.path.exists(PARAMS_FILE):
        params = json.load(open(PARAMS_FILE))
    else:
        params = {}
    out, size = export(params, a.out)
    print("wrote %s (%d KB) with %s" % (out, size // 1024, params))
