import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ParamBot


class Agent(ParamBot):
    PARAMS = dict(open=0.15, limp=0.7, threebet=0.03, call=0.7, call_cap=1.0, station=True, bet_min=4, raise_min=6, bluff=0.0)
