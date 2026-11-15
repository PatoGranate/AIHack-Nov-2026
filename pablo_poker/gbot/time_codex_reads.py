"""Read cost of Codex's v4 profiling candidate vs v4 baseline after a real round of public history."""
import importlib.util, json, os, sys, time, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
from gbot.calib_drift_real import summaries
def load(p, n):
    s = importlib.util.spec_from_file_location(n, os.path.join(ROOT, p)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
d = json.load(open(sorted(glob.glob(os.path.join(ROOT, "hands/external/WBot/saturday_r05*.json")))[0], encoding="utf-8"))
for p in ("sunday/v4_baseline.py", "sunday/v4_identity_bot.py"):
    m = load(p, os.path.basename(p)[:-3])
    a = m.Agent(); a.on_table_start({"seat": d["seat"], "num_players": len(d["players"]), "hands": 1000, "starting_stack": 2000})
    for i, (s, hh) in enumerate(zip(summaries(d), d["hands"])):
        if hasattr(a, "_decision_hand"):
            a._decision_hand = i + 1; a._decision_button = hh["button"]
        s["hand_number"] = i + 1; s["board"] = hh.get("board") or []
        a.on_hand_end(s)
    seats = [x for x in range(len(d["players"])) if x != d["seat"]]
    t = time.perf_counter()
    for _ in range(2000):
        for x in seats:
            a.vpip(x); a.pfr(x); a.ftb(x); a.af(x); a.fold3(x); a.bigrate(x)
    print("%-28s %.1f us per seat per 6 reads; live seats %s, failures %s" % (p, (time.perf_counter() - t) / 2000 / len(seats) * 1e6, len(getattr(getattr(a, "context_model", None), "live", {}) or {}), getattr(a, "context_failures", None)))
