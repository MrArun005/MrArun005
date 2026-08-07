## 1. Diagnosis: the route was stale, but route refresh was not enough

At the 2026-08-07 snapshot, the Top-30 boundary was **2910.4**. We downloaded
102 public episodes from the current scoring submissions under
`kaggle-environments==1.32.4` and kept time order.

Thirty real, complete fit-only routes were screened on the next trajectory for
each current team. The strongest unchanged routes were:

| Fit-only complete route | Development wins |
|---|---:|
| DECEM | **28/30** |
| roma | **28/30** |
| Mohit Rao | 25/30 |
| old public v21 | 2/30 |

DECEM and roma differ at only 18 of 719 turns. The DECEM source replay contains
a stochastic WEED detour around steps 663–671; roma preserves the clean shared
route at that point. The market-aware pair `roma-impact-slots` was therefore
frozen before the outer and later strict-future downloads.

The important decomposition on the later 46 cases is:

```text
old route + old market memory       1/46
current route, market unchanged    36/46
current route + price impact       44/46
```

Route refresh repaired the basin. The order controller supplied another eight
wins without changing production or inventory decisions.
