"""
Submission entry point for the Kaggriculture competition.

Kaggle resolves the entry point with `get_last_callable`, which takes the *last
callable defined in this module*. So `agent` must stay at the bottom of the file —
do not add functions below it.

Rules of the road for submissions:
  - fail SOFT. An exception forfeits the episode; a bad-but-valid action just
    scores poorly. Never let this raise.
  - stay inside the per-turn budget (actTimeout = 1s, 60s total overage).

Submit as a tar.gz so the sibling modules ride along:
    tar -czf submission.tar.gz main.py env_adapter.py rules.py
    kaggle competitions submit kaggriculture -f submission.tar.gz -m "..."
"""

import os
import sys

# The loader appends this file's directory to sys.path only while the module body
# executes, so sibling imports must happen at import time — not lazily inside agent().
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import env_adapter
from rules import Params, decide

PARAMS = Params()          # tune.py writes the searched values into params.json
_PARAMS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params.json")


def _load_tuned_params() -> Params:
    """Pick up tuned thresholds if tune.py has written them; defaults otherwise."""
    try:
        import json
        with open(_PARAMS_FILE) as fh:
            data = json.load(fh)
        fields = {f for f in Params.__dataclass_fields__}
        return Params(**{k: v for k, v in data.items() if k in fields})
    except Exception:
        return Params()


PARAMS = _load_tuned_params()


def _safe_action(observation) -> dict:
    """A valid no-op sized to however many hands we currently have."""
    hands = 0
    try:
        player = observation.get("player", 0)
        hands = len(observation.get("farms", [])[player].get("hands", []) or [])
    except Exception:
        hands = 0
    return {"farmer": ["PASS"], "hands": [["PASS"]] * hands, "market": []}


def agent(observation, configuration=None):
    try:
        obs = env_adapter.parse(observation, configuration)
        return env_adapter.serialize(decide(obs, PARAMS), obs)
    except Exception:
        # Never crash. A no-op beats a forfeit.
        return _safe_action(observation)
