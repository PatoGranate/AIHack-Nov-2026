import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # sunday_v2 clone of YSL_TWIZZY: vpip 0.19 pfr 0.15 3b 0.04 limp 0.01 af 0.20 ftb 0.23 (8000 hands; latest v6 (rounds 38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54))
    PARAMS = {'open': 0.183, 'threebet': 0.058, 'call': 0.097, 'call_cap': 0.15, 'open_size': 2.8, 'limp': 0.0, 'cbet': 0.32, 'bluff': 0.0, 'bet_min': 3, 'call_min': 1, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.2, 'air_call': 0.55}
