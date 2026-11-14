import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of clanker: vpip 0.30 pfr 0.16 3b 0.10 af 0.41 ftb 0.22 (4000 hands)
    PARAMS = {'open': 0.157, 'threebet': 0.116, 'call': 0.183, 'call_cap': 0.275, 'open_size': 2.9, 'limp': 0.0, 'cbet': 0.746, 'bluff': 0.239, 'bet_min': 3, 'call_min': 1, 'raise_min': 4, 'bet_frac': 0.75, 'semibluff': 0.317, 'air_call': 0.581}
