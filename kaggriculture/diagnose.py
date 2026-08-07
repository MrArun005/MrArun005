"""
Per-episode instrumentation. Answers "where is the money not coming from".

The harness tells you whether a change helped. This tells you *what to change*: how many
unit-turns are idle, how much produce rots in the shed, whether land and hands keep up
with the tile count, and what each product actually sold for.

    python diagnose.py --seed 7 --opponent starter
"""

import argparse
from collections import Counter

import env_adapter
import rules
from env_adapter import BASE_PRICE, CROPS, SELLABLE
from rules import Params


def diagnose(params: Params, seed: int = 7, opponent="starter", days_shown=(0, 5, 10, 15, 20, 25, 29)):
    from kaggle_environments import make

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    stats = {
        "unit_turns": 0, "idle": 0, "ops": Counter(), "sold": Counter(),
        "revenue": Counter(), "max_shed": 0, "hands_by_day": {}, "peak_units": 0,
    }
    snaps = []
    prev_shed: dict[str, int] = {}
    prev_cash = [0.0]

    def instrumented(observation, configuration=None):
        obs = env_adapter.parse(observation, configuration)
        crop = rules.choose_crop(obs, params)
        tasks = rules.build_tasks(obs, params, crop)
        ops = rules.assign(obs, params, tasks, rules.plant_budget(obs, params, crop))

        stats["unit_turns"] += len(obs.units)
        stats["peak_units"] = max(stats["peak_units"], len(obs.units))
        for op in ops[: len(obs.units)]:
            stats["ops"][op[0]] += 1
            if op[0] == "PASS":
                stats["idle"] += 1
        stats["max_shed"] = max(stats["max_shed"], obs.shed_used)
        stats["hands_by_day"][obs.day] = max(
            stats["hands_by_day"].get(obs.day, 0), len(obs.units) - 1)

        # Infer completed sales from shed deltas plus the cash delta.
        for item in SELLABLE:
            drop = prev_shed.get(item, 0) - obs.shed.get(item, 0)
            if drop > 0:
                stats["sold"][item] += drop
                stats["revenue"][item] += drop * obs.prices.get(item, BASE_PRICE[item])
        prev_shed.clear()
        prev_shed.update(obs.shed)
        prev_cash[0] = obs.cash

        if obs.hour == 0 and obs.day in days_shown:
            counts = Counter(t.crop for t in obs.tiles if t.state == "PLANT")
            snaps.append({
                "day": obs.day, "cash": obs.cash, "opp": obs.opponent_cash,
                "tiles": dict(counts),
                "empty": sum(1 for t in obs.tiles if t.state == "EMPTY"),
                "weeds": sum(1 for t in obs.tiles if t.state == "WEED"),
                "land": len(obs.unlocked_quadrants), "hands": len(obs.units) - 1,
                "shed": obs.shed_used,
                "prices": {k: obs.prices.get(k) for k in ("MELON", "CARROT", "WHEAT")},
            })
        return env_adapter.serialize(rules.Action(unit_ops=ops,
                                                 market=rules.market_plan(obs, params)), obs)

    env.run([instrumented, opponent])
    final = env.steps[-1]
    me, opp = float(final[0].reward or 0), float(final[1].reward or 0)

    print(f"FINAL  us {me:,.0f}   opponent {opp:,.0f}   ({'WIN' if me > opp else 'LOSS'})\n")
    print("day  cash      opp      land hands empty weeds shed  tiles                     prices")
    for s in snaps:
        print(f"{s['day']:>3}  {s['cash']:>9,.0f} {s['opp']:>8,.0f}  {s['land']:>3} "
              f"{s['hands']:>5} {s['empty']:>5} {s['weeds']:>5} {s['shed']:>4}  "
              f"{str(s['tiles']):<26} {s['prices']}")

    ut = max(1, stats["unit_turns"])
    print(f"\nunit-turns {stats['unit_turns']:,}   idle {stats['idle']:,} "
          f"({100 * stats['idle'] / ut:.1f}%)   peak units {stats['peak_units']}")
    print("ops:", dict(stats["ops"].most_common()))
    print(f"peak shed {stats['max_shed']}/100")
    print("\nitem        sold    revenue    avg $")
    for item, n in stats["sold"].most_common():
        rev = stats["revenue"][item]
        print(f"{item:<10} {n:>6}  {rev:>9,.0f}  {rev / max(1, n):>7.1f}"
              f"   (base {BASE_PRICE[item]})")
    print(f"{'TOTAL':<10} {sum(stats['sold'].values()):>6}  {sum(stats['revenue'].values()):>9,.0f}")
    return me


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--opponent", default="starter")
    args = ap.parse_args()
    diagnose(Params(), args.seed, args.opponent)
