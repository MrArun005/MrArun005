"""Does the demand mix change between games? Unlock order is rng-driven per episode."""
from collections import Counter

from kaggle_environments import make

SHOPS = {
    "BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}

for seed in (901, 902, 903, 904):
    env = make("kaggriculture", configuration={"seed": seed}, debug=False)
    env.run(["nb_v9/decoded_main.py", "nb_v9/decoded_main.py"])
    order = []
    seen = set()
    for si, st in enumerate(env.steps):
        shops = tuple((st[0]["observation"].get("town") or {}).get("unlocked_shops") or ())
        for s in shops:
            if s not in seen:
                seen.add(s)
                order.append((si // 24, s))
    # demand weight per product with the shops unlocked by day 12
    early = [s for d, s in order if d <= 12]
    w = Counter()
    for s in early:
        prods = SHOPS[s]
        for p in prods:
            w[p] += 2 if len(prods) == 1 else 1
    print(f"seed {seed}: unlocks {[f'{d}:{s}' for d, s in order]}")
    print(f"          demand weight by day 12: {dict(w.most_common())}")
