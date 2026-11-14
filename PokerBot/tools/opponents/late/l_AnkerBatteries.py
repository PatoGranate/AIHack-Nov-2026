import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Anker Batteries: vpip 0.20 pfr 0.15 3b 0.12 af 0.40 ftb 0.41 (3000 hands)
    PARAMS = {'open': 0.182, 'threebet': 0.14, 'call': 0.197, 'call_cap': 0.3, 'open_size': 2.6, 'limp': 0.0, 'cbet': 0.78, 'bluff': 0.18, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.4}
