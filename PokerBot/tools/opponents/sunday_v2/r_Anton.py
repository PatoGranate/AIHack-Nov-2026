import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # sunday_v2 clone of Anton: vpip 0.27 pfr 0.25 3b 0.29 limp 0.05 af 0.40 ftb 0.55 (4000 hands; latest v7 (rounds 42,43,44,45,46,47,48,49,50,51,52,53,54))
    PARAMS = {'open': 0.314, 'threebet': 0.332, 'call': 0.436, 'call_cap': 0.3, 'open_size': 4.7, 'limp': 0.0, 'cbet': 0.62, 'bluff': 0.18, 'bet_min': 2, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.4}
