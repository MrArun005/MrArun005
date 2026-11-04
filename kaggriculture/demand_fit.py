"""Demand vs supply: what the town drains each day vs what the tape sells into it.

Replays a tape mirror and tracks, per product per day: units drained by town+shops
(inferred from market inventory movement net of both players' sells), the tape's own
sells, and the resulting price. Shows which products the tape under- or over-supplies.
"""
import sys
from collections import Counter, defaultdict

from kaggle_environments import make

sys.path.insert(0, "nb_v9")
import decoded_main as tape

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 903
env = make("kaggriculture", configuration={"seed": SEED}, debug=False)
env.run(["nb_v9/decoded_main.py", "nb_v9/decoded_main.py"])
steps = env.steps

sold = defaultdict(Counter)     # day -> item -> units both players sold
drained = defaultdict(Counter)  # day -> item -> units removed by town
price_end = {}
prev_inv = None
for si, st in enumerate(steps):
    obs = st[0]["observation"]
    inv = dict((obs.get("market") or {}).get("inventory") or {})
    day = si // 24
    if prev_inv is not None:
        step_sold = Counter()
        for pi in (0, 1):
            act = st[pi].get("action") or {}
            for o in act.get("market") or []:
                if o and o[0] == "SELL" and len(o) >= 3:
                    step_sold[o[1]] += int(o[2])
        for item in inv:
            delta = inv[item] - prev_inv.get(item, inv[item])
            # inventory rises with sells, falls with town consumption
            drain = step_sold[item] - delta
            if drain > 0:
                drained[day][item] += drain
            sold[day][item] += step_sold[item]
    prev_inv = inv
    if si % 24 == 23:
        price_end[day] = dict((obs.get("market") or {}).get("prices") or {})

items = ["WHEAT", "STRAWBERRY", "MILK", "WOOL", "MELON", "FERTILIZER"]
print("day |" + "".join(f"{i[:5]:>22}" for i in items))
print("    |" + "".join(f"{'sold/drain  $':>22}" for _ in items))
for day in range(30):
    row = f"{day:>3} |"
    for item in items:
        s = sold[day][item]
        d = drained[day][item]
        p = price_end.get(day, {}).get(item, 0)
        row += f"{s:>7}/{d:<5}{p:>5}   "
    print(row)

print("\ntotals (both players sold vs town drained):")
tot_s, tot_d = Counter(), Counter()
for day in range(30):
    tot_s.update(sold[day])
    tot_d.update(drained[day])
for item in items:
    over = tot_s[item] - tot_d[item]
    print(f"  {item:<12} sold {tot_s[item]:>5}  drained {tot_d[item]:>5}  "
          f"net glut {over:>+6}  final ${price_end.get(29, {}).get(item, 0)}")
