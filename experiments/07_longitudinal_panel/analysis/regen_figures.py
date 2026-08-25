#!/usr/bin/env python3
"""Regenerate fig_trombone_by_isp.pdf and fig_local_vs_hairpin_cdf.pdf under the
final 5-rule classifier, matching the exact style/layout of the original
exp07_analysis.ipynb cells that produced them."""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Inputs are the analysis CSVs beside this script; outputs are the figures the paper
# includes. Both were previously a single hard-coded absolute temp directory, which
# meant this script only ran on one machine.
HERE = os.path.dirname(os.path.abspath(__file__))
IN   = HERE
OUT  = os.path.abspath(os.path.join(HERE, "..", "..", "..", "paper", "figures"))
os.makedirs(OUT, exist_ok=True)

# ---- fig_trombone_by_isp.pdf ----
trace = pd.read_csv(f"{IN}/final_classified_rounds.csv")
trace["probe_label"] = trace["isp"] + "." + trace["probe_id"].astype(str)

trombone_by_isp = (
    trace.groupby(["probe_label"])["trombone"]
    .mean()
    .reset_index()
    .rename(columns={"trombone": "trombone_rate"})
    .sort_values("trombone_rate", ascending=False)
)

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.barh(trombone_by_isp["probe_label"],
                trombone_by_isp["trombone_rate"] * 100,
                color="steelblue", edgecolor="white")
ax.set_xlabel("Trombone rate (% of rounds)", fontsize=11)
ax.set_title("Tromboning Rate by ISP -- PK-hosted Sites Only", fontsize=12)
ax.grid(axis="x", alpha=0.3)
ax.invert_yaxis()
for bar, val in zip(bars, trombone_by_isp["trombone_rate"] * 100):
    ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
             f"{val:.1f}%", va="center", fontsize=8)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_trombone_by_isp.pdf", bbox_inches="tight")
plt.close()
print("wrote fig_trombone_by_isp.pdf")

# ---- fig_local_vs_hairpin_cdf.pdf ----
m = pd.read_csv(f"{IN}/rq2_merged.csv")
m["trombone"] = m["trombone"].astype(bool)
BLUE, RED = "#2196F3", "#F44336"

fig, ax = plt.subplots(figsize=(8, 5))
for troms, label, color in [(False, "Local", BLUE), (True, "Tromboned", RED)]:
    vals = np.sort(m.loc[m["trombone"] == troms, "rtt_min"].dropna())
    cdf = np.arange(1, len(vals) + 1) / len(vals)
    ax.plot(vals, cdf, color=color, linewidth=2.2,
            label=f"{label} (n={len(vals):,}, median={np.median(vals):.0f} ms)")
ax.set_xlim(0, 300)
ax.set_xlabel("RTT (ms)", fontsize=11)
ax.set_ylabel("CDF", fontsize=11)
ax.set_title("RTT CDF -- Local vs Hairpinned Rounds, PK-hosted Sites (Pooled)", fontsize=12)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_local_vs_hairpin_cdf.pdf", bbox_inches="tight")
plt.close()
print("wrote fig_local_vs_hairpin_cdf.pdf")
