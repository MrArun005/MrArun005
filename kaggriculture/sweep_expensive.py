"""Which lever moves the expensive-hands config? Run several variants on the test's exact setup."""
import sys
from dataclasses import replace
from rules import Params
from harness import run_episode

CFG = {"episodeSteps": 240, "farmHandCostMult": 20}

variants = {
    "v2 as-is": Params(),
    "no hires at all": replace(Params(), max_hands=0),
    "2 hands max": replace(Params(), max_hands=2),
    "4 hands max": replace(Params(), max_hands=4),
    "cheap hires only (max_hire_cost=45)": replace(Params(), max_hire_cost=45.0),
    "no land": replace(Params(), last_land_day=-1),
    "no land, 2 hands": replace(Params(), last_land_day=-1, max_hands=2),
    "hire_until_hour=8": replace(Params(), hire_until_hour=8),
}

for name, p in variants.items():
    scores = [run_episode(p, seed, "starter", 0, CFG) for seed in (0, 1, 2)]
    print(f"{name:<40} {[int(s) for s in scores]}  mean={sum(scores)/3:.0f}")
