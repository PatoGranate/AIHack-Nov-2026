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
FIX.append(("F1 raise-to accounting / raise over bet / folded seat", 8, 0, f1, {
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
FIX.append(("F2 all-in responder", 8, 0, f2, {2: [(5, 0, 0, "flop", 0, 1, False)]}))

# F3: street transitions. Same preflop as F2 (pot 130). Flop: seat 2 bets 60 (ratio 60/130 = 0.46 -> bin 2);
#   seat 3 (IP, heads-up) calls 60. Pot = 250.
# Turn: bets reset. Seat 2 checks (to_call 0 -> not a response), seat 3 bets 200 (ratio 200/250 = 0.80 -> bin 4,
#   since 0.8 >= edge 0.8). Seat 2 faces it: not a raise, heads-up, OOP, TURN term -> folds.
# A preflop response (seat 2 calling the raise) must NOT be counted.
f3 = [H(1, "preflop", "small_blind", 10), H(2, "preflop", "big_blind", 20), H(3, "preflop", "raise", 60)] + \
     [H(s, "preflop", "fold") for s in (4, 5, 6, 7, 0, 1)] + \
     [H(2, "preflop", "call", 40), H(2, "flop", "raise", 60), H(3, "flop", "call", 60),
      H(2, "turn", "check"), H(3, "turn", "raise", 200), H(2, "turn", "fold")]
FIX.append(("F3 street transitions / preflop excluded", 8, 0, f3, {
    3: [(2, 0, 0, "flop", 1, 0, False)],
    2: [(4, 0, 0, "turn", 0, 0, True)],
}))

# F4: heads-up table (2 seats). Engine: SB = button = seat 0, BB = seat 1, postflop first actor = seat 1.
# Preflop: seat 0 calls 10, seat 1 checks. Pot 40. Flop: seat 1 bets 20 (ratio 0.5 -> bin 2).
#   Seat 0 (the button) acts AFTER the bettor -> IP = 1 under engine semantics -> folds.
f4 = [H(0, "preflop", "small_blind", 10), H(1, "preflop", "big_blind", 20), H(0, "preflop", "call", 10),
      H(1, "preflop", "check"), H(1, "flop", "raise", 20), H(0, "flop", "fold")]
FIX.append(("F4 heads-up position (SB = button)", 2, 0, f4, {0: [(2, 0, 0, "flop", 1, 0, True)]}))

# Engine actor order (kit/engine/game.py l.199): postflop the first actor is _next_alive(button). All stacks are
# 2,000 at the start of every hand, so every seat is "alive" and order is (seat - button - 1) % n, whatever folded
# preflop. Expected IP below = responder's order > bettor's order, computed by hand.

# F6: 8 seats, button 6 (wraparound): SB 7, BB 0, UTG 1. The button and intervening seats fold preflop.
# Preflop: seat 1 raises to 60; seats 2-6 fold; SB 7 calls 50; BB 0 calls 40. Pot 180.
# Flop order 7, 0, 1 (orders 0, 1, 2). Seat 7 checks; seat 0 bets 90 (0.50 -> bin 2).
#   Seat 1 (order 2 > 1): IP, multiway (7, 0 live) -> calls.
#   Seat 7 (order 0 < 1): OOP, multiway (0, 1 live) -> folds.
f6 = [H(7, "preflop", "small_blind", 10), H(0, "preflop", "big_blind", 20), H(1, "preflop", "raise", 60)] +      [H(s, "preflop", "fold") for s in (2, 3, 4, 5, 6)] +      [H(7, "preflop", "call", 50), H(0, "preflop", "call", 40),
      H(7, "flop", "check"), H(0, "flop", "raise", 90), H(1, "flop", "call", 90), H(7, "flop", "fold")]
FIX.append(("F6 8-seat, button 6 wraparound, button folded preflop", 8, 6, f6, {
    1: [(2, 0, 1, "flop", 1, 0, False)], 7: [(2, 0, 1, "flop", 0, 0, True)]}))

# F7: 7 seats, button 3: SB 4, BB 5. Intervening seats and both blinds fold preflop.
# Preflop: seat 6 raises to 60; seats 0, 1 fold; seat 2 calls 60; button 3 calls 60; SB 4 and BB 5 fold.
# Pot 210. Flop live seats 6, 2, 3 with orders 2, 5, 6.
#   Seat 6 checks; seat 2 bets 105 (0.50 -> bin 2).
#   Seat 3 (order 6 > 5): IP, multiway -> raises to 315 (adds 315; ratio 315/315 = 1.00 -> bin 4).
#   Seat 6 faces the raise (order 2 < 6): OOP, multiway (2, 3 live) -> folds.
#   Seat 2 faces the raise (order 5 < 6): OOP, heads-up (6 folded) -> calls 210.
f7 = [H(4, "preflop", "small_blind", 10), H(5, "preflop", "big_blind", 20), H(6, "preflop", "raise", 60),
      H(0, "preflop", "fold"), H(1, "preflop", "fold"), H(2, "preflop", "call", 60), H(3, "preflop", "call", 60),
      H(4, "preflop", "fold"), H(5, "preflop", "fold"),
      H(6, "flop", "check"), H(2, "flop", "raise", 105), H(3, "flop", "raise", 315), H(6, "flop", "fold"),
      H(2, "flop", "call", 210)]
FIX.append(("F7 7-seat, button 3, blinds and intervening seats folded", 7, 3, f7, {
    3: [(2, 0, 1, "flop", 1, 0, False)], 6: [(4, 1, 1, "flop", 0, 0, True)], 2: [(4, 1, 0, "flop", 0, 0, False)]}))

# F8: heads-up with the button rotated to seat 1 (SB = button = 1, BB = 0). Postflop first actor = seat 0.
# Preflop: seat 1 calls 10, seat 0 checks. Flop: seat 0 bets 20 (0.50 -> bin 2); seat 1 (button, order 1 > 0): IP -> folds.
f8 = [H(1, "preflop", "small_blind", 10), H(0, "preflop", "big_blind", 20), H(1, "preflop", "call", 10),
      H(0, "preflop", "check"), H(0, "flop", "raise", 20), H(1, "flop", "fold")]
FIX.append(("F8 heads-up, button rotated to seat 1, BB bets", 2, 1, f8, {1: [(2, 0, 0, "flop", 1, 0, True)]}))

# F9: heads-up, button 0 bets. Flop: seat 1 (BB, order 0) checks; seat 0 (button, order 1) bets 20 (bin 2);
#   seat 1 faces it: OOP (0 < 1) -> calls.
f9 = [H(0, "preflop", "small_blind", 10), H(1, "preflop", "big_blind", 20), H(0, "preflop", "call", 10),
      H(1, "preflop", "check"), H(1, "flop", "check"), H(0, "flop", "raise", 20), H(1, "flop", "call", 20)]
FIX.append(("F9 heads-up, button bets, BB responds", 2, 0, f9, {1: [(2, 0, 0, "flop", 0, 0, False)]}))

# Optional second implementation under test: the author's offline extractor (tools/forge_ctx/extract_events.py).
import json, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "forge_ctx"))
try:
    import extract_events as XE
except Exception:
    XE = None


def to_handdata(n, button, hist):
    ev = []; street = "preflop"; nb = {"flop": 3, "turn": 4, "river": 5}
    for h in hist:
        if h["street"] != street:
            street = h["street"]; ev.append(["board", street, ["2c"] * nb[street]])
        if h["action"] in ("small_blind", "big_blind"):
            ev.append(["post", h["seat"], h["amount"]])
        else:
            ev.append(["act", h["seat"], h["action"], h["amount"]])
    return {"ref": "fixture/r001", "players": ["p%d" % i for i in range(n)],
            "hands": [{"n": 1, "button": button, "start_stacks": [2000] * n, "events": ev}]}


def bin_of(r):
    b = 0
    while b < 5 and r >= M.CTX_EDGES[b]:
        b += 1
    return b


ok_bot = ok_x = True
for name, n, button, hist, exp in FIX:
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
            res.append("    [bot] seat %d: (xf %d, xn %d, xe %.6f)  expected (%d, %d, %.6f)  %s"
                       % (s, o.xf, o.xn, o.xe, ef, en, ee, "OK" if good else "MISMATCH"))
        ok_bot &= good
    xres = []
    if XE is not None:
        p = os.path.join(tempfile.mkdtemp(), "fx.json"); json.dump(to_handdata(n, button, hist), open(p, "w"))
        rows = XE.table_events(p)
        got = sorted((r["seat"], bin_of(r["size"]), int(r["kind"] == "raise"), r["mw"], r["street"], r["ip"], r["allin_call"], bool(r["fold"])) for r in rows)
        want = sorted((s,) + tuple(e) for s, L in exp.items() for e in L)
        xg = got == want
        ok_x &= xg
        xres.append("    [extractor] %s%s" % ("OK" if xg else "MISMATCH", "" if xg else "  got %s want %s" % (got, want)))
    vb = "PASS" if all(r.endswith("OK") for r in res) else "FAIL"
    vx = ("PASS" if xres and xres[0].endswith("OK") else "FAIL") if xres else "PENDING"
    print("%s: bot %s | extractor %s" % (name, vb, vx)); print(chr(10).join(res + xres))
x_state = "PENDING (extractor not importable)" if XE is None else ("ALL PASS" if ok_x else "SOME FAIL")
print("bot: %s; extractor: %s" % ("ALL PASS" if ok_bot else "SOME FAIL", x_state))
# exit 0 = every case passed in BOTH implementations; 1 = any failure; 2 = no failure but extractor PENDING (not a full pass)
sys.exit(1 if not (ok_bot and ok_x) else (2 if XE is None else 0))
