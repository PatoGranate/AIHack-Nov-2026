import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Gherkers: vpip 0.28 pfr 0.21 3b 0.10 af 0.44 ftb 0.44 (21000 hands)
    PARAMS = {'open': 0.284, 'threebet': 0.15, 'call': 0.173, 'call_cap': 0.215, 'open_size': 3.2, 'limp': 0.0, 'cbet': 0.744, 'bluff': 0.159, 'bet_min': 2, 'call_min': 1, 'raise_min': 4, 'bet_frac': 0.4, 'semibluff': 0.33, 'trapper': True, 'trap_min': 2}
