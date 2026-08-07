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
    ANIMALS, BASE_PRICE, CROPS, MARKET_I0, SELLABLE,
    Action, Observation, Tile, hire_cost, market_price, walk_map, water_window_start,
)

NEG_INF = float("-inf")

# Per-product reservation prices as a fraction of base, distilled from the public top-meta
# notebooks (Barnyard Economist / Structured Economic Policy — both independently landed on
# nearly identical tables, backed by measured ~90k banks). Products the town shops drain hard
# (milk, wool) hold near base all game; melon has zero shop demand and a quadratic glut curve,
# so waiting for 0.85x base rides it to the floor. Fertilizer's price never refills at all.
SELL_FRACS = {
    "MILK": 0.80, "WOOL": 0.80, "EGG": 0.72, "WHEAT": 0.70, "CARROT": 0.62,
    "MELON": 0.60, "STRAWBERRY": 0.50, "TOMATO": 0.50, "FERTILIZER": 0.15,
}


@dataclass
class Params:
    """Every magic number in one place. tune.py mutates these, not the rules."""

    # --- labour -------------------------------------------------------------
    # 0.16, not 0.11: the whole public top-10 runs 12-13 hands (12 cost $376/day, ~1.3
    # coins per bought action against melon waterings worth ~250). Under-hiring was v1/v2's
    # most expensive habit. The scaled cap below keeps this from leaking into configs where
    # hands cannot pay for themselves.
    # 0.14, chosen on WIN RATE, which is the only thing the ladder pays for. Head-to-head
    # against the previous build over seeds 700-709 x both seats — one consecutive block, so
    # the settings are comparable to each other rather than to whichever seeds flattered them:
    #     0.13 -> 14/20   0.14 -> 17/20   0.15 -> 15/20   0.16 -> 16/20   0.24 -> 0/20
    # Read that honestly: 14-17 out of 20 is inside the noise of this sample, so 0.14 beats
    # the old 0.16 by a single episode and is not a strong result. What actually separates it
    # is the worst-case margin, -1,717 against 0.16's -5,085 — it loses smaller, which is what
    # a win-rate ladder pays for. (An earlier mixed seed set showed 0.14 at 19/20; that was
    # the seed set, not the setting. Do not quote that number.)
    # Idle unit-turns rise with headcount — 10.7% at 0.14, 12.4% at 0.16, 16.4% at 0.20 — so
    # past ~11 hands the extra ones draw wages without reaching work.
    # Tune this on wins, never on mean: 0.15 banks MORE vs starter than 0.14 (161,871 vs
    # 159,346) while winning fewer games, and 0.12 banked more than 0.14 while winning 12/20.
    # `max_hands` never binds either way: 75 workable tiles x 0.14 = 10, under the cap of 13.
    hands_per_tile: float = 0.14      # target hands per unlocked tile
    max_hands: int = 13               # hard cap on hands hired per day
    # Interpreted through a season- and farm-scaled cap (see target_hands): the full 144
    # only applies on a full-length season with a grown farm. On a 240-step episode with
    # farmHandCostMult 20 the scaled cap admits exactly the 2 hands that measured best
    # (4,857 vs 2,946 mean over seeds 5-8).
    max_hire_cost: float = 144.0      # skip a hire once its cost exceeds a hand's day of work
    final_day_hands: int = 8          # cheap re-hires on the last morning, purely to harvest+haul
    hire_until_hour: int = 4          # only hire early; a late hand has few turns left
    max_hires_per_turn: int = 6       # HIREs are one market order each (cap 10/turn)
    hire_cash_reserve: float = 60.0   # keep this much after paying for the day's hands

    # --- land ---------------------------------------------------------------
    land_cash_reserve: float = 1200.0  # cash to keep spare after buying a quadrant
    # Measured, not guessed: 18 and 19 score bit-identically to 22 (no quadrant is ever
    # bought after day 18), so the binding cut is the *last* purchase — the $4k SE quadrant
    # around day 16-18. Blocking it is worth +1,285 (both seats, 48 episodes), because a
    # quadrant that late cannot be filled and worked before the season ends. 12 is worse
    # than 15: it starts blocking expansion that does still pay back.
    last_land_day: int = 15
    # Cows before land: the measured opening-order result from the public meta — the first
    # $3,000 goes into livestock (3 cows by day 3), and the day-15 cash gap decides games.
    # Land bought on day 0 delayed the herd and cost ~9k over the season.
    min_land_day: int = 4
    # 12, not 6: with the strawberry ramp consuming empties a few per day, the 6-empty
    # trigger only fired on day 16 — one day after last_land_day closed the window — so the
    # farm sat on 2 quadrants and $10-30k of idle cash all game while the clones work 3
    # quadrants (75 tiles: 40 strawberry + 14 pens + endgame wheat) from day 12.
    land_empty_threshold: int = 18    # only expand when this few tiles are still empty
    land_lead_days: int = 5           # days needed to fill a new quadrant before its crop cycle
    land_payback_mult: float = 1.5    # a quadrant must earn this multiple of its price
    # 7.0 blocked the third quadrant on the standard config: by mid-game ~50 tiles are worked,
    # the crew tops out around 9-10, and 50+25 > 9*7 vetoed the $2k SW purchase every episode.
    # Replay analysis: every leaderboard agent that beat v1 held 3 quadrants by mid-game. The
    # extra tiles are wheat and pens (cheap upkeep), not melon, so 9 tiles/unit is realistic.
    tiles_per_unit: float = 9.0       # tiles one unit can keep tended per day

    # --- selling ------------------------------------------------------------
    sell_min_frac: float = 0.85       # fallback gate for products missing from SELL_FRACS
    sell_min_frac_pressure: float = 0.28   # relaxed gate when the shed is filling up
    shed_pressure_frac: float = 0.50  # shed fullness that triggers the relaxed gate
    shed_force_frac: float = 0.85     # shed fullness that ignores the price gate entirely
    sell_chunk: int = 8               # units per product per turn (dribble, don't dump)
    dump_turns: int = 72              # turns_remaining <= this -> wheat feed reserve released
    # Terminal glide path: from this many days out, force-sell holdings spread over the
    # remaining turns even below the reserve price. Unsold stock is worth zero, and a pure
    # reservation-price seller measurably dumped its melons into the $1 floor on the last day.
    glide_days: int = 12
    final_dump_turns: int = 3         # last N turns: sell everything regardless of price

    # --- planting -----------------------------------------------------------
    # 12, and do not raise it. Queueing more seeds plants more tiles than the crew can work,
    # and the farm degrades on every axis at once: 18 wins 0/20 head-to-head against this
    # build (worst margin -30,570) and 24 wins 0/20 (-31,303), with escapes going 0.1 -> 1.9
    # -> 3.0 and idle unit-turns 12.4% -> 13.7% -> 18.6%. Idle rising while tile count rises
    # is the tell: the hands are not short of work, they are too far from it. The ~30 tiles
    # left empty at day 15 are not an opportunity, they are the correct fallow at this
    # headcount — land is free, labour is what binds.
    seed_buffer: int = 12             # seeds to keep queued for the chosen crop
    # Lead time on seed purchases, in days. Not a schedule: seeds ordered this turn
    # only exist next turn, so demand must be sized against tiles reaching
    # `harvest_age` within this window or the replant is always a day late.
    seed_lead_days: int = 1
    # MEASURED AND REJECTED — both default OFF. The machinery stays because the failure is
    # informative and the observation behind it is real; the inference was not.
    #
    # Three ladder replays show us a day late on every ramp: on the melon replant day we
    # bought 0 seeds and planted 0 tiles while the opponent bought 12 seeds five hours before
    # his harvest and refilled 10 tiles the same day. His melons cleared at $192-101, ours at
    # $37-7 into the crater he had just made. That is all true, and fixing it loses badly.
    #
    # `seed_anticipate` sizes seed demand from tiles reaching `harvest_age` within
    # `seed_lead_days`, so a tile can be replanted the turn it is harvested. Contested A/B
    # against this build: 1/16, -8,663 a game.
    #
    # `seed_fallthrough` lets seed_orders buy for the next crop when the preferred one is
    # gated (the strawberry drip shuts after `strawberry_seed_hour`). Contested: 0/16,
    # -47,655 a game — it dominates so completely that enabling anticipation on top of it
    # changes nothing. The ladder's refusal to buy is load-bearing: the drip is a deliberate
    # stagger, and spending that cash on melon or carrot seed displaces the strawberry ramp
    # that is actually the backbone.
    #
    # The deeper error in the diagnosis: in a mirror, arriving at the melon glut one day
    # earlier does not win the race, it only moves the collision. The phase lag is real and
    # it is not what is worth fixing.
    seed_anticipate: bool = False
    seed_fallthrough: bool = False
    tiles_per_shed_slot: float = 1.0  # planted tiles allowed per unit of shed capacity
    seed_cash_reserve: float = 120.0
    # 26, and the 13 it replaces is the most expensive mistake this agent has carried.
    # The old value was tuner-confirmed (+5,973 over 16) but tuned ONLY in self-play, where
    # two identical farms dump melon into one market and glut each other. Melon has no town
    # demand, so nothing drains that inventory back down — but the glut is only real if
    # somebody is actually gluttng it. Against an opponent who is not mirroring us the price
    # never sagged at all: 250-286 for the whole game while we sold 70 units.
    # Measured, seeds 700-703 x both seats: vs starter 20 tiles is +11,013 (4.2 sigma, 7/8)
    # and 26 is +14,441 (5.5 sigma, 8/8) over 13. In self-play 26 is +9,997 but only
    # 1.6 sigma at 4/8 — i.e. no worse in a mirror, decisively better outside one.
    # The bet: the field's clones plant 21 melon seeds a game, so they are not the mirror
    # that 13 was defending against. If a melon-heavy field ever shows up, this is the first
    # number to walk back.
    # Plant straight to the cap; do NOT drip it. Melon's first cohort really does crater its
    # own price (275 -> 115 on day 12, no town demand to drain the inventory back down, and
    # the shed_force gate dumps it at any price once 100 slots fill). Spreading the planting
    # to fix that was measured and is much worse: opening at 10 tiles +1/day wins 13/20
    # against the flat cap and banks 155,786 vs starter, opening at 6 +1.5/day wins 0/20 and
    # banks 137,935, against 17/20 and 162,853 for planting flat out. Monotone, so there is
    # no interior optimum hiding in there. The cheap early melon is not being sold badly —
    # it is being converted into hands, land and animals a week before it could be otherwise,
    # and that compounds for the rest of the season.
    melon_tile_cap: int = 26          # tiles of melon before rotating to the next crop
    # Strawberry is the meta premium crop: 24 units/day of town demand once shops unlock and
    # it trades above base late-game. It is ongoing (4 productions, then the tile rots), so
    # waves must be staggered — the seed drip below plants a few per day instead of one death
    # cohort — and planted no later than it can still produce.
    # 44, not 16: measured from the top-2 replays (90153480/90154808) — the converged clone
    # plants 44 strawberry seeds and executes 248-249 units against our 66. Planted by day 15
    # a tile still fires 3-4 of its productions before the season ends.
    strawberry_tile_cap: int = 44
    # 17, not 15: the wave is cash-starved until the first melon harvest lands (~day 11-12),
    # so most of the planting happens after it — cutting at 15 froze the farm at 15 tiles.
    # A tile planted day 17 still fires 2 of its 4 productions (27 and 29), clearing the
    # $100 seed at strawberry's ~$120+ price.
    strawberry_last_day: int = 17
    strawberry_ramp_day: int = 6      # from here strawberry outranks melon replants
    # Hour 8, not 5: at 5 the drip paced ~3.2 tiles/day and the ramp topped out at 38 of
    # 44 tiles before the last-day cutoff; three more buying hours reach the cap by ~day 14.
    strawberry_seed_hour: int = 8     # buy its seeds through the morning: ~a wave per day
    # Seeds bought per morning. Was hardcoded 4 inside `seed_orders`, which is why no
    # throttle experiment ever reached it: `seed_buffer` only governs the non-strawberry
    # branch, and planting priority cannot plant seeds nobody bought. The opponent that beat
    # us 107,059 to 59,905 ramps ~7/day to 41 strawberry tiles by day 12, so raising this
    # looked like the fix. Measured, it is the opposite — monotone collapse:
    #     4 -> 20/20 (bank 120,466)   6 -> 11/20 (113,920)   8 -> 1/20 (108,701)
    # Their farm profits from 60 tiles; ours bleeds from 50. Copying their ramp without
    # whatever services it (they water 938 turns to our 659 on the same labour budget) just
    # plants strawberries that miss waterings and a market share that crashes the price.
    # Fifth confirmation that raw capacity is not our lever. The gap to them is in how a
    # farm SERVICES that many tiles, and that answer is in their replays, not in Params.
    #
    # RE-TESTED under zone 2.0 + conscripted feeds (the servicing rebuild): drip 6 no
    # longer collapses — 20/20 at 127,382 — but still loses ~1.4k to rc2's 128,778. The
    # early-ramp constraint isn't servicing anymore, it's day-6 cash (their wheat engine
    # funds 100-coin seeds we can't afford yet). Their whole ramp shape (drip 6 + stop at
    # day 14) is worse still: 114,930, 18/20. Their organs feed each other; transplants
    # keep dying. Also: strawberry_last_day 17 -> 14 alone loses 12,907 — our late tiles
    # at 2.8 units are NOT garbage, they're profit on land that would otherwise idle
    # (measured idle fell to 8.1% and the freed labour produced nothing).
    strawberry_drip: int = 4
    # 22, not 13, and it moves with melon_tile_cap above — a wider melon field is pointless
    # if replanting stops before it can refill. Melon needs 10 days to harvest, so 22 is the
    # last day a replant still lands before the reward latches.
    last_melon_day: int = 22
    # Wheat at both ends of the season — see `choose_crop`. Both numbers are copied from the
    # agent that beats v4 by ~42k, not guessed: it opens with ~6 wheat tiles for day-4 cash
    # and refills ~31 tiles by day 27.
    # 0: the clone's opening does NOT transplant. Holding 6 wheat tiles to day 5 costs 8
    # melon tiles and drops us from 17/20 to 15/20 with the bank falling 118,570 -> 98,915.
    # Their farm is built around 10 melon tiles; ours is built around 18-26, and melon at
    # 250 base out-earns wheat at 25 by more than the early cash is worth to us.
    #
    # A persistent version (6 tiles all game, wheat_open_last_day=99) was also measured as a
    # "feed garden" — the 107k opponent keeps 5-7 wheat tiles by its pens and feeds from
    # harvests, spending <249 unit-turns on PICKUP to our 582. Through THIS code path it is
    # 14/20 with unfed doubling to 30.9 and floor-priced sales appearing: wheat returned by
    # choose_crop hijacks the one-crop-per-turn seed channel and starves the strawberry
    # drip. The mechanism needs wheat adjacent to pens and feeding from hand-harvests — a
    # dedicated task, not the crop rotation. Don't re-test it through choose_crop.
    wheat_open_tiles: int = 0         # wheat tiles to hold through the opening, for cash flow
    wheat_open_last_day: int = 5      # after this the melon/strawberry ramp takes over
    wheat_refill_day: int = 22        # from here wheat fills whatever the ramps left empty
    # The feed garden was BUILT PROPERLY and measured (2026-08-06): a dedicated task planting
    # 5 wheat tiles within 2 of the pens, seeds bought outside the crop channel, harvest and
    # feed riding the existing machinery — the mechanism proven live in the env first
    # (harvest pays the acting unit's inventory, FEED consumes from it, nightly reset dumps
    # hands to shed). It works mechanically: unfed animal-days halved, 14.8 -> 7.6. It loses
    # anyway, 1/20 head-to-head: five prime tiles by the pens plus the planting ops cost more
    # than the extra feeds earn. The 107k opponent profits from it because its whole layout
    # is built around it; grafted onto this farm it is a tax. Both function bodies are in
    # git history (feat commit before this note) if the layout itself is ever rebuilt.
    #
    # Same experiment's control taught something bigger: a variant differing by ONE inert
    # market order (2 wheat seeds bought, never planted) flipped 20/20 to 18/20. Close games
    # at this architecture's ceiling are chaos-sensitive — any perturbation reshuffles which
    # of them fall our way. Past ~18/20, seed-level wins are luck, not signal; judge changes
    # on bank and the margin distribution, not on the last two wins.
    # v8 mechanism 1: front-run the opponent's melon dump. Their pipeline is visible ten
    # days out (opp_melon_soon in the adapter); when >= this many of their melon tiles are
    # near maturity, our melon harvests at first-yield age instead of waiting for max yield
    # (_plant_tile_tasks) and the sell reserve relaxes toward the post-crash price
    # (sell_orders). Measured on seed 700: their 13-tile wave takes melon 277 -> 81 -> 37 in
    # three days and our default harvest matured one day AFTER the crash — four units at 274
    # beat six at 37 by 7x. A/B on seeds 700-709 x both seats: 20/20 held on both benches,
    # worst margin +442 -> +2,962 (6.7x), cost -1.2% mean bank vs prev, byte-identical vs
    # starter (no melon to react to). Trigger 6 vs 10 near-identical; 6 keeps slightly more.
    # NOTE the sell-gate relax alone was a proven no-op (shed is empty before their dump
    # lands — we were structurally the second seller); the harvest side is what acts.
    frontrun_melon_tiles: int = 6     # opp melon tiles near maturity that trigger the exit
    frontrun_sell_frac: float = 0.45  # relaxed melon reserve while their wave is incoming
    # v8 mechanism 2, ACCEPTED at 2.0: zone ownership in `assign` — every unit owns a
    # quadrant (round-robin) and bids zone_bonus stronger on crop work inside it. The
    # single biggest contested gain of the project. Full measured curve, seeds 700-709
    # x both seats vs the previous config:
    #     1.3 -> 19/20 (noise-zoning loses)      1.6 -> 124,082, worst +7,685
    #     2.0 -> 129,433, floor 119,552, worst +22,796   <- peak
    #     2.5 -> 122,939 (escapes 5.0)            3.0 -> 112,498, 9/20 (herd collapse, 8.8)
    # The trade at 2.0: unfed 16.6 -> 47.2 and escapes 0.1 -> 2.4 — zoned units let the
    # afternoon feeds slip — yet contested bank is +10,863 over unzoned because owned
    # ground converts to crops sold. vs starter it costs 16k (162k -> 146k): zoning is a
    # CONTESTED-play weapon, and the ladder only plays contested games.
    # Measured dead ends: priority-gating the bonus below feed prio (unfed unchanged at
    # 33.5 — the leak is geometry, not bid strength — and 16/20); exempting the farmer to
    # serve the pens (119,110 — an un-zoned unit is a wanderer, not a servant).
    # The escape bleed is mechanism 4's target: pre-assign critical feeds off-market.
    zone_bonus: float = 2.0
    # Temporal stickiness (a bid bonus on last turn's target) was built and measured on
    # top of zones and LOSES, monotonically: 127,278 at 1.3x and 121,491 at 1.8x against
    # 128,778 without. Zones already provide all the persistence this farm can use; a
    # time-lock on top glues units to tiles whose work is finished. Persistence in space
    # pays, persistence in time double-counts it — don't rebuild.
    # Curve-aware sell sizing (from the public "Economics-Driven Farm Manager" notebook;
    # curve model verified 200/200 vs engine source) — measured and REJECTED: -2,693
    # contested (135,037 vs 137,730) and the executed floors caught the mechanism: wool
    # production fell 129 -> 115 because larger early sells shift cash timing and depress
    # the shared market. Per-order price optimization loses to its own second-order market
    # feedback. Keep OFF; the exact market_price model in env_adapter stays — it's useful
    # for anything that needs to price a hypothetical sale.
    marginal_sell: bool = False
    # v8 mechanism 8, ACCEPTED: strawberry's future productions are valued at no less than
    # this fraction of base when planning, because 24/day of town demand recovers a flooded
    # price. Reading spot instead made the farm abandon its backbone whenever an opponent
    # flooded (ladder ep 90422705: strawberry 138 executed vs ~210 normal, a panic 22-tile
    # melon wave, bank 91k vs their 162k). Byte-identical on the bench (prev/starter never
    # crash the price) — accepted as bench-neutral + closes a documented ladder collapse.
    strawberry_plan_floor: float = 0.75
    # v10, MEASURED AND REJECTED — kept behind flags because the machinery is sound and the
    # failure is informative, but both default OFF.
    #
    # `forward_pricing` values a crop at the price projected for the day it matures
    # (`Observation.forward_price`: known town drain + both farms' visible pipeline). It is
    # strictly better information than spot. On its own it changed nothing (0/16, delta 0)
    # because `choose_crop`'s ladder only consults `crop_value` as a `> 0` gate.
    #
    # `dynamic_crop_choice` then ranked crops by that value instead of following the ladder.
    # It played a genuinely adaptive game — rotated off melon as the glut curve bit, pivoted
    # to wheat on day 20, and found carrot as endgame filler (28 tiles, a crop no version of
    # this engine had ever planted) — and lost 0/16 at -22,077 a game (97,982 vs 120,059).
    #
    # Why: value-per-tile-day is the wrong denominator. Unit *actions* are the binding
    # constraint (SPEC "Consequences"), and the ranking is blind to them — carrot re-costs a
    # PLANT every 3 days for $35 units, and the diversification forced by `max_crop_share`
    # spread the crew thin. The ladder is not naive hardcoding; it encodes action cost, the
    # strawberry ramp's compounding and opening cash flow, none of which this model sees.
    # A future attempt should price coins per action, not per tile-day.
    forward_pricing: bool = False
    dynamic_crop_choice: bool = False
    max_crop_share: float = 0.6       # ceiling on one crop's share of planted tiles
    # ACCEPTED (a tombstone correctly reversed): feed already in hands counts against what
    # needs fetching. Pre-rounds this was harmful (unfed 14.7 -> 31.8 — far-carried wheat
    # starved pens). Feeding rounds deliver the carrier to the animal, so the redundant
    # shed trips became pure waste: counting carried wheat is +3,936 contested (133,794 ->
    # 137,730), 20/20, escapes 0. The rhythm audit showed one of our units spending NINE
    # straight hours on pickups; the 2,910-rated opponent does one pickup then feeds five.
    pickup_counts_carried: bool = True
    # Do NOT taper the crew after buildout, however elite the pattern looks: the 2,910
    # opponent runs 6 hands on day 14 to our 12, but copying that (0.08/tile from day 13)
    # loses 38,802 — our slack turns are surge capacity for harvest/water peaks, and wages
    # are trivial next to a missed production day. Sixth organ-transplant death.
    # v8 mechanism 6, ACCEPTED: feeding rounds — from this hour every unfed animal is a
    # conscription order, not a bid (see the critical-feed block in `assign`). Zoning had
    # dropped the herd to 88% fed (unfed 47/episode) because feeds lose auctions on
    # geometry; rounds bring it to ~96% while keeping the whole crop engine. Curve, seeds
    # 700-709 x both seats: h18 -> 131,044, h15 -> 133,156, h12 -> 134,149, h9 -> 133,794.
    # Hour 9 picked on robustness (floor 121,031, worst +26,527, unfed 15.2, vs-starter
    # min 146,814) — the h12 bank edge is noise, the margin edge is not.
    evening_feed_hour: int = 9
    # v8 mechanism 4, ACCEPTED: critical feeds (animal one missed day from escaping)
    # bypass the auction — the nearest wheat-carrying unit is conscripted before bidding
    # opens. Under zoning these feeds lost on geometry and 2.4 animals/episode walked.
    # Measured on the zoned build: escapes 2.4 -> 0.0 across all 40 episodes, contested
    # bank flat (-655, noise), vs starter +2,816. Removes a compounding failure mode for
    # nothing.
    critical_feed_offmarket: bool = True
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
    # 85, not 40: engine-verified (kaggriculture.py:799-800) — every fed+cared day banks +1
    # product paid out on the next fed production day, so one CARE op is worth a whole unit
    # of milk ($160 base) or wool ($200 base), the highest coins/op on the farm. At 40 it
    # lost to crop work and coverage audits showed 6-12 of 14 animals cared per day; the
    # top-2 clones run 100% and collect the mathematical maximum (168 wool from 6 sheep).
    prio_animal_care: float = 85.0
    # FERTILIZE on a producing strawberry: +1 unit on each watered production day for 3 days
    # (engine :769-770), ~$120-180 per application against selling the fertilizer at ~$100.
    prio_fertilize: float = 58.0
    # 38, deliberately below harvest (55), watering (60) and fertilizer collection (50), so
    # planting only happens with turns nothing else wants. It looks wrong — the farm sits on
    # 45 empty tiles around day 13-17 and buys seeds it never plants — but raising it to 50
    # drops us from 17/20 to 8/20 head-to-head (bank 118,570 -> 113,157). Bare earth is not
    # foregone profit here; it is the correct outcome of a labour-bound farm, and a planted
    # tile that steals turns from harvesting and watering is worth less than the bare one.
    # Third independent confirmation of the same ceiling: seed_buffer 18/24 -> 0/20, and
    # hands_per_tile 0.20/0.24 -> 15/20 and 0/20. Do not try to fill the field.
    prio_plant: float = 38.0
    prio_dig: float = 22.0
    prio_haul: float = 12.0

    # 0.9, and this was the binding constraint on the whole farm for far longer than anyone
    # noticed. `assign` scores a task at priority/(1 + move_cost*dist); at 0.4 a job six
    # tiles away still outbids the one a unit is standing on, so 48% of all unit-turns went
    # into walking. Measured against the agent that beats v4: identical unit-turns (6,758 vs
    # 6,759) and it walks slightly MORE than us (50.2%), but spends 656 fewer turns on
    # PICKUP and idles 462 turns to our 744 — the gap was never capacity, it was routing.
    #
    # Head-to-head over seeds 700-709 x both seats, unimodal with the peak at 0.9:
    #     0.25 -> 16/20   0.4 -> 17/20   0.6 -> 17/20   0.9 -> 20/20   1.2 -> 19/20
    #     1.6 -> 18/20
    # At 0.9 the worst margin across all 20 episodes is +614: it does not lose one.
    #
    # This also explains why every capacity change failed: more hands, more seeds, more
    # planting urgency all made a transit problem worse. Fix routing before adding work.
    move_cost: float = 0.9            # walk-distance weight in the value/turn ratio
    # 16, not 40: SELL only sees the shed — produce riding around in a unit's inventory is
    # invisible to the market, and the end-of-day auto-drop lands too late to fund that
    # day's buying. Frequent small hauls keep stock sellable.
    haul_threshold: int = 16           # carry this much before making a shed trip

    # --- livestock ----------------------------------------------------------
    # Animals sell into price curves that crop saturation never touches, which is the
    # whole reason to bother: melon volume is capped by melon's own glut curve, so wool
    # and milk are additive revenue rather than a substitute.
    # The converged public top-10 herd: 8 cows + 6 sheep, zero geese. A goose earns ~32
    # coins/action against a cow's ~95 and a sheep's ~86, and CARE banking (fed+cared days
    # bank a counter paid out on the next fed production day) multiplies a sheep's wool
    # x4 — the best animal in the game when tended daily. Every animal is also a daily
    # FERTILIZER unit (~$100 base, sellable — see SELLABLE).
    target_sheep: int = 6             # WOOL, base $200; cared it produces 4 wool per cycle
    target_cows: int = 8              # MILK, base $160, heavy shop demand
    target_geese: int = 0             # ~32 coins/action; strictly worse than more cows/sheep
    # Timing, not headcount, is what the wool/milk pools respond to. Dropping the buy
    # threshold from $5,000 to $2,500 is worth +2,582 on its own: the labour gate freed the
    # $2,000 SW quadrant, so the cash is there sooner, and an animal placed a few days earlier
    # gets whole extra production cycles. Raising headcount instead is negative every time —
    # 6 sheep, 8/4 and 12/6 all score worse. Measured out of sample, both seats.
    # 900, not 2500: the top-2 clones hold 4 animals by day 3 and 14 by day 12, spending the
    # opening bank down to $10 — each cow placed 2 days earlier is ~3 extra milk (interval 2,
    # +care bank). At 2500 our first cow landed day 0 but the second waited for profit ~day 10.
    animal_cash_reserve: float = 900.0
    feed_cash_floor: float = 150.0     # feeding outranks almost everything; buy wheat above this
    # 3: with the cow-led round-robin this buys 2 cows + 1 sheep per turn when cash
    # allows, front-loading the herd the way the clones do (4 animals by day 3).
    animals_per_turn: int = 3          # stagger purchases instead of dumping the bank
    last_animal_day: int = 21         # placed later than this, it never reaches first yield
    # Fertilize strawberries only while a boosted production can still land before the end:
    # fertilized_until_day = day+2, productions every 2 days, final collectable yield day 29.
    fert_use_last_day: int = 27
    # 7, not 6: at 6 a goose squeaks past the season gate in a 240-step episode (4+6 = exactly
    # the 10 days remaining) and can never repay its coop, feed and care actions there.
    animal_lead_days: int = 7         # production days needed after first yield to repay the animal
    # 2.0. Raising it works exactly as intended and is still wrong: at 3.0 unfed animal-days
    # fall 16.6 -> 12.6 and escapes to 0.0, and the build still drops from 17/20 to 15/20
    # head-to-head (bank vs starter 159,346 -> 142,324); 4.0 gives 14/20 and 92,532. Holding
    # 42 wheat off the market instead of 28 costs more than the milk it buys.
    # The instructive part: this was tested because losses correlated with milk falling
    # behind (700 +2 WIN, 704 -1 WIN, 702 -11 LOSS, 709 -12 LOSS). Feeding the herd better
    # fixed the milk and seed 709 lost anyway — so the milk gap is a correlate of losing,
    # not its cause. Don't re-derive that hypothesis from the same correlation.
    feed_reserve_days: float = 2.0    # days of wheat to hold back from selling per animal
    # 5x3, not 10x2: one carrier holding the whole day's feed cannot walk 14 pastures in
    # the turns it has left (measured 7-11 of 14 fed); three smaller carriers can.
    wheat_pickup_batch: int = 5       # wheat carried per shed trip
    max_pickup_tasks: int = 3         # don't send the whole crew to the shed at once
    # 90: must outrank care (85) — the bank only pays on a FED production day, and a cared
    # but unfed animal both wastes the care op and walks toward escaping. Measured: at 72
    # (below care) coverage inverted to 100% cared / 43% fed and two animals escaped.
    prio_feed_relaxed: float = 90.0      # not fed yet, but not yet at risk of escaping
    # 45, not 33: uncollected yield saturates max_held (6) in ~4 days on a cared cow and
    # every production past the cap is destroyed; the clones collect promptly and hit the
    # theoretical production maximum.
    prio_animal_harvest_partial: float = 45.0  # product waiting, but below max_held
    build_ahead_frac: float = 0.75      # build pens at this fraction of the animal reserve
    prio_pickup: float = 108.0
    prio_place_animal_pickup: float = 102.0
    prio_build: float = 46.0
    prio_place_animal: float = 100.0  # a bought animal earns nothing sitting in the shed
    prio_collect_fert: float = 50.0   # one op nets a ~$100-base unit; just below a full harvest
    # Fertilizer has no town drain, so its price never refills the way crops do — the standard
    # 0.85 gate would permanently block sales once the price sags. Any sale above the walk
    # cost is profit on a free byproduct, hence its own, much lower gate.
    fert_sell_min_frac: float = 0.25


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
    """Coins per tile-day, priced at the market projected for the day it matures.

    Valuing a crop at *today's* price is what produced both of this engine's monocultures:
    a melon planted now does not exist for ten days, and by then the town has drained the
    market and both farms have refilled it. Every term is knowable in advance:

      * the town's drain is deterministic once the unlocked shops are known
        (`obs.drain_over`), and which shops unlock is random per game — so this is the term
        that makes two different games correctly want two different crops
      * the supply already growing on both farms is public (`obs.pipeline`)
      * our own harvest lands the same day, so it is priced in as `extra_supply`

    Wheat matters more than its $25 base suggests: its glut side is `log` (a heavy dump
    still clears ~$19) while scarcity is `sqrt` at 0.80 — the one crop that cannot be
    crashed. The premium crops price themselves out through `linear`/`sq` curves as soon as
    supply arrives, which this forecast sees before the seed goes into the ground.
    """
    c = CROPS[crop]
    if c["ongoing"]:
        if crop != "STRAWBERRY":
            return NEG_INF                  # tomato: 12/day drain, 12-day cycle, never pays
        if obs.day + c["first_yield_day"] > obs.total_days - 2:
            return NEG_INF
        # Price the middle of the production run, not the first tick, and include the
        # spot floor: 24/day of town demand drains a strawberry glut back up, so a crashed
        # price is temporary. Reading spot alone made the farm abandon its backbone when an
        # opponent flooded (ladder ep 90422705: strawberry executed 138 vs our normal ~210,
        # a 22-tile panic melon wave instead, bank 91k).
        cycle = c["first_yield_day"] + c["interval"] * c["max_yield"]
        if p.forward_pricing:
            mid = c["first_yield_day"] + c["interval"] * (c["max_yield"] - 1) // 2
            price = obs.forward_price(crop, mid * obs.turns_per_day,
                                      extra_supply=c["max_yield"])
        else:
            price = obs.prices.get(crop, BASE_PRICE[crop])
        price = max(price, p.strawberry_plan_floor * BASE_PRICE[crop])
        return (c["max_yield"] * price - c["seed"]) / cycle
    age = harvest_age(crop)
    if obs.day + age > obs.total_days - 1:
        return NEG_INF                      # cannot mature before the season ends
    units = expected_yield(crop)
    if p.forward_pricing:
        price = obs.forward_price(crop, age * obs.turns_per_day, extra_supply=units)
    else:
        price = obs.prices.get(crop, BASE_PRICE[crop])
    gross = units * price * _bias(p, crop)
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
    if p.dynamic_crop_choice:
        return choose_crop_dynamic(obs, p)
    counts = crop_tile_counts(obs)
    # Portfolio, not a single value ranking: fill the melon engine first (highest $/tile-day,
    # capped by its own glut curve), then the staggered strawberry waves (premium price,
    # separate demand pool), then whatever filler values best. Spreading revenue across
    # products is what a shared market pays for — each product's price only has to carry a
    # fraction of the farm.
    # Wheat bookends the season, and both ends were measured off the agent that beats us
    # (episodes 90212517 / 90212519 / 90231839 — three names, byte-identical play).
    #
    # Opening: it holds ~6 wheat tiles from day 0. Wheat matures in 4 days against melon's
    # 10, so it has 2,431 coins on day 6 where we have 266 — and it spends them on livestock,
    # holding 6 animals by day 6 and 12 by day 9 against our 3 and 7. Our herd is late
    # because we are broke, not because the buy rule is shy; spending the *opening bank* on
    # animals instead was measured and is far worse (0/8), so the fix is to earn it first.
    #
    # Endgame: it refills ~31 tiles with wheat by day 27 while we sit on ~30 empty ones.
    # Wheat matures in 4 days, so anything planted by day 25 still banks before the latch.
    if crop_value(obs, p, "WHEAT") > 0:
        wheat_tiles = counts.get("WHEAT", 0)
        if obs.day <= p.wheat_open_last_day and wheat_tiles < p.wheat_open_tiles:
            return "WHEAT"
        if obs.day >= p.wheat_refill_day:
            return "WHEAT"

    melon_ok = (obs.day <= p.last_melon_day
                and counts.get("MELON", 0) < p.melon_tile_cap
                and crop_value(obs, p, "MELON") > 0)
    straw_ok = (obs.day <= p.strawberry_last_day
                and counts.get("STRAWBERRY", 0) < p.strawberry_tile_cap
                and crop_value(obs, p, "STRAWBERRY") > 0)
    # Melon leads the opening for cash flow, but from day 5 the strawberry ramp takes
    # precedence: melon replants kept it below its cap all the way to day 12 and starved
    # the strawberry drip at ~13 tiles against the clone's 27-by-day-12. Melon still
    # fills in whenever the day's strawberry wave is bought and planted.
    if straw_ok and obs.day >= p.strawberry_ramp_day:
        return "STRAWBERRY"
    if melon_ok:
        return "MELON"
    if straw_ok:
        return "STRAWBERRY"
    best, best_value = None, 0.0
    for crop in ("WHEAT", "CARROT"):
        value = crop_value(obs, p, crop)
        if value > best_value:
            best, best_value = crop, value
    return best


def choose_crop_dynamic(obs: Observation, p: Params) -> str | None:
    """Plant whatever the market will pay most for on the day it matures.

    The ladder above encodes one fixed portfolio — melon cap, strawberry ramp day, wheat
    bookends — tuned on the average game. But which shops unlock is random per episode, so
    the demand this game actually dealt is different every time: measured across four seeds
    the hungriest product by day 12 was wheat, then strawberry+milk, then wool, then carrot.
    A fixed plan is right on average and wrong in most individual games, and it is what
    every frozen route agent on the ladder is playing.

    Ranking on `crop_value` instead makes the caps emergent rather than magic. Melon needs
    no tile cap here: as melon supply builds, its projected price collapses through the `sq`
    glut curve, its value falls below wheat, and the farm rotates off it on its own. The
    only hard guards left are the ones the forecast cannot see: a per-crop tile ceiling to
    keep one product from owning the whole farm (its price is not the only thing that
    saturates — so does the shed), and the season-end viability check inside `crop_value`.
    """
    counts = crop_tile_counts(obs)
    planted = sum(counts.values()) or 1
    best, best_value = None, 0.0
    for crop in ("WHEAT", "STRAWBERRY", "MELON", "CARROT"):
        if crop == "STRAWBERRY" and obs.day > p.strawberry_last_day:
            continue
        if counts.get(crop, 0) >= planted * p.max_crop_share and planted >= 8:
            continue                        # keep one product from owning the farm
        value = crop_value(obs, p, crop)
        if value > best_value:
            best, best_value = crop, value
    return best


def active_tile_cap(obs: Observation, p: Params) -> int:
    """Most tiles worth having in the ground, given how much the shed can absorb.

    Produce that overflows the shed at the end-of-day dump is destroyed, so planting past
    what can be stored and sold burns seeds and unit-turns for nothing. At the default
    `shedCapacity` of 100 this never binds (a 10x10 farm has at most 100 tiles); it exists
    so a smaller shed scales the whole operation down instead of running at a loss.
    """
    return max(1, int(obs.shed_capacity * p.tiles_per_shed_slot))


def plant_budget(obs: Observation, p: Params, crop: str | None) -> int:
    """How many PLANT ops may be issued this turn.

    Hard-capped by seeds held: the simulator drops *every* PLANT of a crop when the
    turn's requests for it exceed the seed count, so overcommitting wastes the whole
    turn for every unit involved.
    """
    if crop is None:
        return 0
    planted = sum(1 for t in obs.tiles if t.state == "PLANT")
    return min(
        obs.seeds.get(crop, 0),
        sum(1 for t in obs.tiles if t.state == "EMPTY"),
        max(0, active_tile_cap(obs, p) - planted),
    )


# --- livestock --------------------------------------------------------------

def animal_targets(obs: Observation, p: Params) -> dict[str, int]:
    """Headcount targets, scaled down for small boards and short seasons.

    The defaults are sized for the standard 10x10, 30-day game. A 6x6 board has a third
    of the tiles and a 240-step season a third of the production days — holding the full
    herd there burns capital and unit actions that crops repay better.
    """
    scale = min(1.0,
                (obs.board_size ** 2) / 100.0,
                obs.total_days / 30.0)
    # Cows first: the clone opening holds 3 cows + 1 sheep by day 3. Dict order is buy
    # order in animal_orders, and a cow (interval 2) turns care-days into product faster
    # than a sheep (interval 3) when cash rations the first purchases.
    return {"COW": int(p.target_cows * scale),
            "SHEEP": int(p.target_sheep * scale),
            "GOOSE": int(p.target_geese * scale)}


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
    """Shortfall per species: target minus (placed + in shed + carried).

    Carried counts: an animal a unit is walking to its pen is invisible to both the shed
    and the placed census, and skipping it re-bought the same animal every turn of the
    walk — measured 10 cows and 12 sheep bought against targets of 8 and 6, with the
    surplus cows squatting the pastures so 8 sheep died unplaced in the shed.
    """
    census = livestock_census(obs)
    out = {}
    for name, target in animal_targets(obs, p).items():
        carried = sum(u.inventory.get(name, 0) for u in obs.units)
        have = census["placed"].get(name, 0) + census["in_shed"].get(name, 0) + carried
        out[name] = max(0, target - have)
    return out


def wheat_feed_reserve(obs: Observation, p: Params) -> int:
    """Wheat to hold back from the market so livestock never starves.

    A missed second consecutive feed loses the animal outright — 400-500 coins plus the
    rest of the season's production — so this reserve is cheap insurance.

    Zero from `dump_turns` out: the reserve only protects production that still exists.
    Both callers need that cutoff, and only `sell_orders` had it — so for the last
    three days the seller dumped the reserve and `animal_orders` bought it straight back,
    every turn. Seed 393788841: 20 such same-turn round trips on day 29 alone, 137 wheat
    bought on a day the herd is deliberately never fed (nothing produces on day 29).

    The cash was not the loss — the engine quotes a buy at post-buy inventory precisely so
    a round trip nets zero (kaggriculture.py:576-578). **Labour** was the loss: the wheat
    had to be hauled, and PICKUP+DROP ate 164 of 794 unit-turns over days 27-29, versus 87
    once the loop is gone. Those turns went back to HARVEST and COLLECT. Paired self-play,
    9 seeds x both seats: +2,276 +- 334 (6.8 sigma, +2.1%), 17/18.

    Releasing it here does starve days 27-28: 121 of the 182 non-deliberate unfed
    animal-days land there, 35 of them on day 28, which is a cow production day (base only,
    care bank wiped). That is the price and it has been measured twice. A graded taper that
    holds one day of feed per remaining fed day loses anyway: -728 +- 281 (5/18) first time,
    and -393 +- 255 (7/18) re-run after the day-29 pickup loop was fixed, in case that had
    confounded it. It had not. ~28 wheat sold on day 27 is simply worth more than the milk
    it would have bought on day 28. Don't re-add it a third time.
    """
    if obs.turns_remaining <= p.dump_turns:
        # Not zero — escape insurance. An animal that misses two days running is replaced by
        # its bare structure and takes every uncollected unit with it (engine :795-798).
        # Across 20 mirror seeds the score margin correlates +0.77 with the escape
        # differential and the median margin is only 1,128, so escapes decide these games
        # outright: the two blowouts (seeds 42 and 803, ~10k each) were both seats that lost
        # four animals. Reserve one wheat per animal that is *already* one day down rather
        # than the full 2-day herd reserve — roughly 7 wheat instead of 28, which is the part
        # the dump can afford to leave behind.
        # ...but only while a feed can still happen. On the last day nothing is fed, so this
        # would reserve wheat that no animal will ever eat and the dump can no longer sell:
        # measured, stranded$ went 0 -> 117/episode, all of it wheat, in 17 of 40 episodes.
        if not feeding_matters(obs):
            return 0
        return sum(1 for t in obs.tiles
                   if t.state == "ANIMAL" and t.consecutive_unfed >= 1)
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
        # Count carried wheat too: feed-run pickups move the reserve out of the shed and
        # into hands, and a shed-only check re-bought the reserve every turn until cash
        # pinned at the floor (measured: 1,400 wheat bought, episode ended at 10k).
        holding = obs.shed.get("WHEAT", 0) + sum(u.inventory.get("WHEAT", 0)
                                                 for u in obs.units)
        short = reserve - holding
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
    # Round-robin one animal per species per pass, cows leading: buying the whole cow
    # target first pushed every sheep past day 8, and a sheep placed early banks care for
    # each pre-yield day (engine :799-800 — the bank accrues from placement, paying out
    # up to max_held on the first fed production). The clones hold a mixed herd by day 3.
    wanted = {name: want for name, want in _wanted_animals(obs, p).items() if want > 0}
    while wanted and bought < p.animals_per_turn:
        progressed = False
        for name in list(wanted):
            if bought >= p.animals_per_turn:
                break
            # Season-relative payback, per species. `last_animal_day` is absolute and so
            # says nothing in a short season. A $500 sheep that never reaches its first
            # yield is a pure write-off.
            if obs.days_remaining < ANIMALS[name]["first_yield_day"] + p.animal_lead_days:
                del wanted[name]
                continue
            cost = ANIMALS[name]["cost"]
            if cash < cost:
                del wanted[name]
                continue
            orders.append(["BUY_ANIMAL", name, 1])
            cash -= cost
            bought += 1
            progressed = True
            wanted[name] -= 1
            if wanted[name] <= 0:
                del wanted[name]
        if not progressed:
            break
    return orders


def _structure_tasks(obs: Observation, p: Params, empty: list[Tile]) -> list[Task]:
    """Build the pens the animals we intend to own will need."""
    if obs.day > p.last_animal_day or not empty:
        return []
    # Don't fence off tiles for animals we cannot afford yet — an empty pen is a tile that
    # grows nothing, and it blocks the melon rotation that pays for the animal.
    waiting = any(obs.shed.get(n, 0) for n in ANIMALS)
    if not waiting and obs.cash < p.animal_cash_reserve * p.build_ahead_frac:
        return []
    census = livestock_census(obs)
    need = {"PASTURE": 0, "COOP": 0}
    for name, target in animal_targets(obs, p).items():
        # Same season-viability gate as the purchase logic: a pen for an animal that can
        # no longer repay itself is a wasted build op and a tile that grows nothing.
        if obs.days_remaining < ANIMALS[name]["first_yield_day"] + p.animal_lead_days:
            continue
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


def feeding_matters(obs: Observation) -> bool:
    """Whether a feed still buys anything. False on the last day — the production it pays
    into fires at end-of-day, after the reward has latched.

    Named, rather than inlined twice, because every subsystem that touches feed has to agree
    on when it stops: `_animal_tasks` emits the FEED, `_pickup_tasks` fetches the wheat for
    it. Only the first knew to stop, so the second spent all of day 29 sending units to the
    shed for feed nobody would use — at prio_pickup 108, the highest priority in the system,
    which then lost the produce those units should have been hauling.
    """
    return obs.days_remaining > 1


def _pickup_tasks(obs: Observation, p: Params) -> list[Task]:
    """Shed trips to collect what units need in hand: wheat for feeding, animals to place."""
    tasks: list[Task] = []

    carried = {n: sum(u.inventory.get(n, 0) for u in obs.units) for n in ANIMALS}
    for name in ANIMALS:
        in_shed = obs.shed.get(name, 0)
        if in_shed <= 0 or carried.get(name, 0) >= in_shed:
            continue
        for (x, y) in obs.shed_access:
            tasks.append(Task(x, y, ["PICKUP", name, 1], p.prio_place_animal_pickup,
                              "pickup", group=f"get:{name}"))

    unfed = (sum(1 for t in obs.tiles if t.state == "ANIMAL" and not t.fed_today)
             if feeding_matters(obs) else 0)
    if unfed:
        # Deliberately ignore wheat already in units' hands: a hand carrying feed on the
        # far side of the farm suppressed new pickups, and every animal its wheat never
        # reached had its whole care bank zeroed at the day's production (engine :798).
        # A redundant shed trip costs one op; a wiped bank costs a $160-200 product.
        available = obs.shed.get("WHEAT", 0)
        if available > 0:
            # The redundancy above (ignoring carried wheat) was load-bearing pre-rounds:
            # counting carried wheat took unfed 14.7 -> 31.8 because feed in a far hand
            # starved the pens. Feeding rounds changed that — the carrier is conscripted
            # to the animal — so the insurance is re-testable via pickup_counts_carried.
            # Rhythm audit (episode 90347385, day 14): one of our units spent NINE straight
            # hours on pickups; the 2,910-rated opponent does one pickup then feeds five
            # animals from carried stock.
            if p.pickup_counts_carried:
                unfed = max(0, unfed - sum(u.inventory.get("WHEAT", 0) for u in obs.units))
                if not unfed:
                    return tasks
            batches = min(p.max_pickup_tasks, -(-unfed // max(1, p.wheat_pickup_batch)))
            n = min(p.wheat_pickup_batch, available)
            for b in range(batches):
                for (x, y) in obs.shed_access:
                    tasks.append(Task(x, y, ["PICKUP", "WHEAT", n], p.prio_pickup,
                                      "pickup", group=f"feedrun:{b}"))

    # Stage fertilizer the same way wheat is staged for feeding: the FERTILIZE task
    # requires a unit already carrying one.
    need_fert = sum(1 for t in obs.tiles
                    if t.state == "PLANT" and t.crop == "STRAWBERRY"
                    and t.fertilized_until_day < obs.day)
    if need_fert and obs.day <= p.fert_use_last_day:
        have = sum(u.inventory.get("FERTILIZER", 0) for u in obs.units)
        available = obs.shed.get("FERTILIZER", 0)
        if have < need_fert and available > 0:
            n = min(p.wheat_pickup_batch, available, need_fert - have)
            for (x, y) in obs.shed_access:
                tasks.append(Task(x, y, ["PICKUP", "FERTILIZER", n], p.prio_pickup,
                                  "pickup", group="fertrun"))
    return tasks


# --- market -----------------------------------------------------------------

def affordable_hands(obs: Observation, p: Params, workable: int) -> int:
    """Hands we could put in the field today for a farm of `workable` tiles.

    Split out from `target_hands` so the land decision can ask "could we even staff the
    quadrant we are about to buy?" — the answer depends on `farmHandCostMult`, which is why
    an absolute tile threshold cannot express it.
    """
    want = min(p.max_hands, int(round(workable * p.hands_per_tile)))
    budget = obs.cash - p.hire_cash_reserve
    cap = _hire_cap(obs, p, workable)
    spent, allowed = 0.0, 0
    while allowed < want:
        cost = hire_cost(allowed, obs.hire_mult)
        if cost > cap or spent + cost > budget:
            break
        spent += cost
        allowed += 1
    return allowed


def _hire_cap(obs: Observation, p: Params, workable: int) -> float:
    """Marginal hire-cost ceiling, scaled by season length and farm size.

    A hand's daily value is proportional to how much profitable work exists: a full-length
    season on a grown farm justifies the 12th hire at $144, but a 10-day episode on a
    25-tile farm does not justify a $40 one. Scaling by both terms reproduces the measured
    optima at the extremes — 12-13 hands on the standard config, exactly 2 hands on the
    240-step farmHandCostMult=20 config (4,857 vs 2,946 mean over seeds 5-8).
    """
    return (p.max_hire_cost
            * min(1.0, obs.total_days / 30.0)
            * min(1.0, workable / 50.0))


def target_hands(obs: Observation, p: Params) -> int:
    """How many hands today, from workload and affordability."""
    workable = sum(1 for t in obs.tiles if t.state != "LOCKED")
    want = min(p.max_hands, int(round(workable * p.hands_per_tile)))
    # Walk the fib ladder and stop on the first hire that is either unaffordable or not
    # worth it under the scaled marginal-cost cap.
    budget = obs.cash - p.hire_cash_reserve
    cap = _hire_cap(obs, p, workable)
    spent = 0.0
    allowed = obs.hires_today
    while allowed < want:
        cost = hire_cost(allowed, obs.hire_mult)
        if cost > cap or spent + cost > budget:
            break
        spent += cost
        allowed += 1
    return allowed


def sell_orders(obs: Observation, p: Params) -> list[list]:
    """Per-product reservation prices plus a terminal glide path.

    Each product sells in small chunks while its price sits above its own reserve fraction
    of base (SELL_FRACS — shop-drained goods hold near base, melon and fertilizer do not).
    From `glide_days` out, holdings are additionally force-sold spread over the remaining
    turns: unsold stock scores zero, and a pure reservation seller rides melon into the $1
    floor on the final day. Sales at the $1 floor are skipped outright until the final
    unconditional dump — the floor pays a token dollar and is pure loss.
    """
    final_dump = obs.turns_remaining <= p.final_dump_turns
    gliding = obs.days_remaining <= p.glide_days
    under_pressure = obs.shed_used >= obs.shed_capacity * p.shed_pressure_frac
    force = obs.shed_used >= obs.shed_capacity * p.shed_force_frac

    # Livestock eats before the market does; the reserve releases for the last few days.
    reserve = wheat_feed_reserve(obs, p)
    # Fertilizer the strawberries will consume is worth more applied (+1 unit per watered
    # production day, ~$120-180) than sold (~$100); hold back what the active tiles need.
    fert_reserve = 0
    if obs.day <= p.fert_use_last_day and obs.turns_remaining > p.dump_turns:
        fert_reserve = sum(1 for t in obs.tiles
                           if t.state == "PLANT" and t.crop == "STRAWBERRY"
                           and t.fertilized_until_day < obs.day)

    orders = []
    # Sell the most valuable stock first — order position matters under the 10/turn cap.
    for item in sorted(SELLABLE, key=lambda i: -obs.prices.get(i, BASE_PRICE[i])):
        have = obs.shed.get(item, 0)
        if item == "WHEAT":
            have -= reserve
        elif item == "FERTILIZER":
            have -= fert_reserve
        if have <= 0:
            continue

        res = SELL_FRACS.get(item, p.sell_min_frac)
        if item == "FERTILIZER":
            res = min(res, p.fert_sell_min_frac)
        if item == "MELON" and obs.opp_melon_soon >= p.frontrun_melon_tiles:
            # v8's first opponent-aware rule: their melon pipeline is visible ten days out,
            # the glut is quadratic, and nothing refills the price — so when their harvest
            # wave is about to land, whoever sells first gets today's price and whoever
            # sells second gets the crater (observed: 275 -> 115 in one day). Relax our
            # reserve toward the post-wave price and get out ahead of them.
            res = min(res, p.frontrun_sell_frac)
        if under_pressure:
            # Overflow at the end-of-day dump is *destroyed* — shed space outranks price.
            res = min(res, p.sell_min_frac_pressure)
        if force:
            res = 0.0
        at_floor = obs.prices.get(item, BASE_PRICE[item]) <= 1
        price_ok = not at_floor and obs.price_frac(item) >= res

        # Curve-aware sizing: the engine's price curve is known exactly (env_adapter,
        # verified 200/200 vs source), so instead of a blind fixed chunk, sell the largest
        # quantity whose LAST unit still clears this item's reserve. More when the curve is
        # shallow, less near the cliff — every liquidation path gets better realized prices.
        chunk = p.sell_chunk
        if p.marginal_sell and price_ok:
            inv = obs.market_inventory.get(item, MARKET_I0)
            floor_p = max(1.0, res * BASE_PRICE[item])
            lo, hi = 1, have
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if market_price(item, inv + mid - 1) >= floor_p:
                    lo = mid
                else:
                    hi = mid - 1
            chunk = lo

        if final_dump or (force and not at_floor):
            qty = have
        elif gliding:
            # Forced glide: this item's share of the remaining turns, more while the price
            # is still above reserve. Skip floor-priced stock — town demand may lift it
            # before the final dump, and a floor sale pays $1 for a real unit.
            glide_qty = -(-have // max(1, obs.turns_remaining))
            qty = max(glide_qty if not at_floor else 0,
                      chunk if price_ok else 0)
        else:
            qty = chunk if price_ok else 0

        qty = min(have, qty)
        if qty > 0:
            orders.append(["SELL", item, qty])
    return orders


def hire_orders(obs: Observation, p: Params) -> list[list]:
    if obs.turns_remaining <= obs.turns_per_day:
        # Final day: a few of the cheapest hands (fib 1,1,2,3... — pocket change) purely to
        # harvest and haul what one farmer cannot clear before the reward latches. They
        # need the full day to be worth it, hence the tighter hour gate.
        if obs.hour > 1 or obs.turns_remaining <= p.final_dump_turns:
            return []
        want = min(p.final_day_hands, target_hands(obs, p)) - obs.hires_today
        return [["HIRE"]] * max(0, min(want, p.max_hires_per_turn))
    if obs.hour > p.hire_until_hour:
        return []
    want = target_hands(obs, p) - obs.hires_today
    return [["HIRE"]] * max(0, min(want, p.max_hires_per_turn))


def freeing_soon(obs: Observation, p: Params, crop: str | None = None) -> int:
    """One-time crop tiles that will be harvested — and so free — within the seed lead.

    Seeds ordered this turn only exist next turn, so sizing seed demand from tiles that
    are *already* empty makes replanting on the harvest turn impossible. Measured on three
    ladder replays: on the melon replant day we bought 0 seeds and planted 0 tiles while
    the opponent bought 12 seeds five hours ahead of his harvest and refilled 10 tiles the
    same day. That one day of cycle phase decided both losses — his melons cleared at
    $192-101, ours at $37-7 into the crater he had just made.

    Derived from `harvest_age`, not a schedule: a tile is "about to free" when it is within
    the lead of the age at which we would harvest it. Ongoing crops never free their tile
    by being harvested, so they are excluded.
    """
    if not p.seed_anticipate:
        return 0
    n = 0
    for t in obs.tiles:
        if t.state != "PLANT" or not t.crop or CROPS[t.crop]["ongoing"]:
            continue
        if crop is not None and t.crop != crop:
            continue
        if t.age_days >= harvest_age(t.crop) - p.seed_lead_days:
            n += 1
    return n


def plantable_now(obs: Observation, p: Params, crop: str) -> int:
    """Tiles we could commit to this crop by the time the seeds land, respecting its caps.

    Deliberately *not* the same as `plant_budget`. The budget governs PLANT ops issued this
    turn and must see real empty ground; this governs what to buy, and has to look one
    harvest ahead or the seed always arrives a day after the tile.
    """
    planted = sum(1 for t in obs.tiles if t.state == "PLANT")
    freeing = freeing_soon(obs, p)
    room = sum(1 for t in obs.tiles if t.state == "EMPTY") + freeing
    # Tiles about to be harvested still count as `planted`, so credit them back before
    # comparing against the shed-derived ceiling, or the anticipation cancels itself out.
    room = min(room, max(0, active_tile_cap(obs, p) - (planted - freeing)))
    if crop == "MELON":
        held = crop_tile_counts(obs).get("MELON", 0) - freeing_soon(obs, p, "MELON")
        room = min(room, max(0, p.melon_tile_cap - held))
    elif crop == "STRAWBERRY":
        room = min(room, max(0, p.strawberry_tile_cap
                             - crop_tile_counts(obs).get("STRAWBERRY", 0)))
    return room


def _seed_order_for(obs: Observation, p: Params, crop: str) -> list | None:
    """One BUY_SEED order for `crop`, or None if it wants none right now."""
    room = plantable_now(obs, p, crop)
    if room <= 0:
        return None
    if crop == "STRAWBERRY":
        # Strawberries are ongoing: a cohort planted together rots together. The stagger is
        # implemented as a seed drip — buy them only in the morning hours, a couple per turn,
        # so each day plants a small wave instead of one death cohort.
        if obs.hour > p.strawberry_seed_hour:
            return None
        want = min(p.strawberry_drip, room) - obs.seeds.get(crop, 0)
    else:
        # Seeds are the throttle on planting: with a dozen units able to plant a dozen tiles
        # a turn, a small buffer leaves units idle next to bare earth.
        want = min(p.seed_buffer, room) - obs.seeds.get(crop, 0)
    if want <= 0:
        return None
    affordable = int((obs.cash - p.seed_cash_reserve) // CROPS[crop]["seed"])
    want = min(want, max(0, affordable))
    return ["BUY_SEED", crop, want] if want > 0 else None


def seed_orders(obs: Observation, p: Params) -> list[list]:
    """Buy for the preferred crop; fall through if it cannot use seeds this turn.

    The old version took `choose_crop`'s single answer and returned nothing when that crop
    was gated. With strawberry preferred and the drip window shut after
    `strawberry_seed_hour`, every afternoon bought nothing at all — which is why the replays
    show zero melon seeds bought even on the turns *after* twelve melon tiles came free.
    Falling through spends the same cash on the next crop that can actually use it.
    """
    first = choose_crop(obs, p)
    if first is None:
        return []
    candidates = [first]
    if p.seed_fallthrough:
        candidates += [c for c in ("MELON", "STRAWBERRY", "WHEAT", "CARROT") if c != first]
    for crop in candidates:
        if crop_value(obs, p, crop) <= 0:
            continue
        order = _seed_order_for(obs, p, crop)
        if order:
            return [order]
    return []


def land_orders(obs: Observation, p: Params) -> list[list]:
    """Buy land only once we have genuinely run out of room.

    Hands are the scarce input, not tiles: the fib hire ladder means ~12-14 hands a day is
    the affordable ceiling, which is only enough labour for roughly 50-60 worked tiles.
    Buying the last quadrant for $4k of dirt we never plant is a straight loss.
    """
    price = obs.next_land_price()
    if price is None or obs.day > p.last_land_day or obs.day < p.min_land_day:
        return []
    # Season-relative guard. `last_land_day` is an absolute day and so says nothing in a
    # short season: on a 240-step episode every day is <= 15, so the farm kept buying
    # quadrants it could never fill and finished below its opening bank. New tiles have to be
    # planted and then grown, so require a full crop cycle plus fill time to remain.
    # By construction this cannot relax the validated 720-step behaviour: at day <= 15 there
    # are >= 15 days left, already more than melon's 10-day cycle plus lead.
    crop = choose_crop(obs, p)
    if crop is None or obs.days_remaining < harvest_age(crop) + p.land_lead_days:
        return []
    # Labour gate: could the crew we can actually afford service the enlarged farm? Hands are
    # the scarce input, and their cost scales with `farmHandCostMult`, so a tile threshold
    # cannot capture this. With expensive hands the farm bought a quadrant it could not staff
    # and finished below the opening bank — worse than doing nothing at all.
    quadrant = (obs.board_size // 2) ** 2
    workable = sum(1 for t in obs.tiles if t.state != "LOCKED")
    worked = sum(1 for t in obs.tiles if t.state in ("PLANT", "ANIMAL"))
    crew = 1 + affordable_hands(obs, p, workable + quadrant)
    if worked + quadrant > crew * p.tiles_per_unit:
        return []
    # Payback: quadrant *prices* are fixed at $1k/$2k/$4k but quadrant *size* scales with the
    # board, so on a 6x6 farm those same thousands buy 9 tiles instead of 25 and can never
    # earn out. Value the purchase at what the tiles can actually produce in the days left.
    earns = quadrant * crop_value(obs, p, crop) * max(0, obs.days_remaining - p.land_lead_days)
    if earns < price * p.land_payback_mult:
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
    sells = sell_orders(obs, p)
    rest = hire_orders(obs, p) + animal_orders(obs, p) + seed_orders(obs, p) \
        + land_orders(obs, p)
    # Sells still go first in list order (this turn's revenue funds this turn's buys), but
    # they no longer crowd the rest out of the 10-order cap: measured over 3 episodes, the
    # old tail-slice dropped 24 HIREs and 9 feed-wheat buys on the 1.1% of turns that
    # overflowed — worker-days and escape risk cut so a 9th product could be listed. Sells
    # are the safe thing to defer: stock keeps; a missed hire or feed buy does not.
    keep = max(0, obs.max_market_orders - len(rest))
    return (sells[:keep] + rest)[: obs.max_market_orders]


# --- tasks ------------------------------------------------------------------

def _plant_task(obs: Observation, p: Params, tile: Tile, crop: str) -> Task:
    return Task(tile.x, tile.y, ["PLANT", crop], p.prio_plant, "plant")


def _plant_tile_tasks(obs: Observation, p: Params, tile: Tile) -> list[Task]:
    c = CROPS.get(tile.crop)
    if c is None:
        return []
    tasks: list[Task] = []

    decaying = tile.max_lifespan_step >= 0 and obs.step >= tile.max_lifespan_step
    if tile.yield_units > 0 and tile.age_days >= c["first_yield_day"]:
        if decaying:
            tasks.append(Task(tile.x, tile.y, ["HARVEST"], p.prio_harvest_decay, "harvest"))
        elif (tile.crop == "MELON"
              and obs.opp_melon_soon >= p.frontrun_melon_tiles):
            # v8: harvest ahead of the opponent's dump. Their melon pipeline is visible ten
            # days out and the glut is quadratic with no town demand to refill it — measured
            # on seed 700: their 13-tile wave takes the price 277 -> 81 -> 37 in three days,
            # and our own harvest matures one day AFTER the crash by default (harvest_age
            # waits for max yield). Four units at 274 beat six units at 37 by 7x, so once
            # their wave is imminent the marginal yield of waiting is worthless. Priced like
            # decay because it is decay — the value rots per turn once their dump lands.
            tasks.append(Task(tile.x, tile.y, ["HARVEST"], p.prio_harvest_decay, "harvest"))
        elif tile.age_days >= harvest_age(tile.crop):
            tasks.append(Task(tile.x, tile.y, ["HARVEST"], p.prio_harvest_ready, "harvest"))

    # Fertilize a producing strawberry: +1 unit on every watered production day for 3 days
    # (engine :769-770, ongoing crops only). Worth ~$120-180 per application against ~$100
    # for selling the fertilizer — the clones execute ~107 of these per game.
    if (tile.crop == "STRAWBERRY"
            and obs.day <= p.fert_use_last_day
            and tile.fertilized_until_day < obs.day
            and tile.age_days >= c["first_yield_day"] - 2
            and not decaying):
        done = max(0, (tile.age_days - c["first_yield_day"]) // c["interval"] + 1)
        if done < c["max_yield"]:
            tasks.append(Task(tile.x, tile.y, ["FERTILIZE"], p.prio_fertilize,
                              "fertilize", requires="FERTILIZER"))

    if tile.watered_today:
        return tasks
    # Survival: consecutive_unwatered is 1 after any skipped day, and 2 kills the plant
    # at the next end-of-day refresh. Watering only when it is >= 1 (or for yield) skips
    # roughly a quarter of all waterings versus watering everything daily.
    if tile.consecutive_unwatered >= 1:
        tasks.append(Task(tile.x, tile.y, ["WATER"], p.prio_water_urgent, "water"))
        return tasks
    in_window = (not c["ongoing"]
                 and water_window_start(tile.crop) <= tile.age_days <= c["max_yield_day"])
    # Ongoing crops gain nothing from the WATER op itself (engine :381 skips them); their
    # production is calendar-driven. Watering one beyond survival only pays when a fertilizer
    # boost is active, because the +2 requires was_watered on the production day (:769).
    fert_boost_pending = c["ongoing"] and tile.fertilized_until_day >= obs.day
    if (in_window or fert_boost_pending) and tile.yield_units < c["max_yield"]:
        # Tried and rejected: scaling this priority by the crop's unit price. One in-window
        # watering adds exactly one harvestable unit and the window never returns, so a
        # missed melon day looks like $250 lost for one op against ~$30 on wheat — but
        # weighting it that way measured flat-to-negative over 14 out-of-sample seeds.
        # Melon already wins on distance, and starving the cheap crops costs more than the
        # melon it saves.
        tasks.append(Task(tile.x, tile.y, ["WATER"], p.prio_water_bonus, "water"))
    return tasks


def _animal_tasks(obs: Observation, p: Params, tile: Tile) -> list[Task]:
    """The full daily ritual as concurrent tasks, not a serialized chain.

    The old one-task-per-animal version drip-fed feed -> harvest -> fertilizer -> care
    through the queue, and whatever sat last (care, at prio 40) was dropped whenever crop
    work competed: coverage audits showed 6-12 of 14 animals cared per day against the
    clones' 100%. Emitting the whole ritual at once lets different units service the same
    animal in the same day, and the flags are all end-of-day so intra-day order is free.
    """
    a = ANIMALS.get(tile.animal)
    if a is None:
        return []
    tasks: list[Task] = []
    if feeding_matters(obs):
        if not tile.fed_today:
            prio = p.prio_feed_critical if tile.consecutive_unfed >= 1 else p.prio_feed_relaxed
            tasks.append(Task(tile.x, tile.y, ["FEED"], prio, "feed", requires="WHEAT"))
        if not tile.cared_today:
            tasks.append(Task(tile.x, tile.y, ["CARE"], p.prio_animal_care, "care"))
    if tile.yield_units > 0:
        prio = (p.prio_animal_harvest if tile.yield_units >= a["max_held"]
                else p.prio_animal_harvest_partial)
        # Tag "collect", not "harvest": pen work must stay exempt from crop zoning.
        tasks.append(Task(tile.x, tile.y, ["HARVEST"], prio, "collect"))
    if tile.fertilizer_available:
        tasks.append(Task(tile.x, tile.y, ["COLLECT_FERTILIZER"], p.prio_collect_fert, "fert"))
    return tasks


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
            tasks.extend(_plant_tile_tasks(obs, p, tile))
        elif tile.state == "WEED":
            if crop:                      # only worth clearing if we would use the tile
                tasks.append(Task(tile.x, tile.y, ["DIG"], p.prio_dig, "dig"))
        elif tile.state == "ANIMAL":
            tasks.extend(_animal_tasks(obs, p, tile))

    # Pens claim their tiles before crops do, so a build target is never planted over.
    builds = _structure_tasks(obs, p, empty)
    tasks.extend(builds)
    claimed = {t.pos for t in builds}
    if crop:
        tasks.extend(_plant_task(obs, p, t, crop) for t in empty if t.pos not in claimed)

    tasks.extend(_place_tasks(obs, p))
    tasks.extend(_pickup_tasks(obs, p))
    return tasks


def shed_distance_map(obs: Observation) -> dict[tuple[int, int], int]:
    """Walk distance from every reachable tile to the nearest shed-access tile.

    Four BFS passes over a 10x10 board, and only built on the final day, so the cost is
    noise against a 1,000 ms turn budget.
    """
    out: dict[tuple[int, int], int] = {}
    for access in obs.shed_access:
        for pos, (dist, _) in walk_map(obs, access).items():
            if dist < out.get(pos, 1 << 30):
                out[pos] = dist
    return out


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

    # On the last day only the shed scores, so work you cannot walk home from is worse than
    # no work at all. The scoring below is a rate — priority/(1 + move_cost*dist) — so a
    # harvest the unit is standing on (55) outbids its own haul eight tiles out (47), and by
    # the time the haul would win, `dist > turns_remaining` has dropped it from the pool
    # entirely. The unit then farms local tiles until the latch with full hands: measured
    # 1,414 of 1,555 stranded dollars per episode sitting in inventories, not the shed.
    # Filtering here rather than boosting the haul priority lets the drift below carry it
    # home, which is already the right behaviour for a unit with nothing worth doing.
    to_shed = shed_distance_map(obs) if obs.days_remaining <= 1 else None

    # v8 mechanism 2 (zone ownership): each unit owns a quadrant, round-robin by index, and
    # bids stronger on tasks inside it. The greedy assignment otherwise lets every unit bid
    # farm-wide every turn, so the crew criss-crosses and re-shuffles itself — while the
    # agent that beats us runs CALMER units (more PASS than us, fewer pickups, more waters)
    # on identical labour. Ownership is soft: out-of-zone work still happens when nothing
    # local competes, so critical tasks are never orphaned.
    half = obs.board_size // 2
    zone_of = {}
    if p.zone_bonus > 1.0:
        # Blind round-robin over all four quadrants ON PURPOSE, locked ones included.
        # It looks wrong — early units get zones inside locked land, one NW owner outbids
        # the crew, and days 2-3 run a 45-turn cash choke (broke 69 vs 23 unzoned). But
        # dealing zones over unlocked quadrants only was measured and loses 20,849
        # (14/20): the modulus changes every time land unlocks, remapping EVERY unit's
        # zone exactly when the farm grows. Stable ownership beats sensible ownership.
        for i, unit in enumerate(obs.units):
            # Everyone gets a zone, farmer included. Exempting the farmer so it would
            # "serve the pens" was measured and loses 10k contested (119,110 vs 129,433
            # at bonus 2.0): an un-zoned unit is a wanderer, not a servant.
            zone_of[unit.idx] = i % 4

    def zone(x: int, y: int) -> int:
        return (0 if x < half else 1) + (0 if y < half else 2)

    # v8 mechanism 4: critical feeds bypass the auction. An animal one missed day from
    # escaping is not a bid, it's an order — under zoning these feeds were losing on
    # geometry (2.4 escapes/episode at zone 2.0) because every nearby unit had boosted
    # local work. Nearest wheat-carrying unit is conscripted; both leave the market.
    reserved_units: set[int] = set()
    reserved_tasks: set[int] = set()
    if p.critical_feed_offmarket:
        for t_idx, task in enumerate(all_tasks):
            if task.tag != "feed":
                continue
            # Critical feeds always; ordinary feeds too once the evening rounds start —
            # fed_today is read at end of day, so an hour-20 feed pays like an hour-6 one,
            # and by evening the watering that outbids feeds under zoning is mostly done.
            # rc2 runs ~88% fed vs the elite's 99%, and every unfed day zeroes that
            # animal's care bank.
            if (task.priority < p.prio_feed_critical
                    and obs.hour < p.evening_feed_hour):
                continue
            best = None
            for unit in obs.units:
                if unit.idx in reserved_units or unit.inventory.get("WHEAT", 0) <= 0:
                    continue
                hit = maps[unit.idx].get(task.pos)
                if hit is not None and (best is None or hit[0] < best[0]):
                    best = (hit[0], unit.idx, hit[1])
            if best is not None:
                dist, uidx, first = best
                ops[uidx] = list(task.op) if dist == 0 else [first]
                reserved_units.add(uidx)
                reserved_tasks.add(t_idx)

    pairs = []
    for unit in obs.units:
        if unit.idx in reserved_units:
            continue
        reach = maps[unit.idx]
        for t_idx, task in enumerate(all_tasks):
            if t_idx in reserved_tasks:
                continue
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
            if to_shed is not None and task.tag != "haul":
                home = to_shed.get(task.pos)
                # walk there + do it + walk back + DROP has to fit in what is left
                if home is None or dist + 1 + home + 1 > obs.turns_remaining:
                    continue
            # Rate, not difference: a task is worth `priority` and costs `1 + dist`
            # unit-turns to complete, so what we want to maximise is value per turn.
            # Subtracting a linear walk penalty instead let a distant high-priority task
            # outbid work the unit was already standing on, and burned 55% of all
            # unit-turns on walking.
            score = task.priority / (1.0 + p.move_cost * dist)
            # Crop work only: zoning the animal ritual starved it (pens cluster by the
            # shed, and owners of far quadrants under-bid on feeds — measured: unfed
            # 16.6 -> 31.7 and escapes back at 1.9 when every task was zoned).
            if (zone_of and task.tag in ("water", "plant", "harvest", "fertilize", "dig")
                    and zone_of.get(unit.idx, -1) == zone(*task.pos)):
                # Ungated on purpose. The unfed rise that comes with zoning (16.6 -> 35.4)
                # looked like boosted crop bids outbidding feeds, so a gate excluding the
                # critical band was measured: unfed stayed 33.5 (the leak is distance — a
                # zoned-away unit scores feed at 90/(1+0.9*8) and loses to local work on
                # geometry, not on the bonus) while the streak broke to 16/20. Ungated 1.6
                # dominates gated at both tested strengths.
                score *= p.zone_bonus
            pairs.append((score, unit.idx, t_idx, dist, first))

    # Greedy on purpose — exact Hungarian assignment was built and measured twice and
    # loses ~8k contested (129,433 greedy vs 121,264 solver with its group-collapse bug
    # fixed; 118,948 before). Per-turn-optimal matching reshuffles the whole farm whenever
    # marginal totals shift, so units pivot mid-walk; greedy's sequential claims give the
    # same unit the same task turn after turn. This is a repeated game: cross-turn
    # persistence beats per-turn optimality, which is also why zone ownership (adds
    # persistence) is worth +10,863 here. Don't rebuild the solver.
    taken_units: set[int] = set(reserved_units)
    pairs.sort(key=lambda r: -r[0])
    taken_tasks: set[int] = set()
    taken_groups: set[str] = set()
    for _, unit_idx, t_idx, dist, first in pairs:
        if unit_idx in taken_units or t_idx in taken_tasks:
            continue
        task = all_tasks[t_idx]
        if task.group and task.group in taken_groups:
            continue
        if task.tag == "plant":
            # Seeds run out long before empty tiles do; spend on the nearest tiles.
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
