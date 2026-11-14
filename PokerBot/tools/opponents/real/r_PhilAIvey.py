import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Phil AIvey: vpip 0.21 pfr 0.16 3b 0.06 af 0.26 ftb 0.45 (15000 hands)
    PARAMS = {'open': 0.195, 'threebet': 0.078, 'call': 0.132, 'call_cap': 0.15, 'open_size': 3.0, 'limp': 0.0, 'cbet': 0.5, 'bluff': 0.06, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.26}
