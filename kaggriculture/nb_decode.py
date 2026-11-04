"""Decode the notebook's embedded agent WITHOUT executing it: b85 -> zlib -> file."""
import base64
import hashlib
import json
import sys
import zlib

nb = json.load(open(sys.argv[1], encoding="utf-8"))
src = "".join(nb["cells"][11]["source"])
ns: dict = {}
# Extract only the _AGENT_B85_PARTS literal by slicing the source between markers.
start = src.index("_AGENT_B85_PARTS = [")
end = src.index("]", start) + 1
exec(src[start:end], ns)          # evaluates a pure list-of-strings literal only
raw = zlib.decompress(base64.b85decode("".join(ns["_AGENT_B85_PARTS"]).encode()))
print("bytes:", len(raw), "sha256:", hashlib.sha256(raw).hexdigest())
open("nb_v9/decoded_main.py", "wb").write(raw)
print("written to nb_v9/decoded_main.py")
