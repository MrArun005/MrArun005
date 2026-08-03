"""
Threshold search over Params, driven by the harness.

Coordinate descent: sweep one parameter's candidate values at a time, keep a change only
if it beats the incumbent by more than the noise floor, repeat until a full pass finds
nothing. Deliberately not a fancy optimizer — with ~2.5s per episode and a noisy reactive
market, the budget goes into *episodes per candidate*, not into search cleverness.

Every candidate is scored on the same seed set as the incumbent (paired), and a win has
to clear `--sigma` paired standard errors to be accepted. Without that gate you spend the
afternoon ratcheting on noise.

    python tune.py --episodes 8 --sigma 1.5
    python tune.py --episodes 8 --opponent self      # self-play: contests the market
"""

import argparse
import json
import os
import statistics
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

from rules import Params, params_dict

PARAMS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params.json")

# Ordered by expected leverage — the first pass should move the big rocks first.
GRID: dict[str, list] = {
    "melon_tile_cap":        [16, 24, 32, 40, 50, 64],
    "sell_min_frac":         [0.45, 0.58, 0.72, 0.85, 0.95],
    "sell_chunk":            [2, 3, 5, 8, 12],
    "max_hands":             [8, 11, 14, 17, 20],
    "hands_per_tile":        [0.08, 0.11, 0.14, 0.18, 0.24],
    "move_cost":             [0.4, 0.6, 0.9, 1.4, 2.0],
    "seed_buffer":           [12, 20, 30, 45],
    "land_empty_threshold":  [3, 6, 12, 20, 999],
    "shed_pressure_frac":    [0.3, 0.5, 0.7],
    "sell_min_frac_pressure": [0.1, 0.28, 0.5],
    "dump_turns":            [12, 26, 48, 72],
    "seed_cash_reserve":     [120.0, 400.0, 900.0],
    "land_cash_reserve":     [600.0, 1200.0, 2500.0],
    "hire_until_hour":       [1, 4, 8],
    "prio_water_bonus":      [40.0, 60.0, 85.0],
    "prio_plant":            [25.0, 38.0, 55.0, 75.0],
    "prio_harvest_ready":    [55.0, 70.0, 90.0],
    "haul_threshold":        [6, 14, 40],
    "target_sheep":          [0, 2, 4, 6, 9],
    "target_cows":           [0, 2, 4, 6],
    "target_geese":          [0, 2, 4],
    "animal_cash_reserve":   [2000.0, 5000.0, 9000.0, 15000.0],
    "feed_reserve_days":     [2.0, 3.0, 5.0],
    "last_animal_day":       [14, 18, 21, 24],
    "animals_per_turn":      [1, 2, 4],
    "wheat_pickup_batch":    [3, 6, 10],
}


def _score_one(job):
    """Worker: one episode. Imports live in here so each process pays it once."""
    param_kwargs, seed, opponent, seat = job
    import harness
    params = Params(**param_kwargs)
    opp = params if opponent == "self" else opponent
    try:
        return harness.run_episode(params, seed, opp, seat)
    except Exception as exc:            # a crash is a real defect: score it as a loss
        print(f"  ! episode crashed (seed={seed}): {exc!r}")
        return 0.0


def score(params: Params, seeds: list[int], opponent: str, pool, both_seats: bool) -> list[float]:
    kwargs = params_dict(params)
    seats = (0, 1) if both_seats else (0,)
    jobs = [(kwargs, s, opponent, seat) for s in seeds for seat in seats]
    return list(pool.map(_score_one, jobs))


def _verdict(candidate: list[float], incumbent: list[float], sigma: float):
    diffs = [c - b for c, b in zip(candidate, incumbent)]
    delta = statistics.fmean(diffs)
    se = statistics.stdev(diffs) / len(diffs) ** 0.5 if len(diffs) > 1 else 0.0
    return delta, se, delta > sigma * se and delta > 0


def tune(episodes=8, seed=0, opponent="starter", sigma=1.5, passes=2, both_seats=False,
         only: list[str] | None = None, workers=4):
    seeds = [seed + i for i in range(episodes)]
    best = _load()
    keys = [k for k in GRID if not only or k in only]

    with ProcessPoolExecutor(max_workers=workers) as pool:
        base_scores = score(best, seeds, opponent, pool, both_seats)
        print(f"start  mean {statistics.fmean(base_scores):>10,.0f}  "
              f"(n={len(base_scores)}, opponent={opponent})\n")

        for p_no in range(passes):
            improved = False
            for key in keys:
                current = getattr(best, key)
                for value in GRID[key]:
                    if value == current:
                        continue
                    cand = replace(best, **{key: value})
                    cand_scores = score(cand, seeds, opponent, pool, both_seats)
                    delta, se, win = _verdict(cand_scores, base_scores, sigma)
                    flag = "ACCEPT" if win else "      "
                    print(f"{flag} {key:<24} {str(current):>8} -> {str(value):<8} "
                          f"delta {delta:>+9,.0f} ± {se:>7,.0f}")
                    if win:
                        best, base_scores, current, improved = cand, cand_scores, value, True
            print(f"\n-- pass {p_no + 1} done: mean {statistics.fmean(base_scores):>10,.0f}"
                  f"{'' if improved else '  (no change, stopping)'}\n")
            if not improved:
                break

    _save(best)
    print("tuned params written to", PARAMS_FILE)
    print(json.dumps(params_dict(best), indent=2, sort_keys=True))
    return best


def _load() -> Params:
    try:
        with open(PARAMS_FILE) as fh:
            data = json.load(fh)
        fields = set(Params.__dataclass_fields__)
        return Params(**{k: v for k, v in data.items() if k in fields})
    except Exception:
        return Params()


def _save(params: Params) -> None:
    with open(PARAMS_FILE, "w") as fh:
        json.dump(params_dict(params), fh, indent=2, sort_keys=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--opponent", default="starter", help="starter | pass | random | self")
    ap.add_argument("--sigma", type=float, default=1.5)
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--both-seats", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", nargs="*", help="restrict the search to these params")
    args = ap.parse_args()
    tune(args.episodes, args.seed, args.opponent, args.sigma, args.passes,
         args.both_seats, args.only, args.workers)
