#!/usr/bin/env python3
"""
CDF of traceroute hop count, separately for Pakistani, CDN and Abroad sites.

A trace counts only if the destination itself replied, so the hop count is a real path
length rather than how far the probe could see. Probe 62224 (H1, Transworld) is excluded:
11,866 of its 16,252 destination replies arrive at hop 4 with an RTT near 1,004 ms, which
is ICMP-error-generation delay rather than a four-hop path, and it drags the whole
distribution left.

    python paper/make_hopcount_cdf.py
"""
import collections
import gzip
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "experiments", "07_longitudinal_panel")
AN, RES = os.path.join(EXP, "analysis"), os.path.join(EXP, "results")
OUT = os.path.join(ROOT, "paper", "figures", "fig_hopcount_cdf.pdf")

INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
BLUE, GREEN, AMBER = "#2a78d6", "#1baf7a", "#eda100"
EXCLUDE = {1015491, 7764, 62224}      # two panel exclusions plus the filtered H1 probe

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "font.family": "sans-serif",
    "font.size": 9.5, "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
})

cls = pd.read_csv(os.path.join(AN, "targets_corrected.csv")) \
    .set_index("target")["cls_corrected"].to_dict()
meas = json.load(open(os.path.join(RES, "a", "measurements.json"), encoding="utf-8"))
msm = {v: k for k, v in meas["trace"].items()}
print("loading raw archive...")
arch = json.load(gzip.open(os.path.join(RES, "a", "raw_a_20260718_201113.json.gz"),
                           "rt", encoding="utf-8"))

by = collections.defaultdict(list)
for mid, rds in arch.items():
    if not mid.isdigit():
        continue
    c = cls.get(msm.get(int(mid)), "?")
    for rd in rds:
        if rd.get("prb_id") in EXCLUDE:
            continue
        dst = rd.get("dst_addr")
        for i, hh in enumerate(rd.get("result", [])):
            ips = [x.get("from") for x in hh.get("result", []) if x.get("from")]
            if dst and dst in ips:
                if i + 1 < 255:
                    by[c].append(i + 1)
                break

fig, ax = plt.subplots(figsize=(5.2, 3.2))
for name, colour in (("Pakistan", BLUE), ("CDN", AMBER), ("Abroad", GREEN)):
    v = np.sort(np.array(by[name]))
    if not len(v):
        continue
    ax.plot(v, np.arange(1, len(v) + 1) / len(v), color=colour, lw=2.2, zorder=3,
            label="%s (n=%s, median %d)" % (name.replace("Pakistan", "Pakistani"),
                                            format(len(v), ","), int(np.median(v))))
    print("  %-9s n=%7d  median %2d  p10 %2d  p90 %2d"
          % (name, len(v), np.median(v), np.percentile(v, 10), np.percentile(v, 90)))

ax.set_xlim(0, 25)
ax.set_ylim(0, 1.02)
ax.set_xlabel("Hop count to the destination")
ax.set_ylabel("Fraction of traces")
ax.legend(frameon=False, fontsize=8.4, loc="lower right")
fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
print("wrote %s" % os.path.relpath(OUT, ROOT))
