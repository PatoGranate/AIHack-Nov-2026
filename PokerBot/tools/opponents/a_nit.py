import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ParamBot


class Agent(ParamBot):
    PARAMS = dict(open=0.10, threebet=0.03, call=0.07, bet_min=3, call_min=3, raise_min=5, bluff=0.0, cbet=0.4, semibluff=0.1)
