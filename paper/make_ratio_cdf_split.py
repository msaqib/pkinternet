#!/usr/bin/env python3
"""
Latency ratio in two panels, split by how the floor is constructed.

(a) Pakistani and Abroad sites. Both have a single server location, so both are measured
    against straight fibre over their own great-circle distance. They belong on the same
    axis and can be read against each other.

(b) CDN sites. An anycast site has no fixed location, so the floor is the best overlay a
    probe could achieve through another probe. That is a different construction and does
    not compare like for like with (a), which is why it sits on its own axis.

    python paper/make_ratio_cdf_split.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(ROOT, "experiments", "07_longitudinal_panel", "analysis")
OUT = os.path.join(ROOT, "paper", "figures", "ratio_cdf_split.pdf")

INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
BLUE, GREEN, AMBER = "#2a78d6", "#1baf7a", "#eda100"
BANDS = [(0.0, 5.0), (5.0, 15.0), (15.0, float("inf"))]

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "font.family": "sans-serif",
    "font.size": 9, "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
})


def cdf(ax, vals, colour, label):
    v = np.sort(pd.Series(vals).dropna().values)
    ax.plot(v, np.arange(1, len(v) + 1) / len(v), color=colour, lw=2.2, zorder=3,
            label="%s (n=%d, median %.1f$\\times$)" % (label, len(v), np.median(v)))
    return v


r = pd.read_csv(os.path.join(AN, "ratio_corrected.csv"))
ic = r[r.distance_km >= 30]
pk = ic[ic.cls == "Pakistan"]
ab = ic[ic.cls == "Abroad"]
cdn = pd.read_csv(os.path.join(AN, "cdn_overlay.csv"))

fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=True)

# ---- (a) unicast: one server each, floor is straight fibre over its own distance
cdf(ax, pk.ratio, BLUE, "Pakistani")
cdf(ax, ab.ratio, GREEN, "Abroad")
ax.axvline(1, color=MUTED, lw=1.1, ls="--", zorder=2)
for b in (5, 15):
    ax.axvline(b, color=BLUE, lw=0.8, ls=":", alpha=0.5, zorder=1)
ax.set_title("(a) unicast sites", fontsize=9, loc="left", pad=6)
ax.text(0.97, 0.30, "floor: straight fibre", transform=ax.transAxes,
        ha="right", va="bottom", fontsize=7.6, color=INK2, style="italic")
ax.set_ylabel("fraction of pairs")

# ---- (b) CDN: no fixed location, floor is the best overlay through another probe
cdf(bx, cdn.ratio_overlay_q_excl_p, AMBER, "CDN")
bx.axvline(1, color=MUTED, lw=1.1, ls="--", zorder=2)
bx.set_title("(b) CDN sites", fontsize=9, loc="left", pad=6)
bx.text(0.97, 0.30, "floor: best overlay, not comparable to (a)",
        transform=bx.transAxes, ha="right", va="bottom", fontsize=7.6,
        color=INK2, style="italic")

for a in (ax, bx):
    a.set_xlim(0, 40)
    a.set_ylim(0, 1.02)
    a.set_xticks([0, 1, 5, 10, 15, 20, 30, 40])
    a.set_xlabel("latency ratio (measured $\\div$ floor)")
    a.legend(frameon=False, fontsize=7.8, loc="lower right",
             borderpad=0.2, handlelength=1.4)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
print("wrote %s" % os.path.relpath(OUT, ROOT))
for lab, v in (("Pakistani", pk.ratio), ("Abroad", ab.ratio),
               ("CDN", cdn.ratio_overlay_q_excl_p)):
    s = pd.Series(v).dropna()
    print("  %-10s n=%3d  median %5.2f  p75 %6.2f  max %6.2f"
          % (lab, len(s), s.median(), s.quantile(.75), s.max()))
