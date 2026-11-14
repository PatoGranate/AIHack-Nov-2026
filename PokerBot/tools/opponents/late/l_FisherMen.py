import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of FisherMen: vpip 0.26 pfr 0.22 3b 0.12 af 0.27 ftb 0.32 (1000 hands)
    PARAMS = {'open': 0.271, 'threebet': 0.145, 'call': 0.186, 'call_cap': 0.3, 'open_size': 3.9, 'limp': 0.0, 'cbet': 0.4, 'bluff': 0.06, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.27}
