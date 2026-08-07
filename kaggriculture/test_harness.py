"""Guards the guard: a crashed agent must not be reported as a score.

kaggle_environments swallows agent exceptions, so before this check a policy that
raised every turn came back as a clean 3,000.0 (starting cash) with status DONE.
That silently poisons every tune.py search. Run: python test_harness.py
"""
from kaggle_environments import make

import harness
from rules import Params


def _run(agent, steps=20):
    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": 1})
    env.run([agent, "starter"])
    return env


def main():
    def boom(obs, config=None):
        raise RuntimeError("agent blew up")

    env = _run(boom)
    # The premise: the env really does hide the crash behind a plausible score.
    assert env.steps[-1][0].status == "DONE", env.steps[-1][0].status
    assert env.steps[-1][0].reward == 3000.0, env.steps[-1][0].reward
    print(f"  ok    env hides the crash: status DONE, reward {env.steps[-1][0].reward}")

    assert "Traceback" in harness._crash_traceback(env, (0,)), "crash not detected"
    print("  ok    _crash_traceback finds it in env.logs")

    # Seat scoping: seat 1 ran fine, so looking only at seat 1 must stay quiet.
    assert harness._crash_traceback(env, (1,)) == "", "false positive on the clean seat"
    print("  ok    clean seat reports no crash")

    # A healthy episode must still return a score, not trip the guard.
    score = harness.run_episode(Params(), seed=1, opponent="starter",
                                configuration={"episodeSteps": 60})
    assert score > 0, score
    print(f"  ok    healthy episode still scores ({score:,.0f}), guard stays quiet")

    print("\nharness guard ok")


if __name__ == "__main__":
    main()
