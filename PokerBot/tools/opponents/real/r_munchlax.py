import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of munchlax: vpip 0.17 pfr 0.09 3b 0.03 af 0.21 ftb 0.55 (13000 hands)
    PARAMS = {'open': 0.109, 'threebet': 0.046, 'call': 0.133, 'call_cap': 0.3, 'open_size': 3.7, 'limp': 0.0, 'cbet': 0.36, 'bluff': 0.01, 'bet_min': 3, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.21}
