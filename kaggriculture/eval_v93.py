"""v9.3 (dynamic crop) vs the pure tape: paired seeds, both seats."""
import sys
from kaggle_environments import make

OURS = "v93/main.py"
TAPE = "nb_v9/decoded_main.py"
seeds = [int(s) for s in (sys.argv[1:] or ["901", "902", "903", "904", "905", "906"])]

ours, theirs, wins = [], [], 0
for seed in seeds:
    for our_seat in (0, 1):
        agents = [OURS, TAPE] if our_seat == 0 else [TAPE, OURS]
        env = make("kaggriculture", configuration={"seed": seed}, debug=False)
        env.run(agents)
        rw = [x.get("reward") or 0 for x in env.steps[-1]]
        o, t = rw[our_seat], rw[1 - our_seat]
        ours.append(o)
        theirs.append(t)
        wins += o > t
        print(f"  seed {seed} seat {our_seat}: v9.3 {o:>9,.0f}  tape {t:>9,.0f}  "
              f"{'WIN' if o > t else 'loss'}  ({o - t:+,.0f})", flush=True)

n = len(ours)
d = [a - b for a, b in zip(ours, theirs)]
print(f"\nv9.3 {sum(ours)/n:,.0f}  tape {sum(theirs)/n:,.0f}  wins {wins}/{n}  "
      f"mean {sum(d)/n:+,.0f}  worst {min(d):+,.0f}  best {max(d):+,.0f}")
