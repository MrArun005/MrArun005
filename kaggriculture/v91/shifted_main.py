"""Counter-fit agent: the public v22 tape with SELLs shifted earlier.

Set SHIFT_FILE before use (eval harness rewrites the constant line).
"""
import json
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)
import tape

SHIFT_FILE = "actions_shift8.json"

with open(os.path.join(_DIR, SHIFT_FILE)) as _fh:
    tape._ACTIONS = json.load(_fh)


def agent(obs):
    return tape.agent(obs)
