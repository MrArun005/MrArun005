# Results — current build (v10 on the ladder, v8/v9 lineage in code, 2026-08-06)

Everything below is measured, not projected. Local numbers come from `eval_h2h.py`
(paired seeds 700–709, both seats); ladder numbers from real episode replays via
`ladder.py`. The previous version of this file described the v1 melon monobot
(77k vs starter) and survived three majors unchanged — if the numbers here ever
disagree with the `Params` comments in `rules.py`, trust the comments and regenerate this.

## Live ladder (submission history)

| build | submission | rating | real record (replay-verified) |
|---|---|---|---|
| v4 | 55274770 | peaked ~934, drifted to ~920 | 18/34 (53%) — 1/12 vs opponents banking 125k+ |
| v6 | 55285442 | peaked 1029, settled ~999 | 14/28 (50%) |
| v7 | 55286208 | 985.6 and climbing at last check | 16/30 (53%) — losses bunched: 9 of 14 within 5–15k |
| v9 | (id not recorded) | ~2,000 | — |
| v10 | (id not recorded) | **~2,700** | — |

Rating is opponent-weighted win rate, not bank. The field's 125k+ tier is mostly one
public agent running under many names (Faris Abqari, Chaitanya Sonaje, Agzam, tong00,
GzmCR632 — byte-identical play, 152–164k vs v7).

The v9 and v10 rows are ratings reported from the Kaggle UI, not replay-verified — no
submission id or record captured, so `ladder.py` cannot reconstruct them. Everything above
v7 in this table is therefore weaker evidence than the rows below it.

**Naming, because it has already caused confusion:** the ladder build called "v10" is the
v8/v9 accepted stack — opponent front-running, zone ownership, feeding rounds, carried
wheat, the strawberry floor. It is *not* the thing `rules.py` labels v10 (`forward_pricing`
+ `dynamic_crop_choice`), which is measured, rejected, and ships with both flags `False`.
The 2,700 build never calls `forward_price` or `pipeline()`. Do not read the rejection
tombstone as a comment on what is winning.

## Local bench (contested, seeds 700–709 × both seats)

| | vs previous config | vs starter |
|---|---|---|
| v7 (shipped) | 20/20, bank 120,466, worst margin +614 | 20/20, bank 160,677, min 148,649 |

Caveat from the feed-garden control: one inert market order flipped 20/20 → 18/20.
Past ~18/20 the last wins are chaos — judge changes on bank and margin distribution.

## What v7 is (deltas over v4, each paired-measured)

melon uncapped (13→26, +14,441), endgame wheat churn fix (+2,276), feed-pickup gate
(+1,289), stranding filter (+266), escape insurance (escapes 1.2/ep → ~0.1),
hands 0.16→0.14, move_cost 0.4→0.9 (routing was the binding constraint; 20/20).

## Measured dead ends (do not re-run; details live in `rules.py` Params comments)

feed taper (×2) · herd front-load (0/8) · melon planting drip (0/20 at aggressive) ·
seed_buffer 18/24 (0/20) · hands 0.12/0.15/0.20/0.24 · feed_reserve_days 3/4 ·
prio_plant 50 (8/20) · strawberry_drip 6/8/11 (monotone collapse) ·
clone wheat opening (−20k) · feed garden built properly (1/20, unfed halved anyway) ·
whole clone portfolio on our machinery (0/20, −14,874)

## The open problem

The gap to the 125k+ tier is execution, not portfolio: same assets yield them 218 milk
to our 194, 262 strawberry to our 216. Two untouched levers, in order:
**opponent-aware market play** (their whole farm is in our observation; nothing reads it)
and **layout as policy** (every graft of their layout fails because layout is the thing
grafts can't carry).
