"""Which callable does kaggle_environments pick out of v92/main.py?"""
import sys

from kaggle_environments.agent import get_last_callable

path = sys.argv[1] if len(sys.argv) > 1 else "v92/main.py"
fn = get_last_callable(open(path, encoding="utf-8").read(), path=path)
print("picked:", getattr(fn, "__name__", fn))
