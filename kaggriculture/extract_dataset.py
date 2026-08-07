"""Compress each harvested replay into a compact per-player scouting record.

For every replay in dataset/replays/: final rewards + ratings, and per player a
day-by-day build timeline (crops, herd, quads, money, hands) plus — for player 0
only, whose private state the replay exposes — executed product flows.

Output: dataset/records.jsonl (one JSON object per replay).
"""
import glob
import json
import os
from collections import defaultdict

OUT = os.path.join("dataset", "records.jsonl")


def farm_snapshot(farm):
    crops, animals = defaultdict(int), defaultdict(int)
    for row in farm.get("tiles", []):
        for t in row:
            if isinstance(t, dict):
                if t.get("kind") == "PLANT":
                    crops[t["crop"]] += 1
                elif t.get("animal"):
                    animals[t["animal"]] += 1
    return {"crops": dict(crops), "herd": dict(animals),
            "quads": len(farm.get("unlocked_quadrants", [])),
            "money": round(farm.get("money", 0)),
            "hands": len(farm.get("hands", []))}


def totals(private):
    t = defaultdict(int)
    for item, n in private.get("shed", {}).items():
        t[item] += n
    for inv in private.get("inventories", []):
        for item, n in inv.items():
            t[item] += n
    return t


def extract(path):
    r = json.load(open(path))
    steps = r["steps"]
    rewards = [a.get("reward") or 0 for a in steps[-1]]
    tpd = 24
    days = {}
    flows_in = defaultdict(int)
    prev = None
    fert_ops = [0, 0]
    for si, st in enumerate(steps):
        obs = st[0].get("observation", {})
        priv = obs.get("private")
        if priv is not None:
            cur = totals(priv)
            if prev is not None:
                for item in cur:
                    d = cur[item] - prev.get(item, 0)
                    if d > 0:
                        flows_in[item] += d
            prev = cur
        for pi, ag in enumerate(st):
            act = ag.get("action") or {}
            for op in [act.get("farmer") or []] + (act.get("hands") or []):
                if op and op[0] == "FERTILIZE":
                    fert_ops[pi] += 1
        if si % tpd == tpd - 1:
            day = si // tpd
            farms = obs.get("farms", [])
            if len(farms) == 2:
                days[day] = [farm_snapshot(farms[0]), farm_snapshot(farms[1])]
    return {
        "episode": os.path.basename(path).split("-")[1] if "-" in os.path.basename(path) else os.path.basename(path),
        "rewards": rewards,
        "p0_flows": dict(flows_in),
        "fert_ops": fert_ops,
        "days": {str(k): v for k, v in sorted(days.items()) if k in (0, 2, 4, 6, 8, 10, 12, 15, 18, 21, 24, 27, 29)},
    }


def main():
    paths = sorted(glob.glob(os.path.join("dataset", "replays", "*.json")))
    print(f"{len(paths)} replays")
    with open(OUT, "w") as fh:
        for p in paths:
            try:
                rec = extract(p)
                fh.write(json.dumps(rec) + "\n")
                print(f"  ok {os.path.basename(p)}  rewards {rec['rewards']}")
            except Exception as exc:
                print(f"  !  {os.path.basename(p)}: {exc!r}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
