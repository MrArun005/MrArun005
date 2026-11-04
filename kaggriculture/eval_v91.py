"""Paired eval: v9.1 hybrid vs pure tape (the bar), plus v9.1 vs our v8.1 rule engine."""
import sys
from kaggle_environments import make

HYBRID = "v91/main.py"
TAPE = "nb_v9/decoded_main.py"
ENGINE = "main.py"
seeds = [int(s) for s in (sys.argv[1:] or ["901", "902", "903", "904", "905", "906"])]


def duel(a, b, label):
    a_scores, b_scores, a_wins = [], [], 0
    for seed in seeds:
        for a_seat in (0, 1):
            agents = [a, b] if a_seat == 0 else [b, a]
            env = make("kaggriculture", configuration={"seed": seed}, debug=False)
            env.run(agents)
            rw = [x.get("reward") or 0 for x in env.steps[-1]]
            sa, sb = rw[a_seat], rw[1 - a_seat]
            a_scores.append(sa)
            b_scores.append(sb)
            a_wins += sa > sb
    n = len(a_scores)
    print(f"{label}: {sum(a_scores)/n:>9,.0f} vs {sum(b_scores)/n:>9,.0f}  wins {a_wins}/{n}"
          f"  (min {min(a_scores):,.0f})")


duel(HYBRID, TAPE, "v9.1 vs tape  ")
duel(HYBRID, ENGINE, "v9.1 vs v8.1  ")
