"""Automatic round-by-round profile refresh.

    python gbot/auto_refresh.py [--push] [--every 60]

Loop: fetch WBot's hand feed (data/external_tokens.txt -> hands/external/WBot/), and for every NEW round file
that is not a Saturday round, run gbot/refresh_profile.py on it in round order. Each run writes a new
gbot/G_profile_td_<round>.py built on the previous profile (never overwriting anything). With --push the new
bot file and its profile JSON are committed to branch pablo-poker so teammates see them.

Uploading to the tournament stays manual: pick the newest gbot/G_profile_td_<round>.py and upload it.
State: gbot/profiles/processed.json (rounds already refreshed).
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
FEED = os.environ.get("AUTO_FEED", os.path.join(ROOT, "hands", "external", "WBot"))
STATE = os.path.join(HERE, "profiles", "processed.json")
CLONE = os.environ.get("PABLO_PUSH_CLONE", "")


def log(msg):
    print("[auto_refresh %s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def load_state():
    try:
        return set(json.load(open(STATE)))
    except (OSError, ValueError):
        return set()


def save_state(done):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(sorted(done), open(STATE, "w"), indent=1)


def fetch():
    from rsi.field import fetch_external
    for team, line in fetch_external():
        if team == "WBot":
            log("fetch: " + line)


def complete(path):
    try:
        d = json.load(open(path, encoding="utf-8"))
        return len(d.get("hands", [])) >= 900 and "seat" in d
    except (OSError, ValueError):
        return False


def push(files, ref):
    if not CLONE or not os.path.isdir(CLONE):
        log("push skipped: set PABLO_PUSH_CLONE to the pablo-poker clone")
        return
    for f in files:
        dst = os.path.join(CLONE, "pablo_poker", os.path.relpath(f, ROOT))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(f, dst)
    rel = [os.path.join("pablo_poker", os.path.relpath(f, ROOT)).replace("\\", "/") for f in files]
    cmds = [["git", "pull", "-q", "--ff-only", "origin", "pablo-poker"], ["git", "add"] + rel,
            ["git", "commit", "-q", "-m", "pablo_poker/gbot: auto profile refresh after %s (new file, G untouched)\n\n"
             "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" % ref],
            ["git", "push", "-q", "origin", "pablo-poker"]]
    for c in cmds:
        r = subprocess.run(c, cwd=CLONE, capture_output=True, text=True)
        if r.returncode != 0:
            log("push step failed: %s %s" % (" ".join(c[:2]), (r.stderr or r.stdout).strip()[:200]))
            return
    log("pushed %s" % ", ".join(os.path.basename(f) for f in files))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--every", type=int, default=60)
    ap.add_argument("--start", help="local HH:MM:SS of the first check; later checks every --every seconds on that grid")
    a = ap.parse_args()
    next_t = time.time()
    if a.start:
        h, m, sec = [int(x) for x in a.start.split(":")]
        lt = time.localtime()
        next_t = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, h, m, sec, 0, 0, -1))
        log("first check at %s, then every %d s" % (a.start, a.every))
    done = load_state()
    log("watching %s (already processed: %d)" % (FEED, len(done)))
    while True:
        wait = next_t - time.time()
        if wait > 0:
            time.sleep(wait)
        next_t += a.every
        while next_t < time.time():      # never fire a burst of missed checks
            next_t += a.every
        try:
            fetch()
        except Exception as e:      # a failed fetch must never stop the loop
            log("fetch failed: %r" % (e,))
        new = sorted(f for f in glob.glob(os.path.join(FEED, "*.json"))
                     if not os.path.basename(f).startswith(("saturday", "round-")) and os.path.basename(f) not in done)
        for f in new:
            if not complete(f):
                continue
            before = set(glob.glob(os.path.join(HERE, "G_profile_td_*.py")) + glob.glob(os.path.join(HERE, "profiles", "td_prior_*.json")))
            r = subprocess.run([sys.executable, os.path.join(HERE, "refresh_profile.py"), f], capture_output=True, text=True, cwd=ROOT)
            log((r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "refresh: no output")
            done.add(os.path.basename(f))
            save_state(done)
            if r.returncode == 0:   # local copy for manual upload on the website (new file per round, never overwritten)
                up = os.path.join(ROOT, "upload")
                os.makedirs(up, exist_ok=True)
                for b in sorted(set(glob.glob(os.path.join(HERE, "G_profile_td_*.py"))) - before):
                    tag = os.path.basename(b)[len("G_profile_td_"):-3]
                    folder = os.path.join(up, "after_" + tag)   # bot for the round AFTER this one
                    dst = os.path.join(folder, "bot.py")
                    if not os.path.exists(dst):
                        os.makedirs(folder, exist_ok=True)
                        shutil.copy(b, dst)
                        open(os.path.join(folder, "SOURCE.txt"), "w").write(
                            "bot.py = gbot/%s (profile refreshed from %s)\n" % (os.path.basename(b), tag))
                        log("ready to upload: %s" % dst)
            if r.returncode == 0 and a.push:
                after = set(glob.glob(os.path.join(HERE, "G_profile_td_*.py")) + glob.glob(os.path.join(HERE, "profiles", "td_prior_*.json")))
                push(sorted(after - before), os.path.basename(f)[:-5])


if __name__ == "__main__":
    main()
