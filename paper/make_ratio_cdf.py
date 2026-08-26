#!/usr/bin/env python3
"""
Figure 5 of running_draft.tex, annotated: the latency-ratio CDF with the three visible
steps marked and labelled by the median probe-site distance in each band.

The steps are a denominator effect. The ratio is measured RTT divided by a floor derived
from distance, so a short pair has a tiny floor and a few ms of fixed access overhead
inflates its ratio far more than it inflates a long pair's. Labelling each band with its
median distance makes that visible instead of leaving it to be misread as three routing
regimes.

    python paper/make_ratio_cdf.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(ROOT, "experiments", "07_longitudinal_panel", "analysis")
OUT = os.path.join(ROOT, "paper", "figures", "ratio_cdf_all3.png")

INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
BLUE, GREEN, AMBER = "#2a78d6", "#1baf7a", "#eda100"
BANDS = [(0.0, 5.0), (5.0, 15.0), (15.0, float('inf'))]

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "font.family": "sans-serif",
    "font.size": 11, "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True,
})

r = pd.read_csv(os.path.join(AN, "ratio_corrected.csv"))
ic = r[r.distance_km >= 30]                      # intercity pairs only, as in geo.py
cdn = pd.read_csv(os.path.join(AN, "cdn_overlay.csv"))

series = [("Pakistan", ic[ic.cls == "Pakistan"].ratio, BLUE),
          ("Abroad", ic[ic.cls == "Abroad"].ratio, GREEN)]
if "ratio_overlay_q_incl_p" in cdn.columns:
    series.append(("CDN", cdn.ratio_overlay_q_incl_p, AMBER))

fig, ax = plt.subplots(figsize=(7.6, 5.0))

# shade the three bands the Pakistani curve steps through
for i, (lo, hi) in enumerate(BANDS):
    if i % 2 == 0:
        ax.axvspan(lo, min(hi, 40.0), color=GRID, alpha=0.35, lw=0, zorder=0)
for lo, hi in BANDS[1:]:
    ax.axvline(lo, color=BLUE, lw=0.9, ls=":", alpha=0.55, zorder=1)

for name, vals, c in series:
    v = np.sort(vals.dropna().values)
    y = np.arange(1, len(v) + 1) / len(v)
    ax.plot(v, y, color=c, lw=2.2, zorder=3,
            label=f"{name} (median {np.median(v):.1f}×)")

ax.axvline(1, color=MUTED, lw=1.2, ls="--", zorder=2)
ax.text(1.35, 0.985, "1× = theoretical minimum",
        fontsize=8.4, color=INK2, va="top", zorder=4)

# band statistics are described in the prose, not on the figure; the dotted lines
# above only mark where the two steps in the Pakistani curve fall
pk = ic[ic.cls == "Pakistan"]
ab = ic[ic.cls == "Abroad"]
cd = cdn.ratio_overlay_q_incl_p.dropna() if "ratio_overlay_q_incl_p" in cdn.columns else None

ax.set_xlim(0, 40)
ax.set_ylim(0, 1.02)
ax.set_xticks([0, 1, 2, 3, 5, 10, 15, 20, 25, 30, 35, 40])
ax.set_xlabel("latency ratio (measured ÷ theoretical minimum)")
ax.set_ylabel("fraction of connections")
ax.legend(frameon=False, fontsize=9.5, loc="center right")
fig.tight_layout()
fig.savefig(OUT, dpi=170, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
print("wrote %s" % os.path.relpath(OUT, ROOT))
print("%-10s %-22s %-22s %s" % ("band", "Pakistan", "Abroad", "CDN"))
for lo, hi in BANDS:
    out = []
    for sub in (pk, ab):
        t = sub[(sub.ratio >= lo) & (sub.ratio < hi)]
        out.append("n=%3d  %6s km  %5s ms"
                   % (len(t),
                      format(int(t.distance_km.median()), ",") if len(t) else "-",
                      ("%.1f" % t.measured_ms.median()) if len(t) else "-"))
    n_cdn = int(((cd >= lo) & (cd < hi)).sum()) if cd is not None else 0
    print("%-10s %-22s %-22s n=%3d" % ("%g to %g" % (lo, hi), out[0], out[1], n_cdn))
