import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Jump Street: vpip 0.22 pfr 0.14 3b 0.08 af 0.32 ftb 0.44 (14000 hands)
    PARAMS = {'open': 0.227, 'threebet': 0.127, 'call': 0.217, 'call_cap': 0.344, 'open_size': 3.2, 'limp': 0.0, 'cbet': 0.445, 'bluff': 0.111, 'bet_min': 3, 'call_min': 1, 'raise_min': 4, 'bet_frac': 0.4, 'semibluff': 0.4}
