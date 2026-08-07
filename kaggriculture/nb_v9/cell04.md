## 2. What the public forks taught us

Attribution and validation are separate questions. These are the public works
most relevant to this release:

| Notebook | What is strong | How v22 uses it |
|---|---|---|
| [Kaito v21.1 Conditional Memory](https://www.kaggle.com/code/kaitofukami/177-180-fresh-top-30-v21-1-conditional-memory) | exact public artifact and the route/memory baseline | upstream agent; now tested as a stale control |
| [Rayk — Findings from Zero to Top Meta](https://www.kaggle.com/code/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta) | unusually precise upstream byte/hash boundary; isolates one SELL-ranking substitution | direct inspiration for price-impact ranking; independently reimplemented here |
| [boatlee — Order-Safe Premium Control](https://www.kaggle.com/code/boatlee/v13-r3-top-meta-order-safe-premium-control) | quantity-conserving preemption and the warning not to move BUY/HIRE slots | v22 preserves every non-SELL slot, but rejects preemption without fresh gain |
| [fle3n — v21.1 No Preemption](https://www.kaggle.com/code/fleongg/kaggriculture-public-2830-4-v21-1-no-preemption) | narrow ablation showing repeated early SELL can decay | ordinary v22 turns create no SELL |
| [Desyat — 93% WR vs Kaito v21.1](https://www.kaggle.com/code/desyatio/93-wr-vs-kaito-s-v21-1-local-tuning-experiment) | clear terminal-only contribution boundary | retained as an adversarial idea, not promoted from version-specific evidence |
| [webcainiao — v21 Tactical Memory](https://www.kaggle.com/code/web3cainiao/kaggriculture-v21-tactical-memory) | explicit Kaito attribution | evidence that v21 became a population prior; not treated as independent validation |
| [Furina — What the Top Farms Do](https://www.kaggle.com/code/cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta) | daily population drift and exact 1.32.x price-cliff warning | engine pin and a post-freeze time slice |
| [prvsiyan — The Moon Counts Melons](https://www.kaggle.com/code/prvsiyan/kaggriculture-frontier-the-moon-counts-melons) | market timing inside a converged production basin | market and route are ablated separately |

The public route embedded here is a real replay from team **roma**, submission
`55299523`, episode `90473746`, source seat `0`, action hash
`cd4380d55c4a13c2ed4fd0c9463268c5764599f7e3f58b91e960b49d7dfd5d77`.
That provenance is credited; it is not claimed as a newly invented production
plan. The contribution of this Notebook is the refreshed selection protocol,
the safe price-impact controller, rejected-branch evidence, and exact artifact
verification.
