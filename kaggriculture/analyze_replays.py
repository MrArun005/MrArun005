"""Analyze downloaded Kaggle episode replays: who won, by how much, and what the opponent did."""
import json
import glob
import os

for path in sorted(glob.glob("replays/episode-*-replay.json")):
    ep = os.path.basename(path).split("-")[1]
    with open(path) as f:
        r = json.load(f)
    info = r.get("info", {})
    team_names = info.get("TeamNames", ["?", "?"])
    steps = r.get("steps", [])
    if not steps:
        print(f"{ep}: no steps")
        continue
    last = steps[-1]
    rewards = [a.get("reward") for a in last]
    statuses = [a.get("status") for a in last]

    # final board state from last observation of agent 0
    obs = last[0].get("observation", {})
    farms = obs.get("farms", [])
    moneys = [f.get("money") for f in farms] if farms else rewards

    # count planted crops + structures per farm at a mid-late step for flavor
    def farm_summary(farm):
        crops, animals, hands = {}, {}, 0
        for row in farm.get("tiles", []):
            for t in row:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT":
                        crops[t["crop"]] = crops.get(t["crop"], 0) + 1
                    elif t.get("kind") in ("COOP", "PASTURE") and t.get("animal"):
                        animals[t["animal"]] = animals.get(t["animal"], 0) + 1
        return crops, animals, len(farm.get("hands", [])), len(farm.get("unlocked_quadrants", []))

    mid = steps[len(steps) // 2][0].get("observation", {})
    mid_farms = mid.get("farms", [])

    print(f"episode {ep}: teams={team_names}")
    print(f"  final rewards: {rewards}  statuses: {statuses}")
    for i, farm in enumerate(mid_farms):
        crops, animals, nhands, quads = farm_summary(farm)
        print(f"  mid-game farm {i} ({team_names[i] if i < len(team_names) else '?'}): "
              f"crops={crops} animals={animals} hands={nhands} quadrants={quads}")
    print()
