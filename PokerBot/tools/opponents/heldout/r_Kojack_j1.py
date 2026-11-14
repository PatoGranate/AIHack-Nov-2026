import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Kojack: vpip 0.18 pfr 0.14 3b 0.07 af 0.32 ftb 0.42 (17000 hands)
    PARAMS = {'open': 0.158, 'threebet': 0.078, 'call': 0.131, 'call_cap': 0.155, 'open_size': 2.7, 'limp': 0.0, 'cbet': 0.67, 'bluff': 0.088, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.6, 'semibluff': 0.294}
