import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of FisherMen: vpip 0.32 pfr 0.20 3b 0.11 af 0.38 ftb 0.49 (20000 hands)
    PARAMS = {'open': 0.254, 'threebet': 0.132, 'call': 0.186, 'call_cap': 0.3, 'open_size': 4.0, 'limp': 0.0, 'cbet': 0.42, 'bluff': 0.16, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.38}
