import json
import os
import sys

path = sys.argv[1]
nb = json.load(open(path, encoding="utf-8"))
os.makedirs("nb_v9", exist_ok=True)
for i in (0, 1, 2, 4, 5, 6, 8, 9, 10):
    src = "".join(nb["cells"][i]["source"])
    open(os.path.join("nb_v9", f"cell{i:02}.md"), "w", encoding="utf-8").write(src)
for i in (3, 7, 11):
    src = "".join(nb["cells"][i]["source"])
    open(os.path.join("nb_v9", f"cell{i:02}.py"), "w", encoding="utf-8").write(src)
print("dumped to nb_v9/")
