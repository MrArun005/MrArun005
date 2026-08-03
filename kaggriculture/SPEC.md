# SPEC — Kaggriculture (Phase 1)

Source of truth: `kaggle_environments/envs/kaggriculture/kaggriculture.py` (v0.1.0), shipped
inside the `kaggle-environments` PyPI package. **The simulator is available offline — you do
not need the Kaggle API to extract the spec.**

```bash
pip install -U kaggle-environments
python -c "import kaggle_environments.envs.kaggriculture as k; print(k.__file__)"
```

Two variants ship: `kaggriculture` (advanced, 2 players, animals + hands + land) and
`kaggriculture_beginner` (single quadrant, no animals, no hands, harvest auto-sells). This
project targets **`kaggriculture`**.

> Where the shipped `README.md` and the Python source disagree, **the source wins**. Known
> stale entries in the README table: Goose cost is **300** (README says 200), Sheep is **500**
> (README says 400), and Wheat max yield is **6** (beginner README says 4).

---

## 1. Observation

A plain `dict` handed to the agent each turn.

```py
{
  "player": int,            # 0 or 1
  "step":   int,            # global turn counter, 0-indexed (framework-supplied)
  "day":    int,            # step // turnsPerDay
  "hour":   int,            # step %  turnsPerDay
  "farms":  [farm, farm],   # PUBLIC — both farms visible, indexed by player id
  "market": {"inventory": {product: int}, "prices": {product: int}},   # shared
  "town":   {"unlocked_shops": [str, ...]},                            # shared
  "private": {              # THIS player only
      "shed":        {item: int},   # harvested produce, animals, fertilizer
      "seeds":       {crop: int},   # separate slot, uncapped, consumed by PLANT
      "inventories": [farmer_inv, hand1_inv, ...],   # [0] is the main farmer
  },
}
```

`farm` (public):

```py
{"money": float, "tiles": [[tile,...],...],   # tiles[y][x], y grows DOWNWARD
 "farmer": [x, y], "hands": [[x, y], ...],
 "unlocked_quadrants": ["NW", ...], "hires_today": int}
```

`tile` is one of: `None` (empty, unlocked) · `"LOCKED"` · plant dict · `{"kind":"WEED"}` ·
structure dict.

- plant: `kind="PLANT"`, `crop`, `planted_day`, `watered_today`, `consecutive_unwatered`,
  `yield_units`, `max_lifespan_step`, `fertilized_until_day`
- structure: `kind="COOP"|"PASTURE"`, and once occupied also `animal`, `placed_day`,
  `yield_units`, `fed_today`, `consecutive_unfed`, `cared_today`, `fertilizer_available`,
  `pending_care_bonus`

Opponent `private` is hidden. Opponent **tiles and money are visible**.

## 2. Action space

```py
{"farmer": [op, ...args],          # one op for the main farmer
 "hands":  [[op, ...args], ...],   # one op per hired hand, in farm["hands"] order
 "market": [[op, ...args], ...]}   # ordered; only the first maxMarketOrdersPerTurn count
```

Unit ops (farmer and each hand act **independently, one op per turn each**):

| Group | Ops |
| --- | --- |
| Move | `NORTH` `SOUTH` `EAST` `WEST` (blocked by board edge and `LOCKED`), `PASS` |
| Shed | `PICKUP <item> [n]`, `PLACE <item> [n]`, `DROP` — all require shed-adjacency |
| Plant | `PLANT <crop>`, `WATER`, `HARVEST`, `FERTILIZE` |
| Animal | `BUILD_COOP`, `BUILD_PASTURE`, `PLACE <animal>`, `FEED`, `CARE`, `COLLECT_FERTILIZER` |
| Terrain | `DIG` (plant / weed / **empty** coop-pasture; will not remove a placed animal) |

Market ops: `["BUY_SEED", crop, n]`, `["BUY_PRODUCT", item, n]` (**only `WHEAT` and
`FERTILIZER` are buyable**), `["BUY_ANIMAL", animal, n]`, `["SELL", item, n]`, `["HIRE"]`,
`["BUY_LAND"]`.

**Invalid actions are silent no-ops — they never raise and never forfeit.** One exception
worth knowing: PLANT is validated atomically per crop per turn — if the number of units
requesting `PLANT X` exceeds seeds held, *every* `PLANT X` that turn is dropped.

Shed adjacency = the four centre tiles `{(h-1,h-1), (h,h-1), (h-1,h), (h,h)}` for
`h = boardSize//2`, i.e. `(4,4) (5,4) (4,5) (5,5)` on a 10×10 board. Note only `(4,4)` is in
the starting NW quadrant.

## 3. Turn structure

720 turns = **24 turns/day × 30 days**. Per turn, in order (`interpreter`):

1. Unit actions for both players (simultaneous), farmer then hands.
2. Market queue — see §4.
3. Town consumption, then price refresh.
4. Plant decay tick.
5. **End of day** if `(step+1) % 24 == 0`:
   - plants: `watered_today` → `consecutive_unwatered` (2+ ⇒ becomes a WEED); ongoing crops
     tick scheduled production; animals: `consecutive_unfed` (2+ ⇒ animal escapes, structure
     remains); CARE bonus banks; `fertilizer_available = True`
   - weeds spawn on empty tiles (`weedSpawnChance` 0.005 each)
   - **all unit inventories dump into the shed, overflow past 100 is DISCARDED**
   - farmer respawns at the shed, **all hands vanish, `hires_today` resets to 0**
   - a new town shop unlocks every `townShopUnlockInterval` (3) days, chosen at random

Reward/`DONE` fire when `step >= episodeSteps - 2`, i.e. at **step 718** — one turn earlier
than you would guess. Everything must already be sold by then.

## 4. Market clearing (the whole game)

```
price(inv) = base ± amp · f(|inv − I0|)        amp = target · base / f(T)
             +  if inv < I0 (scarcity)  ·  −  if inv > I0 (glut)
f ∈ {linear, sq, sqrt, log(=ln(1+x)), log10}   floor $1, rounded to int
```

Every product starts at `I0 = 10 000`, priced at `base`. Selling raises inventory (price
down); town consumption and `BUY_PRODUCT` lower it (price up).

| Resource | base | T | below f / target | above f / target | glut behaviour |
| --- | --- | --- | --- | --- | --- |
| WHEAT | 25 | 400 | sqrt / 0.80 | **log** / 0.20 | ~$20 no matter how much you dump |
| CARROT | 35 | 450 | log / 0.20 | sqrt / 0.70 | soft — 400 units ⇒ $12 |
| TOMATO | 60 | 200 | linear / 0.40 | sqrt / 0.60 | soft |
| STRAWBERRY | 120 | 100 | sqrt / 0.70 | **linear** / 1.60 | −$1.92 **per unit** — trap |
| MELON | 250 | 300 | log / 0.20 | **sq** / 3.60 | −$0.01·n² — fine to ~100, then cliff |
| EGG | 50 | 332 | linear / 0.40 | **log** / 0.20 | ~$40 forever |
| MILK | 160 | 122 | sqrt / 0.60 | **linear** / 1.60 | −$2.10 per unit — trap at scale |
| WOOL | 200 | 105 | log / 0.20 | **sq** / 3.20 | −$0.058·n² — knife-edge |
| FERTILIZER | 100 | 200 | linear / 0.40 | linear / 0.40 | buy-only, cannot be sold |

**Clearing is per-unit lockstep across both players.** For each order slot, both players'
current unit is quoted against the *same* pre-commit inventory, then both commit, then the
price is re-derived — repeat until both orders drain. Consequences:

- A bulk `SELL X 40` walks its own price down 40 times. **Dribbling small quantities across
  turns strictly dominates dumping**, because town demand refills the gap between turns.
- Sells at the `$1` floor still pay $1 but do **not** add to inventory, so the floor stays
  responsive.
- Buy price is quoted at post-buy inventory, sell at pre-sell — a buy/sell round trip nets
  exactly zero.
- `HIRE` and `BUY_LAND` are atomic and resolve before the per-unit loop, in player order.

**Town demand is the renewable revenue source.** Town centre consumes 1 of every non-fertilizer
product every 12 turns, ×2 after day 10, ×4 after day 20 — about **140 units per product per
season**. Each unlocked shop consumes 1 of each of its products every 4 turns (6/day;
single-product shops 2×). Melon is demanded by **no shop** — town centre only. Wool is the
`YARN_STORE`'s only product at 2× (12/day once unlocked).

Selling at roughly the drain rate keeps price pinned near `base`. That is the entire edge.

## 5. Scoring

`reward = farm["money"]` at the end — **final cash only**. Unsold produce, seeds, land,
animals and standing crops are all worth **zero**. Most coins wins; ties possible. Leaderboard
is pairwise episodes against other submissions, so the opponent shares — and moves — the market.

## 6. Limits

| Limit | Value |
| --- | --- |
| `actTimeout` | **1 second per turn** |
| `remainingOverageTime` | 60 s total slack for the episode |
| Agents per episode | exactly 2 |
| Submission | `main.py` at root exporting `agent`; multi-file via `tar.gz` |
| Imports | standard Kaggle image; no network at episode time |

`agent` must be the **last callable defined** in `main.py` (`kaggle_environments` resolves the
entry point with `get_last_callable`).

---

## Derived economics (the numbers the policy is built on)

Watering bonus window for one-time crops is `ceil(max_yield_day/2) … max_yield_day`, adding
+1 harvestable unit per watered day (+2 while fertilized), capped at `max_yield`. Plants start
at `yield_units = 1` with `consecutive_unwatered = 1`, so **a new seed must be watered on its
planting day or it dies at the next end-of-day**. After that, every-other-day watering
survives; only the bonus window needs consecutive watering.

| Crop | seed | first / max yield day | units w/ perfect watering | cycle | $/tile/day | actions/cycle |
| --- | --- | --- | --- | --- | --- | --- |
| **MELON** | 80 | 10 / 12 | **6** (cap hit at age 10) | **10 d** | **~$150** | ~13 |
| CARROT | 20 | 2 / 3 | 3 | 3 d | ~$35 | ~6 |
| WHEAT | 10 | 2 / 4 | 4 (6 if fertilized) | 4 d | ~$25 | ~7 |
| TOMATO | 50 | 8 / — | 4 **total**, then decays | 12 d | ~$20 | ~14 |
| STRAWBERRY | 100 | 10 / — | 4 **total**, then decays | 17 d | ~$28 | ~19 |

Ongoing crops cap at 4 *cumulative* productions and then rot — they are traps, not annuities.
**Melon is ~4× better per tile-day than anything else**, and its cap is reached at age 10,
exactly `first_yield_day`, so the cycle is a clean 10 days: plant day 0 → harvest day 10 →
replant → harvest day 20. Last useful melon planting day is **19**.

| Animal | cost | first / interval | w/ CARE | product $ | $/tile/day | actions/day |
| --- | --- | --- | --- | --- | --- | --- |
| SHEEP | 500 | 6 d / 3 d | 4 wool / 3 d | 200 | ~$267 | ~2.3 |
| COW | 400 | 8 d / 2 d | 3 milk / 2 d | 160 | ~$240 | ~2.5 |
| GOOSE | 300 | 4 d / 1 d | 2 eggs / d | 50 | ~$100 | ~2.5 |

Animals also eat **1 WHEAT per animal per day** (from the acting unit's inventory, so feeding
needs a `PICKUP WHEAT` trip), and their high-base products are exactly the ones that crash.

**Hiring is drastically underpriced.** Cost of the n-th hire *today* is `fib(n)` = 1, 1, 2, 3,
5, 8, 13, 21, 34, 55 — and it resets daily. Ten hands cost **$143 for the day** and buy
`10 × 23 = 230` extra actions. There is **no cap on hand count** in the source. Actions, not
money, are the real constraint mid-game, and hands convert money into actions at a
near-free rate. This is the single largest exploitable asymmetry in the game.

Land: NW (25 tiles) free; NE/SW/SE cost $1 000 / $2 000 / $4 000. One melon tile grosses
~$1 500 per 10-day cycle, so every quadrant pays for itself in one cycle — provided you have
the hands to water it.

## Consequences for the policy

1. **Hire aggressively every day** (hands vanish nightly; re-hire at hour 0).
2. **Melon monoculture**, staggered, with carrot/wheat filling short windows and the tail.
3. **Buy all three quadrants** as soon as cash allows.
4. **Water minimally**: only when `consecutive_unwatered >= 1` (survival) or inside the bonus
   window (yield). Saves ~25% of water actions versus watering daily.
5. **Dribble sales gated on price** — sell only while `price >= frac · base`, a few units per
   turn. This automatically tracks town drain and keeps price pinned near base.
6. **Respect the shed cap (100).** Overflow at end-of-day is destroyed, so force-sell through
   the price gate under shed pressure.
7. **Liquidate before step 718**, not 719 — and get produce out of unit inventories into the
   shed on the final day, because the free end-of-day dump comes too late to be sold.
