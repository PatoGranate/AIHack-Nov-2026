import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ParamBot


class Agent(ParamBot):
    PARAMS = dict(open=0.06, limp=0.6, threebet=0.02, call=0.45, call_cap=0.2, bet_min=3, call_min=1, raise_min=5, bluff=0.02, cbet=0.3, semibluff=0.0, bet_frac=0.4)
