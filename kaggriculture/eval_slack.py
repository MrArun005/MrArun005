"""Duel slack-shift variants vs pure tape + solo sanity (vs starter)."""
import sys
from kaggle_environments import make

TAPE = "nb_v9/decoded_main.py"
seeds = [901, 902, 903, 904, 905, 906]

for cap in (int(x) for x in (sys.argv[1:] or ["4", "8", "16"])):
    ours_file = f"v91/main_slack{cap}.py"
    ours, theirs, wins = [], [], 0
    for seed in seeds:
        for our_seat in (0, 1):
            agents = [ours_file, TAPE] if our_seat == 0 else [TAPE, ours_file]
            env = make("kaggriculture", configuration={"seed": seed}, debug=False)
            env.run(agents)
            rw = [x.get("reward") or 0 for x in env.steps[-1]]
            o, t = rw[our_seat], rw[1 - our_seat]
            ours.append(o)
            theirs.append(t)
            wins += o > t
    k = len(ours)
    env = make("kaggriculture", configuration={"seed": 901}, debug=False)
    env.run([ours_file, "starter"])
    solo = env.steps[-1][0].get("reward") or 0
    print(f"slack{cap:>2}: ours {sum(ours)/k:>9,.0f}  tape {sum(theirs)/k:>9,.0f}  "
          f"wins {wins}/{k}  min {min(ours):,.0f}  solo {solo:,.0f}", flush=True)
