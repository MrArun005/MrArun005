"""Measure EXECUTED product flows for player 0 from a replay JSON.

Production = sum of positive per-step deltas of (shed + all inventories)[product].
Consumption/sales = negative deltas. No action-count inference.
"""
import json
import sys
from collections import defaultdict

def totals(private):
    t = defaultdict(int)
    for item, n in private.get("shed", {}).items():
        t[item] += n
    for inv in private.get("inventories", []):
        for item, n in inv.items():
            t[item] += n
    return t

for path in sys.argv[1:]:
    r = json.load(open(path))
    teams = r.get("info", {}).get("TeamNames", ["?", "?"])
    steps = r["steps"]
    prod, cons = defaultdict(int), defaultdict(int)
    prev = None
    money_by_day = {}
    for st in steps:
        obs = st[0].get("observation", {})
        priv = obs.get("private")
        if priv is None:
            continue
        cur = totals(priv)
        if prev is not None:
            for item in set(cur) | set(prev):
                d = cur[item] - prev[item]
                if d > 0:
                    prod[item] += d
                elif d < 0:
                    cons[item] -= d
        prev = cur
        farms = obs.get("farms", [])
        if farms:
            money_by_day[obs.get("day", 0)] = farms[0].get("money", 0)
    rw = [a.get("reward") or 0 for a in steps[-1]]
    print(f"=== {path.split(chr(92))[-1]}  p0={teams[0]}  final {rw[0]:,.0f} vs {rw[1]:,.0f}")
    print(f"  produced (units into shed/inv): {dict(sorted(prod.items(), key=lambda kv: -kv[1]))}")
    print(f"  consumed/sold (units out):      {dict(sorted(cons.items(), key=lambda kv: -kv[1]))}")
    days = sorted(money_by_day)
    curve = {d: round(money_by_day[d]) for d in days if d % 4 == 0 or d == days[-1]}
    print(f"  money by day: {curve}")
    print()
