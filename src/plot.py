"""
plot.py — turns results/*.csv into the charts in results/ (PNG).

Usage:  python3 plot.py        (needs matplotlib:  pip install matplotlib)
"""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")

# Colorblind-validated categorical palette, assigned in fixed order.
COLORS = {"py_pure": "#2a78d6", "c_O0": "#eb6834", "c_O2": "#1baf7a",
          "c_O2_ikj": "#eda100", "py_numpy": "#e87ba4"}
LABELS = {"py_pure": "Python (pure)", "c_O0": "C  -O0", "c_O2": "C  -O2",
          "c_O2_ikj": "C  -O2, ikj order", "py_numpy": "NumPy (1 thread)"}
ORDER = ["py_pure", "c_O0", "c_O2", "c_O2_ikj", "py_numpy"]
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 13, "axes.edgecolor": GRID,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
})


def read(name):
    with open(os.path.join(RES, name)) as f:
        return list(csv.DictReader(f))


def style(ax):
    ax.grid(axis="y", color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def scaling():
    rows = read("results.csv")
    series = defaultdict(list)
    for r in rows:
        series[r["impl"]].append((int(r["n"]), float(r["median_s"])))
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for impl in ORDER:
        pts = sorted(series[impl])
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=COLORS[impl], linewidth=2.5, marker="o", markersize=8,
                markeredgecolor=SURF, markeredgewidth=2, label=LABELS[impl])
        dy = {"c_O0": 9, "c_O2": -9}.get(impl, 0)  # these two end at the same point
        ax.annotate(LABELS[impl], (xs[-1], ys[-1]), xytext=(10, dy), textcoords="offset points",
                    va="center", color=INK, fontsize=12)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks([64, 128, 256, 512, 1024], ["64", "128", "256", "512", "1024"])
    ax.set_xlim(50, 2600)
    ax.set_xlabel("Matrix size N  (N × N doubles)")
    ax.set_ylabel("Median time per multiply (seconds, log scale)")
    ax.set_title("Time to multiply two N×N matrices", loc="left", color=INK, fontsize=16, pad=14)
    ax.legend(frameon=False, loc="upper left", fontsize=11)
    style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "scaling.png"), dpi=160)


def speedup(n=512):
    rows = {r["impl"]: float(r["median_s"]) for r in read("results.csv") if int(r["n"]) == n}
    base = rows["py_pure"]
    impls = ORDER
    vals = [base / rows[i] for i in impls]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    y = range(len(impls))[::-1]
    ax.barh(list(y), vals, color="#2a78d6", height=0.6)
    for yi, v, i in zip(y, vals, impls):
        ax.text(v * 1.12, yi, f"{v:,.0f}×   ({rows[i]:.3g} s)", va="center", color=INK, fontsize=12)
    ax.set_yticks(list(y), [LABELS[i] for i in impls])
    ax.set_xscale("log")
    ax.set_xlim(0.8, 40000)
    ax.set_xlabel("Speedup vs. pure Python (log scale; higher is faster)")
    ax.set_title(f"Same answer, N = {n}: how much faster than pure Python?", loc="left",
                 color=INK, fontsize=16, pad=14)
    ax.grid(axis="x", color=GRID)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "speedup_512.png"), dpi=160)


def cache():
    rows = read("results.csv")
    sizes = [256, 512, 1024]
    impls = ["c_O0", "c_O2", "c_O2_ikj"]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    w = 0.26
    for k, impl in enumerate(impls):
        vals = [next(float(r["median_s"]) for r in rows if r["impl"] == impl and int(r["n"]) == n)
                for n in sizes]
        xs = [i + (k - 1) * (w + 0.02) for i in range(len(sizes))]
        ax.bar(xs, vals, width=w, color=COLORS[impl], label=LABELS[impl])
        for x, v in zip(xs, vals):
            ax.text(x, v * 1.08, f"{v:.3g}s", ha="center", color=INK, fontsize=11)
    ax.set_yscale("log")
    ax.set_xticks(range(len(sizes)), [f"N = {n}" for n in sizes])
    ax.set_ylabel("Median seconds (log scale)")
    ax.set_title("At N = 1024, -O2 stops helping — loop order (cache use) matters more",
                 loc="left", color=INK, fontsize=16, pad=14)
    ax.legend(frameon=False, loc="upper left")
    style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "cache_effect.png"), dpi=160)


def noise():
    rows = read("noise.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, impl in zip(axes, ["c_O2", "py_pure"]):
        ts = [1000 * float(r["seconds"]) for r in rows if r["impl"] == impl]
        med = sorted(ts)[len(ts) // 2]
        ax.plot(range(1, len(ts) + 1), ts, "o", color=COLORS[impl], markersize=8,
                markeredgecolor=SURF, markeredgewidth=2)
        ax.axhline(med, color=INK2, linewidth=1.5, linestyle="--")
        ax.text(len(ts) + 0.8, med * 0.93, f"median\n{med:.2f} ms", va="top", color=INK2, fontsize=11)
        ax.set_title(f"{LABELS[impl]},  N = 128", loc="left", color=INK, fontsize=14)
        ax.set_xlabel("Run # (each a fresh process)")
        ax.set_ylabel("ms per multiply")
        ax.set_xlim(0, len(ts) + 6)
        ax.set_ylim(0, max(ts) * 1.15)
        style(ax)
        ax.text(1, max(ts) * 1.07, f"slowest / fastest = {max(ts)/min(ts):.2f}×", color=INK, fontsize=11)
    fig.suptitle("Same program, same input, 30 runs: the times are not identical", x=0.01,
                 ha="left", color=INK, fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "noise.png"), dpi=160)


if __name__ == "__main__":
    scaling()
    speedup()
    cache()
    noise()
    print("charts written to results/")
