"""
Sweep seeds and rank what the agent is wasting. The debugging tool, not the tuning tool.

`harness.py` says whether a change helped. `diagnose.py` opens one episode by hand. This
runs many seeds and scores each one against every leak we have *already confirmed against
the engine* — so a regression shows up as a number instead of being found by reading a
24 MB replay again. Every detector here earned its place by having been a real bug:

  churn      selling and buying the same product on one turn. The engine quotes a buy at
             post-buy inventory so the cash nets zero (kaggriculture.py:576-578) — the cost
             is the hauling, and it cost 2.3k until `wheat_feed_reserve` got its cutoff.
  stranded   sellable stock still held when the reward latches. Scores exactly zero.
  unfed      placed animal that did not eat that day: zeroes its care bank (:796-800), and
             two in a row loses the animal outright.
  escaped    the animal actually walked. Worst case of the above.
  idle       PASS unit-turns. A hired hand costs wages whether or not it does anything.
  haul       PICKUP/DROP share of unit-turns. Pure logistics, produces nothing by itself.
  floor      SELL orders placed while the price sits at PRICE_FLOOR — a token dollar for
             stock that had an alternative. Attempts, not executions: see the caveat below.
  broke      turns with cash under `feed_cash_floor`. v4 shipped a bug that pinned cash at
             150 all episode and the score collapsed to 10k; it looked fine in the mean.

Attempts vs executions: action lists are what we *asked* for. Only shed/inventory deltas
are what happened. churn/floor are attempt counts (both are wrong to even ask for), the
rest are read off state.

    python leaks.py                    # default seed set, mirror self-play
    python leaks.py 700 701 42         # specific seeds
"""

import statistics
import sys
from collections import Counter

from env_adapter import SELLABLE

PRICE_FLOOR = 1
DEFAULT_SEEDS = [42, 700, 701, 702, 703, 704, 705, 706, 707, 393788841]


def _held(priv: dict) -> Counter:
    """Everything the player owns that a market would take: shed plus every pair of hands."""
    out = Counter(priv.get("shed") or {})
    for inv in priv.get("inventories") or []:
        out.update(inv)
    return out


def scan(steps: list, seat: int) -> dict:
    """One player's leaks over one episode, plus executed production for the floor gates
    (bank alone can hide a milk collapse behind a melon spike)."""
    ops: Counter = Counter()
    made: Counter = Counter()
    prev_held = None
    churn = floor = broke = unfed = escaped = 0
    unit_turns = 0
    prev_animals: dict | None = None
    day_seen = -1

    for st in steps:
        entry = st[seat]
        obs, act = entry.get("observation") or {}, entry.get("action") or {}
        farms = obs.get("farms") or []
        if len(farms) <= seat:
            continue
        farm, prices = farms[seat], (obs.get("market") or {}).get("prices") or {}
        priv_now = obs.get("private")
        if priv_now is not None:
            cur = _held(priv_now)
            if prev_held is not None:
                for item in ("MILK", "WOOL", "STRAWBERRY", "MELON"):
                    d = cur[item] - prev_held[item]
                    if d > 0:
                        made[item] += d
            prev_held = cur

        for op in (act.get("hands") or []) + [act.get("farmer") or []]:
            if op:
                ops[op[0]] += 1
                unit_turns += 1

        market = act.get("market") or []
        sells = {o[1] for o in market if o and o[0] == "SELL"}
        if sells & {o[1] for o in market if o and o[0] == "BUY_PRODUCT"}:
            churn += 1
        floor += sum(1 for item in sells if prices.get(item, 99) <= PRICE_FLOOR)
        if farm.get("money", 0) < 150:
            broke += 1

        # Animal state is only meaningful once per day; read it at the last hour so the
        # day's feeding has had all 24 turns to happen.
        if obs.get("hour") == 23 and obs.get("day") != day_seen:
            day_seen = obs.get("day")
            animals = {}
            for y, row in enumerate(farm.get("tiles") or []):
                for x, t in enumerate(row):
                    if isinstance(t, dict) and "animal" in t:
                        animals[(x, y)] = t
            # The last day is deliberately unfed — nothing produces on day 29, so feeding
            # it is pure cost. Counting it would flag the optimisation as a leak.
            if day_seen < 29:
                unfed += sum(1 for t in animals.values() if not t.get("fed_today"))
            if prev_animals is not None:
                escaped += len(set(prev_animals) - set(animals))
            prev_animals = animals

    last = steps[-1][seat]
    priv = (last.get("observation") or {}).get("private") or {}
    prices = ((last.get("observation") or {}).get("market") or {}).get("prices") or {}
    stranded = {k: v for k, v in _held(priv).items() if k in SELLABLE and v}
    # Only the shed can sell. Anything still in a pair of hands at the latch had to be
    # DROPped first and never was, which is a different bug from "held out for a price".
    in_hands = Counter()
    for inv in priv.get("inventories") or []:
        in_hands.update({k: v for k, v in inv.items() if k in SELLABLE})
    return {
        "score": float(last.get("reward") or 0.0),
        "milk": made["MILK"], "wool": made["WOOL"],
        "straw": made["STRAWBERRY"], "melon": made["MELON"],
        "churn": churn,
        "stranded$": sum(v * prices.get(k, 0) for k, v in stranded.items()),
        "hands$": sum(v * prices.get(k, 0) for k, v in in_hands.items()),
        "stranded": stranded,
        "unfed": unfed,
        "escaped": escaped,
        "idle%": 100 * ops["PASS"] / max(1, unit_turns),
        "haul%": 100 * (ops["PICKUP"] + ops["DROP"]) / max(1, unit_turns),
        "floor": floor,
        "broke": broke,
    }


def sweep(seeds: list[int], agent="main.py", opponent=None) -> list[dict]:
    """Mirror self-play by default: one episode yields a sample for each seat, and the
    contested market is the condition that actually decides the leaderboard."""
    from kaggle_environments import make

    opponent = opponent or agent
    rows = []
    cols = ("score", "churn", "stranded$", "hands$", "unfed", "escaped", "idle%", "haul%",
            "floor", "broke")
    print(f"{'seed':>11} {'st':>2} " + " ".join(f"{c:>9}" for c in cols))
    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([agent, opponent])
        for seat in (0, 1):
            r = scan(env.steps, seat)
            r["seed"], r["seat"] = seed, seat
            rows.append(r)
            print(f"{seed:>11} {seat:>2} " + " ".join(
                f"{r[c]:>9,.0f}" if isinstance(r[c], float) else f"{r[c]:>9,}" for c in cols),
                flush=True)
        del env  # a 720-step episode holds ~25 MB of observations

    print()
    for c in cols:
        vals = [r[c] for r in rows]
        worst = max(rows, key=lambda r: r[c])
        print(f"  {c:<10} mean {statistics.fmean(vals):>10,.1f}   worst {worst[c]:>10,.1f}"
              f"  (seed {worst['seed']}/{worst['seat']})")
    leaky = [r for r in rows if r["stranded$"] > 0]
    if leaky:
        merged = Counter()
        for r in leaky:
            merged.update(r["stranded"])
        print(f"\n  stranded stock across {len(leaky)}/{len(rows)} episodes: {dict(merged)}")
    return rows


if __name__ == "__main__":
    sweep([int(a) for a in sys.argv[1:]] or DEFAULT_SEEDS)
