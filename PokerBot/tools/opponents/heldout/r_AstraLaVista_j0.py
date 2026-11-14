import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Astra La Vista: vpip 0.20 pfr 0.14 3b 0.06 af 0.46 ftb 0.40 (16000 hands)
    PARAMS = {'open': 0.183, 'threebet': 0.079, 'call': 0.165, 'call_cap': 0.166, 'open_size': 2.8, 'limp': 0.0, 'cbet': 0.739, 'bluff': 0.278, 'bet_min': 1, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.75, 'semibluff': 0.472}
