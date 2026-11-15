import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "pablo_poker"))
from sim.fieldbot import FieldBot
import random
class Agent(FieldBot):
    def __init__(self):
        FieldBot.__init__(self, "Chinese people can fly", seed=sum(map(ord, __name__ + "td")))
