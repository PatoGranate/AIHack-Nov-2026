import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # sunday_v2 clone of Resonance Qt: vpip 0.22 pfr 0.16 3b 0.11 limp 0.00 af 0.39 ftb 0.39 (23000 hands; all Saturday tables)
    PARAMS = {'open': 0.206, 'threebet': 0.13, 'call': 0.183, 'call_cap': 0.3, 'open_size': 2.8, 'limp': 0.0, 'cbet': 0.79, 'bluff': 0.17, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.39}
