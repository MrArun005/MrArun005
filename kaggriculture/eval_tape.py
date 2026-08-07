"""Head-to-head: the public v22 tape agent vs our current main.py, both seats, seeded."""
import sys
from kaggle_environments import make

TAPE = "nb_v9/decoded_main.py"
OURS = "main.py"
seeds = [int(s) for s in (sys.argv[1:] or ["901", "902", "903", "904", "905", "906"])]

tape_scores, our_scores, tape_wins = [], [], 0
for seed in seeds:
    for tape_seat in (0, 1):
        agents = [TAPE, OURS] if tape_seat == 0 else [OURS, TAPE]
        env = make("kaggriculture", configuration={"seed": seed}, debug=False)
        env.run(agents)
        rw = [a.get("reward") or 0 for a in env.steps[-1]]
        t, o = rw[tape_seat], rw[1 - tape_seat]
        tape_scores.append(t)
        our_scores.append(o)
        tape_wins += t > o
        print(f"seed {seed} tape_seat {tape_seat}: tape {t:>10,.0f}  ours {o:>10,.0f}  {'TAPE' if t > o else 'OURS'}")

n = len(tape_scores)
print(f"\ntape mean {sum(tape_scores)/n:,.0f}   ours mean {sum(our_scores)/n:,.0f}   tape wins {tape_wins}/{n}")
