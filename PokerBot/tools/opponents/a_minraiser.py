import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ParamBot


class Agent(ParamBot):
    PARAMS = dict(open=0.30, open_size=2.0, threebet=0.10, call=0.3, call_cap=0.3, bet_min=1, call_min=1, raise_min=3, bluff=0.15, bet_frac=0.25, cbet=0.9)
