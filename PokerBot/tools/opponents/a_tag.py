import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ParamBot


class Agent(ParamBot):
    PARAMS = dict(open=0.20, threebet=0.06, call=0.12, bet_min=2, call_min=2, raise_min=4, bluff=0.05, cbet=0.7)
