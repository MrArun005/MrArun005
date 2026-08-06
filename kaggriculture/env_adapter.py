"""
Adapter boundary.

Everything that knows the raw competition schema lives HERE and nowhere else.
`rules.py`, `harness.py` and `tune.py` are written against Observation/Action.

If you find yourself reaching for a raw competition dict outside this file,
stop and add a field to Observation instead.

Game constants are duplicated from the shipped simulator rather than imported,
so the submission has no dependency on `kaggle_environments` at episode time.
Verified against kaggriculture.py v0.1.0 — see SPEC.md.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Any

# --- game constants (mirrored from kaggriculture.py) ------------------------

CROPS = {
    "WHEAT":      {"seed": 10,  "first_yield_day": 2,  "max_yield_day": 4,  "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first_yield_day": 2,  "max_yield_day": 3,  "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first_yield_day": 8,  "max_yield_day": 8,  "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]

# base sale price at I0; used to normalise price gates into "fraction of base".
BASE_PRICE = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
    "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100,
}

# The shipped README claims fertilizer is buy-only, but the simulator's SELL handler
# accepts any item in PRODUCTS — verified against kaggriculture.py v0.1.0 (SELL branch),
# and confirmed in leaderboard replays where top agents sell 100+ FERTILIZER per episode.
SELLABLE = list(PRODUCTS)

LAND_PRICES = [1000, 2000, 4000]

# The engine's exact market curve (kaggriculture.py:38-61, verified 1.32.4). Selling walks
# inventory up and the price down along these shapes; knowing the curve exactly lets the
# seller size an order so the LAST unit still clears its reserve, instead of dumping a
# blind fixed chunk.
MARKET_I0 = 10000
MARKET_PARAMS = {
    "WHEAT":      {"base":  25, "T": 400, "bf": "sqrt",   "bt": 0.80, "af": "log",    "at": 0.20},
    "CARROT":     {"base":  35, "T": 450, "bf": "log",    "bt": 0.20, "af": "sqrt",   "at": 0.70},
    "TOMATO":     {"base":  60, "T": 200, "bf": "linear", "bt": 0.40, "af": "sqrt",   "at": 0.60},
    "STRAWBERRY": {"base": 120, "T": 100, "bf": "sqrt",   "bt": 0.70, "af": "linear", "at": 1.60},
    "MELON":      {"base": 250, "T": 300, "bf": "log",    "bt": 0.20, "af": "sq",     "at": 3.60},
    "EGG":        {"base":  50, "T": 332, "bf": "linear", "bt": 0.40, "af": "log",    "at": 0.20},
    "MILK":       {"base": 160, "T": 122, "bf": "sqrt",   "bt": 0.60, "af": "linear", "at": 1.60},
    "WOOL":       {"base": 200, "T": 105, "bf": "log",    "bt": 0.20, "af": "sq",     "at": 3.20},
    "FERTILIZER": {"base": 100, "T": 200, "bf": "linear", "bt": 0.40, "af": "linear", "at": 0.40},
}


def _shape(func: str, x: float) -> float:
    import math
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    return x


def market_price(item: str, inventory: float) -> int:
    """Exact engine price at a given market inventory (floor 1)."""
    p = MARKET_PARAMS[item]
    base = p["base"]
    if inventory < MARKET_I0:
        amp = p["bt"] * base / _shape(p["bf"], p["T"])
        price = base + amp * _shape(p["bf"], MARKET_I0 - inventory)
    else:
        amp = p["at"] * base / _shape(p["af"], p["T"])
        price = base - amp * _shape(p["af"], inventory - MARKET_I0)
    return max(1, int(round(price)))

DIRECTIONS = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


def water_window_start(crop: str) -> int:
    """First age (in days) at which WATER adds bonus yield. ceil(max_yield_day / 2)."""
    return (CROPS[crop]["max_yield_day"] + 1) // 2


def fib(n: int) -> int:
    """fib(0)=1, fib(1)=1, fib(2)=2, ... — matches the simulator's hire cost."""
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def hire_cost(hires_today: int, mult: int = 1) -> int:
    return mult * fib(hires_today)


# --- normalized view --------------------------------------------------------

@dataclass
class Tile:
    x: int = 0
    y: int = 0
    # EMPTY | LOCKED | PLANT | WEED | COOP | PASTURE | ANIMAL
    state: str = "EMPTY"
    crop: str | None = None
    animal: str | None = None
    age_days: int = 0
    watered_today: bool = False
    consecutive_unwatered: int = 0
    yield_units: int = 0
    max_lifespan_step: int = -1
    fertilized_until_day: int = -1
    fed_today: bool = False
    cared_today: bool = False
    consecutive_unfed: int = 0
    fertilizer_available: bool = False
    pending_care_bonus: int = 0

    @property
    def pos(self) -> tuple[int, int]:
        return (self.x, self.y)

    @property
    def is_empty(self) -> bool:
        return self.state == "EMPTY"

    @property
    def is_plant(self) -> bool:
        return self.state == "PLANT"


@dataclass
class Unit:
    """The main farmer (idx 0) or a hired hand (idx 1+). One op per turn each."""
    idx: int = 0
    x: int = 0
    y: int = 0
    inventory: dict[str, int] = field(default_factory=dict)

    @property
    def pos(self) -> tuple[int, int]:
        return (self.x, self.y)

    def carrying(self) -> int:
        return sum(self.inventory.values())


@dataclass
class Observation:
    """Normalized view of game state."""
    player: int = 0
    step: int = 0
    day: int = 0
    hour: int = 0
    turns_per_day: int = 24
    episode_steps: int = 720
    board_size: int = 10
    max_market_orders: int = 10
    shed_capacity: int = 100
    hire_mult: int = 1

    cash: float = 0.0
    opponent_cash: float = 0.0
    # Opponent melon tiles within ~3 days of maturity (age >= 7 of melon's 10). Their whole
    # farm is visible every turn; this is the one number that prices tomorrow's melon
    # market, because melon gluts quadratically and nothing drains it back down.
    opp_melon_soon: int = 0

    tiles: list[Tile] = field(default_factory=list)          # flat, all cells
    grid: dict[tuple[int, int], Tile] = field(default_factory=dict)
    units: list[Unit] = field(default_factory=list)          # [0] = main farmer

    shed: dict[str, int] = field(default_factory=dict)
    seeds: dict[str, int] = field(default_factory=dict)
    prices: dict[str, int] = field(default_factory=dict)
    market_inventory: dict[str, int] = field(default_factory=dict)

    unlocked_quadrants: list[str] = field(default_factory=list)
    hires_today: int = 0
    shops: list[str] = field(default_factory=list)

    shed_access: list[tuple[int, int]] = field(default_factory=list)
    raw: Any = None

    # --- derived helpers ---------------------------------------------------

    @property
    def total_days(self) -> int:
        return max(1, self.episode_steps // self.turns_per_day)

    @property
    def days_remaining(self) -> int:
        """Whole days of play left, including today."""
        return max(0, self.total_days - self.day)

    @property
    def turns_remaining(self) -> int:
        # reward is latched at episode_steps - 2, so that is the effective horizon
        return max(0, (self.episode_steps - 2) - self.step)

    @property
    def shed_used(self) -> int:
        return sum(self.shed.values())

    @property
    def shed_free(self) -> int:
        return max(0, self.shed_capacity - self.shed_used)

    def price_frac(self, item: str) -> float:
        """Current price as a fraction of the item's base price."""
        base = BASE_PRICE.get(item, 1) or 1
        return self.prices.get(item, base) / base

    def is_shed_adjacent(self, pos) -> bool:
        return tuple(pos) in set(self.shed_access)

    def empty_tiles(self) -> list[Tile]:
        return [t for t in self.tiles if t.state == "EMPTY"]

    def next_land_price(self) -> int | None:
        extra = len(self.unlocked_quadrants) - 1
        if extra < 0 or extra >= len(LAND_PRICES):
            return None
        return LAND_PRICES[extra]


@dataclass
class Action:
    """Normalized action. unit_ops[0] is the main farmer, then one per hired hand."""
    unit_ops: list[list] = field(default_factory=list)
    market: list[list] = field(default_factory=list)


# --- parsing ----------------------------------------------------------------

def _cfg(cfg: Any, key: str, default):
    if cfg is None:
        return default
    if isinstance(cfg, dict):
        value = cfg.get(key, default)
    else:
        value = getattr(cfg, key, default)
    return default if value is None else value


def shed_access_tiles(board_size: int) -> list[tuple[int, int]]:
    """Four inner-corner tiles around the shed, NWSE order."""
    h = board_size // 2
    return [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]


def _parse_tile(raw, x: int, y: int, day: int) -> Tile:
    if raw is None:
        return Tile(x=x, y=y, state="EMPTY")
    if raw == "LOCKED":
        return Tile(x=x, y=y, state="LOCKED")
    if not isinstance(raw, dict):
        return Tile(x=x, y=y, state="LOCKED")  # unknown ⇒ treat as unusable

    kind = raw.get("kind")
    if kind == "PLANT":
        return Tile(
            x=x, y=y, state="PLANT", crop=raw.get("crop"),
            age_days=day - int(raw.get("planted_day", day)),
            watered_today=bool(raw.get("watered_today", False)),
            consecutive_unwatered=int(raw.get("consecutive_unwatered", 0)),
            yield_units=int(raw.get("yield_units", 0)),
            max_lifespan_step=int(raw.get("max_lifespan_step", -1)),
            fertilized_until_day=int(raw.get("fertilized_until_day", -1)),
        )
    if kind == "WEED":
        return Tile(x=x, y=y, state="WEED")
    if kind in ("COOP", "PASTURE"):
        animal = raw.get("animal")
        return Tile(
            x=x, y=y, state="ANIMAL" if animal else kind, crop=None, animal=animal,
            age_days=day - int(raw.get("placed_day", day)),
            yield_units=int(raw.get("yield_units", 0)),
            fed_today=bool(raw.get("fed_today", False)),
            cared_today=bool(raw.get("cared_today", False)),
            consecutive_unfed=int(raw.get("consecutive_unfed", 0)),
            fertilizer_available=bool(raw.get("fertilizer_available", False)),
            pending_care_bonus=int(raw.get("pending_care_bonus", 0)),
        )
    return Tile(x=x, y=y, state="LOCKED")


def parse(raw_obs: Any, raw_cfg: Any = None) -> Observation:
    """Competition state -> Observation."""
    get = raw_obs.get if isinstance(raw_obs, dict) else (lambda k, d=None: getattr(raw_obs, k, d))

    player = int(get("player", 0) or 0)
    turns_per_day = int(_cfg(raw_cfg, "turnsPerDay", 24) or 24)
    episode_steps = int(_cfg(raw_cfg, "episodeSteps", 720) or 720)

    day = int(get("day", 0) or 0)
    hour = int(get("hour", 0) or 0)
    step = get("step", None)
    step = day * turns_per_day + hour if step is None else int(step)

    farms = get("farms", []) or []
    farm = farms[player] if player < len(farms) else {}
    board_size = len(farm.get("tiles", [])) or int(_cfg(raw_cfg, "boardSize", 10) or 10)

    obs = Observation(
        player=player, step=step, day=day, hour=hour,
        turns_per_day=turns_per_day, episode_steps=episode_steps, board_size=board_size,
        max_market_orders=int(_cfg(raw_cfg, "maxMarketOrdersPerTurn", 10) or 10),
        shed_capacity=int(_cfg(raw_cfg, "shedCapacity", 100) or 100),
        hire_mult=int(_cfg(raw_cfg, "farmHandCostMult", 1) or 1),
        cash=float(farm.get("money", 0.0) or 0.0),
        unlocked_quadrants=list(farm.get("unlocked_quadrants", ["NW"]) or ["NW"]),
        hires_today=int(farm.get("hires_today", 0) or 0),
        shed_access=shed_access_tiles(board_size),
        raw=raw_obs,
    )

    for i, other in enumerate(farms):
        if i != player:
            obs.opponent_cash = float(other.get("money", 0.0) or 0.0)
            for orow in other.get("tiles", []) or []:
                for cell in orow:
                    if (isinstance(cell, dict) and cell.get("kind") == "PLANT"
                            and cell.get("crop") == "MELON"
                            and day - int(cell.get("planted_day", day)) >= 7):
                        obs.opp_melon_soon += 1
            break

    rows = farm.get("tiles", []) or []
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            tile = _parse_tile(cell, x, y, day)
            obs.tiles.append(tile)
            obs.grid[(x, y)] = tile

    private = get("private", {}) or {}
    inventories = private.get("inventories", [{}]) or [{}]
    fx, fy = (farm.get("farmer") or [0, 0])[:2]
    obs.units.append(Unit(idx=0, x=int(fx), y=int(fy),
                          inventory=dict(inventories[0] if inventories else {})))
    for h_idx, pos in enumerate(farm.get("hands", []) or []):
        inv = inventories[h_idx + 1] if h_idx + 1 < len(inventories) else {}
        obs.units.append(Unit(idx=h_idx + 1, x=int(pos[0]), y=int(pos[1]), inventory=dict(inv)))

    obs.shed = {k: int(v) for k, v in (private.get("shed", {}) or {}).items()}
    obs.seeds = {k: int(v) for k, v in (private.get("seeds", {}) or {}).items()}

    market = get("market", {}) or {}
    obs.prices = {k: int(v) for k, v in (market.get("prices", {}) or {}).items()}
    obs.market_inventory = {k: int(v) for k, v in (market.get("inventory", {}) or {}).items()}

    obs.shops = list((get("town", {}) or {}).get("unlocked_shops", []) or [])
    return obs


def serialize(action: Action, obs: Observation) -> dict:
    """Action -> the dict the competition expects returned."""
    ops = list(action.unit_ops)
    n_units = max(1, len(obs.units))
    while len(ops) < n_units:
        ops.append(["PASS"])
    farmer = ops[0] if ops and isinstance(ops[0], list) and ops[0] else ["PASS"]
    hands = [op if isinstance(op, list) and op else ["PASS"] for op in ops[1:n_units]]
    return {
        "farmer": farmer,
        "hands": hands,
        "market": [o for o in action.market if isinstance(o, list) and o][: obs.max_market_orders],
    }


# --- pathing ----------------------------------------------------------------

def walk_map(obs: Observation, start: tuple[int, int]) -> dict[tuple[int, int], tuple[int, str]]:
    """BFS over walkable (non-LOCKED) tiles.

    Returns {pos: (distance, first_step_direction)}. The start maps to (0, "PASS").
    Board is 10x10, so this is ~100 cells per unit per turn — cheap enough to do
    exactly rather than approximating with Manhattan distance, which would be wrong
    whenever a locked quadrant sits between a unit and its task.
    """
    n = obs.board_size
    out: dict[tuple[int, int], tuple[int, str]] = {}
    start = (int(start[0]), int(start[1]))
    if obs.grid.get(start) is None:
        return out
    # A unit may legitimately *stand* on a LOCKED tile — hands spawn on shed-access
    # tiles, and three of the four are outside the starting NW quadrant. The simulator
    # checks the move op before it checks the current tile, so such a unit can still
    # walk off. Seed the BFS from it regardless; only expansion requires unlocked.
    out[start] = (0, "PASS")
    queue = deque([start])
    while queue:
        pos = queue.popleft()
        dist, first = out[pos]
        for name, (dx, dy) in DIRECTIONS.items():
            nxt = (pos[0] + dx, pos[1] + dy)
            if not (0 <= nxt[0] < n and 0 <= nxt[1] < n) or nxt in out:
                continue
            cell = obs.grid.get(nxt)
            if cell is None or cell.state == "LOCKED":
                continue
            out[nxt] = (dist + 1, name if dist == 0 else first)
            queue.append(nxt)
    return out
