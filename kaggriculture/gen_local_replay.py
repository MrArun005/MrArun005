"""Run one local episode (our agent vs itself) and dump a replay-shaped JSON.

Usage: gen_local_replay.py [out.json] [seed]
Always pass a seed when comparing runs — mirror totals swing +-20k on the random seed
even with near-identical production, so unseeded runs are not comparable.
"""
import json
import sys
from kaggle_environments import make

out = sys.argv[1] if len(sys.argv) > 1 else "local_ep.json"
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
env = make("kaggriculture", configuration={"seed": seed}, debug=True)
env.run(["main.py", "main.py"])
json.dump({"info": {"TeamNames": ["v3-local", "v3-local"]}, "steps": env.steps}, open(out, "w"))
print("wrote", out, "steps:", len(env.steps), "seed:", seed)
