"""What does the dynamic chooser actually plant, day by day, and does it react to shops?"""
import sys
from collections import Counter

from kaggle_environments import make

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 903
env = make("kaggriculture", configuration={"seed": seed}, debug=False)
env.run(["main.py", "main.py"])
steps = env.steps

planted = Counter()
by_day = {}
for si, st in enumerate(steps):
    act = st[0].get("action") or {}
    for op in [act.get("farmer") or []] + (act.get("hands") or []):
        if op and op[0] == "PLANT" and len(op) > 1:
            planted[op[1]] += 1
    if si % 24 == 23:
        obs = st[0]["observation"]
        farm = (obs.get("farms") or [{}])[0]
        crops = Counter()
        for row in farm.get("tiles", []):
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    crops[t["crop"]] += 1
        shops = (obs.get("town") or {}).get("unlocked_shops") or []
        by_day[si // 24] = (dict(crops), round(farm.get("money", 0)), len(shops))

print(f"seed {seed}  rewards {[a.get('reward') for a in steps[-1]]}")
print("total planted:", dict(planted))
for day in (2, 5, 8, 11, 14, 17, 20, 23, 26, 29):
    if day in by_day:
        crops, money, nshops = by_day[day]
        print(f"  day {day:>2}: shops {nshops}  ${money:>7,}  {crops}")
