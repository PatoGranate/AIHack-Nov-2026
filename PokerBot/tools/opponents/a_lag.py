import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ParamBot


class Agent(ParamBot):
    PARAMS = dict(open=0.38, threebet=0.14, call=0.25, call_cap=0.25, bet_min=1, call_min=1, raise_min=3, bluff=0.3, cbet=0.85, bet_frac=0.75)
