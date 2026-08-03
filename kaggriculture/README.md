# Kaggriculture — a rule-engine agent

Competition: [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) — a two-player
farming sim. Each player works a 10×10 farm over a 30-day season and sells into a **shared,
reactive market**. Score is final cash. Nothing else counts.

No RL, no ML, no frameworks. A prioritized rule engine plus a task dispatcher, ~700 lines of
loops and conditionals, with every threshold searched by a local harness.

Measured over 10 seeds × both seats per opponent (`results.md`, regenerate with `report.py`):

| Matchup | Our mean | Stdev | Their mean | Win rate |
| --- | --- | --- | --- | --- |
| vs `pass` (built-in) | **71,938** | 1,865 | 3,000 | 100% |
| vs `starter` (built-in carrot loop) | **71,645** | 1,870 | 3,497 | 100% |
| vs `random` (built-in) | **71,456** | 1,732 | 10 | 100% |
| **vs itself (self-play)** | **35,040** | 2,261 | 35,040 | 45% |

**~20× the `starter` baseline, and never loses to a built-in.** But read the self-play row
before believing the headline: against an opponent that also farms properly, the score
*halves*. Both agents drain the same finite town demand, so revenue is split rather than
doubled. The agent degrades gracefully rather than collapsing — the price gate keeps it from
selling into a floor — but 72k is a number earned against passive opponents, and ~35k is what
a contested market pays. Expect the leaderboard to sit closer to the latter.

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
| `tune.py` | Coordinate-descent threshold search, gated on significance *and* effect size |
| `test_agent.py` | Submission safety suite — run before every submit |
| `report.py` | Generates `results.md` |
| `package.sh` | Runs the safety suite, then builds `submission.tar.gz` |

```bash
pip install -U kaggle-environments
python test_agent.py                          # submission safety checks
python harness.py --episodes 30 --benchmark   # score vs every built-in
python diagnose.py --seed 7                   # one episode, instrumented
python tune.py --episodes 8 --sigma 1.5       # search thresholds
./package.sh                                  # test + build submission.tar.gz
```

Submit as a tarball with `main.py` at the root — the loader puts the archive directory on
`sys.path`, so the sibling modules import normally:

```bash
kaggle competitions submit kaggriculture -f submission.tar.gz -m "rule engine v1"
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
- **`main.py` would not have loaded at all.** It used `os.path.dirname(__file__)` to find its
  siblings, and Kaggle `exec`s the submission against a bare globals dict where `__file__`
  does not exist. The agent worked perfectly under `import` and would have been rejected on
  upload. `test_agent.py` now exercises the real `get_last_callable` path.

## Two results that contradicted the analysis

Worth recording because the numbers won and the reasoning lost.

**More livestock is worse, even though wool and milk sell *above* base price.** Diagnostics
show milk realising $254 against a $160 base and wool $249 against $200 — both are trading at
*scarcity* prices, meaning town demand outruns our supply and there is clearly headroom. Yet
6 sheep + 4 cows scores −7.9k against 4 + 2, and 8 + 8 scores −24k.

My first explanation was a priority conflict: `prio_feed_critical` (120) outranks
`prio_water_urgent` (95), so extra animals should pull the crew onto feed runs while crops go
unwatered. Testing it refuted it — dropping feed priority below watering is **worse** again
(−4.4k), because animals then miss two feeds and escape outright. The actual ceiling is
plain action cost: roughly 4 unit-turns per animal per day (feed, care, harvest, and shed
trips for wheat) out of a ~5,200-turn season, and past ~6 animals the marginal animal costs
more in displaced farming than its product is worth. The revenue pool is real and
unreachable — we cannot buy the actions to harvest it.

**Value-weighting the watering priority did nothing.** A missed in-window watering costs
exactly one harvestable unit and the window never returns, so skipping a melon looks like
$250 lost for one op against ~$30 on wheat — an obvious case for scaling priority by unit
price. Measured over 14 out-of-sample seeds it was flat to *negative*. Melon already wins the
distance tiebreak often enough, and starving the cheap crops costs more than the melon it
saves. The code was reverted; only the comment survives.

**The hand-derived parameters were already near a local optimum.** A 28-parameter coordinate
search moved the mean from 69.2k to 71.9k — about +4%. Only three accepted changes were worth
more than a rounding error (`sell_chunk` 3→8, `move_cost` 0.9→0.4, `seed_buffer` 30→12).
Everything that mattered came from reading the simulator, not from searching over it. The
tuned set was then validated on 16 seeds the search never saw: **+3,106 out of sample**, and
stdev down from 3,390 to 1,134 — it generalised and got steadier, so no overfit.

## Method

Single-episode results are noise: the market is reactive, weeds spawn randomly, and the
town-shop unlock order is random. Every change is judged by `harness.compare` on **paired
seeds** — same seeds for both arms — and accepted only if the delta clears ~2 paired standard
errors.

Significance alone turned out not to be enough. Episodes are deterministic given a seed, so a
change that nudges every episode by the same small amount has a near-zero paired standard
error and clears any sigma gate: the search happily accepted a **+5 coin** change on a 69,000
baseline at 1.7σ. `tune.py` now also requires an absolute effect floor, and whatever it
produces is validated on **seeds it never saw** before shipping — coordinate descent over 28
knobs on 8 seeds can memorise the seed set.

`diagnose.py` exists because the harness only says *whether* something helped. The
instrumentation — idle unit-turns, ops histogram, peak shed occupancy, realised price per
product — is what said "55% of your turns are walking", "the shed is pinned at its 100 cap, so
you are destroying produce at every end-of-day", and "wool is selling above base, so the
constraint is not the market".

## Known limits

- **Tuned against `starter`, which sells only carrots.** The thresholds were searched in an
  uncontested market, and self-play shows the environment is very different when it isn't.
  `tune.py --opponent self` re-runs the search under contention; that is the obvious next
  move and it was not done here.
- **No opponent modelling.** Opponent tiles and cash are fully visible in the observation, so
  their melon pipeline is countable ~10 days before it hits the market. Given that self-play
  halves revenue, selling ahead of a visible glut is the largest single unexploited edge left.
- **Livestock revenue is visible but unreachable.** Wool and milk trade *above* base price,
  meaning town demand is unmet, but every extra animal costs ~4 unit-turns a day and past ~6
  animals the displaced farming is worth more. Only a cheaper source of actions would unlock
  it, and hands are already priced out by the fib ladder at ~11.
- **Fertilizer is unused.** `COLLECT_FERTILIZER` yields 1/animal/day for free and fertilizing
  wheat lifts its yield from 4 to 6, but at ~2 actions per +$50 it loses to spending those
  actions on melon. Worth revisiting only if the action budget stops binding.
- **Degrades badly with a small shed.** At `shedCapacity=10` the agent finishes *below* its
  opening bank — seed and hire spending is not conditioned on how much produce can be stored.
  The competition default is 100, so this is off-spec rather than urgent.
- Seat 0 has a small structural edge (atomic orders resolve in player order). Use
  `--both-seats` when a result needs to be seat-independent.
