import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Lehman Brothers: vpip 0.24 pfr 0.16 3b 0.04 af 0.44 ftb 0.30 (1000 hands)
    PARAMS = {'open': 0.203, 'threebet': 0.058, 'call': 0.136, 'call_cap': 0.3, 'open_size': 2.5, 'limp': 0.0, 'cbet': 0.78, 'bluff': 0.22, 'bet_min': 2, 'call_min': 1, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.44}
