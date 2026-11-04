"""v3 validation: head-to-head vs v2-configured params, plus starter sanity.

The baseline shares v3's code (sell logic included) but is configured like v2:
melon monoculture, geese, fewer hands, no strawberries, no glide. If v3 wins
decisively, the portfolio + labour + timing changes are the delta.
"""
from dataclasses import replace
from rules import Params
from harness import evaluate

V2 = replace(Params(),
             melon_tile_cap=24, strawberry_tile_cap=0,
             target_cows=6, target_sheep=6, target_geese=3,
             hands_per_tile=0.11, max_hands=14,
             min_land_day=0, haul_threshold=40,
             glide_days=3, final_day_hands=0)
V3 = Params()

print("=== head-to-head: v3 (us) vs v2-config (opponent), 8 seeds x both seats ===")
a = evaluate(V3, episodes=8, seed=400, opponent=V2, both_seats=True)
print(f"v3 mean {a['mean']:.0f}  ± {a['stdev']:.0f}  min {a['min']:.0f}  max {a['max']:.0f}")

b = evaluate(V2, episodes=8, seed=400, opponent=V3, both_seats=True)
print(f"v2 mean {b['mean']:.0f}  ± {b['stdev']:.0f}  min {b['min']:.0f}  max {b['max']:.0f}")

wins = sum(1 for x, y in zip(a["scores"], b["scores"]) if x > y)
print(f"v3 beats v2 in {wins}/{len(a['scores'])} paired episodes")

print("=== v3 vs starter (uncontested sanity) ===")
c = evaluate(V3, episodes=6, seed=500, opponent="starter", both_seats=True)
print(f"v3 vs starter mean {c['mean']:.0f}  ± {c['stdev']:.0f}")
