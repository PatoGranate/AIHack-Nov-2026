import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # sunday_v2 clone of Anker Batteries: vpip 0.22 pfr 0.17 3b 0.12 limp 0.00 af 0.43 ftb 0.43 (20000 hands; latest v4 (rounds 25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54))
    PARAMS = {'open': 0.207, 'threebet': 0.144, 'call': 0.203, 'call_cap': 0.3, 'open_size': 2.6, 'limp': 0.0, 'cbet': 0.72, 'bluff': 0.21, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.43}
