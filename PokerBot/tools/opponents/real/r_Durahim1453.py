import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Durahim 1453: vpip 0.24 pfr 0.19 3b 0.08 af 0.38 ftb 0.47 (13000 hands)
    PARAMS = {'open': 0.238, 'threebet': 0.1, 'call': 0.152, 'call_cap': 0.15, 'open_size': 2.7, 'limp': 0.0, 'cbet': 0.59, 'bluff': 0.16, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.38}
