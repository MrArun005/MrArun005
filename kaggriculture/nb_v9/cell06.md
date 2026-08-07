## 4. Price impact, not unit price and not guessed identity

For an existing order `SELL item quantity`, define:

\[
I = q\,\max\left(0,\;p(s)-p(s+q)\right)
\]

where `s` is current shared market inventory and `p` is the official 1.32.4
quote function. This estimates how much quote damage our own order causes. A
large low-unit-price order can outrank a small expensive order when its
nonlinear market impact is larger.

The exact default price-floor distances from equilibrium are:

| product | units to the $1 floor |
|---|---:|
| WOOL | 59 |
| STRAWBERRY | 62 |
| MILK | 76 |
| MELON | 158 |

The score does **not** claim to know the opponent's current order. It is a
state-based risk ranking for the actions our route has already decided to take.
