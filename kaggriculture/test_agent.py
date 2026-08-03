"""
Submission safety tests. Run before every submit.

These do not check that the agent is *good* — the harness does that. They check the things
that turn a working agent into a zero: a module that will not import the way Kaggle imports
it, an action the interpreter rejects, an exception escaping `agent`, or a turn that blows
the 1-second budget.

    python test_agent.py
"""

import statistics
import time

import env_adapter
import rules
from env_adapter import ANIMALS, CROPS, water_window_start
from rules import Params, expected_yield, harvest_age

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}{'' if condition else '  <- ' + detail}")
    if not condition:
        FAILURES.append(name)


def test_entry_point() -> None:
    """Kaggle execs the file with a bare globals dict and takes the LAST callable."""
    print("entry point")
    from kaggle_environments.agent import get_last_callable
    fn = get_last_callable(open("main.py").read(), path="main.py")
    check("main.py imports under exec (no __file__)", True)
    check("last callable is `agent`", fn.__name__ == "agent", f"got {fn.__name__}")
    check("agent accepts (obs, config)", fn.__code__.co_argcount == 2)


def test_derived_economics() -> None:
    """The yield model the crop ranking depends on, checked against the shipped rules."""
    print("derived economics")
    check("melon harvests 6 units at age 10",
          (harvest_age("MELON"), expected_yield("MELON")) == (10, 6),
          f"{harvest_age('MELON')}, {expected_yield('MELON')}")
    check("carrot harvests 3 units at age 3",
          (harvest_age("CARROT"), expected_yield("CARROT")) == (3, 3))
    check("wheat harvests 4 units at age 4",
          (harvest_age("WHEAT"), expected_yield("WHEAT")) == (4, 4))
    check("harvest age is never before first_yield_day",
          all(harvest_age(c) >= CROPS[c]["first_yield_day"]
              for c in CROPS if not CROPS[c]["ongoing"]))
    check("water window start matches ceil(max_yield_day/2)",
          water_window_start("MELON") == 6 and water_window_start("WHEAT") == 2)


def test_action_shape() -> None:
    """Serialized actions must match the interpreter's expectations exactly."""
    print("action shape")
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 40, "seed": 1})
    bad: list[str] = []

    def checker(observation, configuration=None):
        obs = env_adapter.parse(observation, configuration)
        act = env_adapter.serialize(rules.decide(obs, Params()), obs)
        if set(act) != {"farmer", "hands", "market"}:
            bad.append(f"keys {set(act)}")
        if len(act["hands"]) != len(obs.units) - 1:
            bad.append(f"hands {len(act['hands'])} vs units {len(obs.units)}")
        if len(act["market"]) > obs.max_market_orders:
            bad.append(f"market orders {len(act['market'])}")
        for op in [act["farmer"], *act["hands"]]:
            if not isinstance(op, list) or not op or not isinstance(op[0], str):
                bad.append(f"malformed unit op {op!r}")
        # PLANT is validated atomically: exceeding seeds drops every PLANT that turn.
        wanted: dict[str, int] = {}
        for op in [act["farmer"], *act["hands"]]:
            if op[0] == "PLANT":
                wanted[op[1]] = wanted.get(op[1], 0) + 1
        for crop, n in wanted.items():
            if n > obs.seeds.get(crop, 0):
                bad.append(f"over-planted {crop}: {n} ops vs {obs.seeds.get(crop, 0)} seeds")
        return act

    env.run([checker, "starter"])
    check("action dict well-formed every turn", not bad, "; ".join(sorted(set(bad))[:3]))


def test_never_raises() -> None:
    """`agent` must swallow everything — an exception forfeits the episode."""
    print("fail-soft")
    from kaggle_environments.agent import get_last_callable
    agent = get_last_callable(open("main.py").read(), path="main.py")
    for label, obs in [
        ("empty dict", {}),
        ("no farms", {"player": 0, "day": 0, "hour": 0}),
        ("garbage tiles", {"player": 0, "farms": [{"money": 1, "tiles": "nope"}]}),
        ("None private", {"player": 0, "farms": [{"money": 1, "tiles": [[None]]}],
                          "private": None}),
        ("player out of range", {"player": 5, "farms": [], "private": {}}),
    ]:
        try:
            out = agent(obs, {})
            check(f"survives {label}", isinstance(out, dict) and "farmer" in out)
        except Exception as exc:
            check(f"survives {label}", False, repr(exc))


def test_alternate_configs() -> None:
    """The leaderboard may not run the defaults. Nothing may crash, seat included."""
    print("alternate configurations")
    from kaggle_environments import make
    for label, cfg, seat in [
        ("short season (200 steps)", {"episodeSteps": 200}, 0),
        ("small board (6x6)", {"episodeSteps": 240, "boardSize": 6}, 0),
        ("seat 1", {"episodeSteps": 240}, 1),
        ("expensive hands", {"episodeSteps": 240, "farmHandCostMult": 20}, 0),
        ("tiny shed", {"episodeSteps": 240, "shedCapacity": 10}, 0),
    ]:
        cfg = dict(cfg, seed=5)
        env = make("kaggriculture", configuration=cfg, debug=True)
        players = ["main.py", "starter"] if seat == 0 else ["starter", "main.py"]
        try:
            env.run(players)
            reward = env.steps[-1][seat].reward
            status = env.steps[-1][seat].status
            check(f"{label}: finished (score {reward:,.0f})",
                  status == "DONE" and reward is not None and reward > 0, f"status={status}")
        except Exception as exc:
            check(f"{label}: finished", False, repr(exc))


def test_latency() -> None:
    """actTimeout is 1s per turn with 60s of episode overage."""
    print("latency")
    from kaggle_environments import make
    times: list[float] = []
    p = Params()

    def timed(observation, configuration=None):
        t0 = time.perf_counter()
        obs = env_adapter.parse(observation, configuration)
        out = env_adapter.serialize(rules.decide(obs, p), obs)
        times.append(time.perf_counter() - t0)
        return out

    make("kaggriculture", configuration={"episodeSteps": 720, "seed": 2}).run([timed, "starter"])
    worst, total = max(times) * 1000, sum(times)
    check(f"worst turn {worst:.1f}ms < 1000ms", worst < 500, f"{worst:.1f}ms")
    check(f"episode total {total:.1f}s well under budget", total < 30, f"{total:.1f}s")
    print(f"        mean {statistics.fmean(times) * 1000:.2f}ms over {len(times)} turns")


if __name__ == "__main__":
    for fn in (test_entry_point, test_derived_economics, test_action_shape,
               test_never_raises, test_alternate_configs, test_latency):
        fn()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {', '.join(FAILURES)}")
        raise SystemExit(1)
    print("all submission checks passed")
