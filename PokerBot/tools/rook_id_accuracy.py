"""Rook: identification accuracy of g_id_ftb_v1 on REAL Saturday tables (names known), no MC.
Usage: python -I tools/rook_id_accuracy.py <candidate.py> <hand-json>...  Prints top-1 accuracy and mean conf
at hands 25/100/300/1000, and how often a WRONG id has conf >= 0.9 (overconfidence)."""
import importlib.util, json, sys, collections
sp = importlib.util.spec_from_file_location("c", sys.argv[1]); M = importlib.util.module_from_spec(sp); sp.loader.exec_module(M)
marks = (25, 100, 300, 1000); acc = collections.defaultdict(lambda: [0, 0, 0, 0.0])  # n, right, wrong&conf>=.9, sumconf
for f in sys.argv[2:]:
    d = json.loads(open(f, "rb").read().decode("utf-8-sig")); names = d["players"]; n = len(names)
    a = M.Agent(); a.on_table_start({"seat": d["seat"], "num_players": n})
    for hi, h in enumerate(d["hands"], 1):
        hist = []; st = "preflop"
        for e in h["events"]:
            if e[0] == "board": st = e[1]
            elif e[0] == "post": hist.append({"seat": e[1], "street": "preflop", "action": "small_blind" if not hist else "big_blind", "amount": e[2]})
            elif e[0] == "act": hist.append({"seat": e[1], "street": st, "action": e[2], "amount": e[3]})
        a._id_learn(hist)
        if hi in marks:
            for s in range(n):
                if s == d["seat"] or names[s] not in M.IDLIB["bots"]: continue
                q = a.post.get(s); r = acc[hi]; r[0] += 1
                if q and a.idn.get(s, 0) >= M.ID_MIN:
                    r[3] += q[1]
                    if q[2] == names[s]: r[1] += 1
                    elif q[1] >= 0.9: r[2] += 1
for m in marks:
    n, ok, bad, sc = acc[m]
    if n: print("hand %4d: seats %4d  top-1 correct %.2f  wrong-with-conf>=0.9 %.2f  mean conf %.2f" % (m, n, ok / n, bad / n, sc / n))
