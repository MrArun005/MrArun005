"""Snowball-crawl the kaggriculture episode graph and index the strong opponents.

Phase 1 (this script): starting from our submission ids, walk ListEpisodes outward.
Every episode names both agents (submissionId, teamId, updatedScore), so each hop
discovers new, usually stronger, submissions. Produces dataset/index.json with every
submission and episode seen.

Replay files themselves are downloaded separately with the kaggle CLI (phase 2) —
the JSON replay endpoint needs browser auth, the CLI does not.

    C:\\kv\\Scripts\\python.exe harvest.py [max_api_calls]
"""
import json
import os
import sys
import time
import urllib.request

API = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
SEEDS = [55300776, 55296535, 55290996, 55286208, 55285442, 55274770]
OUT_DIR = "dataset"
INDEX = os.path.join(OUT_DIR, "index.json")


def list_episodes(sub_id: int) -> dict:
    body = json.dumps({"submissionId": sub_id}).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def main(max_calls: int = 120) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    subs: dict[str, dict] = {}      # subId -> {score, teamId}
    episodes: dict[str, dict] = {}  # epId  -> {agents: [(sub, reward, score)], endTime}
    visited: set[int] = set()
    frontier: list[int] = list(SEEDS)
    calls = 0

    while frontier and calls < max_calls:
        # Highest-rated unvisited submission first: the crawl climbs the ladder.
        frontier.sort(key=lambda s: -(subs.get(str(s), {}).get("score") or 0))
        sub = frontier.pop(0)
        if sub in visited:
            continue
        visited.add(sub)
        try:
            data = list_episodes(sub)
            calls += 1
        except Exception as exc:
            print(f"  ! {sub}: {exc!r}")
            time.sleep(3)
            continue

        for ep in data.get("episodes", []):
            if ep.get("state") != "COMPLETED":
                continue
            agents = []
            for ag in ep.get("agents", []):
                sid = ag.get("submissionId")
                score = ag.get("updatedScore") or 0
                prev = subs.get(str(sid), {})
                if score >= (prev.get("score") or 0):
                    subs[str(sid)] = {"score": score, "teamId": ag.get("teamId")}
                agents.append({"sub": sid, "reward": ag.get("reward"),
                               "score": score, "seat": ag.get("index", 0)})
                if sid not in visited and sid not in frontier:
                    frontier.append(sid)
            episodes[str(ep["id"])] = {"agents": agents, "endTime": ep.get("endTime")}
        best = max((v["score"] for v in subs.values()), default=0)
        print(f"call {calls:>3}: sub {sub}  subs {len(subs):>4}  eps {len(episodes):>5}  best {best:,.0f}")
        time.sleep(0.8)

    with open(INDEX, "w") as fh:
        json.dump({"submissions": subs, "episodes": episodes}, fh)
    strong = sorted(((v["score"], k) for k, v in subs.items()), reverse=True)[:40]
    print(f"\nindexed {len(subs)} submissions, {len(episodes)} episodes -> {INDEX}")
    print("top 40 submissions by rating:")
    for score, sid in strong:
        print(f"  {sid}  {score:>8,.0f}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 120)
