import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Lehman Brothers: vpip 0.32 pfr 0.22 3b 0.13 af 0.48 ftb 0.44 (17000 hands)
    PARAMS = {'open': 0.21, 'threebet': 0.16, 'call': 0.253, 'call_cap': 0.214, 'open_size': 2.6, 'limp': 0.0, 'cbet': 0.601, 'bluff': 0.278, 'bet_min': 1, 'call_min': 3, 'raise_min': 4, 'bet_frac': 1.0, 'semibluff': 0.571}
