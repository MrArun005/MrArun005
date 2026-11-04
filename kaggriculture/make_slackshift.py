"""Slack-aware counter-fit: move only WHEAT and FERTILIZER sells earlier, each by
min(observed slack, CAP) turns, leaving the zero-slack products untouched.

Slack comes from an actual tape-mirror replay (shed contents per step), so a shifted
sell always fires with stock on hand. Output: self-contained agent file.
"""
import base64
import json
import sys
import textwrap
import zlib

from kaggle_environments import make

sys.path.insert(0, "nb_v9")
import decoded_main as tape

CAP = int(sys.argv[1]) if len(sys.argv) > 1 else 8
OUT = sys.argv[2] if len(sys.argv) > 2 else f"v91/main_slack{CAP}.py"
MOVABLE = {"WHEAT", "FERTILIZER"}
MAX_ORDERS = 10

env = make("kaggriculture", configuration={"seed": 901}, debug=False)
env.run(["nb_v9/decoded_main.py", "nb_v9/decoded_main.py"])
shed = [dict((st[0]["observation"].get("private", {}) or {}).get("shed", {}) or {})
        for st in env.steps]

actions = [dict(a or {}, market=[list(o) for o in (a or {}).get("market", []) or []])
           for a in tape._ACTIONS]
moves = []
for step, act in enumerate(actions):
    keep = []
    for order in act["market"]:
        if order and order[0] == "SELL" and order[1] in MOVABLE and len(order) >= 3:
            item, qty = order[1], int(order[2])
            s = 0
            while (s < CAP and step - s - 1 >= 0
                   and shed[min(step - s - 1, len(shed) - 1)].get(item, 0) >= qty):
                s += 1
            if s > 0:
                moves.append((step - s, order))
                continue
        keep.append(order)
    act["market"] = keep
for target, order in moves:
    t = target
    while t < len(actions) and len(actions[t]["market"]) >= MAX_ORDERS:
        t += 1
    if t < len(actions):
        actions[t]["market"].append(order)

blob = base64.b85encode(zlib.compress(json.dumps(actions).encode(), 9)).decode()
payload = "\n".join(f"    {p!r}" for p in textwrap.wrap(blob, 100))
src = open("nb_v9/decoded_main.py", encoding="utf-8").read()
start = src.index("_ACTIONS = json.loads(zlib.decompress(base64.b85decode(")
end = src.index(')).decode("utf-8"))', start) + len(')).decode("utf-8"))')
src = (src[:start]
       + "_ACTIONS = json.loads(zlib.decompress(base64.b85decode(\n    (\n"
       + payload + "\n    )\n)).decode(\"utf-8\"))"
       + src[end:])
src = src.replace('"""v22 price-impact route agent for Kaggriculture.',
                  f'"""v9.1 slack-shift: v22 route, WHEAT+FERT sells up to {CAP} turns early.', 1)
open(OUT, "w", encoding="utf-8").write(src)
ns = {}
exec(compile(src, OUT, "exec"), ns)
print(f"wrote {OUT}: moved {len(moves)} sells (cap {CAP})")
