#!/usr/bin/env python3
"""
Figure 1 of running_draft.tex: RIPE Atlas vantage points, labelled with the
anonymised probe IDs used in Table 3 (tab:probes).

Probe-to-city assignment is Table 3, i.e. the deployment record, NOT the RIPE
Atlas platform coordinates. Two probes differ between the two: 65892 (C2) and
64078 (G1) are recorded at Lahore on the platform but were deployed to
Islamabad and Rawalpindi respectively. Table 3 wins here.

Basemap: data/ne50_pk_region.geojson, Natural Earth 50m admin-0 boundaries
trimmed to this frame (public domain, naturalearthdata.com).

    python paper/make_probe_map.py            # writes all four variants
    python paper/make_probe_map.py a          # writes variant a only

Variants:
    a  city bubble sized by probe count, probe labels listed beneath
    b  one labelled dot per probe, fanned out around its city
    c  ISP letters inside the bubble
    d  plain numbered bubbles, probe labels in a legend block below the map
    e  plain numbered bubbles, probe labels in an inset panel inside the map
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "paper", "figures")
GEO = os.path.join(ROOT, "data", "ne50_pk_region.geojson")
os.makedirs(FIG, exist_ok=True)

BLUE = "#2a78d6"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, SURF = "#e1e0d9", "#fcfcfb"
PK_FILL, PK_EDGE = "#eef1ea", "#4a4a46"
NB_FILL, NB_EDGE = "#e6e5df", "#c3c2b7"

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "font.family": "sans-serif",
    "font.size": 10.5, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
})

LON0, LON1, LAT0, LAT1 = 59.5, 78.5, 22.5, 38.5

# ---- Table 3 (tab:probes): city -> (lat, lon, [probe labels], bubble offset (dlon, dlat)) ----
# Offsets pull the bubble off the true position so labels do not collide; a leader
# line joins each bubble back to its real coordinate.
CITIES = {
    "Karachi":    (24.86, 67.01, ["A2", "A3", "F1", "G2"], ( 0.0, -0.5)),
    "Haripur":    (34.00, 72.93, ["A1"],                   ( 2.9,  0.5)),
    "Islamabad":  (33.68, 73.05, ["B1", "C1", "C2"],       (-3.9,  2.2)),
    "Rawalpindi": (33.60, 73.05, ["G1"],                   (-6.8, -0.5)),
    "Mianwali":   (32.57, 71.53, ["F2"],                   (-2.6, -1.9)),
    "Lahore":     (31.52, 74.36, ["D1", "F3", "H1", "I1"], ( 2.1, -0.5)),
    "Faisalabad": (31.40, 73.12, ["E1"],                   ( 0.4, -3.4)),
}
# F3 is probe 7764 (PTCL Lahore). It is ICMP-filtered: all 16,721 of its traceroute
# rows have a null hop_count, so it contributes to ping/RTT results only, not to the
# traceroute-based tromboning analysis. 15 probes measured, 14 usable for traceroute.

NEIGHBOURS = {
    "AFG": ("Afghanistan", 64.4, 34.8),
    "IRN": ("Iran", 61.4, 28.8),
    "IND": ("India", 76.9, 25.6),
    "CHN": ("China", 77.3, 36.6),
}


def draw_basemap(ax):
    fc = json.load(open(GEO, encoding="utf-8"))
    for feat in fc["features"]:
        iso = feat["properties"]["iso"]
        is_pk = iso == "PAK"
        geom = feat["geometry"]
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        for poly in polys:
            for i, ring in enumerate(poly):
                ax.add_patch(MplPolygon(
                    ring, closed=True, zorder=1 if not is_pk else 2,
                    facecolor=(PK_FILL if is_pk else NB_FILL) if i == 0 else SURF,
                    edgecolor=PK_EDGE if is_pk else NB_EDGE,
                    linewidth=1.1 if is_pk else 0.6,
                ))
    for iso, (name, lon, lat) in NEIGHBOURS.items():
        ax.text(lon, lat, name, fontsize=9, style="italic", color=MUTED,
                ha="center", va="center", zorder=3)
    ax.set_xlim(LON0, LON1)
    ax.set_ylim(LAT0, LAT1)
    ax.set_xlabel("longitude ($^\\circ$E)")
    ax.set_ylabel("latitude ($^\\circ$N)")
    ax.set_aspect(1.13)


def bubble(ax, lon, lat, n, text=None, r_scale=1.0):
    size = (250 + 165 * n) * r_scale
    ax.scatter([lon], [lat], s=size, color=BLUE, alpha=0.9,
               edgecolor=INK, linewidth=0.8, zorder=6)
    if text:
        ax.text(lon, lat, text, fontsize=9.0 if len(text) < 4 else 7.6,
                color="white", ha="center", va="center",
                fontweight="bold", zorder=7)


def leader(ax, lon, lat, dlon, dlat):
    """Small true-position dot plus a line to the offset bubble."""
    if dlon == 0 and dlat == 0:
        return lon, lat
    ax.scatter([lon], [lat], s=9, color=INK, zorder=5)
    ax.plot([lon, lon + dlon], [lat, lat + dlat], color=MUTED,
            linewidth=0.7, zorder=4)
    return lon + dlon, lat + dlat


def new_fig(with_legend=False):
    if with_legend:
        fig, (ax, axl) = plt.subplots(
            2, 1, figsize=(6.6, 7.6), gridspec_kw={"height_ratios": [3.4, 1.0]})
        axl.axis("off")
        return fig, ax, axl
    fig, ax = plt.subplots(figsize=(6.6, 6.0))
    return fig, ax, None


def finish(fig, name, title):
    fig.axes[0].set_title(title, loc="left", fontsize=12, pad=10, color="black")
    fig.tight_layout()
    out = os.path.join(FIG, name)
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {os.path.relpath(out, ROOT)}")


TITLE = "Vantage points: 15 probes across 7 cities"


def variant_a():
    """City bubble sized by probe count, probe labels listed beneath. Full-black text."""
    fig, ax, _ = new_fig()
    draw_basemap(ax)
    for city, (lat, lon, labels, (dlon, dlat)) in CITIES.items():
        bx, by = leader(ax, lon, lat, dlon, dlat)
        bubble(ax, bx, by, len(labels), str(len(labels)))
        ax.text(bx, by - 0.95, f"{city}\n{', '.join(labels)}",
                fontsize=8.2, color="black", ha="center", va="top", zorder=7,
                linespacing=1.35)
    # axis furniture black too
    ax.xaxis.label.set_color("black")
    ax.yaxis.label.set_color("black")
    ax.tick_params(colors="black")
    finish(fig, "fig_probe_map_a.png", TITLE)


def variant_b():
    """One labelled dot per probe, fanned out around its city."""
    import math
    fig, ax, _ = new_fig()
    draw_basemap(ax)
    for city, (lat, lon, labels, (dlon, dlat)) in CITIES.items():
        cx, cy = lon + dlon, lat + dlat
        if dlon or dlat:
            ax.scatter([lon], [lat], s=9, color=INK, zorder=5)
            ax.plot([lon, cx], [lat, cy], color=MUTED, linewidth=0.7, zorder=4)
        n = len(labels)
        rad = 0.0 if n == 1 else 0.72
        for i, lab in enumerate(labels):
            ang = math.pi / 2 - 2 * math.pi * i / n
            px, py = cx + rad * math.cos(ang) * 1.15, cy + rad * math.sin(ang)
            ax.scatter([px], [py], s=190, color=BLUE, alpha=0.9,
                       edgecolor=INK, linewidth=0.7, zorder=6)
            ax.text(px, py, lab, fontsize=7.0, color="white", ha="center",
                    va="center", fontweight="bold", zorder=7)
        ax.text(cx, cy - rad - 0.75, city, fontsize=8.4, color=INK2,
                ha="center", va="top", zorder=7)
    finish(fig, "fig_probe_map_b.png", TITLE)


def variant_c():
    """ISP letters inside the bubble."""
    fig, ax, _ = new_fig()
    draw_basemap(ax)
    for city, (lat, lon, labels, (dlon, dlat)) in CITIES.items():
        bx, by = leader(ax, lon, lat, dlon, dlat)
        letters = " ".join(lab[0] for lab in labels)
        bubble(ax, bx, by, len(labels), letters, r_scale=1.35)
        ax.text(bx, by - 1.05, city, fontsize=8.4, color=INK2,
                ha="center", va="top", zorder=7)
    finish(fig, "fig_probe_map_c.png", TITLE)


def variant_d():
    """Plain numbered bubbles, probe labels in a legend block below."""
    fig, ax, axl = new_fig(with_legend=True)
    draw_basemap(ax)
    for city, (lat, lon, labels, (dlon, dlat)) in CITIES.items():
        bx, by = leader(ax, lon, lat, dlon, dlat)
        bubble(ax, bx, by, len(labels), str(len(labels)))
        ax.text(bx, by - 0.95, city, fontsize=8.4, color=INK2,
                ha="center", va="top", zorder=7)
    rows = sorted(CITIES.items(), key=lambda kv: (-len(kv[1][2]), kv[0]))
    tbl = axl.table(
        cellText=[[c, str(len(l)), ", ".join(l)] for c, (_, _, l, _) in rows],
        colLabels=["City", "Probes", "Vantages (Table 3 labels)"],
        cellLoc="left", colLoc="left", loc="upper center",
        colWidths=[0.26, 0.13, 0.45],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.4)
    tbl.scale(1, 1.28)
    for (r, _), cell in tbl.get_celld().items():
        cell.set_linewidth(0.4)
        cell.set_edgecolor(GRID)
        if r == 0:
            cell.set_text_props(fontweight="bold")
            cell.set_facecolor("#eeeeea")
    finish(fig, "fig_probe_map_d.png", TITLE)


def variant_e():
    """Plain numbered bubbles, probe labels in a compact inset panel, top left."""
    fig, ax, _ = new_fig()
    draw_basemap(ax)
    for city, (lat, lon, labels, (dlon, dlat)) in CITIES.items():
        bx, by = leader(ax, lon, lat, dlon, dlat)
        bubble(ax, bx, by, len(labels), str(len(labels)))
        ax.text(bx, by - 0.95, city, fontsize=8.4, color=INK2,
                ha="center", va="top", zorder=7)

    rows = sorted(CITIES.items(), key=lambda kv: (-len(kv[1][2]), kv[0]))
    w = max(len(c) for c, _ in rows)
    lines = [f"{'City'.ljust(w)}  n  Vantages"]
    lines += [f"{c.ljust(w)}  {len(l)}  {', '.join(l)}" for c, (_, _, l, _) in rows]
    ax.text(0.015, 0.985, "\n".join(lines),
            transform=ax.transAxes, ha="left", va="top", zorder=9,
            fontsize=6.6, family="monospace", color=INK2, linespacing=1.5,
            bbox=dict(boxstyle="round,pad=0.45", facecolor="white",
                      edgecolor=GRID, linewidth=0.7, alpha=0.94))
    finish(fig, "fig_probe_map_e.png", TITLE)


def variant_f():
    """Single-panel map with the Table 3 roster as an inset panel, top left."""
    # Re-fan the Haripur/Islamabad/Rawalpindi cluster to the right so the top-left
    # corner is free for the roster. Keys must match CITIES.
    offsets = {
        "Karachi":    ( 0.0, -0.5),
        "Haripur":    ( 2.9,  1.6),
        "Islamabad":  ( 1.0,  3.4),
        "Rawalpindi": ( 3.4, -0.6),
        "Mianwali":   (-1.4, -2.1),
        "Lahore":     ( 2.1, -0.5),
        "Faisalabad": ( 0.4, -3.4),
    }
    fig, ax = plt.subplots(figsize=(5.6, 5.2))
    draw_basemap(ax)
    for t in list(ax.texts):          # drop the neighbour labels that clash
        if t.get_text() in ("Afghanistan", "Iran"):
            t.remove()
    ax.text(63.2, 30.6, "Iran", fontsize=9, style="italic", color=MUTED,
            ha="center", va="center", zorder=3)
    ax.text(63.9, 33.1, "Afghanistan", fontsize=8, style="italic", color=MUTED,
            ha="center", va="center", zorder=3)

    for city, (lat, lon, labels, _) in CITIES.items():
        dlon, dlat = offsets[city]
        bx, by = leader(ax, lon, lat, dlon, dlat)
        bubble(ax, bx, by, len(labels), str(len(labels)))
        ax.text(bx, by - 0.95, city, fontsize=8.6, color="black",
                ha="center", va="top", zorder=7)
    ax.xaxis.label.set_color("black")
    ax.yaxis.label.set_color("black")
    ax.tick_params(colors="black")

    by_isp = {}
    for city, (_, _, labels, _) in CITIES.items():
        for lab in labels:
            by_isp.setdefault(lab[0], []).append((lab, city))
    rows = []
    for isp in sorted(by_isp):
        items = sorted(by_isp[isp])
        seen = []
        for _, c in items:
            if c not in seen:
                seen.append(c)
        cities = ", ".join(
            c if sum(1 for _, x in items if x == c) == 1
            else c + " x" + str(sum(1 for _, x in items if x == c))
            for c in seen)
        rows.append("%-2s %-26s %s" % (isp, cities, ", ".join(p for p, _ in items)))
    NL = chr(10)
    body = (NL.join(["%-2s %-26s %s" % ("", "Cities", "Probes")] + rows))
    ax.text(0.015, 0.985, body, transform=ax.transAxes, ha="left", va="top",
            zorder=9, fontsize=6.4, family="monospace", color="black",
            linespacing=1.42,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor=INK2, linewidth=0.7, alpha=0.95))
    ax.text(0.985, 0.018, "F3 is retained for ping analysis only.",
            transform=ax.transAxes, ha="right", va="bottom", zorder=9,
            fontsize=6.4, style="italic", color=INK2)
    finish(fig, "fig_probe_map_f.png", TITLE)


VARIANTS = {"a": variant_a, "b": variant_b, "c": variant_c,
            "d": variant_d, "e": variant_e, "f": variant_f}

if __name__ == "__main__":
    which = sys.argv[1:] or list(VARIANTS)
    for k in which:
        VARIANTS[k]()
