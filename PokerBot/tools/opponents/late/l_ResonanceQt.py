import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Resonance Qt: vpip 0.21 pfr 0.16 3b 0.15 af 0.37 ftb 0.32 (2000 hands)
    PARAMS = {'open': 0.206, 'threebet': 0.17, 'call': 0.209, 'call_cap': 0.3, 'open_size': 2.8, 'limp': 0.0, 'cbet': 0.69, 'bluff': 0.15, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.37}
