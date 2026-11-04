# Official 1.32.4 post-equilibrium quotes, reproduced without network access.
import math

params = {
    "WOOL": (200, 105, "sq", 3.2),
    "STRAWBERRY": (120, 100, "linear", 1.6),
    "MILK": (160, 122, "linear", 1.6),
    "MELON": (250, 300, "sq", 3.6),
}

def shape(name, x):
    return x if name == "linear" else x * x

def quote(item, surplus):
    base, scale, fn, target = params[item]
    amp = target * base / shape(fn, scale)
    return max(1, int(round(base - amp * shape(fn, surplus))))

curve = pd.DataFrame([
    [item, surplus, quote(item, surplus)]
    for item in params for surplus in range(0, 181)
], columns=["product", "surplus inventory", "quote"])
ax = curve.pivot(index="surplus inventory", columns="product", values="quote").plot(
    figsize=(9, 4.2), linewidth=2
)
ax.set(title="Official nonlinear price damage after market equilibrium",
       ylabel="unit quote ($)")
ax.grid(alpha=0.25)
plt.tight_layout()