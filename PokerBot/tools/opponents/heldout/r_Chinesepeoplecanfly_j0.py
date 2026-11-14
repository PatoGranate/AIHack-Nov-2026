import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Chinese people can fly: vpip 0.36 pfr 0.20 3b 0.06 af 0.45 ftb 0.45 (16000 hands)
    PARAMS = {'open': 0.263, 'threebet': 0.101, 'call': 0.291, 'call_cap': 0.289, 'open_size': 2.6, 'limp': 0.0, 'cbet': 0.716, 'bluff': 0.203, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.4, 'semibluff': 0.567}
