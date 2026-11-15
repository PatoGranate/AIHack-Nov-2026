"""Execute both actual source expressions against an independent chip ledger.
Run from repository root: python pablo_poker/tools/test_raise_ev_accounting.py
No agent import, simulation, training data or third-party dependency required.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = [
    # pot, hero current street bet, villain current bet, hero future addition,
    # hero/villain final street caps. Only matched contestable amounts apply.
    (300, 0, 100, 300, 1000, 1000),
    (200, 50, 50, 200, 1000, 1000),
    (250, 50, 100, 200, 250, 400),
    (250, 50, 100, 250, 500, 300),
]


def expression(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    method = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "simulate")
    values = [n.value for n in ast.walk(method)
              if isinstance(n, ast.Assign) and isinstance(n.value, ast.BinOp)
              and any(isinstance(t, ast.Name) and t.id == "raised" for t in n.targets)]
    assert len(values) == 1, "Expected exactly one HU raised-response expression"
    return compile(ast.Expression(values[0]), str(path), "eval")


def main():
    for relative in ("pablo_poker/bot.py", "pablo_poker/pokerbot/v2.py"):
        actual = expression(ROOT / relative)
        checked = 0
        for pot, my_bet, bet_j, a2, hero_cap, villain_cap in CASES:
            final_target = my_bet + a2
            assert final_target <= min(hero_cap, villain_cap)
            for sh in (0.0, 0.5, 0.6, 1.0):
                # Existing pot already contains both current street wagers.
                # Villain only adds chips from its current bet to the final target.
                new_hero_chips = a2
                new_villain_chips = final_target - bet_j
                ledger = sh * (pot + new_hero_chips + new_villain_chips) - new_hero_chips
                got = eval(actual, {"__builtins__": {}},
                           dict(sh=sh, pot=pot, a2=a2, bet_j=bet_j, my_bet=my_bet))
                assert abs(got - ledger) < 1e-10, (relative, pot, my_bet, bet_j, a2, sh, got, ledger)
                checked += 1
        print("%s: %d source-expression ledger fixtures PASS" % (relative, checked))
    # A target beyond either cap would need refund/layered-pot treatment.
    # These fixtures intentionally do not certify that different branch.


if __name__ == "__main__":
    main()
