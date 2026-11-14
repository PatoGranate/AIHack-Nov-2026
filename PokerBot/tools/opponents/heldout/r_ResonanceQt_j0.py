import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Resonance Qt: vpip 0.22 pfr 0.17 3b 0.11 af 0.36 ftb 0.41 (17000 hands)
    PARAMS = {'open': 0.168, 'threebet': 0.127, 'call': 0.129, 'call_cap': 0.241, 'open_size': 2.9, 'limp': 0.0, 'cbet': 0.736, 'bluff': 0.113, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.75, 'semibluff': 0.345}
