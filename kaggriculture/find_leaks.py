"""What does the tape leave on the table? Stranded stock + idle units, measured."""
import sys
from collections import Counter

from kaggle_environments import make

sys.path.insert(0, "nb_v9")
import decoded_main as tape

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 901
env = make("kaggriculture", configuration={"seed": seed}, debug=False)
env.run(["nb_v9/decoded_main.py", "nb_v9/decoded_main.py"])
steps = env.steps
LATCH = len(steps) - 2

# 1. stranded stock at the latch
final = steps[LATCH][0]["observation"]
priv = final.get("private", {}) or {}
shed = dict(priv.get("shed", {}) or {})
carried = Counter()
for inv in priv.get("inventories", []) or []:
    for k, v in inv.items():
        carried[k] += v
prices = (final.get("market", {}) or {}).get("prices", {}) or {}
strand_value = 0
print("stranded at reward latch (step %d):" % LATCH)
for item, n in sorted(shed.items()):
    if n > 0 and item in prices:
        v = n * prices[item]
        strand_value += v
        print(f"  shed {item:<12} {n:>4} x {prices[item]:>4} = {v:>8,}")
for item, n in sorted(carried.items()):
    if n > 0 and item in prices:
        v = n * prices[item]
        strand_value += v
        print(f"  hand {item:<12} {n:>4} x {prices[item]:>4} = {v:>8,}")
print(f"  TOTAL stranded value ~ {strand_value:,}")

# 2. idle units and what they were standing on
idle = 0
idle_on_work = Counter()
total_unit_turns = 0
for si, st in enumerate(steps[:LATCH]):
    obs = st[0]["observation"]
    act = st[0].get("action") or {}
    farm = (obs.get("farms") or [{}])[0]
    tiles = farm.get("tiles", [])
    positions = [farm.get("farmer"), *(farm.get("hands") or [])]
    ops = [act.get("farmer") or ["PASS"], *(act.get("hands") or [])]
    for pos, op in zip(positions, ops):
        total_unit_turns += 1
        if not (op and op[0] == "PASS"):
            continue
        idle += 1
        try:
            t = tiles[int(pos[1])][int(pos[0])]
        except (IndexError, TypeError, ValueError):
            continue
        if isinstance(t, dict):
            if t.get("kind") == "PLANT" and t.get("yield_units", 0) > 0:
                idle_on_work["harvestable_crop"] += 1
            elif "animal" in t and t.get("yield_units", 0) > 0:
                idle_on_work["harvestable_animal"] += 1
            elif "animal" in t and t.get("fertilizer_available"):
                idle_on_work["fertilizer_ready"] += 1
            elif "animal" in t and not t.get("cared_today"):
                idle_on_work["uncared_animal"] += 1
            elif t.get("kind") == "PLANT" and not t.get("watered_today"):
                idle_on_work["unwatered_crop"] += 1
            elif t.get("kind") == "WEED":
                idle_on_work["weed"] += 1
        elif t is None:
            idle_on_work["empty_tile"] += 1
print(f"\nunit-turns {total_unit_turns:,}, PASS {idle:,} ({100*idle/max(1,total_unit_turns):.1f}%)")
print("PASS while standing on:")
for k, v in idle_on_work.most_common():
    print(f"  {k:<20} {v:>6}")
