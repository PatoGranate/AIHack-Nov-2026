import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Poke: vpip 0.40 pfr 0.16 3b 0.03 af 0.51 ftb 0.45 (1000 hands)
    PARAMS = {'open': 0.195, 'threebet': 0.047, 'call': 0.151, 'call_cap': 0.3, 'open_size': 2.5, 'limp': 0.438, 'cbet': 0.86, 'bluff': 0.28, 'bet_min': 1, 'call_min': 2, 'raise_min': 3, 'bet_frac': 0.7, 'semibluff': 0.51}
