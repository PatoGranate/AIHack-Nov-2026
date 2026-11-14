import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Chinese people can fly: vpip 0.36 pfr 0.25 3b 0.06 af 0.27 ftb 0.39 (2000 hands)
    PARAMS = {'open': 0.307, 'threebet': 0.081, 'call': 0.184, 'call_cap': 0.3, 'open_size': 2.5, 'limp': 0.0, 'cbet': 0.36, 'bluff': 0.06, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.27}
