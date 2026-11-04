---
name: kaggriculture-competition-state
description: "Kaggle kaggriculture competition — verified engine mechanics, top-clone meta facts, and version history v1-v4"
metadata: 
  node_type: memory
  type: project
  originSessionId: ec1a8cb4-0d22-42d5-b82d-b6649fbd40f6
  modified: 2026-08-05T13:14:46.629Z
---

Kaggle "kaggriculture" farming sim competition ($50k). Agent code in `repo/kaggriculture/` (main.py, rules.py, env_adapter.py). Venv at `C:\kv` (short path — project .venv breaks on Windows 260-char limit).

**Why:** User's goal is climbing the live leaderboard; new submissions always start ~600 and must EARN rating via win rate — there is no way to start at 2,000+.

**Verified engine facts (from `C:\kv\Lib\site-packages\kaggle_environments\envs\kaggriculture\kaggriculture.py`):**
- CARE: every fed+cared day banks +1 product, paid on next FED production day (:796-800). Cow interval 2, sheep 3. Perfect ritual = 3 milk/2d, 4 wool/3d.
- Animal unfed 2 consecutive days → escapes (:787-789). FEED consumes 1 WHEAT from unit's hand.
- FERTILIZE: 1 fert → fertilized_until_day=day+2; doubles ongoing-crop production on watered days (:769-770); WATER op adds nothing to ongoing crops (:381).
- Terminal: reward latched at step 718; step-719 auto-drop worthless.
- Starting cash 3000; pens free to build; land $1k/$2k/$4k.

**Top-clone meta (measured EXECUTED flows from replays 90153480/90154808 — never trust attempted-op counts):** all top players run one identical public agent: 21 melon seeds, 44 strawberry (27 tiles by day 12, 40 by 20), 8 cows + 6 sheep (4 animals by day 3, 14 by day 12, spend to $10), 100% daily feed+care (mathematical max production: 216 milk, 168 wool), ~107 FERTILIZE ops on strawberries, ~292 fert produced, 3 quadrants by day 12, endgame wheat refill (32 tiles day 28). Final scores 121k-141k. lucaskna additionally runs a wheat buy/sell market loop (27k-31k units).

**Version history (live ratings):** v1 720→632 (melon mono), v2 ~589 stagnant, v3 (sub 55269770) oscillates 593-695. v4 (built 2026-08-05) fixed: serialized animal task chain → concurrent ritual tasks; care prio 40→85, feed relaxed 72→90 (feed MUST outrank care); animal overbuy bug (carried animals invisible to census → 12 sheep bought, 8 died in shed); strawberry 16→44 tiles ramp from day 6, last day 17; melon stop day 12; FERTILIZE task + fert sell reserve; animal_cash_reserve 2500→900. Mirror self-play: 71k → ~104-108k.

**How to apply:** measure changes with `measure_flows.py` (executed shed/inv deltas) and `audit_animals.py` (daily fed/cared coverage) on a `gen_local_replay.py` episode; validate with paired-seed harness evals (`v4_eval.py` pattern) before any submission; run `test_agent.py` (21 checks) before submitting. Mirror-run totals vary by random seed — only paired seeds are comparable.
