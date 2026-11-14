import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Joca: vpip 0.23 pfr 0.10 3b 0.11 af 0.42 ftb 0.37 (18000 hands)
    PARAMS = {'open': 0.152, 'threebet': 0.138, 'call': 0.217, 'call_cap': 0.251, 'open_size': 4.7, 'limp': 0.0, 'cbet': 0.95, 'bluff': 0.242, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.75, 'semibluff': 0.472}
