"""v10 A/B: dynamic, forward-priced crop choice vs the v8.1 fixed portfolio ladder."""
from dataclasses import replace

from harness import evaluate
from rules import Params

V10 = Params()
V81 = replace(Params(), forward_pricing=False, dynamic_crop_choice=False)

print("=== v10 dynamic+forward vs v8.1 fixed ladder, 8 seeds x both seats ===")
a = evaluate(V10, episodes=8, seed=700, opponent=V81, both_seats=True)
b = evaluate(V81, episodes=8, seed=700, opponent=V10, both_seats=True)
wins = sum(1 for x, y in zip(a["scores"], b["scores"]) if x > y)
deltas = [x - y for x, y in zip(a["scores"], b["scores"])]
print(f"v10  {a['mean']:>9,.0f}  +-{a['stdev']:>7,.0f}  min {a['min']:>9,.0f}")
print(f"v8.1 {b['mean']:>9,.0f}  +-{b['stdev']:>7,.0f}  min {b['min']:>9,.0f}")
print(f"v10 wins {wins}/{len(deltas)}  mean delta {sum(deltas)/len(deltas):+,.0f}  "
      f"worst {min(deltas):+,.0f}  best {max(deltas):+,.0f}")

print("\n=== uncontested sanity vs starter ===")
c = evaluate(V10, episodes=6, seed=800, opponent="starter", both_seats=True)
print(f"v10 vs starter {c['mean']:,.0f}  +-{c['stdev']:,.0f}")
