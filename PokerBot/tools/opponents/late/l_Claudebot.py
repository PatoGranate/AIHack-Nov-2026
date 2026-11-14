import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Claudebot: vpip 0.17 pfr 0.13 3b 0.03 af 0.41 ftb 0.34 (2000 hands)
    PARAMS = {'open': 0.163, 'threebet': 0.042, 'call': 0.086, 'call_cap': 0.15, 'open_size': 2.5, 'limp': 0.0, 'cbet': 0.72, 'bluff': 0.19, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.41}
