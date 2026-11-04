"""For every SELL in the tape, how many turns earlier did the shed already hold the goods?

Replays a tape-vs-tape mirror (seed 901), records p0's shed per step, then walks each
scheduled sell backward while stock covered it. Slack histogram tells us whether the
sell-shift lever has any room at all.
"""
import json
import sys
from collections import Counter, defaultdict

from kaggle_environments import make

sys.path.insert(0, "nb_v9")
import decoded_main as tape

env = make("kaggriculture", configuration={"seed": 901}, debug=False)
env.run(["nb_v9/decoded_main.py", "nb_v9/decoded_main.py"])

shed_by_step = []
for st in env.steps:
    priv = st[0]["observation"].get("private", {}) or {}
    shed_by_step.append(dict(priv.get("shed", {}) or {}))

slack_hist = Counter()
per_item = defaultdict(list)
for step, act in enumerate(tape._ACTIONS):
    for order in (act or {}).get("market", []) or []:
        if not (order and order[0] == "SELL" and len(order) >= 3):
            continue
        item, qty = order[1], int(order[2])
        s = 0
        while step - s - 1 >= 0 and shed_by_step[min(step - s - 1, len(shed_by_step) - 1)].get(item, 0) >= qty:
            s += 1
            if s > 48:
                break
        slack_hist[min(s, 48)] += 1
        per_item[item].append(s)

print("slack (turns a sell could move earlier) -> count of sells")
for s in sorted(slack_hist):
    print(f"  {s:>3}: {slack_hist[s]}")
print("\nby product (median slack):")
for item, ss in sorted(per_item.items()):
    ss.sort()
    print(f"  {item:<12} n={len(ss):>3}  median {ss[len(ss)//2]:>2}  max {max(ss)}")
