import json
import os
import sys

path = sys.argv[1]
nb = json.load(open(path, encoding="utf-8"))
print("cells:", len(nb["cells"]))
for i, c in enumerate(nb["cells"]):
    src = "".join(c["source"])
    head = src.strip().splitlines()[0][:100] if src.strip() else "(empty)"
    print(f"{i:>3} {c['cell_type']:<8} {len(src):>7}ch  {head}")
