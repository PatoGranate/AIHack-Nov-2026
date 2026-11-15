"""Rook: counterfactual replay of OUR real decisions facing a big postflop bet (to_call >= FRAC of our stack).

Usage (from PokerBot/): python tools/rook_replay_allin.py <bot.py> <hand-json>... [--frac 0.5]

For every real hand the bot learns from the real history (on_hand_end), exactly as live. At each real spot where
WBot faced a postflop bet of >= FRAC of its remaining stack, the state is rebuilt with engine semantics and the bot
is asked what it would do. If it would FOLD where WBot actually called, the hand's result becomes
-(chips we had committed before that decision); otherwise the real result stands. Only fold-vs-call
counterfactuals are scored (a different raise is scored as the real result: conservative).
"""
import importlib.util, json, sys

args = [a for a in sys.argv[1:] if not a.startswith("--")]
FRAC = 0.5
if "--frac" in sys.argv:
    FRAC = float(sys.argv[sys.argv.index("--frac") + 1])
bot, files = args[0], args[1:]
sp = importlib.util.spec_from_file_location("cand", bot); M = importlib.util.module_from_spec(sp); sp.loader.exec_module(M)

tot = dict(spots=0, real_call=0, cf_fold=0, real_chips=0, cf_chips=0, saved_on_folds=0)
for f in files:
    d = json.loads(open(f, "rb").read().decode("utf-8-sig"))
    me, P = d["seat"], d["players"]; n = len(P)
    a = M.Agent(); a.on_table_start({"seat": me, "num_players": n, "hands": len(d["hands"]), "starting_stack": 2000})
    for h in d["hands"]:
        stacks = list(h["start_stacks"]); bets = [0] * n; contrib = [0] * n; folded = [False] * n
        street, board, hist, cur, raises = "preflop", [], [], 0, 0
        btn = h["button"]; hole = h["hole"].get(str(me)); posts = 0
        cf_fold_at = None; real_action = None
        for e in h["events"]:
            if e[0] == "post":
                s, x = e[1], e[2]
                stacks[s] -= x; bets[s] += x; contrib[s] += x; cur = max(cur, bets[s])
                hist.append({"seat": s, "street": "preflop", "action": "small_blind" if posts == 0 else "big_blind", "amount": x}); posts += 1
                continue
            if e[0] == "board":
                street, board = e[1], e[2]; bets = [0] * n; cur = 0; raises = 0
                continue
            if e[0] != "act":
                continue
            _, s, act, amt = e
            to_call = cur - bets[s]
            if (s == me and street != "preflop" and to_call > 0 and hole and cf_fold_at is None
                    and to_call >= FRAC * stacks[me] and act == "call"):
                stack_to = bets[me] + stacks[me]
                can_raise = stack_to > cur and any(not folded[j] and stacks[j] > 0 for j in range(n) if j != me)
                state = {"type": "act", "hand_number": h["n"], "street": street, "seat": me, "button": btn,
                         "hole_cards": hole, "board": board, "small_blind": 10, "big_blind": 20, "blind_level": 0,
                         "pot": sum(contrib), "stacks": list(stacks), "bets": list(bets), "folded": list(folded),
                         "to_call": to_call, "min_raise_to": min(cur + max(20, cur), stack_to) if can_raise else None,
                         "max_raise_to": stack_to if can_raise else None,
                         "legal_actions": ["fold", "call"] + (["raise"] if can_raise else []),
                         "betting": "no_limit", "raise_cap": None, "raises_this_street": raises, "history": list(hist)}
                out = a.act(state) or {}
                tot["spots"] += 1; tot["real_call"] += 1
                if out.get("action") == "fold":
                    cf_fold_at = contrib[me]
            if act == "raise":
                add = amt - bets[s]; stacks[s] -= add; contrib[s] += add; bets[s] = amt; cur = amt; raises += 1
            elif act == "call":
                stacks[s] -= amt; contrib[s] += amt; bets[s] += amt
            elif act == "fold":
                folded[s] = True
            hist.append({"seat": s, "street": street, "action": act, "amount": amt})
        res = h["result"]
        if cf_fold_at is not None:
            tot["cf_fold"] += 1; cf = -cf_fold_at; tot["saved_on_folds"] += cf - res
        else:
            cf = res
        if tot["spots"] and (cf_fold_at is not None or any(True for _ in [0])):
            pass
        tot["real_chips"] += res; tot["cf_chips"] += cf
        a.on_hand_end({"hand_number": h["n"], "board": h.get("board"), "shown": h.get("showdown") or {},
                       "history": hist, "results": h["results"]})
hands = sum(len(json.loads(open(f, "rb").read().decode("utf-8-sig"))["hands"]) for f in files)
print("big-bet call spots: %d | candidate folds %d of them | chips saved by those folds %+d (%+.1f bb/100 over %d hands)"
      % (tot["spots"], tot["cf_fold"], tot["saved_on_folds"], tot["saved_on_folds"] / 20 / hands * 100, hands))
