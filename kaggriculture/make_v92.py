"""v9.2 = the v22 tape + idle-worker overlay, emitted as one self-contained main.py.

Only units the tape has PASSing are touched, and only with operations that leave the
unit standing where it is, so the route never desynchronizes:

  CARE               on a fed, uncared animal   -> banks +1 product (engine :799-800)
  COLLECT_FERTILIZER on an animal with one ready -> ~$100 byproduct
  HARVEST            animal, or an ONGOING crop  -> both re-accumulate, so early
                     collection only avoids hitting the max_held/max_yield cap

Deliberately excluded: HARVEST on non-ongoing crops (wheat/carrot/melon). Those tiles
vanish when harvested and their yield is still growing, so an early harvest would take
fewer units than the tape's scheduled one.
"""
OVERLAY = '''

# --- v9.2 idle-worker overlay -------------------------------------------------
_ONGOING = {"STRAWBERRY", "TOMATO"}


def _idle_work(obs, action):
    """Give in-place work to units the tape leaves on PASS. Position never changes."""
    seat = _seat(obs)
    farm = _farm(obs, seat)
    tiles = _get(farm, "tiles", []) or []
    positions = [_get(farm, "farmer"), *list(_get(farm, "hands", []) or [])]
    units = [action.get("farmer") or ["PASS"], *list(action.get("hands") or [])]
    claimed = set()

    for idx, (pos, op) in enumerate(zip(positions, units)):
        if not (isinstance(op, list) and op and op[0] == "PASS"):
            continue
        try:
            x, y = int(pos[0]), int(pos[1])
            tile = tiles[y][x]
        except (IndexError, TypeError, ValueError):
            continue
        if not isinstance(tile, dict) or (x, y) in claimed:
            continue

        if "animal" in tile:
            if int(tile.get("yield_units", 0) or 0) > 0:
                units[idx] = ["HARVEST"]
            elif tile.get("fertilizer_available"):
                units[idx] = ["COLLECT_FERTILIZER"]
            elif tile.get("fed_today") and not tile.get("cared_today"):
                units[idx] = ["CARE"]
            else:
                continue
            claimed.add((x, y))
        elif (tile.get("kind") == "PLANT" and tile.get("crop") in _ONGOING
              and int(tile.get("yield_units", 0) or 0) > 0):
            units[idx] = ["HARVEST"]
            claimed.add((x, y))

    action["farmer"] = units[0] if units else ["PASS"]
    action["hands"] = units[1:]
    return action


_v92_tape_agent = agent


def _v92_agent(obs):
    action = _v92_tape_agent(obs)
    try:
        return _align_hands(_idle_work(obs, _copy_action(action)), obs)
    except Exception:
        return action


agent = _v92_agent
_kaggle_submission_entrypoint = _v92_agent


# kaggle_environments picks the LAST NEWLY BOUND callable in module order, and a
# `def agent` here would only rebind the tape's existing key at its original
# position — silently shipping the unmodified tape. This fresh name must stay last.
def v92_entrypoint(obs):
    return _v92_agent(obs)
'''

src = open("nb_v9/decoded_main.py", encoding="utf-8").read()
src = src.replace('"""v22 price-impact route agent for Kaggriculture.',
                  '"""v9.2: v22 route tape + idle-worker in-place overlay.', 1)
out = "v92/main.py"
import os
os.makedirs("v92", exist_ok=True)
open(out, "w", encoding="utf-8").write(src + OVERLAY)

ns = {}
exec(compile(open(out, encoding="utf-8").read(), out, "exec"), ns)
assert len(ns["_ACTIONS"]) == 719
print("wrote", out, "- import-clean, 719 actions")
