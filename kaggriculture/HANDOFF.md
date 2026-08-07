# Kaggriculture — project handoff (2026-08-05)

Complete context for continuing this project on a new machine. Everything in here was
verified against a primary source (engine code, replay data, paired evals) — the project
rule is **never guess; fact-check every claim** (also in `~/.claude/CLAUDE.md`).

## What this is

Kaggle simulation competition **kaggriculture** ($50k pool): 2-player farming sim,
720 steps = 30 days x 24 hours, shared reactive market, most money banked wins.
Our agent is a rule engine: `main.py` (entry) + `env_adapter.py` (obs parsing) +
`rules.py` (all logic; every magic number in the `Params` dataclass).

- Kaggle user: Arun Mallikarjuna. Submissions: 5/day; slots used 2026-08-05: 3 of 5.
- Repo branch: `claude/kaggle-competition-xh1lrz` on https://github.com/MrArun005/MrArun005.git
- Local layout on old machine: repo at `Desktop\kaggliculture\repo\kaggriculture`,
  venv at `C:\kv` (short path — the project-local `.venv` breaks on Windows 260-char
  path limit inside orbax, a transitive dependency of kaggle-environments).

## Version history (live ladder)

| Version | Submission | Rating | Notes |
|---|---|---|---|
| v1 melon mono | — | peaked 720 → sank to 632 | field improves daily; frozen agents sink |
| v2 +fert sales | 55262179 | ~574, stagnant | ~50% win rate |
| v3 meta portfolio | 55269770 | oscillates 593–695 | 16 melon/16 straw/8 cow/6 sheep |
| v4 parity build | **not submitted** | — | this working tree; see below |

New submissions always start ~600 and climb only by win rate. There is no way to
start at 2,000+ — fast climbers are just agents that win nearly every episode.

## The verified meta (top of the leaderboard)

All top players (lucaskna #2, trantrikien239, Dennis Gioche) run byte-identical clones
of one public agent. Measured from their real episodes (IDs 90153480, 90154808 —
27 MB replay JSONs, re-download via `kaggle competitions replay <id>`), **executed
units** (shed-inventory deltas, NOT action counts — action counts are attempts and
massively overstate):

- 21 melon seeds lifetime, 44 strawberry (27 tiles by day 12, 40 by day 20)
- 8 cows + 6 sheep; 4 animals by day 3 (spend opening $3,000 down to $10); 14 by day 12
- 100% daily feed+care ritual → the mathematical production maximum: 216 milk, 168 wool
- ~107 FERTILIZE ops on strawberries; ~292 fertilizer produced, rest sold
- 3 quadrants by day 12; endgame wheat refill (32 tiles on day 28)
- Final banks: 121k–141k. lucaskna additionally runs a wheat buy/sell loop
  (27k–31k units cycled) worth a few extra k — not yet replicated here.

## Engine facts that drive everything

Source: `<venv>\Lib\site-packages\kaggle_environments\envs\kaggriculture\kaggriculture.py`

- **CARE banking** (:796–800): every fed+cared day banks +1 product, paid on the next
  FED production day. An unfed production day pays base only and **zeroes the bank**.
  Unfed 2 consecutive days → animal escapes (structure remains).
- **FERTILIZE** (:769–770, :418–424): 1 fertilizer → 3 days coverage; doubles ongoing-crop
  production on watered days. The WATER op itself adds nothing to ongoing crops (:381).
- Cow: interval 2, first yield day 8, max_held 6. Sheep: 3 / 6 / 6. Goose: worthless.
- Melon glut: `sq` above-curve — price collapses quadratically with net units sold.
  Strawberry/milk/wool have town-shop demand that drains the market back down; melon has none.
- Terminal: reward latches at step 718; anything not in the shed by then is worth zero.
- Starting cash 3,000; pens free to build; land $1k/$2k/$4k fixed.

## v4 — what changed today (71k → ~124k contested)

All in `rules.py`, commented with the measurement that justified each:

1. **Concurrent animal ritual** — `_animal_tasks` emits feed+care+collect+harvest
   together (was a serialized chain; care coverage was 43–85%, now 100% from day 16).
2. **Feed (90) outranks care (85)** — inverted once during dev: animals got cared,
   unfed, two escaped. Feed first, always.
3. **Census counts carried animals** — fixed overbuy (was 10 cows + 12 sheep for 8+6
   targets; 8 sheep died unplaced in the shed = $4k dead).
4. **Feed-wheat accounting counts hands** — shed-only check re-bought wheat every turn,
   cash pinned at $150 floor, episode collapsed to 10k. Caught locally.
5. **Strawberry 44 tiles**, ramp day 6, plant through day 17, seed drip 4/turn to hour 8.
6. **FERTILIZE task** on producing strawberries + fertilizer sell-reserve + shed pickup runs.
7. **Melon 13 tiles, no replant after day 13** (tuner-confirmed +5,973 ± 1,632).
8. **Land threshold 18** — 3rd quadrant by day 12 (was stuck at 2 quadrants with idle cash).
9. **Herd front-load** — reserve 900, cow-led round-robin, 3 buys/turn.

### v4 validation (paired seeds, both seats)

- vs v3-config: **16/16 wins, 124,588 vs 88,559** (seeds 700–707)
- vs starter (uncontested): **140,757 ± 5,229** — clone's best observed game is 140,912
- Contested self-play mean after tuning: **114,698** (tuner log: `tune_v4.log`)
- All 21 submission checks pass (`test_agent.py`), worst turn ~60 ms vs 1,000 ms budget.

### Open items toward the 160k goal (est. +17k identified)

- Wool 136 vs 168 (biggest): remaining single missed feeds during herd ramp days 9–15.
- FERTILIZE ops 79 vs 107; milk 201 vs 216; endgame wheat refill not implemented.
- lucaskna's wheat market loop (advanced, risky, ~+3k).
- **Opponent adaptation** (reading rival's farm, front-running dumps) — untouched, the
  biggest differentiator per the notebook research; nobody in the public meta does it well.

## Workflow (the measurement loop)

```
C:\kv\Scripts\python.exe gen_local_replay.py out.json 42   # seeded mirror episode
C:\kv\Scripts\python.exe measure_flows.py out.json          # EXECUTED units + money curve
C:\kv\Scripts\python.exe audit_animals.py out.json          # daily fed/cared coverage
C:\kv\Scripts\python.exe check_quads.py out.json            # land timing
C:\kv\Scripts\python.exe analyze_top.py <replay.json>       # opponent build timeline
C:\kv\Scripts\python.exe v4_eval.py                         # paired eval vs prior config
C:\kv\Scripts\python.exe tune.py --episodes 8 --opponent self --both-seats --only <keys>
C:\kv\Scripts\python.exe test_agent.py                      # 21 checks; MUST pass pre-submit
bash submit.sh "message"                                    # preflight + tarball + submit
```

**Cardinal rules of measurement**
- Single mirror episodes swing ±20k on seed alone. Never compare unseeded runs.
  Only paired same-seed evals (harness/tune.py) can justify a change.
- Replay "sells" from action lists are *attempts*. Only shed-delta flows are real.
- tune.py accepts only >1.5σ AND >0.5% absolute — significance alone overfits the seed set.

## New machine setup

1. Clone the repo, branch `claude/kaggle-competition-xh1lrz`.
2. Python 3.12 venv at a SHORT path (e.g. `C:\kv`): `python -m venv C:\kv`
3. `C:\kv\Scripts\pip install kaggle-environments kaggle` — if the proxy corrupts the
   big wheel, download it with `curl --retry 20 -C -` and install from file.
4. Kaggle auth: token from https://www.kaggle.com/settings/api → `%USERPROFILE%\.kaggle\`
   (never commit this).
5. Useful checks: `kaggle competitions submissions kaggriculture`,
   `kaggle competitions episodes <submission_id>`.

## Decision state at handoff

- v4 is validated locally, **unsubmitted** — Arun's standing instruction: submit only
  when the local evidence reaches top-clone level / 160k ambition. Contested mean is
  114.7k tuned (clone-parity on most lines); uncontested 140.8k. 2 submission slots
  remained for 2026-08-05.
- Progress dashboard (static snapshots, republish on request):
  https://claude.ai/code/artifact/ec31b8c7-03d9-4373-87dd-8fa67a92e00f
