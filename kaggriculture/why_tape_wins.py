"""Same seed, same opponent: what does the tape do that our engine doesn't?

Runs tape-as-p0 and engine-as-p0 against each other, and reports for each the
executed product flows, the build timeline, and labour/land usage.
"""
import json
from collections import Counter, defaultdict

from kaggle_environments import make

SEED = 903
TAPE = "nb_v9/decoded_main.py"
ENGINE = "main.py"


def totals(priv):
    t = Counter()
    for item, n in (priv.get("shed") or {}).items():
        t[item] += n
    for inv in priv.get("inventories") or []:
        for item, n in inv.items():
            t[item] += n
    return t


def profile(steps, label):
    produced = Counter()
    prev = None
    ops = Counter()
    hands_by_day = {}
    for si, st in enumerate(steps):
        obs = st[0]["observation"]
        priv = obs.get("private")
        if priv:
            cur = totals(priv)
            if prev is not None:
                for k in cur:
                    d = cur[k] - prev.get(k, 0)
                    if d > 0:
                        produced[k] += d
            prev = cur
        act = st[0].get("action") or {}
        for op in [act.get("farmer") or []] + (act.get("hands") or []):
            if op:
                ops[op[0]] += 1
        if si % 24 == 23:
            farm = (obs.get("farms") or [{}])[0]
            crops = Counter()
            herd = Counter()
            for row in farm.get("tiles", []):
                for t in row:
                    if isinstance(t, dict):
                        if t.get("kind") == "PLANT":
                            crops[t["crop"]] += 1
                        elif t.get("animal"):
                            herd[t["animal"]] += 1
            hands_by_day[si // 24] = (len(farm.get("hands") or []),
                                      len(farm.get("unlocked_quadrants") or []),
                                      round(farm.get("money", 0)), dict(crops), dict(herd))
    print(f"\n===== {label} =====")
    print("produced:", dict(produced.most_common()))
    print("ops:", dict(ops.most_common(10)))
    for day in (4, 8, 12, 16, 20, 24, 28):
        if day in hands_by_day:
            h, q, m, c, a = hands_by_day[day]
            print(f"  day {day:>2}: hands {h:>2} quads {q} ${m:>7,} crops {c} herd {a}")


env = make("kaggriculture", configuration={"seed": SEED}, debug=False)
env.run([TAPE, ENGINE])
rw = [a.get("reward") or 0 for a in env.steps[-1]]
print(f"tape {rw[0]:,.0f}  engine {rw[1]:,.0f}")
profile(env.steps, "TAPE (p0)")

env2 = make("kaggriculture", configuration={"seed": SEED}, debug=False)
env2.run([ENGINE, TAPE])
rw2 = [a.get("reward") or 0 for a in env2.steps[-1]]
print(f"\nengine {rw2[0]:,.0f}  tape {rw2[1]:,.0f}")
profile(env2.steps, "ENGINE (p0)")
