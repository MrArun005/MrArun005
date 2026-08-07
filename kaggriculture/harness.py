"""
Local evaluation harness. The point is variance, not mean.

Kaggriculture has a reactive shared market, random weed spawns and a randomly ordered
town-shop unlock schedule, so single-episode scores are close to meaningless. If you tune
on one run you will confidently ship a worse agent. Rule of thumb below: treat a change as
real only if it clears ~2 standard errors of the *paired* delta.

Usage:
    python harness.py --episodes 30 --seed 7
    python harness.py --episodes 30 --opponent starter --both-seats
"""

import argparse
import statistics

from rules import Params, decide
import env_adapter

_ENV_NAME = "kaggriculture"


def make_agent(params: Params, strict: bool = True):
    """A stateless agent closure bound to a specific Params.

    `strict` re-raises instead of falling back to PASS. Submissions must fail soft, but
    during development that silently turns a crash into a do-nothing agent that still
    "scores" — which is how you end up tuning a broken policy. Default to loud here.
    """

    def _agent(observation, configuration=None):
        try:
            obs = env_adapter.parse(observation, configuration)
            return env_adapter.serialize(decide(obs, params), obs)
        except Exception:
            if strict:
                raise
            hands = 0
            try:
                player = observation.get("player", 0)
                hands = len(observation.get("farms", [])[player].get("hands", []) or [])
            except Exception:
                pass
            return {"farmer": ["PASS"], "hands": [["PASS"]] * hands, "market": []}

    return _agent


def _crash_traceback(env, seats) -> str:
    """The traceback of the first crashed seat, or "" if all ran clean.

    `make_agent(strict=True)` cannot actually be loud on its own: kaggle_environments
    catches whatever the agent closure raises one layer above it, so a policy that
    raises on every single turn still finishes with status DONE and a tidy
    starting-cash reward. Measured, not assumed — an agent that raised 20/20 turns
    scored 3,000.0 with no exception reaching the caller and nothing on our stderr.

    That is the worst failure mode this project has: a broken policy is indistinguishable
    from a merely bad one, so tune.py scores the wreckage and moves on. env.logs is the
    only place the evidence survives.
    """
    for step_logs in env.logs or []:
        for seat in seats:
            entry = step_logs[seat] if seat < len(step_logs) else None
            stderr = (entry or {}).get("stderr") or ""
            if "Traceback" in stderr:  # substring, not just truthy: benign warnings land here too
                return stderr
    return ""


def run_episode(params: Params, seed: int, opponent="starter", seat: int = 0,
                configuration: dict | None = None) -> float:
    """Drive the shipped simulator; return our final score (cash).

    `seat` matters: market orders resolve in player order, so seat 0 has a small
    structural edge. Evaluate on both seats to avoid tuning into that artefact.

    Raises if either of our agents crashed — see `_crash_traceback`. Every eval path
    (evaluate, compare, benchmark, tune.py, sweep_expensive.py) funnels through here,
    so this is the one place the check has to live.
    """
    from kaggle_environments import make

    config = {"episodeSteps": 720, "seed": seed}
    if configuration:
        config.update(configuration)
    env = make(_ENV_NAME, configuration=config)

    me = make_agent(params)
    opp = make_agent(opponent) if isinstance(opponent, Params) else opponent
    players = [me, opp] if seat == 0 else [opp, me]
    env.run(players)

    # Check the opponent seat too when the opponent is our own code — a crashed baseline
    # silently turns a paired comparison into "we beat a corpse".
    ours = (0, 1) if isinstance(opponent, Params) else (seat,)
    crash = _crash_traceback(env, ours)
    if crash:
        raise RuntimeError(
            f"agent crashed during episode (seed={seed}, seat={seat}); "
            f"score would have been a meaningless {env.steps[-1][seat].reward}:\n{crash}")

    return float(env.steps[-1][seat].reward or 0.0)


def _summary(scores: list[float], episodes: int) -> dict:
    stdev = statistics.stdev(scores) if len(scores) > 1 else 0.0
    return {
        "episodes": episodes,
        "mean": statistics.fmean(scores) if scores else 0.0,
        "stdev": stdev,
        "stderr": stdev / (len(scores) ** 0.5) if scores else 0.0,
        "min": min(scores, default=0.0),
        "max": max(scores, default=0.0),
    }


def evaluate(params: Params, episodes: int = 30, seed: int = 0, opponent="starter",
             both_seats: bool = False, configuration: dict | None = None) -> dict:
    scores: list[float] = []
    seats = (0, 1) if both_seats else (0,)
    for i in range(episodes):
        for seat in seats:
            scores.append(run_episode(params, seed + i, opponent, seat, configuration))
    out = _summary(scores, len(scores))
    out["scores"] = scores
    return out


def compare(baseline: Params, candidate: Params, episodes: int = 30, seed: int = 0,
            opponent="starter", both_seats: bool = False, quiet: bool = False):
    """Same seeds for both — paired comparison, much lower variance than two
    independent means. The paired stderr is what the verdict is based on."""
    b = evaluate(baseline, episodes, seed, opponent, both_seats)
    c = evaluate(candidate, episodes, seed, opponent, both_seats)
    diffs = [x - y for x, y in zip(c["scores"], b["scores"])]
    delta = statistics.fmean(diffs)
    paired_se = (statistics.stdev(diffs) / len(diffs) ** 0.5) if len(diffs) > 1 else 0.0
    verdict = "REAL" if paired_se and abs(delta) > 2 * paired_se else "NOISE"
    if not quiet:
        print(f"baseline  {b['mean']:>12.0f}  ± {b['stdev']:.0f}")
        print(f"candidate {c['mean']:>12.0f}  ± {c['stdev']:.0f}")
        print(f"delta     {delta:>12.0f}  ± {paired_se:.0f} (paired se)  -> {verdict}")
    return delta, paired_se, verdict


def benchmark(episodes: int = 20, seed: int = 0, both_seats: bool = True):
    """Score against every built-in opponent, both seats."""
    base = Params()
    for opponent in ("pass", "starter", "random"):
        out = evaluate(base, episodes, seed, opponent, both_seats)
        print(f"vs {opponent:<8} mean {out['mean']:>10.0f}  ± {out['stdev']:>8.0f}"
              f"  min {out['min']:>9.0f}  max {out['max']:>10.0f}  (n={out['episodes']})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--opponent", default="starter")
    ap.add_argument("--both-seats", action="store_true")
    ap.add_argument("--benchmark", action="store_true")
    args = ap.parse_args()

    if args.benchmark:
        benchmark(args.episodes, args.seed)
    else:
        base = Params()
        out = evaluate(base, args.episodes, args.seed, args.opponent, args.both_seats)
        out.pop("scores", None)
        print(out)
