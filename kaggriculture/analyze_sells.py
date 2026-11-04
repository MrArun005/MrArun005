"""What did each player actually SELL, and roughly what revenue per product?"""
import json
import glob
import os
from collections import defaultdict

for path in sorted(glob.glob("replays/episode-*-replay.json")):
    ep = os.path.basename(path).split("-")[1]
    with open(path) as f:
        r = json.load(f)
    teams = r.get("info", {}).get("TeamNames", ["?", "?"])
    steps = r.get("steps", [])
    sells = [defaultdict(int), defaultdict(int)]  # units requested per product per player
    land = [0, 0]
    hires = [0, 0]
    for st in steps:
        for pi, agent in enumerate(st):
            act = agent.get("action") or {}
            for order in act.get("market", []) or []:
                if not order:
                    continue
                op = order[0]
                if op == "SELL" and len(order) >= 3:
                    try:
                        sells[pi][order[1]] += int(order[2])
                    except (ValueError, TypeError):
                        pass
                elif op == "BUY_LAND":
                    land[pi] += 1
                elif op == "HIRE":
                    hires[pi] += 1
    final = steps[-1]
    rewards = [a.get("reward") for a in final]
    print(f"episode {ep}  {teams[0]} vs {teams[1]}  rewards={rewards}")
    for pi in range(2):
        s = dict(sorted(sells[pi].items(), key=lambda kv: -kv[1]))
        print(f"  p{pi} ({teams[pi]}): sells={s} land_buys={land[pi]} hire_ops={hires[pi]}")
    print()
