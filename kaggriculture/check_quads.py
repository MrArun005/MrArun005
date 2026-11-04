import json
import sys
r = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "local_v4b.json"))
steps = r["steps"]
for day in (6, 8, 10, 12, 14, 16, 20):
    step = min((day + 1) * 24 - 1, len(steps) - 1)
    farm = steps[step][0]["observation"]["farms"][0]
    print(f"day {day:>2}: quads {len(farm['unlocked_quadrants'])} {farm['unlocked_quadrants']}  money {farm['money']:,.0f}")
