import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of bigRoddy: vpip 0.30 pfr 0.20 3b 0.18 af 0.33 ftb 0.51 (18000 hands)
    PARAMS = {'open': 0.189, 'threebet': 0.256, 'call': 0.273, 'call_cap': 0.374, 'open_size': 3, 'limp': 0.0, 'cbet': 0.569, 'bluff': 0.121, 'bet_min': 3, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.4, 'semibluff': 0.348}
