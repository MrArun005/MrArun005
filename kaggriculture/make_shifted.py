"""Build a fully self-contained shifted-tape agent file.

Takes the original decoded tape source and swaps its embedded _ACTIONS payload for
our sell-shifted schedule, re-encoded the same way (zlib + base85). Output has zero
file dependencies, exactly like the original.
"""
import base64
import json
import sys
import textwrap
import zlib

sys.path.insert(0, "nb_v9")
import decoded_main as tape
from counterfit import shift_sells

n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
out_path = sys.argv[2] if len(sys.argv) > 2 else f"v91/main_shift{n}.py"

shifted = shift_sells(tape._ACTIONS, n)
blob = base64.b85encode(zlib.compress(json.dumps(shifted).encode(), 9)).decode()
parts = textwrap.wrap(blob, 100)
payload = "\n".join(f"    {part!r}" for part in parts)

src = open("nb_v9/decoded_main.py", encoding="utf-8").read()
start = src.index("_ACTIONS = json.loads(zlib.decompress(base64.b85decode(")
end = src.index(")).decode(\"utf-8\"))", start) + len(")).decode(\"utf-8\"))")
replacement = (
    "_ACTIONS = json.loads(zlib.decompress(base64.b85decode(\n"
    "    (\n" + payload + "\n    )\n"
    ")).decode(\"utf-8\"))"
)
new_src = src[:start] + replacement + src[end:]
new_src = new_src.replace(
    '"""v22 price-impact route agent for Kaggriculture.',
    f'"""v9.1 counter-fit: v22 route with all SELLs shifted {n} turns earlier.',
    1,
)
open(out_path, "w", encoding="utf-8").write(new_src)

ns = {}
exec(compile(new_src, out_path, "exec"), ns)
assert len(ns["_ACTIONS"]) == len(tape._ACTIONS)
sells = sum(1 for a in ns["_ACTIONS"] for o in (a or {}).get("market", []) or [] if o and o[0] == "SELL")
print(f"wrote {out_path}: {sells} sells, self-contained, import-clean")
