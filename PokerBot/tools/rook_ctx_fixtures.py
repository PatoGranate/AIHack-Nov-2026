"""Rook: public-history edge-case fixtures for forge_ctx_v1's context features (_learn_ctx).

Usage (from PokerBot/):  python -I tools/rook_ctx_fixtures.py [tools/cands/forge_ctx_v1.py]

Each fixture is a hand-built `summary["history"]` that follows kit/engine/game.py semantics:
- blinds are logged as small_blind / big_blind with the posted amount;
- `raise` logs the raise-TO total for the street, `call` logs the chips added (to_call);
- postflop the first actor is the next seat after the button;
- heads-up, the small blind is the button.
Expected features (size bin, facing-raise, multiway, street, in-position vs bettor, all-in) are written
out BY HAND in each fixture and turned into an expected fold probability with the candidate's published
constants. The constants are inputs, not under test. The candidate's per-seat (xf, xn, xe) are then compared.
No arena run, no Monte Carlo.
"""
import importlib.util, math, sys

CAND = sys.argv[1] if len(sys.argv) > 1 else "tools/cands/forge_ctx_v1.py"
sp = importlib.util.spec_from_file_location("cand", CAND); M = importlib.util.module_from_spec(sp); sp.loader.exec_module(M)


def sig(x): return 1 / (1 + math.exp(-x))


def expected_p(b, raise_, mw, street, ip, allin):
    x = (M.CTX_C + M.CTX_SZ[b] + (M.CTX_RAISE if raise_ else 0) + M.CTX_MW * mw + M.CTX_ST[street]
         + M.CTX_IP * ip + M.CTX_MWIP * mw * ip + (M.CTX_ALLIN if allin else 0))
    return sig(x)


def H(seat, street, action, amount=0):
    return {"seat": seat, "street": street, "action": action, "amount": amount}


FIX = []

# F1: raise-to accounting, a raise over a bet, and a folded seat leaving the multiway count.
# 8 seats, button 0 -> SB 1, BB 2. Preflop: seat 3 raises to 60, seats 4-7 and 0 fold, SB calls 50, BB calls 40.
# Pot before the flop = 180. Flop: seat 1 bets 90 (ratio 90/180 = 0.50 -> bin 2).
#   Seat 2 faces it: not a raise, multiway (1, 3 live), IP (offset 1 > 0) -> raises to 270
#   (adds 270; ratio 270/270 = 1.00 -> bin 4).
#   Seat 3 faces the raise: raise=1, multiway (1, 2 live), IP (offset 2 > aggressor offset 1), flop -> folds.
#   Seat 1 faces the raise: raise=1, heads-up (only 2 live; 3 folded), OOP (offset 0 < 1) -> calls 180.
f1 = [H(1, "preflop", "small_blind", 10), H(2, "preflop", "big_blind", 20), H(3, "preflop", "raise", 60)] + \
     [H(s, "preflop", "fold") for s in (4, 5, 6, 7, 0)] + \
     [H(1, "preflop", "call", 50), H(2, "preflop", "call", 40),
      H(1, "flop", "raise", 90), H(2, "flop", "raise", 270), H(3, "flop", "fold"), H(1, "flop", "call", 180)]
FIX.append(("F1 raise-to accounting / raise over bet / folded seat", 8, f1, {
    2: [(2, 0, 1, "flop", 1, 0, False)],
    3: [(4, 1, 1, "flop", 1, 0, True)],
    1: [(4, 1, 0, "flop", 0, 0, False)],
}))

# F2: all-in responder. Button 0, SB 1 folds preflop (10 dead), BB 2 calls 40 vs seat 3's raise to 60.
# Pot before the flop = 130. Flop: seat 2 checks, seat 3 shoves to 1940 (its whole remaining stack;
# ratio 1940/130 -> bin 5).
#   Seat 2 faces to_call 1940 = 2000 - 60 -> all-in term. Heads-up, OOP (offset 1 < 2) -> calls.
f2 = [H(1, "preflop", "small_blind", 10), H(2, "preflop", "big_blind", 20), H(3, "preflop", "raise", 60)] + \
     [H(s, "preflop", "fold") for s in (4, 5, 6, 7, 0, 1)] + \
     [H(2, "preflop", "call", 40), H(2, "flop", "check"), H(3, "flop", "raise", 1940), H(2, "flop", "call", 1940)]
FIX.append(("F2 all-in responder", 8, f2, {2: [(5, 0, 0, "flop", 0, 1, False)]}))

# F3: street transitions. Same preflop as F2 (pot 130). Flop: seat 2 bets 60 (ratio 60/130 = 0.46 -> bin 2);
#   seat 3 (IP, heads-up) calls 60. Pot = 250.
# Turn: bets reset. Seat 2 checks (to_call 0 -> not a response), seat 3 bets 200 (ratio 200/250 = 0.80 -> bin 4,
#   since 0.8 >= edge 0.8). Seat 2 faces it: not a raise, heads-up, OOP, TURN term -> folds.
# A preflop response (seat 2 calling the raise) must NOT be counted.
f3 = [H(1, "preflop", "small_blind", 10), H(2, "preflop", "big_blind", 20), H(3, "preflop", "raise", 60)] + \
     [H(s, "preflop", "fold") for s in (4, 5, 6, 7, 0, 1)] + \
     [H(2, "preflop", "call", 40), H(2, "flop", "raise", 60), H(3, "flop", "call", 60),
      H(2, "turn", "check"), H(3, "turn", "raise", 200), H(2, "turn", "fold")]
FIX.append(("F3 street transitions / preflop excluded", 8, f3, {
    3: [(2, 0, 0, "flop", 1, 0, False)],
    2: [(4, 0, 0, "turn", 0, 0, True)],
}))

# F4: heads-up table (2 seats). Engine: SB = button = seat 0, BB = seat 1, postflop first actor = seat 1.
# Preflop: seat 0 calls 10, seat 1 checks. Pot 40. Flop: seat 1 bets 20 (ratio 0.5 -> bin 2).
#   Seat 0 (the button) acts AFTER the bettor -> IP = 1 under engine semantics -> folds.
f4 = [H(0, "preflop", "small_blind", 10), H(1, "preflop", "big_blind", 20), H(0, "preflop", "call", 10),
      H(1, "preflop", "check"), H(1, "flop", "raise", 20), H(0, "flop", "fold")]
FIX.append(("F4 heads-up position (SB = button)", 2, f4, {0: [(2, 0, 0, "flop", 1, 0, True)]}))

ok_all = True
for name, n, hist, exp in FIX:
    a = M.Agent()
    a.on_table_start({"num_players": n, "starting_stack": 2000, "seat": 0})
    a._learn_ctx({"history": hist})
    res = []
    for s in range(n):
        o = a.S(s)
        E = exp.get(s, [])
        ef = sum(1 for e in E if e[6]); en = len(E); ee = sum(expected_p(*e[:6]) for e in E)
        good = (o.xf == ef and o.xn == en and abs(o.xe - ee) < 1e-9)
        if en or o.xn:
            res.append("    seat %d: bot (xf %d, xn %d, xe %.6f)  expected (%d, %d, %.6f)  %s"
                       % (s, o.xf, o.xn, o.xe, ef, en, ee, "OK" if good else "MISMATCH"))
        ok_all &= good
    verdict = "PASS" if all(r.endswith("OK") for r in res) else "FAIL"
    print("%s: %s" % (name, verdict)); print("\n".join(res))
print("ALL PASS" if ok_all else "SOME FAIL")
