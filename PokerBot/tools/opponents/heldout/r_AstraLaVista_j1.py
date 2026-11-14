import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Astra La Vista: vpip 0.20 pfr 0.14 3b 0.06 af 0.46 ftb 0.40 (16000 hands)
    PARAMS = {'open': 0.184, 'threebet': 0.093, 'call': 0.164, 'call_cap': 0.174, 'open_size': 2.8, 'limp': 0.0, 'cbet': 0.854, 'bluff': 0.264, 'bet_min': 0, 'call_min': 2, 'raise_min': 4, 'bet_frac': 1.0, 'semibluff': 0.385}
