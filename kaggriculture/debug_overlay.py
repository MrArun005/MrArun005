"""Instrument v9.2's overlay: how often does it actually change an action?"""
import sys

sys.path.insert(0, "v92")
import main as v92
from kaggle_environments import make

fires = {"total": 0, "by_op": {}}
_orig = v92._idle_work


def counting(obs, action):
    before = [action.get("farmer"), *(action.get("hands") or [])]
    out = _orig(obs, action)
    after = [out.get("farmer"), *(out.get("hands") or [])]
    for b, a in zip(before, after):
        if b != a:
            fires["total"] += 1
            fires["by_op"][a[0]] = fires["by_op"].get(a[0], 0) + 1
    return out


v92._idle_work = counting

env = make("kaggriculture", configuration={"seed": 901}, debug=True)
env.run([v92.agent, "nb_v9/decoded_main.py"])
print("reward:", [a.get("reward") for a in env.steps[-1]])
print("overlay fired:", fires["total"], fires["by_op"])
