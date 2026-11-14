import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # sunday_v2 clone of Poke: vpip 0.43 pfr 0.17 3b 0.03 limp 0.29 af 0.58 ftb 0.55 (12000 hands; latest v2 (rounds 22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54))
    PARAMS = {'open': 0.219, 'threebet': 0.043, 'call': 0.16, 'call_cap': 0.3, 'open_size': 2.5, 'limp': 0.468, 'cbet': 0.89, 'bluff': 0.34, 'bet_min': 1, 'call_min': 3, 'raise_min': 3, 'bet_frac': 0.7, 'semibluff': 0.58}
