"""Rook: refresh G_profile_td's starting guesses (GP_ROSTER) from new hand data, using G's OWN stat definitions.

Usage (from PokerBot/):
  python -I tools/rook_roster_update.py --base ../pablo_poker/gbot/G_profile_td.py --out tools/cands/G_profile_td_r<tag>.py \
      [--teams "Poke,Resonance Qt,..."] [--me WBot] <hand-json> ...

- Replays every hand through G's own _learn (from the base file), so every rate uses exactly the counters
  G reads (vpip, pfr, big, f3=o3fold/o3, ftr=f3fold/f3, ftb=ffold/faced, af=pbet/(pbet+pcall+pcheck)).
- Pools all seats except ours, or only the named teams. Prints the old and new values with sample sizes.
- Writes a NEW file with only the GP_ROSTER line replaced. The base file and G are never modified.
"""
import argparse, ast, importlib.util, json, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--teams", default="")
ap.add_argument("--me", default="WBot")
ap.add_argument("files", nargs="+")
a = ap.parse_args()
teams = set(t.strip() for t in a.teams.split(",") if t.strip())
sp = importlib.util.spec_from_file_location("base", a.base); M = importlib.util.module_from_spec(sp); sp.loader.exec_module(M)
Base = M._GBase                      # frozen G's Agent (the profiling subclass wraps it)

K = ("hands", "vpip", "pfr", "big", "o3", "o3fold", "f3", "f3fold", "faced", "ffold", "pbet", "pcall", "pcheck")
tot = dict.fromkeys(K, 0); used = 0; seen = set()
for f in a.files:
    d = json.loads(open(f, "rb").read().decode("utf-8-sig"))
    key = (d.get("ref"), tuple(d["players"]))
    if key in seen or "practice" in str(d.get("ref")):
        continue                     # same table seen by two accounts, or a practice round
    seen.add(key)
    names = d["players"]; n = len(names)
    g = Base(); g.on_table_start({"seat": d.get("seat", 0), "num_players": n})
    for h in d["hands"]:
        hist = []; st = "preflop"; posts = 0
        for e in h["events"]:
            if e[0] == "board":
                st = e[1]
            elif e[0] == "post":
                hist.append({"seat": e[1], "street": "preflop", "action": "small_blind" if posts == 0 else "big_blind", "amount": e[2]}); posts += 1
            elif e[0] == "act":
                hist.append({"seat": e[1], "street": st, "action": e[2], "amount": e[3]})
        g._learn({"history": hist, "shown": h.get("showdown") or {}})
    for s, o in g.st.items():
        nm = names[s]
        if nm == a.me or (teams and nm not in teams):
            continue
        used += 1
        for k in K:
            tot[k] += getattr(o, k)
r = lambda x, y: tot[x] / float(max(1, tot[y]))
new = {"vpip": r("vpip", "hands"), "pfr": r("pfr", "hands"), "big": r("big", "hands"), "f3": r("o3fold", "o3"),
       "ftr": r("f3fold", "f3"), "ftb": r("ffold", "faced"),
       "af": tot["pbet"] / float(max(1, tot["pbet"] + tot["pcall"] + tot["pcheck"]))}
new = {k: round(v, 4) for k, v in new.items()}
src = open(a.base, encoding="utf-8").read()
m = re.search(r"^GP_ROSTER = (\{.*?\})\n", src, re.M | re.S)
old = ast.literal_eval(m.group(1))
print("seat-tables pooled: %d, hands %d, opens-faced f3 n=%d, ftr n=%d, ftb n=%d" % (used, tot["hands"], tot["o3"], tot["f3"], tot["faced"]))
for k in new:
    print("  %-5s old %.4f  new %.4f" % (k, old[k], new[k]))
out = src[:m.start(1)] + repr(new) + src[m.end(1):]
out = out.replace("# pooled Table D tendencies (data/v3_model.json, Saturday rounds, recency-weighted)",
                  "# pooled tendencies refreshed by tools/rook_roster_update.py from %d hand files (G's own stat definitions)" % len(a.files))
open(a.out, "w", encoding="utf-8", newline="\n").write(out)
print("wrote", a.out)
