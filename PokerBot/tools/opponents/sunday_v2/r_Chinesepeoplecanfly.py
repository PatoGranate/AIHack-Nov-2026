import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # sunday_v2 clone of Chinese people can fly: vpip 0.33 pfr 0.22 3b 0.08 limp 0.00 af 0.27 ftb 0.41 (7000 hands; latest v17 (rounds 42,43,44,45,46,47,48,49,50,51,52,53,54))
    PARAMS = {'open': 0.273, 'threebet': 0.094, 'call': 0.189, 'call_cap': 0.3, 'open_size': 2.5, 'limp': 0.0, 'cbet': 0.47, 'bluff': 0.06, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.27}
