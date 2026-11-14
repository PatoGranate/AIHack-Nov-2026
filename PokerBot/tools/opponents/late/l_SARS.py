import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of SARS: vpip 0.19 pfr 0.14 3b 0.07 af 0.46 ftb 0.41 (3000 hands)
    PARAMS = {'open': 0.17, 'threebet': 0.085, 'call': 0.14, 'call_cap': 0.15, 'open_size': 2.5, 'limp': 0.0, 'cbet': 0.74, 'bluff': 0.24, 'bet_min': 1, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.46}
