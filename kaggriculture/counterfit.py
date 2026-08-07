"""Counter-fit transform: shift every scheduled SELL earlier by N turns.

Writes v91/actions_shift{N}.json. Constraint respected: max 10 market orders per
turn (excess spills one turn earlier, recursively toward turn 0).
"""
import json
import sys

sys.path.insert(0, "nb_v9")
import decoded_main as tape

MAX_ORDERS = 10


def shift_sells(actions, n):
    out = [dict(a or {}, market=[list(o) for o in (a or {}).get("market", []) or []])
           for a in actions]
    moves = []
    for step, act in enumerate(out):
        keep = []
        for order in act["market"]:
            if order and order[0] == "SELL":
                moves.append((max(0, step - n), order))
            else:
                keep.append(order)
        act["market"] = keep
    for target, order in moves:
        t = target
        while t >= 0 and len(out[t]["market"]) >= MAX_ORDERS:
            t -= 1
        if t < 0:
            t = target
            while t < len(out) and len(out[t]["market"]) >= MAX_ORDERS:
                t += 1
            if t >= len(out):
                continue
        out[t]["market"].append(order)
    return out


n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
shifted = shift_sells(tape._ACTIONS, n)
path = f"v91/actions_shift{n}.json"
json.dump(shifted, open(path, "w"))
sells_orig = sum(1 for a in tape._ACTIONS for o in (a or {}).get("market", []) or [] if o and o[0] == "SELL")
sells_new = sum(1 for a in shifted for o in a.get("market", []) or [] if o and o[0] == "SELL")
print(f"shift {n}: {sells_orig} sells -> {sells_new} preserved, wrote {path}")
