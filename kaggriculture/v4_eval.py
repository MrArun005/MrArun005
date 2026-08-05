"""v4 validation: head-to-head vs v3-configured params, plus starter sanity.

The baseline shares v4's code but is configured like v3: 16-tile strawberry cap, care at
40, serialized-era priorities, 2500 animal reserve, fertilizer never applied. Code-level
fixes (multi-task ritual emission, carried-animal census) remain in both, so the baseline
is strictly stronger than the real v3 — beating it decisively is the harder test.
"""
from dataclasses import replace
from rules import Params
from harness import evaluate

V3 = replace(Params(),
             melon_tile_cap=16, strawberry_tile_cap=16, strawberry_last_day=18,
             strawberry_ramp_day=99, last_melon_day=99,
             prio_animal_care=40.0, prio_feed_relaxed=72.0,
             prio_animal_harvest_partial=33.0,
             wheat_pickup_batch=6, max_pickup_tasks=2,
             animal_cash_reserve=2500.0, fert_use_last_day=-1)
V4 = Params()

print("=== head-to-head: v4 (us) vs v3-config (opponent), 8 seeds x both seats ===")
a = evaluate(V4, episodes=8, seed=700, opponent=V3, both_seats=True)
print(f"v4 mean {a['mean']:.0f}  ± {a['stdev']:.0f}  min {a['min']:.0f}  max {a['max']:.0f}")

b = evaluate(V3, episodes=8, seed=700, opponent=V4, both_seats=True)
print(f"v3 mean {b['mean']:.0f}  ± {b['stdev']:.0f}  min {b['min']:.0f}  max {b['max']:.0f}")

wins = sum(1 for x, y in zip(a["scores"], b["scores"]) if x > y)
print(f"v4 beats v3 in {wins}/{len(a['scores'])} paired episodes")

print("=== v4 vs starter (uncontested sanity) ===")
c = evaluate(V4, episodes=6, seed=800, opponent="starter", both_seats=True)
print(f"v4 vs starter mean {c['mean']:.0f}  ± {c['stdev']:.0f}")
