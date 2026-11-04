# 44/46 Strict-Future Top-30 | v22 Price Impact

**A current complete route plus an order-only estimate of real nonlinear price damage.**

The public v21 route did not gradually lose because its mirror threshold became
slightly wrong. On episodes created after this candidate was frozen, that old
artifact won only **1/46**.
Refreshing the complete route reached
**36/46**; ranking
the route's already-planned SELLs by official price impact reached
**44/46**.

| Chronological gate | v22 | Seat 0 | Seat 1 |
|---|---:|---:|---:|
| development | **30/30** | 20/20 | 10/10 |
| untouched newest-two outer | **42/44** | 19/20 | 23/24 |
| episodes created after freeze | **44/46** | 20/20 | 24/26 |
| frozen `main.py`, exact game-level replay | **44/46** | 20/20 | 24/26 |

`44/46` is a local strict-future counterfactual replay result, **not an official
Public-LB score**. Replay opponents execute their recorded public trajectories
and do not react to our counterfactual policy.

```text
719-step current route
  + actor-local WEED transaction repair
  + official 1.32.4 price curve
  + SELL ranking inside existing SELL slots
  = no new SELL, no resized SELL, no moved BUY/HIRE slot
```
