import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Poke: vpip 0.22 pfr 0.13 3b 0.05 af 0.39 ftb 0.51 (8000 hands)
    PARAMS = {'open': 0.17, 'threebet': 0.063, 'call': 0.161, 'call_cap': 0.172, 'open_size': 2.9, 'limp': 0.0, 'cbet': 0.678, 'bluff': 0.204, 'bet_min': 1, 'call_min': 2, 'raise_min': 4, 'bet_frac': 1.0, 'semibluff': 0.344}
