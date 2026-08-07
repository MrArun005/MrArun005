"""Map the tape's routine: when it buys seeds, plants, hires, and pivots crops."""
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "nb_v9")
import decoded_main as tape

plants = defaultdict(Counter)     # day -> crop -> count
seeds = defaultdict(Counter)
hires = Counter()
land = []
animals = defaultdict(Counter)
sells = defaultdict(Counter)

for step, act in enumerate(tape._ACTIONS):
    day = step // 24
    for op in [(act or {}).get("farmer") or []] + ((act or {}).get("hands") or []):
        if op and op[0] == "PLANT" and len(op) > 1:
            plants[day][op[1]] += 1
    for order in (act or {}).get("market", []) or []:
        if not order:
            continue
        if order[0] == "BUY_SEED":
            seeds[day][order[1]] += int(order[2]) if len(order) > 2 else 1
        elif order[0] == "HIRE":
            hires[day] += 1
        elif order[0] == "BUY_LAND":
            land.append(day)
        elif order[0] == "BUY_ANIMAL":
            animals[day][order[1]] += int(order[2]) if len(order) > 2 else 1
        elif order[0] == "SELL":
            sells[day][order[1]] += int(order[2]) if len(order) > 2 else 0

print("day | hires | plants                         | seeds bought              | animals")
for day in range(30):
    p = dict(plants[day]) or ""
    s = dict(seeds[day]) or ""
    a = dict(animals[day]) or ""
    mark = "  <-- LAND" if day in land else ""
    if p or s or a or hires[day]:
        print(f"{day:>3} | {hires[day]:>5} | {str(p):<30} | {str(s):<25} | {a}{mark}")

print("\ntotal seeds:", dict(sum(seeds.values(), Counter())))
print("total plants:", dict(sum(plants.values(), Counter())))
print("land days:", land)
print("total hires:", sum(hires.values()))
print("\nsells by day (units):")
for day in range(30):
    if sells[day]:
        print(f"  {day:>2}: {dict(sells[day])}")
