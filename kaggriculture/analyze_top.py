"""Deep-dive a replay: build timeline, sells, hires, land, herd, crop mix per player."""
import json
import sys
from collections import defaultdict

def farm_stats(farm):
    crops, animals = defaultdict(int), defaultdict(int)
    pens = 0
    for row in farm.get("tiles", []):
        for t in row:
            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    crops[t["crop"]] += 1
                elif k in ("COOP", "PASTURE"):
                    pens += 1
                    if t.get("animal"):
                        animals[t["animal"]] += 1
    return dict(crops), dict(animals), pens, len(farm.get("unlocked_quadrants", [])), farm.get("money", 0)

for path in sys.argv[1:]:
    r = json.load(open(path))
    teams = r.get("info", {}).get("TeamNames", ["?", "?"])
    steps = r["steps"]
    rw = [a.get("reward") or 0 for a in steps[-1]]
    print(f"=== {path}: {teams[0]} vs {teams[1]}  final {rw[0]:,.0f} vs {rw[1]:,.0f} ===")

    sells = [defaultdict(int), defaultdict(int)]
    buys = [defaultdict(int), defaultdict(int)]
    hires = [0, 0]
    ferts = [0, 0]   # FERTILIZE unit ops
    for st in steps:
        for pi, ag in enumerate(st):
            act = ag.get("action") or {}
            for o in act.get("market", []) or []:
                if not o:
                    continue
                if o[0] == "SELL" and len(o) >= 3:
                    try: sells[pi][o[1]] += int(o[2])
                    except (ValueError, TypeError): pass
                elif o[0] in ("BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL") and len(o) >= 3:
                    try: buys[pi][f"{o[0]}:{o[1]}"] += int(o[2])
                    except (ValueError, TypeError): pass
                elif o[0] == "HIRE":
                    hires[pi] += 1
            for op in [act.get("farmer") or []] + (act.get("hands") or []):
                if op and op[0] == "FERTILIZE":
                    ferts[pi] += 1

    for pi in range(2):
        print(f"-- p{pi} {teams[pi]}")
        print(f"   sells: {dict(sorted(sells[pi].items(), key=lambda kv: -kv[1]))}")
        print(f"   buys:  {dict(sorted(buys[pi].items(), key=lambda kv: -kv[1]))}")
        print(f"   hire ops {hires[pi]}, FERTILIZE ops {ferts[pi]}")

    # timeline snapshots at days 3, 7, 12, 20, 28
    for day in (3, 7, 12, 20, 28):
        step = min(day * 24, len(steps) - 1)
        obs = steps[step][0].get("observation", {})
        farms = obs.get("farms", [])
        if not farms:
            continue
        line = f"   day {day:>2}: "
        parts = []
        for pi, farm in enumerate(farms):
            crops, animals, pens, quads, money = farm_stats(farm)
            parts.append(f"p{pi} ${money:>7,.0f} quads={quads} crops={crops} herd={animals}")
        print(line + "  |  ".join(parts))
    print()
