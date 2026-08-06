"""
Submission entry point for the Kaggriculture competition.

Two hard constraints imposed by how Kaggle loads this file, both verified against
`kaggle_environments/agent.py`:

  1. The entry point is resolved with `get_last_callable`, which takes the *last callable
     defined in the module namespace*. So `agent` must stay at the bottom — do not add
     functions below it.
  2. The file is `exec`'d against a bare globals dict, so **`__file__` does not exist**.
     Referencing it raises NameError at import and the submission is rejected outright.
     The loader does append this file's directory to `sys.path` for the duration of the
     module body, which is why the sibling imports below work and why they must happen at
     import time rather than lazily inside `agent`.

Rules of the road:
  - fail SOFT. An exception forfeits the episode; a bad-but-valid action just scores
    poorly. Never let `agent` raise.
  - stay inside the per-turn budget (actTimeout = 1s, plus 60s of episode overage).

Submit as a tar.gz so the sibling modules ride along:
    tar -czf submission.tar.gz main.py env_adapter.py rules.py params.json
    kaggle competitions submit kaggriculture -f submission.tar.gz -m "..."
"""

import os
import sys


def _candidate_dirs():
    """Where our sibling files might live, best guess first.

    `__file__` is read through `globals()` because it is genuinely absent under Kaggle's
    exec-based loader; a direct reference is a NameError, not a fallback.
    """
    found, out = set(), []
    here = globals().get("__file__")
    for d in ([os.path.dirname(os.path.abspath(here))] if here else []) + list(sys.path) + [os.getcwd()]:
        if d and d not in found:
            found.add(d)
            out.append(d)
    return out


_DIRS = [d for d in _candidate_dirs() if os.path.isfile(os.path.join(d, "env_adapter.py"))]
for _d in reversed(_DIRS):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import env_adapter
from rules import Params, decide


def _load_tuned_params():
    """Pick up tune.py's searched thresholds if they shipped; defaults otherwise."""
    import json
    for d in _DIRS or _candidate_dirs():
        path = os.path.join(d, "params.json")
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as fh:
                data = json.load(fh)
            fields = set(Params.__dataclass_fields__)
            return Params(**{k: v for k, v in data.items() if k in fields})
        except Exception:
            # A corrupt params.json earlier in the search order must not mask a valid
            # one later — and the failure belongs in the Kaggle logs, not in silence.
            import traceback
            print(f"params.json at {path} unusable, trying next candidate:",
                  file=sys.stderr)
            traceback.print_exc()
            continue
    return Params()


PARAMS = _load_tuned_params()


def _safe_action(observation):
    """A valid no-op, sized to however many hands we currently have."""
    hands = 0
    try:
        player = observation.get("player", 0)
        hands = len(observation.get("farms", [])[player].get("hands", []) or [])
    except Exception:
        hands = 0
    return {"farmer": ["PASS"], "hands": [["PASS"]] * hands, "market": []}


_ERRORS_LOGGED = 0


def agent(observation, configuration=None):
    global _ERRORS_LOGGED
    try:
        obs = env_adapter.parse(observation, configuration)
        return env_adapter.serialize(decide(obs, PARAMS), obs)
    except Exception:
        # Never crash — a no-op beats a forfeit. But say so: a swallowed exception makes a
        # broken build indistinguishable from a weak policy, and stderr survives into
        # `kaggle competitions logs <episode> <seat>`. First few only; 720 tracebacks of
        # the same bug help nobody.
        if _ERRORS_LOGGED < 3:
            _ERRORS_LOGGED += 1
            import traceback
            print(f"agent error at step {observation.get('step', '?')} "
                  f"(falling back to PASS):", file=sys.stderr)
            traceback.print_exc()
        return _safe_action(observation)
