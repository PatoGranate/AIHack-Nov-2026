import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Anker Batteries: vpip 0.22 pfr 0.16 3b 0.10 af 0.43 ftb 0.45 (14000 hands)
    PARAMS = {'open': 0.227, 'threebet': 0.127, 'call': 0.182, 'call_cap': 0.289, 'open_size': 2.6, 'limp': 0.0, 'cbet': 0.95, 'bluff': 0.149, 'bet_min': 2, 'call_min': 1, 'raise_min': 4, 'bet_frac': 1.0, 'semibluff': 0.428}
