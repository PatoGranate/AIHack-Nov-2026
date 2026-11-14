import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Poke: vpip 0.22 pfr 0.13 3b 0.05 af 0.39 ftb 0.51 (8000 hands)
    PARAMS = {'open': 0.183, 'threebet': 0.06, 'call': 0.096, 'call_cap': 0.135, 'open_size': 2.9, 'limp': 0.0, 'cbet': 0.493, 'bluff': 0.184, 'bet_min': 2, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.75, 'semibluff': 0.5}
