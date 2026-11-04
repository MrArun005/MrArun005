import pandas as pd
import matplotlib.pyplot as plt

results = pd.DataFrame([
    ["old public v21", 1, 46, -7839.760869565217],
    ["current route only", 36, 46, 1838.1739130434783],
    ["v22 price impact", 44, 46, 3508.9347826086955],
], columns=["policy", "wins", "games", "mean margin"])
results["win rate"] = results.wins / results.games
display(results)

ax = results.plot.barh(
    x="policy", y="win rate", legend=False, figsize=(8.8, 3.4),
    color=["#94a3b8", "#38bdf8", "#0f766e"],
)
ax.axvline(0.5, color="#64748b", linestyle="--", linewidth=1)
ax.set(xlabel="Post-freeze win rate", ylabel="", xlim=(0, 1),
       title="Separate route refresh from the market contribution")
ax.grid(axis="x", alpha=0.25)
plt.tight_layout()