"""
Threshold search over Params, driven by the harness.

Coordinate descent: sweep one parameter's candidate values at a time, keep a change only
if it beats the incumbent by more than the noise floor, repeat until a full pass finds
nothing. Deliberately not a fancy optimizer — with ~2.5s per episode and a noisy reactive
market, the budget goes into *episodes per candidate*, not into search cleverness.

Every candidate is scored on the same seed set as the incumbent (paired), and a win must
clear BOTH `--sigma` paired standard errors and an absolute effect floor
(`--min-effect-frac`, default 0.5% of the baseline mean). Significance alone is not enough:
episodes are deterministic given a seed, so a change that nudges every episode identically
has a near-zero standard error and clears any sigma gate on a +5 coin difference.

Whatever this search produces, validate it **out of sample** — on seeds it never saw — before
shipping. Coordinate descent over ~28 knobs on 8 seeds can memorise the seed set.

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
    # Ordered by measured leverage. Keys a sensitivity audit showed cannot change the
    # outcome under default config are deliberately ABSENT — max_hands, max_hire_cost,
    # hire_until_hour, hire/land/seed cash reserves, haul_threshold, prio_haul,
    # prio_haul_final, prio_pickup, shed_force_frac, final_dump_turns, last_animal_day and
    # melon_bias are masked by tighter constraints upstream. They remain in Params as
    # defensive rails for off-default configurations; searching them was ~26% of a previous
    # run's budget and produced bit-identical episodes every time.
    "melon_tile_cap":        [16, 20, 24, 28, 32],
    "prio_harvest_ready":    [40.0, 47.0, 55.0, 62.0, 70.0],
    "prio_plant":            [25.0, 32.0, 38.0, 45.0],
    "hands_per_tile":        [0.09, 0.10, 0.11, 0.12, 0.13],
    "prio_water_urgent":     [75.0, 85.0, 95.0, 110.0],
    "move_cost":             [0.2, 0.3, 0.4, 0.5, 0.6],
    "prio_water_bonus":      [45.0, 52.0, 60.0, 70.0],
    "sell_chunk":            [5, 6, 8, 10],
    "last_land_day":         [12, 14, 15, 16, 18],
    "land_empty_threshold":  [4, 6, 8],
    "land_lead_days":        [3, 5, 8],
    "land_payback_mult":     [1.0, 1.5, 3.0, 6.0],
    "tiles_per_unit":        [5.0, 6.0, 7.0, 9.0, 12.0],
    "shed_pressure_frac":    [0.35, 0.5, 0.65],
    "sell_min_frac":         [0.70, 0.78, 0.85, 0.92],
    "seed_buffer":           [8, 12, 16],
    # Livestock ranges re-centred on v2's replay-derived targets (winners run 8-11 animals),
    # and the fertilizer knobs added with it. animal_lead_days floors at 7: 6 lets a goose
    # through the season gate on 240-step configs and re-breaks test_agent's alternates.
    "target_sheep":          [4, 5, 6, 8],
    "target_cows":           [3, 4, 6, 8],
    "target_geese":          [0, 2, 3, 5],
    "fert_sell_min_frac":    [0.15, 0.25, 0.40, 0.60],
    "prio_collect_fert":     [35.0, 50.0, 65.0],
    "animal_cash_reserve":   [2000.0, 2500.0, 3000.0, 4000.0],
    "animal_lead_days":      [7, 8, 9],
    "prio_animal_care":      [28.0, 34.0, 40.0, 48.0],
    "prio_place_animal":     [80.0, 100.0, 120.0],
    "prio_build":            [34.0, 40.0, 46.0, 55.0],
    "prio_feed_relaxed":     [55.0, 72.0, 90.0],
    "prio_animal_harvest_partial": [22.0, 33.0, 44.0],
    "prio_dig":              [14.0, 22.0, 30.0],
    "feed_reserve_days":     [1.5, 2.0, 2.5],
    "animals_per_turn":      [1, 2, 3],
    "build_ahead_frac":      [0.5, 0.75, 1.0],
    "tiles_per_shed_slot":   [0.8, 1.0, 1.3],
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


def _verdict(candidate: list[float], incumbent: list[float], sigma: float,
             min_effect: float = 0.0):
    """Accept only wins that are both statistically real and worth having.

    The significance gate alone is not enough. Episodes are deterministic given a seed, so a
    change that shifts every episode by the same tiny amount has a near-zero paired standard
    error and clears any sigma threshold — this search accepted a +5 coin change on a 69,000
    baseline at 1.7 sigma. Ratcheting through dozens of those fits the seed set, not the game,
    so a win must also clear an absolute effect floor.
    """
    diffs = [c - b for c, b in zip(candidate, incumbent)]
    delta = statistics.fmean(diffs)
    se = statistics.stdev(diffs) / len(diffs) ** 0.5 if len(diffs) > 1 else 0.0
    return delta, se, delta > sigma * se and delta > max(0.0, min_effect)


def tune(episodes=8, seed=0, opponent="starter", sigma=1.5, passes=2, both_seats=False,
         only: list[str] | None = None, workers=4, min_effect_frac=0.005):
    seeds = [seed + i for i in range(episodes)]
    best = _load()
    keys = [k for k in GRID if not only or k in only]

    with ProcessPoolExecutor(max_workers=workers) as pool:
        base_scores = score(best, seeds, opponent, pool, both_seats)
        min_effect = min_effect_frac * abs(statistics.fmean(base_scores))
        print(f"start  mean {statistics.fmean(base_scores):>10,.0f}  "
              f"(n={len(base_scores)}, opponent={opponent}, "
              f"need >{sigma}sigma and >{min_effect:,.0f})\n")

        for p_no in range(passes):
            improved = False
            for key in keys:
                current = getattr(best, key)
                for value in GRID[key]:
                    if value == current:
                        continue
                    cand = replace(best, **{key: value})
                    cand_scores = score(cand, seeds, opponent, pool, both_seats)
                    delta, se, win = _verdict(cand_scores, base_scores, sigma, min_effect)
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
    ap.add_argument("--min-effect-frac", type=float, default=0.005,
                    help="minimum win as a fraction of baseline mean (effect-size floor)")
    args = ap.parse_args()
    tune(args.episodes, args.seed, args.opponent, args.sigma, args.passes,
         args.both_seats, args.only, args.workers, args.min_effect_frac)
