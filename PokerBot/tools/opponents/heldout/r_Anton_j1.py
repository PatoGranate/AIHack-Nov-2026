import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Anton: vpip 0.33 pfr 0.26 3b 0.25 af 0.29 ftb 0.44 (16000 hands)
    PARAMS = {'open': 0.305, 'threebet': 0.293, 'call': 0.555, 'call_cap': 0.352, 'open_size': 5.0, 'limp': 0.0, 'cbet': 0.424, 'bluff': 0.101, 'bet_min': 3, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.6, 'semibluff': 0.332}
