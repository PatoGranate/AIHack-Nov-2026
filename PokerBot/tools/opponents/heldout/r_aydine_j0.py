import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of aydine: vpip 0.22 pfr 0.14 3b 0.03 af 0.37 ftb 0.44 (14000 hands)
    PARAMS = {'open': 0.164, 'threebet': 0.051, 'call': 0.105, 'call_cap': 0.375, 'open_size': 3.6, 'limp': 0.0, 'cbet': 0.832, 'bluff': 0.187, 'bet_min': 2, 'call_min': 1, 'raise_min': 4, 'bet_frac': 0.6, 'semibluff': 0.34}
