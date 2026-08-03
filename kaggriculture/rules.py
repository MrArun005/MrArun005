"""
Prioritized rule engine for Kaggriculture.

Three independent decisions per turn, in this order:

  1. `market_plan`  — orders (sell / hire / livestock / seeds / land). Free: no unit actions.
  2. `build_tasks`  — scan the farm, emit one prioritized task per tile that wants work.
  3. `assign`       — greedily match units to tasks by value per turn,
                      `priority / (1 + move_cost * distance)`, then emit either the op
                      (already standing there) or one step toward it.

Every magic number lives in `Params` so `tune.py` can search them without touching logic.

Why this shape rather than the market-portfolio engine the plan first assumed: the binding
constraint in this game is *unit actions*, not cash. One op per unit per turn, 24 turns per
day, and hands cost fib(n) coins — see SPEC.md. So the engine is a dispatcher, and the
market side is a price-gated dribbler.
"""

from dataclasses import dataclass, asdict

from env_adapter import (
    ANIMALS, BASE_PRICE, CROPS, SELLABLE,
    Action, Observation, Tile, hire_cost, walk_map, water_window_start,
)

NEG_INF = float("-inf")


@dataclass
class Params:
    """Every magic number in one place. tune.py mutates these, not the rules."""

    # --- labour -------------------------------------------------------------
    hands_per_tile: float = 0.11      # target hands per unlocked tile
    max_hands: int = 14               # hard cap on hands hired per day
    max_hire_cost: float = 144.0      # skip a hire once fib(n) exceeds a hand's day of work
    hire_until_hour: int = 4          # only hire early; a late hand has few turns left
    max_hires_per_turn: int = 6       # HIREs are one market order each (cap 10/turn)
    hire_cash_reserve: float = 60.0   # keep this much after paying for the day's hands

    # --- land ---------------------------------------------------------------
    land_cash_reserve: float = 1200.0  # cash to keep spare after buying a quadrant
    last_land_day: int = 22           # past this, new land cannot pay for itself
    land_empty_threshold: int = 6     # only expand when this few tiles are still empty

    # --- selling ------------------------------------------------------------
    sell_min_frac: float = 0.85       # sell only while price >= frac * base
    sell_min_frac_pressure: float = 0.28   # relaxed gate when the shed is filling up
    shed_pressure_frac: float = 0.50  # shed fullness that triggers the relaxed gate
    shed_force_frac: float = 0.85     # shed fullness that ignores the price gate entirely
    sell_chunk: int = 8               # units per product per turn (dribble, don't dump)
    dump_turns: int = 72              # turns_remaining <= this -> start liquidating
    final_dump_turns: int = 3         # last N turns: sell everything regardless of price

    # --- planting -----------------------------------------------------------
    seed_buffer: int = 12             # seeds to keep queued for the chosen crop
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
    prio_harvest_ready: float = 55.0
    prio_water_bonus: float = 60.0    # inside the yield window
    prio_animal_harvest: float = 55.0
    prio_animal_care: float = 40.0
    prio_plant: float = 38.0
    prio_dig: float = 22.0
    prio_haul: float = 12.0

    move_cost: float = 0.4            # walk-distance weight in the value/turn ratio
    haul_threshold: int = 40           # carry this much before making a shed trip

    # --- livestock ----------------------------------------------------------
    # Animals sell into price curves that crop saturation never touches, which is the
    # whole reason to bother: melon volume is capped by melon's own glut curve, so wool
    # and milk are additive revenue rather than a substitute.
    target_sheep: int = 4             # WOOL, base $200, the best $/action of the three
    target_cows: int = 2              # MILK, base $160
    target_geese: int = 0             # EGG only $50; poor $/action, glut-proof though
    animal_cash_reserve: float = 5000.0  # buy livestock out of melon profit, not seed capital
    feed_cash_floor: float = 150.0     # feeding outranks almost everything; buy wheat above this
    animals_per_turn: int = 2          # stagger purchases instead of dumping the bank
    last_animal_day: int = 21         # placed later than this, it never reaches first yield
    feed_reserve_days: float = 2.0    # days of wheat to hold back from selling per animal
    wheat_pickup_batch: int = 6       # wheat carried per shed trip
    max_pickup_tasks: int = 2         # don't send the whole crew to the shed at once
    prio_pickup: float = 108.0
    prio_build: float = 46.0
    prio_place_animal: float = 100.0  # a bought animal earns nothing sitting in the shed


@dataclass
class Task:
    x: int
    y: int
    op: list
    priority: float
    tag: str = ""
    # Item the acting unit must already be carrying. FEED consumes wheat from the unit's
    # own inventory, not the shed, and PLACE needs the animal in hand — so these tasks
    # are only offered to units that can actually perform them.
    requires: str | None = None
    # Tasks sharing a group are mutually exclusive. Shed errands are emitted at all four
    # access tiles so any unit can take the nearest one, but the errand itself only needs
    # doing once — the group stops four units all running to the shed for one job.
    group: str | None = None
    # Unit this task belongs exclusively to (shed trips are per-unit: only the unit holding
    # the produce can usefully drop it).
    owner: int | None = None

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


# --- livestock --------------------------------------------------------------

def animal_targets(p: Params) -> dict[str, int]:
    return {"SHEEP": p.target_sheep, "COW": p.target_cows, "GOOSE": p.target_geese}


def livestock_census(obs: Observation) -> dict:
    """Counts of placed animals, vacant structures, and animals waiting in the shed."""
    placed: dict[str, int] = {}
    vacant: dict[str, int] = {"COOP": 0, "PASTURE": 0}
    for tile in obs.tiles:
        if tile.state == "ANIMAL" and tile.animal:
            placed[tile.animal] = placed.get(tile.animal, 0) + 1
        elif tile.state in ("COOP", "PASTURE"):
            vacant[tile.state] += 1
    in_shed = {name: obs.shed.get(name, 0) for name in ANIMALS}
    return {"placed": placed, "vacant": vacant, "in_shed": in_shed}


def _wanted_animals(obs: Observation, p: Params) -> dict[str, int]:
    """Shortfall per species: target minus (placed + already bought)."""
    census = livestock_census(obs)
    out = {}
    for name, target in animal_targets(p).items():
        have = census["placed"].get(name, 0) + census["in_shed"].get(name, 0)
        out[name] = max(0, target - have)
    return out


def wheat_feed_reserve(obs: Observation, p: Params) -> int:
    """Wheat to hold back from the market so livestock never starves.

    A missed second consecutive feed loses the animal outright — 400-500 coins plus the
    rest of the season's production — so this reserve is cheap insurance.
    """
    n = sum(livestock_census(obs)["placed"].values())
    return int(round(n * p.feed_reserve_days)) if n else 0


def animal_orders(obs: Observation, p: Params) -> list[list]:
    """Feed first, then expand. Order matters — see below.

    Livestock is a leveraged bet that goes to zero if it ever misses two feeds: the animal
    escapes, the structure survives, and the restocking logic buys a replacement that
    starves the same way. Two guards prevent that death spiral:

      - **Feed is bought before animals are**, from a low cash floor, because a starved
        animal is a total loss while a delayed purchase costs only a few days of yield.
      - **Animals are bought out of profit, not capital.** They cost 300-500 each against a
        $3 000 opening bank, and the melon engine needs that bank for seeds and hands.
        Buying on day 0 starved the whole farm and returned nothing at all.
    """
    orders: list[list] = []
    placed = sum(livestock_census(obs)["placed"].values())

    reserve = wheat_feed_reserve(obs, p)
    if reserve:
        short = reserve - obs.shed.get("WHEAT", 0)
        budget = obs.cash - p.feed_cash_floor
        unit = max(1, obs.prices.get("WHEAT", 25))
        n = min(short, int(budget // unit))
        if n > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", n])

    if obs.day > p.last_animal_day or obs.cash < p.animal_cash_reserve:
        return orders
    # Never take on a mouth we cannot feed for at least a few days.
    feed_on_hand = obs.shed.get("WHEAT", 0) + int((obs.cash - p.animal_cash_reserve) // 40)
    if feed_on_hand < (placed + 1) * p.feed_reserve_days:
        return orders

    cash = obs.cash - p.animal_cash_reserve
    bought = 0
    for name, want in _wanted_animals(obs, p).items():
        if want <= 0 or bought >= p.animals_per_turn:
            continue
        cost = ANIMALS[name]["cost"]
        n = min(want, p.animals_per_turn - bought, int(cash // cost))
        if n > 0:
            orders.append(["BUY_ANIMAL", name, n])
            cash -= n * cost
            bought += n
    return orders


def _structure_tasks(obs: Observation, p: Params, empty: list[Tile]) -> list[Task]:
    """Build the pens the animals we intend to own will need."""
    if obs.day > p.last_animal_day or not empty:
        return []
    # Don't fence off tiles for animals we cannot afford yet — an empty pen is a tile that
    # grows nothing, and it blocks the melon rotation that pays for the animal.
    waiting = any(obs.shed.get(n, 0) for n in ANIMALS)
    if not waiting and obs.cash < p.animal_cash_reserve * 0.75:
        return []
    census = livestock_census(obs)
    need = {"PASTURE": 0, "COOP": 0}
    for name, target in animal_targets(p).items():
        structure = ANIMALS[name]["structure"]
        need[structure] += target
    for name, n in census["placed"].items():
        need[ANIMALS[name]["structure"]] -= n
    for structure, n in census["vacant"].items():
        need[structure] -= n

    tasks: list[Task] = []
    # Build near the shed: every feed and harvest trip starts from there.
    empty = sorted(empty, key=lambda t: min(abs(t.x - sx) + abs(t.y - sy)
                                            for sx, sy in obs.shed_access))
    for structure, count in need.items():
        op = "BUILD_PASTURE" if structure == "PASTURE" else "BUILD_COOP"
        for tile in empty[:max(0, count)]:
            tasks.append(Task(tile.x, tile.y, [op], p.prio_build, "build"))
        empty = empty[max(0, count):]
    return tasks


def _place_tasks(obs: Observation, p: Params) -> list[Task]:
    """Move bought animals from the shed onto matching vacant structures."""
    waiting = {n: obs.shed.get(n, 0) + sum(u.inventory.get(n, 0) for u in obs.units)
               for n in ANIMALS}
    if not any(waiting.values()):
        return []
    tasks: list[Task] = []
    for tile in obs.tiles:
        if tile.state not in ("COOP", "PASTURE"):
            continue
        for name, n in waiting.items():
            if n > 0 and ANIMALS[name]["structure"] == tile.state:
                tasks.append(Task(tile.x, tile.y, ["PLACE", name],
                                  p.prio_place_animal, "place", requires=name))
                waiting[name] -= 1
                break
    return tasks


def _pickup_tasks(obs: Observation, p: Params) -> list[Task]:
    """Shed trips to collect what units need in hand: wheat for feeding, animals to place."""
    tasks: list[Task] = []

    carried = {n: sum(u.inventory.get(n, 0) for u in obs.units) for n in ANIMALS}
    for name in ANIMALS:
        in_shed = obs.shed.get(name, 0)
        if in_shed <= 0 or carried.get(name, 0) >= in_shed:
            continue
        for (x, y) in obs.shed_access:
            tasks.append(Task(x, y, ["PICKUP", name, 1], p.prio_place_animal + 2,
                              "pickup", group=f"get:{name}"))

    unfed = sum(1 for t in obs.tiles if t.state == "ANIMAL" and not t.fed_today)
    if unfed:
        have = sum(u.inventory.get("WHEAT", 0) for u in obs.units)
        deficit = unfed - have
        available = obs.shed.get("WHEAT", 0)
        if deficit > 0 and available > 0:
            batches = min(p.max_pickup_tasks, -(-deficit // max(1, p.wheat_pickup_batch)))
            n = min(p.wheat_pickup_batch, available)
            for b in range(batches):
                for (x, y) in obs.shed_access:
                    tasks.append(Task(x, y, ["PICKUP", "WHEAT", n], p.prio_pickup,
                                      "pickup", group=f"feedrun:{b}"))
    return tasks


# --- market -----------------------------------------------------------------

def target_hands(obs: Observation, p: Params) -> int:
    """How many hands today, from workload and affordability."""
    workable = sum(1 for t in obs.tiles if t.state != "LOCKED")
    want = min(p.max_hands, int(round(workable * p.hands_per_tile)))
    # Walk the fib ladder and stop on the first hire that is either unaffordable or simply
    # not worth it. The marginal-cost cap matters more than the affordability one: a hand
    # produces at most ~23 actions, worth roughly $300 at our realised $/action, but the
    # 14th hire alone costs $377 and the 15th $610. Measured, 14 hands scores ~11k *worse*
    # than 11 — the extra hands are bought with money and paid for in nothing.
    budget = obs.cash - p.hire_cash_reserve
    spent = 0.0
    allowed = obs.hires_today
    while allowed < want:
        cost = hire_cost(allowed, obs.hire_mult)
        if cost > p.max_hire_cost or spent + cost > budget:
            break
        spent += cost
        allowed += 1
    return allowed


def sell_orders(obs: Observation, p: Params) -> list[list]:
    """Price-gated dribble. Bulk sells walk their own price down; town demand refills
    the gap between turns, so many small sells beat one big one."""
    liquidating = obs.turns_remaining <= p.dump_turns
    if obs.shed_used >= obs.shed_capacity * p.shed_force_frac:
        # Overflow at the end-of-day dump is *destroyed*, so a sale at the $1 floor still
        # beats holding for a better price. Diagnostics had the shed pinned at 100/100,
        # which means produce was being thrown away while the price gate held firm.
        gate = 0.0
    elif obs.shed_used >= obs.shed_capacity * p.shed_pressure_frac:
        gate = p.sell_min_frac_pressure
    else:
        gate = p.sell_min_frac

    reserve = 0 if liquidating else wheat_feed_reserve(obs, p)

    orders = []
    # Sell the most valuable stock first — order position matters under the 10/turn cap.
    for item in sorted(SELLABLE, key=lambda i: -obs.prices.get(i, BASE_PRICE[i])):
        have = obs.shed.get(item, 0)
        if item == "WHEAT":
            have -= reserve               # livestock eats before the market does
        if have <= 0:
            continue
        if liquidating:
            # Spread the liquidation over the turns that are left instead of dumping in
            # one order. Clearing is per-unit lockstep, so a single SELL of everything
            # walks its own price down once per unit — and town demand still drains
            # supply between turns, which a one-shot dump throws away. Only the last few
            # turns sell unconditionally, because unsold stock scores zero.
            turns = max(1, obs.turns_remaining)
            qty = have if turns <= p.final_dump_turns else max(p.sell_chunk, -(-have // turns))
            orders.append(["SELL", item, min(have, qty)])
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
    orders += animal_orders(obs, p)
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
        # Tried and rejected: scaling this priority by the crop's unit price. One in-window
        # watering adds exactly one harvestable unit and the window never returns, so a
        # missed melon day looks like $250 lost for one op against ~$30 on wheat — but
        # weighting it that way measured flat-to-negative over 14 out-of-sample seeds.
        # Melon already wins on distance, and starving the cheap crops costs more than the
        # melon it saves.
        return Task(tile.x, tile.y, ["WATER"], p.prio_water_bonus, "water")
    return None


def _animal_task(obs: Observation, p: Params, tile: Tile) -> Task | None:
    a = ANIMALS.get(tile.animal)
    if a is None:
        return None
    if not tile.fed_today:
        prio = p.prio_feed_critical if tile.consecutive_unfed >= 1 else p.prio_feed_critical * 0.6
        return Task(tile.x, tile.y, ["FEED"], prio, "feed", requires="WHEAT")
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
    empty: list[Tile] = []
    for tile in obs.tiles:
        if tile.state == "LOCKED":
            continue
        if tile.state == "EMPTY":
            empty.append(tile)
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

    # Pens claim their tiles before crops do, so a build target is never planted over.
    builds = _structure_tasks(obs, p, empty)
    tasks.extend(builds)
    claimed = {t.pos for t in builds}
    if crop:
        tasks.extend(_plant_task(obs, p, t, crop) for t in empty if t.pos not in claimed)

    tasks.extend(_place_tasks(obs, p))
    tasks.extend(_pickup_tasks(obs, p))
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
    return [Task(x, y, ["DROP"], prio, "haul", owner=unit_idx, group=f"haul:{unit_idx}")
            for (x, y) in obs.shed_access]


# --- assignment -------------------------------------------------------------

def assign(obs: Observation, p: Params, tasks: list[Task], plants_allowed: int = 0) -> list[list]:
    """Greedy: score every (unit, task) pair, take the best pair, repeat.

    Cheap and good enough — a Hungarian solve would buy little, since priorities are
    coarse and the board is small.
    """
    ops: list[list] = [["PASS"] for _ in obs.units]
    maps = {u.idx: walk_map(obs, u.pos) for u in obs.units}

    all_tasks = list(tasks)
    for unit in obs.units:
        all_tasks.extend(haul_tasks(obs, p, unit.idx, unit.carrying()))

    pairs = []
    for unit in obs.units:
        reach = maps[unit.idx]
        for t_idx, task in enumerate(all_tasks):
            if task.owner is not None and task.owner != unit.idx:
                continue
            if task.requires and unit.inventory.get(task.requires, 0) <= 0:
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
    taken_groups: set[str] = set()
    for _, unit_idx, t_idx, dist, first in pairs:
        if unit_idx in taken_units or t_idx in taken_tasks:
            continue
        task = all_tasks[t_idx]
        if task.group and task.group in taken_groups:
            continue
        if task.tag == "plant":
            # Seeds run out long before empty tiles do; spend them on the nearest tiles.
            if plants_allowed <= 0:
                continue
            plants_allowed -= 1
        taken_units.add(unit_idx)
        taken_tasks.add(t_idx)
        if task.group:
            taken_groups.add(task.group)
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
