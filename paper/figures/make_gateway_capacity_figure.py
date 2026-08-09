#!/usr/bin/env python3
"""
Recreate PACRA's Pakistan international bandwidth capacity chart (FY23), coloured
by gateway operator instead of PACRA's plain blue/green, so the "who owns which
cable" story (PTCL / Transworld / SCO / Cybernet) is visible at a glance.
Data is transcribed as-is from the PACRA rating report chart (pacra2023twa) --
no values altered or estimated.

    python paper/make_gateway_capacity_figure.py   # -> paper/figures/fig_gateway_capacity.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "paper", "figures"); os.makedirs(FIG, exist_ok=True)

# validated reference palette (light mode) -- same hexes as make_figures.py
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, GRID, BASE, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": BASE, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "font.family": "sans-serif",
    "font.size": 11, "axes.titlesize": 12.5, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
})

# (cable, operator, installed_Tbps, activated_Tbps) -- transcribed from the PACRA chart
# SMW3 excluded: PACRA lists it at 0.0/0.0 (fully decommissioned), so it draws no bar
# and only clutters the axis.
DATA = [
    ("SMW4",  "PTCL",       1.1, 1.0),
    ("IMEWE", "PTCL",       1.9, 1.4),
    ("AA-1",  "PTCL",       4.8, 2.5),
    ("SMW5",  "Transworld", 1.4, 1.0),
    ("TW1",   "Transworld", 1.5, 1.0),
    ("OFC",   "SCO",        1.0, 0.2),
    ("PEACE", "Cybernet",   1.6, 0.6),
]
OP_COLOR = {"PTCL": BLUE, "Transworld": ORANGE, "SCO": YELLOW, "Cybernet": AQUA}

cables   = [d[0] for d in DATA]
ops      = [d[1] for d in DATA]
installed = [d[2] for d in DATA]
activated = [d[3] for d in DATA]
colors    = [OP_COLOR[o] for o in ops]

n = len(DATA)
x = np.arange(n) + np.array([i // 1 for i in range(n)]) * 0  # placeholder, gaps added below
# add a visual gap between operator groups
gap = 0.9
xs, cur = [], 0.0
prev_op = None
for _, op, _, _ in DATA:
    if prev_op is not None and op != prev_op:
        cur += gap
    xs.append(cur)
    cur += 1.0
    prev_op = op
xs = np.array(xs)

bar_w = 0.34
fig, ax = plt.subplots(figsize=(9.6, 4.6))
b_installed = ax.bar(xs - bar_w/2, installed, width=bar_w, color=colors, alpha=1.0,
                      edgecolor=SURF, linewidth=1.2, label="Installed")
b_activated = ax.bar(xs + bar_w/2, activated, width=bar_w, color=colors, alpha=0.45,
                      edgecolor=SURF, linewidth=1.2, label="Activated")

for xi, v in zip(xs - bar_w/2, installed):
    ax.text(xi, v + 0.08, f"{v:.1f}", ha="center", va="bottom", color=INK2, fontsize=8.5)
for xi, v in zip(xs + bar_w/2, activated):
    ax.text(xi, v + 0.08, f"{v:.1f}", ha="center", va="bottom", color=INK2, fontsize=8.5)

ax.set_xticks(xs)
ax.set_xticklabels(cables, fontsize=9.5)

# operator group labels beneath the cable ticks
op_spans = {}
for xi, op in zip(xs, ops):
    op_spans.setdefault(op, []).append(xi)
for op, span in op_spans.items():
    mid = (min(span) + max(span)) / 2
    ax.text(mid, -1.05, op, ha="center", va="top", color=INK, fontsize=10.5, fontweight="bold")

ax.set_ylim(0, 5.4)
ax.set_ylabel("International bandwidth capacity (Tbps)")
ax.set_title("Pakistan's international bandwidth capacity by cable system, FY23", loc="left")
ax.grid(axis="x", visible=False)

# legend: alpha (installed vs activated) -- operator identity is already labelled below the axis
from matplotlib.patches import Patch
legend_elems = [
    Patch(facecolor=MUTED, alpha=1.0, edgecolor=SURF, label="Installed"),
    Patch(facecolor=MUTED, alpha=0.45, edgecolor=SURF, label="Activated"),
]
ax.legend(handles=legend_elems, frameon=False, loc="upper left")

fig.tight_layout(rect=[0, 0.04, 1, 1])
fig.savefig(os.path.join(FIG, "fig_gateway_capacity.png"), dpi=200)
plt.close(fig)
print("wrote paper/figures/fig_gateway_capacity.png")
