#!/usr/bin/env python3
"""
Figure 3: RTT CDF for local vs tromboned rounds on Pakistani-hosted sites.

Replaces fig_local_vs_hairpin_cdf.pdf, whose in-image title and filename both said
"hairpinned" while the paper says "tromboned" everywhere else.

Source is rq2_merged.csv: ping rounds joined to a co-timed traceroute verdict. That is
why n here (72,368) is smaller than the 75,600 traceroute rounds of the detector, and the
paper says so explicitly.

    python paper/make_local_vs_trombone_cdf.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AN = os.path.join(ROOT, "experiments", "07_longitudinal_panel", "analysis")
OUT = os.path.join(ROOT, "paper", "figures", "fig_local_vs_trombone_cdf.pdf")

BLUE, RED = "#2196F3", "#F44336"

m = pd.read_csv(os.path.join(AN, "rq2_merged.csv"))
m["trombone"] = m["trombone"].astype(bool)

fig, ax = plt.subplots(figsize=(8, 5))
for flag, label, color in [(False, "Local", BLUE), (True, "Tromboned", RED)]:
    v = np.sort(m.loc[m["trombone"] == flag, "rtt_min"].dropna().values)
    cdf = np.arange(1, len(v) + 1) / len(v)
    ax.plot(v, cdf, color=color, linewidth=2.2,
            label=f"{label} (n={len(v):,}, median={np.median(v):.0f} ms)")
    print("  %-10s n=%6d  median %.1f ms" % (label, len(v), np.median(v)))

ax.set_xlim(0, 300)
ax.set_ylim(0, 1.0)
ax.set_xlabel("RTT (ms)", fontsize=11)
ax.set_ylabel("CDF", fontsize=11)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
print("wrote %s" % os.path.relpath(OUT, ROOT))
