"""Head-to-head acceptance test: candidate (current Params, plus key=value overrides) vs the
previous shipped config and vs starter, paired on seeds 700-709 x both seats, with the
leaks.py detectors riding along.

    python eval_h2h.py <tag> [param=value ...]


Acceptance is head-to-head WIN RATE against the previous shipped build, not mean score —
rating moves on wins. A change that lifts the mean while losing episodes is a regression.
Detectors ride along so a score gain bought by breaking something shows up immediately.

    python loop_eval.py <tag>
"""
import json
import statistics
import sys
from dataclasses import replace

from kaggle_environments import make

import harness
import leaks
from rules import Params

TAG = sys.argv[1] if len(sys.argv) > 1 else "run"
SP = ("/private/tmp/claude-501/-Users-arunmallikarjun-Desktop-kaggle-competition/"
      "fd3a33de-6f40-4def-ab63-e8f31acb42ca/scratchpad")
SEEDS = list(range(700, 710))   # 10 consecutive seeds, both seats — Arun's acceptance bar

# Extra args are `key=value` overrides on Params, so a candidate never needs a code edit
# before it has earned one.
OVERRIDES = {}
for arg in sys.argv[2:]:
    k, _, v = arg.partition("=")
    t = type(getattr(Params(), k))
    # bool("False") is True, which silently turns a control run into a second copy of the
    # candidate — caught exactly once, by a control that failed to reproduce its baseline.
    OVERRIDES[k] = v.lower() in ("1", "true", "yes") if t is bool else t(v)
SHIP = replace(Params(), **OVERRIDES) if OVERRIDES else Params()
if OVERRIDES:
    print(f"  candidate: {OVERRIDES}")
# The build we have to beat: v5 melon settings, everything else current.
PREV = replace(SHIP, melon_tile_cap=13, last_melon_day=13)


def duel(opponent, seed, seat):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    me = harness.make_agent(SHIP)
    opp = harness.make_agent(opponent) if isinstance(opponent, Params) else opponent
    env.run([me, opp] if seat == 0 else [opp, me])
    # kaggle_environments swallows agent exceptions into DONE + a plausible score, so a
    # crashing candidate scores ~0 instead of raising — this eval once recorded a
    # KeyError'ing agent as an honest 0/20. Same guard run_episode has; every eval that
    # calls env.run directly needs it.
    ours_seats = (0, 1) if isinstance(opponent, Params) else (seat,)
    crash = harness._crash_traceback(env, ours_seats)
    if crash:
        raise RuntimeError(f"agent crashed during eval (seed={seed}, seat={seat}):\n{crash}")
    ours = float(env.steps[-1][seat].reward or 0)
    theirs = float(env.steps[-1][1 - seat].reward or 0)
    scan = leaks.scan(env.steps, seat)
    del env
    return ours, theirs, scan


out = {}
for label, opponent in (("prev", PREV), ("starter", "starter")):
    rows = [duel(opponent, s, seat) for s in SEEDS for seat in (0, 1)]
    ours = [r[0] for r in rows]
    margins = [r[0] - r[1] for r in rows]
    wins = sum(m > 0 for m in margins)
    losses = [f"{s}/{seat}" for (s, seat), m
              in zip([(s, t) for s in SEEDS for t in (0, 1)], margins) if m <= 0]
    det = {k: statistics.fmean([r[2][k] for r in rows])
           for k in ("stranded$", "unfed", "escaped", "idle%", "churn", "floor")}
    out[label] = {"wins": wins, "n": len(rows), "ours": ours, "margins": margins,
                  "losses": losses, "det": det}
    print(f"  vs {label:<8} {wins:>2}/{len(rows)} wins   bank {statistics.fmean(ours):>9,.0f}"
          f"  min {min(ours):>9,.0f}  sd {statistics.stdev(ours):>7,.0f}"
          f"  worst {min(margins):>+9,.0f}")
    print(f"     losses: {', '.join(losses) or 'none'}")
    print(f"     detectors: " + "  ".join(f"{k} {v:,.1f}" for k, v in det.items()), flush=True)

json.dump(out, open(f"{SP}/loop_{TAG}.json", "w"))
