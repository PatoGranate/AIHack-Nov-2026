import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of SARS: vpip 0.24 pfr 0.16 3b 0.06 af 0.42 ftb 0.44 (18000 hands)
    PARAMS = {'open': 0.163, 'threebet': 0.088, 'call': 0.131, 'call_cap': 0.33, 'open_size': 2.9, 'limp': 0.0, 'cbet': 0.698, 'bluff': 0.232, 'bet_min': 2, 'call_min': 1, 'raise_min': 4, 'bet_frac': 1.0, 'semibluff': 0.411}
