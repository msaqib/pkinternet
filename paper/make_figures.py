#!/usr/bin/env python3
"""
Generate the paper figures from the committed data (Exp 4.1 census + Exp 1.4 hosting).
Palette = the validated dataviz reference (CVD-safe categorical slots); bars carry direct
labels so identity is never colour-alone.

    python paper/make_figures.py      # -> paper/figures/*.png
"""
import os, csv, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "paper", "figures"); os.makedirs(FIG, exist_ok=True)
CENSUS = os.path.join(ROOT, "experiments/04.1_small_isp_tromboning/results/run_20260627_192918/census_20260627_192918.csv")
HOST = os.path.join(ROOT, "experiments/01.4_pk100_hosting/results/combined_hosting.csv")

# validated reference palette (light mode)
BLUE, AQUA, YELLOW, GREEN, VIOLET, RED, MAGENTA, ORANGE = (
    "#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948", "#e87ba4", "#eb6834")
INK, INK2, MUTED, GRID, BASE, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": BASE, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "font.family": "sans-serif",
    "font.size": 11, "axes.titlesize": 12.5, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
})

def load(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))

rows = load(CENSUS)

# ---- Fig 1: CDF of max path RTT, local vs hairpinned ----
def rtts(status):
    out = []
    for r in rows:
        if r["status"] == status and r["max_rtt"]:
            try: out.append(float(r["max_rtt"]))
            except ValueError: pass
    return np.sort(np.array(out))
loc, tro = rtts("local"), rtts("trombone")
fig, ax = plt.subplots(figsize=(6.2, 4.0))
for data, color, lab in [(loc, BLUE, f"local (n={len(loc)})"), (tro, ORANGE, f"hairpinned (n={len(tro)})")]:
    y = np.arange(1, len(data) + 1) / len(data)
    ax.plot(data, y, color=color, lw=2, label=lab)
ax.axvline(45, color=MUTED, lw=1, ls="--")
ax.text(46, 0.06, "45 ms\ndetector\nthreshold", color=MUTED, fontsize=8, va="bottom")
ax.set_xlim(0, 320); ax.set_ylim(0, 1)
ax.set_xlabel("maximum path RTT (ms)"); ax.set_ylabel("cumulative fraction of traces")
ax.set_title("Path RTT: local vs hairpinned traces", loc="left")
ax.legend(frameon=False, loc="lower right")
ax.grid(axis="x", visible=False)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig_rtt_cdf.png"), dpi=200); plt.close(fig)

# ---- Fig 2: trombone rate by source probe ----
by = collections.defaultdict(lambda: [0, 0])   # source -> [trombone, total]
for r in rows:
    by[r["source"]][1] += 1
    if r["status"] == "trombone": by[r["source"]][0] += 1
items = sorted(((s, t / n * 100, n) for s, (t, n) in by.items()), key=lambda x: x[1])
labels = [s for s, _, _ in items]; vals = [p for _, p, _ in items]
fig, ax = plt.subplots(figsize=(6.2, 3.8))
ax.barh(labels, vals, color=BLUE, height=0.62)
for i, (s, p, n) in enumerate(items):
    ax.text(p + 0.6, i, f"{p:.0f}%", va="center", color=INK2, fontsize=9)
ax.set_xlim(0, max(vals) * 1.15); ax.set_xlabel("share of traces that hairpin abroad (%)")
ax.set_title("Tromboning rate by source ISP / probe", loc="left")
ax.grid(axis="y", visible=False)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig_trombone_by_source.png"), dpi=200); plt.close(fig)

# ---- Fig 3: trombones by transit (LDI) and by exit country ----
tro_rows = [r for r in rows if r["status"] == "trombone"]
ASN = {"9541": "Cybernet", "174": "Cogent", "9557": "AS9557", "17911": "AS17911",
       "23966": "AS23966", "?": "unresolved"}
tr = collections.Counter(ASN.get(r["transit"], r["transit"]) for r in tro_rows)
cc = collections.Counter((r["exit_cc"] or "?") for r in tro_rows)
cc_named = {"CN": "China", "US": "USA", "SG": "Singapore", "AE": "UAE", "SE": "Sweden",
            "ID": "Indonesia", "NL": "Neth.", "?": "unresolved", "": "unresolved"}
fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.9))
for ax, counter, title, namer in [
    (axes[0], tr, "Transit that hands off abroad", lambda k: k),
    (axes[1], cc, "Foreign exit country", lambda k: cc_named.get(k, k))]:
    top = counter.most_common(7)[::-1]
    labs = [namer(k) for k, _ in top]; vs = [v for _, v in top]
    ax.barh(labs, vs, color=BLUE, height=0.62)
    for i, v in enumerate(vs):
        ax.text(v + max(vs) * 0.01, i, str(v), va="center", color=INK2, fontsize=9)
    ax.set_xlim(0, max(vs) * 1.15); ax.set_title(title, loc="left", fontsize=11.5)
    ax.set_xlabel("trombone traces"); ax.grid(axis="y", visible=False)
fig.suptitle(f"Where the {len(tro_rows)} hairpins go (Exp 4.1)", x=0.01, ha="left", fontsize=12.5)
fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(os.path.join(FIG, "fig_trombone_transit_exit.png"), dpi=200); plt.close(fig)

# ---- Fig 4: hosting split (Exp 1.4 combined) ----
h = load(HOST)
cat = collections.Counter(x["category"] for x in h)
order = [("Pakistan", GREEN), ("CDN", BLUE), ("Abroad", ORANGE)]
tot = sum(cat.values())
labs = [c for c, _ in order]; vs = [cat.get(c, 0) for c, _ in order]; cols = [col for _, col in order]
fig, ax = plt.subplots(figsize=(6.2, 2.9))
ax.barh(labs[::-1], vs[::-1], color=cols[::-1], height=0.6)
for i, (c, _) in enumerate(order[::-1]):
    v = cat.get(c, 0); ax.text(v + tot * 0.01, i, f"{v}  ({v/tot*100:.0f}%)", va="center", color=INK2, fontsize=9)
ax.set_xlim(0, max(vs) * 1.18); ax.set_xlabel("number of sites")
ax.set_title(f"Where the top-{tot} Pakistani sites are hosted", loc="left")
ax.grid(axis="y", visible=False)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig_hosting_split.png"), dpi=200); plt.close(fig)

print("wrote 4 figures to paper/figures/:")
print(f"  fig_rtt_cdf.png            local n={len(loc)}, hairpinned n={len(tro)}")
print(f"  fig_trombone_by_source.png {len(items)} sources")
print(f"  fig_trombone_transit_exit.png  {len(tro_rows)} trombones")
print(f"  fig_hosting_split.png      {dict(cat)}")
