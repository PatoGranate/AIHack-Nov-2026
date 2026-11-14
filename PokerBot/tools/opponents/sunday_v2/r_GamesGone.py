import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # sunday_v2 clone of GamesGone: vpip 0.26 pfr 0.16 3b 0.03 limp 0.01 af 0.50 ftb 0.43 (23000 hands; all Saturday tables)
    PARAMS = {'open': 0.203, 'threebet': 0.042, 'call': 0.139, 'call_cap': 0.3, 'open_size': 2.3, 'limp': 0.0, 'cbet': 0.73, 'bluff': 0.27, 'bet_min': 1, 'call_min': 2, 'raise_min': 3, 'bet_frac': 0.7, 'semibluff': 0.5}
