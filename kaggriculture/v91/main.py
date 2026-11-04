"""v9.1 hybrid: the public v22 route tape as backbone + an adaptive market overlay.

The tape's farmer/hand choreography is position-critical, so unit actions pass
through untouched (weed repair included). All adaptation lives in channels that
cannot desynchronize the route:

  1. SELL acceleration: if the opponent's shed-visible pipeline is about to glut a
     product's market, our scheduled sells for it move earlier — never later.
  2. Terminal sweep: from the last morning, any shed stock the tape would strand
     gets dribbled out before the reward latches at step 718.
  3. Escape insurance: an animal one missed feed from escaping gets an in-place
     FEED from a unit the tape has PASSing that turn (no movement, no desync).
"""
import tape  # the unmodified public v22 agent (nb sha256 62fb5a5f...)

TURNS_PER_DAY = 24
EPISODE_STEPS = 720
REWARD_LATCH = EPISODE_STEPS - 2
SWEEP_FROM = REWARD_LATCH - TURNS_PER_DAY          # last day: step 694 onward
SELLABLE = list(tape._MARKET_PARAMS)
MAX_ORDERS = 10
SWEEP_CHUNK = 10


def _shed(obs, seat):
    priv = tape._get(obs, "private", {}) or {}
    return tape._get(priv, "shed", {}) or {}


def _scheduled_sells(step):
    """Products the remaining tape ever sells, so the sweep only adds what it forgot."""
    remaining = set()
    for future in tape._ACTIONS[step:]:
        for order in (future or {}).get("market", []) or []:
            if order and order[0] == "SELL":
                remaining.add(order[1])
    return remaining


def _terminal_sweep(obs, action, step):
    if step < SWEEP_FROM or step >= REWARD_LATCH:
        return action
    seat = tape._seat(obs)
    shed = _shed(obs, seat)
    planned = _scheduled_sells(step)
    market = list(action.get("market") or [])
    prices = tape._get(tape._get(obs, "market", {}) or {}, "prices", {}) or {}
    for item in sorted(SELLABLE, key=lambda i: -(prices.get(i) or 0)):
        if len(market) >= MAX_ORDERS:
            break
        have = int(shed.get(item, 0) or 0)
        if have <= 0 or item in planned:
            continue
        if any(o and o[0] == "SELL" and o[1] == item for o in market):
            continue
        market.append(["SELL", item, min(have, SWEEP_CHUNK)])
    action["market"] = market[:MAX_ORDERS]
    return action


def _opponent_pipeline(obs, seat, item):
    """Visible uncollected supply of `item` ripening on the opponent's farm."""
    crop_of = {"MELON": "MELON", "STRAWBERRY": "STRAWBERRY", "WHEAT": "WHEAT",
               "CARROT": "CARROT", "TOMATO": "TOMATO"}
    if item not in crop_of:
        return 0
    farm = tape._farm(obs, 1 - seat)
    total = 0
    for row in tape._get(farm, "tiles", []) or []:
        for t in row or []:
            if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == item:
                total += int(t.get("yield_units", 0) or 0)
    return total


def _accelerate_sells(obs, action, step):
    """When the opponent's ripening stock would crash a price, our future sells for
    that product move to now (bounded by shed stock and the order cap)."""
    seat = tape._seat(obs)
    shed = _shed(obs, seat)
    market = list(action.get("market") or [])
    if len(market) >= MAX_ORDERS:
        return action
    inv = tape._get(tape._get(obs, "market", {}) or {}, "inventory", {}) or {}
    for item in ("MELON", "STRAWBERRY"):
        have = int(shed.get(item, 0) or 0)
        if have <= 0:
            continue
        threat = _opponent_pipeline(obs, seat, item)
        if threat < 12:                     # not enough incoming supply to matter
            continue
        now = int(tape._get(inv, item, 10000) or 10000)
        drop = tape._market_price(item, now) - tape._market_price(item, now + threat)
        if drop < 25:                       # their dump barely moves the price
            continue
        already = sum(int(o[2]) for o in market
                      if o and o[0] == "SELL" and o[1] == item and len(o) >= 3)
        extra = min(have - already, SWEEP_CHUNK)
        if extra > 0 and len(market) < MAX_ORDERS:
            market.append(["SELL", item, extra])
    action["market"] = market[:MAX_ORDERS]
    return action


def _escape_insurance(obs, action):
    """Feed any animal one missed feed from escaping, using only PASSing units
    already standing on that animal's tile and already holding wheat."""
    seat = tape._seat(obs)
    farm = tape._farm(obs, seat)
    tiles = tape._get(farm, "tiles", []) or []
    at_risk = set()
    for y, row in enumerate(tiles):
        for x, t in enumerate(row or []):
            if (isinstance(t, dict) and "animal" in t and not t.get("fed_today")
                    and int(t.get("consecutive_unfed", 0) or 0) >= 1):
                at_risk.add((x, y))
    if not at_risk:
        return action
    priv = tape._get(obs, "private", {}) or {}
    invs = list(tape._get(priv, "inventories", []) or [])
    positions = [tape._get(farm, "farmer"), *list(tape._get(farm, "hands", []) or [])]
    units = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
    for idx, (pos, op) in enumerate(zip(positions, units)):
        if not at_risk:
            break
        if not (isinstance(op, list) and op and op[0] == "PASS"):
            continue
        try:
            key = (int(pos[0]), int(pos[1]))
        except (TypeError, ValueError, IndexError):
            continue
        wheat = int((invs[idx] if idx < len(invs) else {}).get("WHEAT", 0) or 0)
        if key in at_risk and wheat > 0:
            units[idx] = ["FEED"]
            at_risk.discard(key)
    action["farmer"] = units[0]
    action["hands"] = units[1:]
    return action


def agent(obs):
    action = tape.agent(obs)
    try:
        step = int(tape._get(obs, "step", 0) or 0)
        action = _accelerate_sells(obs, action, step)
        action = _terminal_sweep(obs, action, step)
        action = _escape_insurance(obs, action)
    except Exception:
        pass                                # overlay must never break the tape
    return action
