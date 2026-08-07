## 5. The order-slot safety contract

Suppose the complete route requests:

```python
[
    ["BUY_PRODUCT", "WHEAT", 2],
    ["SELL", "WHEAT", 20],
    ["HIRE"],
    ["SELL", "STRAWBERRY", 12],
]
```

If strawberry has larger self-impact, v22 returns:

```python
[
    ["BUY_PRODUCT", "WHEAT", 2],
    ["SELL", "STRAWBERRY", 12],
    ["HIRE"],
    ["SELL", "WHEAT", 20],
]
```

Only the contents of indices 1 and 3 changed. This matters because moving a
SELL ahead of a BUY/HIRE can change cash availability and create a different
production trajectory. v22 deliberately refuses that larger intervention.

Runtime invariants:

- same farmer and hand actions;
- same number of market orders;
- same SELL products and quantities;
- same non-SELL orders and positions;
- no ordinary-turn preemption;
- no opponent name, team id, submission id, episode id, or private shed.
