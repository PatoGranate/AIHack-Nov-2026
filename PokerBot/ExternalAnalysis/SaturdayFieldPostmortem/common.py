"""Paths shared by the post-mortem scripts.

Hand files: set POSTMORTEM_HANDS to one or more globs separated by os.pathsep
(';' on Windows, ':' elsewhere). Default = the hand archives in this repository.
Tables seen by more than one account are de-duplicated by (round ref, seat names).
"""
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
POKER = os.path.dirname(os.path.dirname(HERE))  # PokerBot/
DEFAULT_GLOBS = [
    os.path.join(POKER, "Hand_data", "SaturdayRealRounds", "*.json"),
    os.path.join(POKER, "Hand_data", "ExternalTeamData", "*", "SaturdayRealRounds", "*.json"),
]


def hand_files():
    env = os.environ.get("POSTMORTEM_HANDS")
    globs = env.split(os.pathsep) if env else DEFAULT_GLOBS
    return sorted(f for g in globs for f in glob.glob(g))
