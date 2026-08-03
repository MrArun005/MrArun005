"""
Prioritized rule engine for Kaggriculture.

Three independent decisions per turn, in this order:

  1. `market_plan`  — orders (sell / hire / seeds / land). Free: costs no unit actions.
  2. `build_tasks`  — scan the farm, emit one prioritized task per tile that wants work.
  3. `assign`       — greedily match units to tasks by `priority - move_cost * distance`,
                      then emit either the op (already standing there) or a step toward it.

Every magic number lives in `Params` so `tune.py` can search them without touching logic.

Why this shape rather than the market-portfolio engine the plan first assumed: the binding
constraint in this game is *unit actions*, not cash. One op per unit per turn, 24 turns per
day, and hands cost fib(n) coins — see SPEC.md. So the engine is a dispatcher, and the
market side is a price-gated dribbler.
"""

from dataclasses import dataclass, asdict

from env_adapter import (
    ANIMALS, BASE_PRICE, CROPS, LAND_PRICES, PRODUCTS, SELLABLE,
    Action, Observation, Tile, hire_cost, walk_map, water_window_start,
)

NEG_INF = float("-inf")


@dataclass
class Params:
    """Every magic number in one place. tune.py mutates these, not the rules."""

    # --- labour -------------------------------------------------------------
    hands_per_tile: float = 0.11      # target hands per unlocked tile
    max_hands: int = 14               # hard cap on hands hired per day
    hire_until_hour: int = 4          # only hire early; a late hand has few turns left
    max_hires_per_turn: int = 6       # HIREs are one market order each (cap 10/turn)
    hire_cash_reserve: float = 60.0   # keep this much after paying for the day's hands

    # --- land ---------------------------------------------------------------
    land_cash_reserve: float = 1200.0  # cash to keep spare after buying a quadrant
    last_land_day: int = 22           # past this, new land cannot pay for itself
    land_empty_threshold: int = 6     # only expand when this few tiles are still empty

    # --- selling ------------------------------------------------------------
    sell_min_frac: float = 0.72       # sell only while price >= frac * base
    sell_min_frac_pressure: float = 0.28   # relaxed gate when the shed is filling up
    shed_pressure_frac: float = 0.50  # shed fullness that triggers the relaxed gate
    sell_chunk: int = 5               # units per product per turn (dribble, don't dump)
    dump_turns: int = 26              # turns_remaining <= this -> liquidate everything

    # --- planting -----------------------------------------------------------
    seed_buffer: int = 30             # seeds to keep queued for the chosen crop
    seed_cash_reserve: float = 120.0
    melon_tile_cap: int = 24          # tiles of melon before rotating to the next crop
    melon_bias: float = 1.0           # thumb on the scale per crop, for tuning
    carrot_bias: float = 1.0
    wheat_bias: float = 1.0

    # --- task priorities (higher = more urgent) -----------------------------
    prio_haul_final: float = 200.0    # last-day: get produce into the shed or lose it
    prio_feed_critical: float = 120.0
    prio_water_urgent: float = 95.0   # plant dies tonight if not watered
    prio_harvest_decay: float = 90.0  # losing a unit every other turn
    prio_harvest_ready: float = 70.0
    prio_water_bonus: float = 60.0    # inside the yield window
    prio_animal_harvest: float = 55.0
    prio_animal_care: float = 40.0
    prio_plant: float = 38.0
    prio_dig: float = 22.0
    prio_haul: float = 12.0

    move_cost: float = 0.9            # walk-distance weight in the value/turn ratio
    haul_threshold: int = 14           # carry this much before making a shed trip


@dataclass
class Task:
    x: int
    y: int
    op: list
    priority: float
    tag: str = ""

    @property
    def pos(self) -> tuple[int, int]:
        return (self.x, self.y)


# --- crop economics ---------------------------------------------------------

def harvest_age(crop: str) -> int:
    """Age (days) at which we harvest: the first age where yield is maxed out.

    Yield starts at 1 and gains +1 per watered day inside the bonus window, so the
    cap is reached at `window_start + max_yield - 2`, clamped to the window's end and
    floored at first_yield_day (HARVEST is rejected before that).
    """
    c = CROPS[crop]
    cap_age = water_window_start(crop) + c["max_yield"] - 2
    return max(c["first_yield_day"], min(c["max_yield_day"], cap_age))


def expected_yield(crop: str) -> int:
    """Units harvested at `harvest_age` with perfect in-window watering, no fertilizer."""
    c = CROPS[crop]
    window = max(0, min(c["max_yield_day"], harvest_age(crop)) - water_window_start(crop) + 1)
    return min(c["max_yield"], 1 + window)


def _bias(p: Params, crop: str) -> float:
    return {"MELON": p.melon_bias, "CARROT": p.carrot_bias, "WHEAT": p.wheat_bias}.get(crop, 1.0)


def crop_value(obs: Observation, p: Params, crop: str) -> float:
    """Expected coins per tile per day, at current market price.

    Using the *live* price is what makes the agent contrarian without any explicit
    crash rule: once we have flooded melon, melon's value falls below carrot's and
    plantings rotate on their own.
    """
    c = CROPS[crop]
    if c["ongoing"]:
        # Ongoing crops cap at 4 cumulative productions and then rot. Never worth a tile.
        return NEG_INF
    age = harvest_age(crop)
    if obs.day + age > obs.total_days - 1:
        return NEG_INF                      # cannot mature before the season ends
    price = obs.prices.get(crop, BASE_PRICE[crop])
    gross = expected_yield(crop) * price * _bias(p, crop)
    return (gross - c["seed"]) / age


def crop_tile_counts(obs: Observation) -> dict[str, int]:
    counts: dict[str, int] = {}
    for tile in obs.tiles:
        if tile.state == "PLANT" and tile.crop:
            counts[tile.crop] = counts.get(tile.crop, 0) + 1
    return counts


def choose_crop(obs: Observation, p: Params) -> str | None:
    """Best plantable crop right now, or None if nothing can pay off in time.

    Melon is capped by tile count, not by price. Melon is ~4x the best per tile-day, so
    an uncapped value ranking plants nothing else — but melon is demanded by no town shop,
    so the season can only absorb ~150-250 of them before `sq` glut pricing guts the
    price, and every melon past that is a wasted tile *and* a wasted 10 days of watering.
    Capping tiles instead of reacting to price also fixes the cash-flow hole: melon pays
    nothing until day 10, so the remaining tiles go to carrot and keep the lights on.
    """
    counts = crop_tile_counts(obs)
    best, best_value = None, 0.0
    for crop in CROPS:
        if crop == "MELON" and counts.get("MELON", 0) >= p.melon_tile_cap:
            continue
        value = crop_value(obs, p, crop)
        if value > best_value:
            best, best_value = crop, value
    return best


def plant_budget(obs: Observation, p: Params, crop: str | None) -> int:
    """How many PLANT ops may be issued this turn.

    Hard-capped by seeds held: the simulator drops *every* PLANT of a crop when the
    turn's requests for it exceed the seed count, so overcommitting wastes the whole
    turn for every unit involved.
    """
    if crop is None:
        return 0
    return min(obs.seeds.get(crop, 0), sum(1 for t in obs.tiles if t.state == "EMPTY"))


# --- market -----------------------------------------------------------------

def target_hands(obs: Observation, p: Params) -> int:
    """How many hands today, from workload and affordability."""
    workable = sum(1 for t in obs.tiles if t.state != "LOCKED")
    want = min(p.max_hands, int(round(workable * p.hands_per_tile)))
    # Walk the fib ladder and stop where the day's wage bill stops being affordable.
    budget = obs.cash - p.hire_cash_reserve
    spent = 0.0
    allowed = obs.hires_today
    while allowed < want:
        spent += hire_cost(allowed, obs.hire_mult)
        if spent > budget:
            break
        allowed += 1
    return allowed


def sell_orders(obs: Observation, p: Params) -> list[list]:
    """Price-gated dribble. Bulk sells walk their own price down; town demand refills
    the gap between turns, so many small sells beat one big one."""
    liquidating = obs.turns_remaining <= p.dump_turns
    pressured = obs.shed_used >= obs.shed_capacity * p.shed_pressure_frac
    gate = p.sell_min_frac_pressure if pressured else p.sell_min_frac

    orders = []
    # Sell the most valuable stock first — order position matters under the 10/turn cap.
    for item in sorted(SELLABLE, key=lambda i: -obs.prices.get(i, BASE_PRICE[i])):
        have = obs.shed.get(item, 0)
        if have <= 0:
            continue
        if liquidating:
            orders.append(["SELL", item, have])
        elif obs.price_frac(item) >= gate:
            orders.append(["SELL", item, min(have, p.sell_chunk)])
    return orders


def hire_orders(obs: Observation, p: Params) -> list[list]:
    if obs.hour > p.hire_until_hour or obs.turns_remaining <= obs.turns_per_day:
        return []
    want = target_hands(obs, p) - obs.hires_today
    return [["HIRE"]] * max(0, min(want, p.max_hires_per_turn))


def plantable_now(obs: Observation, p: Params, crop: str) -> int:
    """Empty tiles we would actually commit to this crop, respecting its tile cap."""
    empty = sum(1 for t in obs.tiles if t.state == "EMPTY")
    if crop == "MELON":
        empty = min(empty, max(0, p.melon_tile_cap - crop_tile_counts(obs).get("MELON", 0)))
    return empty


def seed_orders(obs: Observation, p: Params) -> list[list]:
    crop = choose_crop(obs, p)
    if crop is None:
        return []
    room = plantable_now(obs, p, crop)
    if room <= 0:
        return []
    # Seeds are the throttle on planting: with a dozen units able to plant a dozen tiles
    # a turn, a small buffer leaves units idle next to bare earth. Buy up to the tiles
    # we can actually fill.
    want = min(p.seed_buffer, room) - obs.seeds.get(crop, 0)
    if want <= 0:
        return []
    affordable = int((obs.cash - p.seed_cash_reserve) // CROPS[crop]["seed"])
    want = min(want, max(0, affordable))
    return [["BUY_SEED", crop, want]] if want > 0 else []


def land_orders(obs: Observation, p: Params) -> list[list]:
    """Buy land only once we have genuinely run out of room.

    Hands are the scarce input, not tiles: the fib hire ladder means ~12-14 hands a day is
    the affordable ceiling, which is only enough labour for roughly 50-60 worked tiles.
    Buying the last quadrant for $4k of dirt we never plant is a straight loss.
    """
    price = obs.next_land_price()
    if price is None or obs.day > p.last_land_day:
        return []
    if obs.cash < price + p.land_cash_reserve:
        return []
    empty = sum(1 for t in obs.tiles if t.state == "EMPTY")
    if empty > p.land_empty_threshold:
        return []
    return [["BUY_LAND"]]


def market_plan(obs: Observation, p: Params) -> list[list]:
    """Sells go first: orders resolve in list order, so this turn's revenue funds
    this turn's purchases."""
    orders = sell_orders(obs, p)
    orders += hire_orders(obs, p)
    orders += seed_orders(obs, p)
    orders += land_orders(obs, p)
    return orders[: obs.max_market_orders]


# --- tasks ------------------------------------------------------------------

def _plant_task(obs: Observation, p: Params, tile: Tile, crop: str) -> Task:
    return Task(tile.x, tile.y, ["PLANT", crop], p.prio_plant, "plant")


def _plant_tile_task(obs: Observation, p: Params, tile: Tile) -> Task | None:
    c = CROPS.get(tile.crop)
    if c is None:
        return None

    decaying = tile.max_lifespan_step >= 0 and obs.step >= tile.max_lifespan_step
    if tile.yield_units > 0 and tile.age_days >= c["first_yield_day"]:
        if decaying:
            return Task(tile.x, tile.y, ["HARVEST"], p.prio_harvest_decay, "harvest")
        if tile.age_days >= harvest_age(tile.crop):
            return Task(tile.x, tile.y, ["HARVEST"], p.prio_harvest_ready, "harvest")

    if tile.watered_today:
        return None
    # Survival: consecutive_unwatered is 1 after any skipped day, and 2 kills the plant
    # at the next end-of-day refresh. Watering only when it is >= 1 (or for yield) skips
    # roughly a quarter of all waterings versus watering everything daily.
    if tile.consecutive_unwatered >= 1:
        return Task(tile.x, tile.y, ["WATER"], p.prio_water_urgent, "water")
    in_window = water_window_start(tile.crop) <= tile.age_days <= c["max_yield_day"]
    if in_window and tile.yield_units < c["max_yield"]:
        return Task(tile.x, tile.y, ["WATER"], p.prio_water_bonus, "water")
    return None


def _animal_task(obs: Observation, p: Params, tile: Tile) -> Task | None:
    a = ANIMALS.get(tile.animal)
    if a is None:
        return None
    if not tile.fed_today:
        prio = p.prio_feed_critical if tile.consecutive_unfed >= 1 else p.prio_feed_critical * 0.6
        return Task(tile.x, tile.y, ["FEED"], prio, "feed")
    if tile.yield_units >= a["max_held"]:
        return Task(tile.x, tile.y, ["HARVEST"], p.prio_animal_harvest, "harvest")
    if not tile.cared_today:
        return Task(tile.x, tile.y, ["CARE"], p.prio_animal_care, "care")
    if tile.yield_units > 0:
        return Task(tile.x, tile.y, ["HARVEST"], p.prio_animal_harvest * 0.6, "harvest")
    return None


def build_tasks(obs: Observation, p: Params, crop: str | None) -> list[Task]:
    """One task per tile, at most.

    A plant task is emitted for *every* empty tile even though only `plant_budget` of
    them can be honoured. Truncating here would hand out the first N tiles in row-major
    order — which is how the farmer ended up walking four tiles north to plant while
    standing on bare earth. The budget is enforced during assignment instead, so the
    tiles actually planted are the ones closest to a free unit.
    """
    tasks: list[Task] = []
    for tile in obs.tiles:
        if tile.state == "LOCKED":
            continue
        if tile.state == "EMPTY":
            if crop:
                tasks.append(_plant_task(obs, p, tile, crop))
        elif tile.state == "PLANT":
            task = _plant_tile_task(obs, p, tile)
            if task:
                tasks.append(task)
        elif tile.state == "WEED":
            if crop:                      # only worth clearing if we would use the tile
                tasks.append(Task(tile.x, tile.y, ["DIG"], p.prio_dig, "dig"))
        elif tile.state == "ANIMAL":
            task = _animal_task(obs, p, tile)
            if task:
                tasks.append(task)
    return tasks


def haul_tasks(obs: Observation, p: Params, unit_idx: int, carrying: int) -> list[Task]:
    """Trips to the shed. Mandatory on the final day: the free end-of-day dump lands
    at step 719, one turn after the reward is latched at step 718, so anything still
    in a unit's hands then is worth nothing."""
    if carrying <= 0:
        return []
    final_day = obs.day >= obs.total_days - 1
    if not final_day and carrying < p.haul_threshold:
        return []
    prio = p.prio_haul_final if final_day else p.prio_haul
    return [Task(x, y, ["DROP"], prio, "haul") for (x, y) in obs.shed_access]


# --- assignment -------------------------------------------------------------

def assign(obs: Observation, p: Params, tasks: list[Task], plants_allowed: int = 0) -> list[list]:
    """Greedy: score every (unit, task) pair, take the best pair, repeat.

    Cheap and good enough — a Hungarian solve would buy little, since priorities are
    coarse and the board is small.
    """
    ops: list[list] = [["PASS"] for _ in obs.units]
    maps = {u.idx: walk_map(obs, u.pos) for u in obs.units}

    all_tasks = list(tasks)
    per_unit_offset = len(all_tasks)
    unit_haul: dict[int, range] = {}
    for unit in obs.units:
        hauls = haul_tasks(obs, p, unit.idx, unit.carrying())
        unit_haul[unit.idx] = range(per_unit_offset, per_unit_offset + len(hauls))
        all_tasks.extend(hauls)
        per_unit_offset += len(hauls)

    pairs = []
    for unit in obs.units:
        reach = maps[unit.idx]
        for t_idx, task in enumerate(all_tasks):
            # A unit's private haul tasks are not available to anybody else.
            owner = next((idx for idx, rng in unit_haul.items() if t_idx in rng), None)
            if owner is not None and owner != unit.idx:
                continue
            hit = reach.get(task.pos)
            if hit is None:
                continue
            dist, first = hit
            if dist > obs.turns_remaining:
                continue
            # Rate, not difference: a task is worth `priority` and costs `1 + dist`
            # unit-turns to complete, so what we want to maximise is value per turn.
            # Subtracting a linear walk penalty instead let a distant high-priority task
            # outbid work the unit was already standing on, and burned 55% of all
            # unit-turns on walking.
            pairs.append((task.priority / (1.0 + p.move_cost * dist), unit.idx, t_idx, dist, first))

    pairs.sort(key=lambda r: -r[0])
    taken_units: set[int] = set()
    taken_tasks: set[int] = set()
    for _, unit_idx, t_idx, dist, first in pairs:
        if unit_idx in taken_units or t_idx in taken_tasks:
            continue
        task = all_tasks[t_idx]
        if task.tag == "plant":
            # Seeds run out long before empty tiles do; spend them on the nearest tiles.
            if plants_allowed <= 0:
                continue
            plants_allowed -= 1
        taken_units.add(unit_idx)
        taken_tasks.add(t_idx)
        ops[unit_idx] = list(task.op) if dist == 0 else [first]

    # Idle units drift toward the shed so they start the next task closer to supply.
    for unit in obs.units:
        if unit.idx in taken_units:
            continue
        if unit.carrying() > 0 and not obs.is_shed_adjacent(unit.pos):
            hit = maps[unit.idx]
            step = min(
                (hit[pos] for pos in obs.shed_access if pos in hit),
                key=lambda r: r[0], default=None,
            )
            if step and step[0] > 0:
                ops[unit.idx] = [step[1]]
    return ops


# --- entry point ------------------------------------------------------------

def decide(obs: Observation, p: Params | None = None) -> Action:
    p = p or Params()
    crop = choose_crop(obs, p)
    tasks = build_tasks(obs, p, crop)
    ops = assign(obs, p, tasks, plant_budget(obs, p, crop))
    return Action(unit_ops=ops, market=market_plan(obs, p))


def params_dict(p: Params) -> dict:
    return asdict(p)
