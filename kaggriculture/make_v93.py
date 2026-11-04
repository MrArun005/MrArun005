"""v9.3 = the v22 route tape with DYNAMIC crop choice, emitted as one main.py.

The tape's choreography is kept exactly: same turns, same tiles, same workers. Only
two decisions become adaptive, and neither moves a unit:

  BUY_SEED  -> buy the crop with the best forward value, not the scripted one
  PLANT     -> plant the best crop we actually hold seeds for

Forward value is computed, not guessed. The town's drain is deterministic:
  * every `shop_interval` steps each unlocked shop removes 1 unit of each product
    it sells (2 when the shop sells only one product)
  * every `center_interval` steps the town centre removes `mult` of every product
    except FERTILIZER, where mult is 1 / 2 / 4 from days 0 / 10 / 20
So for a crop maturing in N steps we can price its harvest before planting it:

  price_then = market_price(inventory_now - drain(N) + our_pipeline + their_pipeline)
  value      = (units * price_then - seed_cost) / days_occupied

That formula is what makes the farm rotate on its own: whichever product the town is
starved of wins the next planting, and a crop that gluts stops winning.
"""
OVERLAY = '''

# --- v9.3 dynamic crop selection ---------------------------------------------
_CROPS = {
    # crop: (seed, first_yield_day, max_yield_day, interval, max_yield, ongoing)
    "WHEAT":      (10, 2, 4, 0, 6, False),
    "CARROT":     (20, 2, 3, 0, 4, False),
    "STRAWBERRY": (100, 10, 10, 2, 4, True),
    "MELON":      (80, 10, 12, 0, 6, False),
    "TOMATO":     (50, 8, 8, 1, 4, True),
}
_SHOPS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_SHOP_INTERVAL = 4
_CENTER_INTERVAL = 12
_TURNS_PER_DAY = 24
_TOTAL_DAYS = 30
_CANDIDATES = ("WHEAT", "STRAWBERRY", "MELON", "CARROT")


def _drain_over(obs, item, steps):
    """Units of `item` the town will remove over the next `steps` steps."""
    step = int(_get(obs, "step", 0) or 0)
    town = _get(obs, "town", {}) or {}
    shops = list(_get(town, "unlocked_shops", []) or [])
    per_shop_tick = 0
    for name in shops:
        products = _SHOPS.get(name, ())
        if item in products:
            per_shop_tick += 2 if len(products) == 1 else 1
    total = 0
    for s in range(step + 1, step + steps + 1):
        if s % _SHOP_INTERVAL == 0:
            total += per_shop_tick
        if s % _CENTER_INTERVAL == 0 and item != "FERTILIZER":
            day = s // _TURNS_PER_DAY
            total += 4 if day >= 20 else (2 if day >= 10 else 1)
    return total


def _pipeline(obs, item):
    """Uncollected units of `item` already growing on either farm."""
    total = 0
    for farm in list(_get(obs, "farms", []) or []):
        for row in _get(farm, "tiles", []) or []:
            for tile in row or []:
                if (isinstance(tile, dict) and tile.get("kind") == "PLANT"
                        and tile.get("crop") == item):
                    total += int(tile.get("yield_units", 0) or 0)
    return total


def _harvest_age(crop):
    seed, first, maxday, interval, maxyield, ongoing = _CROPS[crop]
    if ongoing:
        return first + interval * (maxyield - 1)
    window_start = (maxday + 1) // 2
    return max(first, min(maxday, window_start + maxyield - 2))


def _expected_units(crop):
    seed, first, maxday, interval, maxyield, ongoing = _CROPS[crop]
    if ongoing:
        return maxyield
    window_start = (maxday + 1) // 2
    window = max(0, min(maxday, _harvest_age(crop)) - window_start + 1)
    return min(maxyield, 1 + window)


def _crop_value(obs, crop):
    """Coins per tile-day, priced at the market we project when it matures."""
    seed = _CROPS[crop][0]
    age = _harvest_age(crop)
    day = int(_get(obs, "day", 0) or 0)
    days_left = _TOTAL_DAYS - day
    if days_left <= age:
        return float("-inf")                     # cannot mature in time
    market = _get(obs, "market", {}) or {}
    inv = _get(market, "inventory", {}) or {}
    now = int(_get(inv, crop, 10000) or 10000)
    units = _expected_units(crop)
    steps = age * _TURNS_PER_DAY
    projected = now - _drain_over(obs, crop, steps) + _pipeline(obs, crop) + units
    price = _market_price(crop, projected)
    return (units * price - seed) / float(age)


def _best_crop(obs, affordable_only_cash=None):
    best, best_v = None, 0.0
    for crop in _CANDIDATES:
        if affordable_only_cash is not None and _CROPS[crop][0] > affordable_only_cash:
            continue
        v = _crop_value(obs, crop)
        if v > best_v:
            best, best_v = crop, v
    return best


def _dynamic_market(obs, action):
    """Re-point scripted BUY_SEED orders at the best-value crop (same slot, same cash
    scale). Quantity is rescaled so we never spend more than the tape planned."""
    seat = _seat(obs)
    farm = _farm(obs, seat)
    cash = float(_get(farm, "money", 0) or 0)
    orders = []
    for order in action.get("market") or []:
        if (isinstance(order, (list, tuple)) and len(order) >= 3
                and order[0] == "BUY_SEED" and order[1] in _CROPS):
            scripted, qty = order[1], int(order[2])
            budget = _CROPS[scripted][0] * qty
            pick = _best_crop(obs, cash)
            if pick and pick != scripted:
                new_qty = max(1, min(qty, int(budget // _CROPS[pick][0])))
                orders.append([order[0], pick, new_qty])
                continue
        orders.append(list(order))
    action["market"] = orders
    return action


def _dynamic_plants(obs, action):
    """Plant the best crop we actually hold seeds for; never plant what we lack."""
    priv = _get(obs, "private", {}) or {}
    held = dict(_get(priv, "seeds", {}) or {})
    ranked = sorted((c for c in _CANDIDATES if held.get(c, 0) > 0),
                    key=lambda c: -_crop_value(obs, c))
    if not ranked:
        return action
    units = [action.get("farmer") or ["PASS"], *list(action.get("hands") or [])]
    for idx, op in enumerate(units):
        if not (isinstance(op, list) and len(op) >= 2 and op[0] == "PLANT"):
            continue
        for crop in ranked:
            if held.get(crop, 0) > 0:
                if crop != op[1]:
                    units[idx] = ["PLANT", crop]
                held[crop] -= 1
                break
        ranked = [c for c in ranked if held.get(c, 0) > 0]
        if not ranked:
            break
    action["farmer"] = units[0]
    action["hands"] = units[1:]
    return action


_v93_tape_agent = agent


def _v93_agent(obs):
    action = _v93_tape_agent(obs)
    try:
        action = _copy_action(action)
        action = _dynamic_market(obs, action)
        action = _dynamic_plants(obs, action)
        return _align_hands(action, obs)
    except Exception:
        return action


agent = _v93_agent
_kaggle_submission_entrypoint = _v93_agent


# The loader takes the LAST NEWLY BOUND callable, and `def agent` here would only
# rebind the tape's existing key at its original position, silently shipping the
# unmodified tape. This fresh name must remain last in the file.
def v93_entrypoint(obs):
    return _v93_agent(obs)
'''

import os

src = open("nb_v9/decoded_main.py", encoding="utf-8").read()
src = src.replace('"""v22 price-impact route agent for Kaggriculture.',
                  '"""v9.3: v22 route tape with demand-forecast dynamic crop choice.', 1)
os.makedirs("v93", exist_ok=True)
out = "v93/main.py"
open(out, "w", encoding="utf-8").write(src + OVERLAY)
ns = {}
exec(compile(open(out, encoding="utf-8").read(), out, "exec"), ns)
assert len(ns["_ACTIONS"]) == 719
print("wrote", out, "- import-clean, 719 actions")
