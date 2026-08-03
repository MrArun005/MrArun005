# Kaggriculture — a rule-engine agent

Competition: [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) — a two-player
farming sim. Each player works a 10×10 farm over a 30-day season and sells into a **shared,
reactive market**. Score is final cash. Nothing else counts.

No RL, no ML, no frameworks. A prioritized rule engine plus a task dispatcher, ~700 lines of
loops and conditionals, with every threshold searched by a local harness.

| Agent | Mean final cash | vs baseline |
| --- | --- | --- |
| `pass` (built-in) | 3,000 | — |
| `starter` (built-in carrot loop) | ~3,500 | 1.0× |
| **this agent** | **see `results.md`** | **~20×** |

---

## Layout

| File | Role |
| --- | --- |
| `SPEC.md` | Phase 1 output: the extracted rules, price curves and derived economics |
| `env_adapter.py` | The **only** file that knows the raw competition schema |
| `rules.py` | `Params` + the policy: market plan, task generation, assignment |
| `main.py` | Submission entry point. Thin, fail-soft, `agent` defined last |
| `harness.py` | N-episode evaluation: mean, stdev, paired comparison |
| `diagnose.py` | Single-episode instrumentation: where the money isn't coming from |
| `tune.py` | Coordinate-descent threshold search, gated on paired significance |
| `results.md` | Measured results and the tuned parameter set |

```bash
pip install -U kaggle-environments
python harness.py --episodes 30 --benchmark   # score vs every built-in
python diagnose.py --seed 7                   # one episode, instrumented
python tune.py --episodes 8 --sigma 1.5       # search thresholds
```

---

## The one thing that mattered

**The simulator ships inside the `kaggle-environments` PyPI package.** The entire Phase 1
spec — turn order, exact price curves, yield formulas — is readable offline, no Kaggle API
and no reverse-engineering required:

```bash
python -c "import kaggle_environments.envs.kaggriculture as k; print(k.__file__)"
```

Everything below is a consequence of reading that file rather than the prose description.
Where the shipped `README.md` disagrees with the source, the source wins — the README's
animal costs and wheat yield are stale.

## What the spec actually says

**Actions are the scarce resource, not money.** Each unit gets exactly one op per turn, 24
turns per day. Watering a tile, walking one square, and harvesting a $250 melon all cost the
same single op. Every design decision follows from that.

**Hiring is drastically underpriced.** The n-th hire *of the day* costs `fib(n)` = 1, 1, 2,
3, 5, 8, 13, 21… and the counter resets every morning. Ten hands cost **$143 for a day** and
buy 230 extra actions. There is no cap on hand count in the source. This is the single
largest exploitable asymmetry in the game, and the built-in `starter` agent never hires once.

The fib ladder does eventually bite — the 15th hand alone costs $610 — which caps a day's
crew at roughly 12–14 hands and therefore caps *worked* tiles at ~50–60. That is why buying
the fourth quadrant for $4,000 was a straight loss until land purchases were gated on
actually running out of room.

**Melon is the whole crop economy.** ~$150 per tile-day against carrot's $35, and ~6× better
per *action* than wheat. Its yield cap is reached at age 10, exactly its `first_yield_day`,
so the cycle is a clean 10 days.

**But melon volume is price-capped, and no town shop demands it.** Melon is drained only by
the town centre (~140 units/season) and its glut curve is `sq` with a 3.6 target: a net
excess of 158 units takes it from $250 to the $1 floor. So melon is capped by *tile count*,
not by price signals — by the time price feedback says stop, you have already given away the
margin. Everything else goes to carrot and wheat.

**Ongoing crops are traps.** Tomato and strawberry read like annuities — "yields every day" —
but `max_yield` is a cap on *cumulative productions*: 4 total, then the plant rots. Tomato
returns ~$20/tile-day over 12 days. The engine scores them at `-inf`.

**Town demand is the renewable revenue source.** Shops and the town centre consume product
for free, forever, which is what lets price recover between turns. Selling at roughly the
drain rate keeps price pinned near base — so the seller **dribbles a few units per turn
behind a price gate** instead of dumping. Market clearing is per-unit lockstep, so a bulk
`SELL X 40` walks its own price down forty times.

**The reward latches at step 718, not 719.** One turn *before* the free end-of-day dump that
moves produce from unit inventories into the shed. Anything still in a farmhand's arms on the
final day is worth zero, so the last day gets a mandatory haul-to-shed priority.

## How the engine is shaped

Three independent decisions per turn:

1. **`market_plan`** — sells first (orders resolve in list order, so this turn's revenue funds
   this turn's purchases), then hiring, livestock, seeds, land. Capped at 10 orders.
2. **`build_tasks`** — one prioritized task per tile that wants work: water, harvest, plant,
   dig, feed, care, build, place, shed errand.
3. **`assign`** — greedily match units to tasks, scoring each pair by **value per turn**,
   `priority / (1 + move_cost · distance)`, over a real BFS distance that respects locked
   quadrants.

That ratio was the second-biggest single win. Scoring pairs by `priority − move_cost · dist`
instead let a distant high-priority task outbid work the unit was already standing on, and
burned **55% of all unit-turns on walking**.

Two mechanics force per-unit task eligibility, so tasks carry a `requires` field: `FEED`
consumes wheat from the *acting unit's* inventory rather than the shed, and `PLACE` needs the
animal in hand. Shed errands are emitted at all four access tiles and share a `group` so any
unit can take the nearest one but the errand is only done once.

## Things that were wrong on the first try

Kept here because the failures were more informative than the successes.

- **Fail-soft hid a crash.** A typo (`p.shed_capacity` for `obs.shed_capacity`) made the
  agent throw every single turn; the `except` returned PASS, and the episode still "scored"
  3,000. The harness now runs **strict** by default and re-raises — submissions must fail
  soft, but a development harness that swallows exceptions will happily tune a broken policy.
- **Plant tasks went to the first N empty tiles in row-major order**, not the nearest ones, so
  the farmer walked four tiles north to plant while standing on bare earth. Fixed by emitting
  a task for every empty tile and enforcing the seed budget during *assignment*.
- **Hands stranded on locked tiles.** Hands spawn on the four shed-access tiles, three of
  which sit outside the starting NW quadrant. The BFS refused to start from a locked tile, so
  those hands sat still all game — while the simulator would happily have let them walk off,
  because it checks the move op before it checks the current tile.
- **Livestock, first attempt: −57%.** Buying 6 sheep and 4 cows on day 0 spent $4,600 of a
  $3,000 opening bank, left **$36** in the till, and bought no wheat — so the animals starved,
  escaped, and the restocking logic bought replacements that starved the same way. It also
  halved our unit-turns, because there was nothing left to hire hands with. Livestock only
  pays when it is bought out of *melon profit* and when feed is purchased *before* animals.
  A modest 4 sheep + 2 cows then adds ~13%; 6 sheep + 4 cows is worse than none at all.

## Method

Single-episode results are noise: the market is reactive, weeds spawn randomly, and the
town-shop unlock order is random. Every change is judged by `harness.compare` on **paired
seeds**, and accepted only if the delta clears ~2 paired standard errors. `tune.py` applies
the same gate to every candidate — without it you spend the afternoon ratcheting on noise.

`diagnose.py` exists because the harness only says *whether* something helped. The
instrumentation — idle unit-turns, ops histogram, peak shed occupancy, realised price per
product — is what said "55% of your turns are walking" and "the shed is pinned at its 100 cap,
so you are destroying produce at every end-of-day".

## Known limits

- **Tuned against `starter`, which sells only carrots.** A real opponent contests the melon
  and wool pools, which lowers realised prices for both players. `tune.py --opponent self`
  runs self-play to check the tuned parameters are not exploiting a passive market.
- **No opponent modelling.** Opponent tiles and cash are fully visible in the observation, so
  their melon pipeline is countable ~10 days ahead of the glut. Selling into that before they
  harvest is a real, unexploited edge.
- **Fertilizer is unused.** `COLLECT_FERTILIZER` yields 1/animal/day for free and fertilizing
  wheat lifts its yield from 4 to 6, but at ~2 actions per +$50 it loses to spending those
  actions on melon. Worth revisiting only if the action budget stops binding.
- Seat 0 has a small structural edge (atomic orders resolve in player order). Use
  `--both-seats` when a result needs to be seat-independent.
