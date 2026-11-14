import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ParamBot


class Agent(ParamBot):
    PARAMS = dict(open=0.65, threebet=0.35, call=0.5, call_cap=0.5, open_size=4.0, bet_min=0, call_min=1, raise_min=2, bluff=0.6, bet_frac=1.0, cbet=1.0)
