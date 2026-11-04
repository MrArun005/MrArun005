"""v2 validation: head-to-head vs v1 params, and standard benchmark sanity."""
from dataclasses import replace
from rules import Params
from harness import evaluate

V1 = replace(Params(),
             max_hire_cost=144.0, tiles_per_unit=7.0, animal_lead_days=6,
             target_sheep=5, target_cows=3, target_geese=0,
             # keep fertilizer effectively v1-gated for the baseline: same 0.85 gate as crops
             fert_sell_min_frac=1.0)
V2 = Params()

print("=== head-to-head: v2 (us) vs v1 params (opponent), 8 seeds x both seats ===")
out = evaluate(V2, episodes=8, seed=100, opponent=V1, both_seats=True)
print(f"v2 mean {out['mean']:.0f}  ± {out['stdev']:.0f}  min {out['min']:.0f}  max {out['max']:.0f}  (n={out['episodes']})")

print("=== reverse seat check: v1 params vs v2 as opponent ===")
out2 = evaluate(V1, episodes=8, seed=100, opponent=V2, both_seats=True)
print(f"v1 mean {out2['mean']:.0f}  ± {out2['stdev']:.0f}  min {out2['min']:.0f}  max {out2['max']:.0f}  (n={out2['episodes']})")

wins = sum(1 for a, b in zip(out["scores"], out2["scores"]) if a > b)
print(f"v2 beats v1 in {wins}/{len(out['scores'])} paired episodes")

print("=== v2 vs starter (standard-config sanity, target ~77k+) ===")
out3 = evaluate(V2, episodes=6, seed=200, opponent="starter", both_seats=True)
print(f"v2 vs starter mean {out3['mean']:.0f}  ± {out3['stdev']:.0f}  (n={out3['episodes']})")
