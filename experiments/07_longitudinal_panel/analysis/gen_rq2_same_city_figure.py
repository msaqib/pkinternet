#!/usr/bin/env python3
"""
New-RQ2 same-city figure: CDN vs domestic median RTT per ISP, held to one city,
Karachi and Lahore side by side. Run rq2_same_city_domestic.py first (domestic
numbers) and geo.py cdn (CDN numbers, already in cdn.csv). Style matches
regen_figures.py (figsize, steelblue/red palette, grid alpha).
"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER_FIGS = os.path.join(HERE, "..", "..", "..", "paper", "figures")

KARACHI = {1016126: "PTCL", 1016143: "Cybernet", 1016154: "Cybernet", 64722: "TES"}
LAHORE = {1015679: "Nova", 62224: "Transworld", 7613: "Zcom", 65892: "Nayatel"}

cdn = pd.read_csv(os.path.join(HERE, "cdn.csv"))
domestic = pd.read_csv(os.path.join(HERE, "rq2_same_city_domestic.csv"))


def cdn_stats(probes):
    d = cdn[cdn.probe_id.isin(probes)].copy()
    d["isp_label"] = d.probe_id.map(probes)
    return d.groupby("isp_label")["min_rtt_ms"].median()


CDN_BLUE, DOM_ORANGE = "#2196F3", "#FF9800"

fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=False)

for ax, probes, label in [(axes[0], KARACHI, "Karachi"), (axes[1], LAHORE, "Lahore")]:
    c = cdn_stats(probes)
    dom = domestic[domestic.city == label].set_index("isp_label")["median_rtt"]
    isps = sorted(set(c.index) | set(dom.index), key=lambda i: c.get(i, 0))
    x = np.arange(len(isps))
    w = 0.35
    cdn_vals = [c.get(i, np.nan) for i in isps]
    dom_vals = [dom.get(i, np.nan) for i in isps]
    ax.bar(x - w / 2, cdn_vals, w, label="CDN-hosted", color=CDN_BLUE, edgecolor="white")
    ax.bar(x + w / 2, dom_vals, w, label="Pakistani-hosted", color=DOM_ORANGE, edgecolor="white")
    for xi, v in zip(x - w / 2, cdn_vals):
        ax.text(xi, v + 2, f"{v:.1f}", ha="center", fontsize=8)
    for xi, v in zip(x + w / 2, dom_vals):
        ax.text(xi, v + 2, f"{v:.1f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(isps, rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("Median RTT (ms)", fontsize=10)
    cdn_spread = max(cdn_vals) / min(cdn_vals)
    dom_spread = max(dom_vals) / min(dom_vals)
    ax.set_title(f"{label}\nCDN spread {cdn_spread:.1f}$\\times$, domestic spread {dom_spread:.1f}$\\times$",
                 fontsize=10)
    ax.grid(axis="y", alpha=0.3)

axes[0].legend(fontsize=9, loc="upper left")
plt.suptitle("Same-City ISP Comparison: CDN vs Domestic Content", fontsize=12)
plt.tight_layout()
out_path = os.path.join(PAPER_FIGS, "fig_rq2_same_city_domestic_vs_cdn.pdf")
plt.savefig(out_path, bbox_inches="tight")
plt.close()
print(f"wrote {out_path}")
