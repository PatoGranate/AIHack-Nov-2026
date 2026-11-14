import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of pokermon: vpip 0.25 pfr 0.16 3b 0.07 af 0.50 ftb 0.61 (16000 hands)
    PARAMS = {'open': 0.183, 'threebet': 0.078, 'call': 0.165, 'call_cap': 0.233, 'open_size': 3.0, 'limp': 0.0, 'cbet': 0.819, 'bluff': 0.203, 'bet_min': 0, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.6, 'semibluff': 0.535}
