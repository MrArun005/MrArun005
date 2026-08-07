"""Per-day animal ritual audit for player 0 of a replay JSON: fed/cared coverage, wheat stock, escapes."""
import json
import sys

path = sys.argv[1]
r = json.load(open(path))
steps = r["steps"]
tpd = 24
prev_animals = {}
print("day  animals  fedOK caredOK  shedWheat  escapes  (at last hour of day)")
for day in range(30):
    step = min((day + 1) * tpd - 1, len(steps) - 1)
    obs = steps[step][0]["observation"]
    farm = obs["farms"][0]
    priv = obs["private"]
    animals = {}
    fed = cared = tot = 0
    for y, row in enumerate(farm["tiles"]):
        for x, t in enumerate(row):
            if isinstance(t, dict) and "animal" in t:
                tot += 1
                animals[(x, y)] = t["animal"]
                fed += t["fed_today"]
                cared += t["cared_today"]
    escaped = [f"{a}@{xy}" for xy, a in prev_animals.items() if xy not in animals]
    wheat = priv["shed"].get("WHEAT", 0) + sum(i.get("WHEAT", 0) for i in priv["inventories"])
    flag = " <<<" if (tot and (fed < tot or cared < tot)) or escaped else ""
    print(f"{day:>3}  {tot:>7}  {fed:>5} {cared:>7}  {wheat:>9}  {','.join(escaped) or '-'}{flag}")
    prev_animals = animals
    if step >= len(steps) - 1:
        break
