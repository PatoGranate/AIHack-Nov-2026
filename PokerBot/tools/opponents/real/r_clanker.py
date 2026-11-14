import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of clanker: vpip 0.30 pfr 0.16 3b 0.10 af 0.41 ftb 0.22 (4000 hands)
    PARAMS = {'open': 0.197, 'threebet': 0.12, 'call': 0.215, 'call_cap': 0.3, 'open_size': 2.9, 'limp': 0.0, 'cbet': 0.77, 'bluff': 0.19, 'bet_min': 2, 'call_min': 1, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.41, 'air_call': 0.55}
