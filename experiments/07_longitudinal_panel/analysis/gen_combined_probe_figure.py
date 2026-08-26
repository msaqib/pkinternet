#!/usr/bin/env python3
"""
Combine the existing probe map (fig_probe_map.png) and the probe roster into a
single, genuinely composited image, map on top, roster table rendered
underneath, both baked into one PNG, not a map image with a separate LaTeX
tabular stacked below it in the same float.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER_FIGS = os.path.join(HERE, "..", "..", "..", "paper", "figures")

MAP_PATH = os.path.join(PAPER_FIGS, "fig_probe_map.png")

ROWS = [
    ("Cybernet (9541)", "Haripur", "1016036"),
    ("", "Karachi", "1016143"),
    ("", "Karachi", "1016154"),
    ("Fasttel (150683)", "Islamabad", "1014872"),
    ("Nayatel (23674)", "Islamabad", "60223"),
    ("", "Lahore", "65892"),
    ("Nova (136174)", "Lahore", "1015679"),
    ("Orbit (151983)", "Faisalabad", "64535"),
    ("PTCL (17557)", "Karachi", "1016126"),
    ("", "Mianwali", "1016393"),
    ("TES (135407)", "Rawalpindi", "64078"),
    ("", "Karachi", "64722"),
    ("Transworld (38193)", "Lahore", "62224"),
    ("Zcom (152605)", "Lahore", "7613"),
]

img = mpimg.imread(MAP_PATH)
h, w = img.shape[0], img.shape[1]

fig = plt.figure(figsize=(6.0, 6.0 * (h / w) + 3.6))
gs = fig.add_gridspec(2, 1, height_ratios=[h / w, 3.6 / (6.0 * (h / w))])

ax_map = fig.add_subplot(gs[0])
ax_map.imshow(img)
ax_map.axis("off")

ax_tbl = fig.add_subplot(gs[1])
ax_tbl.axis("off")
table = ax_tbl.table(
    cellText=[[isp, city, pid] for isp, city, pid in ROWS] + [["Total 9 ISPs", "7 cities", "14 probes"]],
    colLabels=["ISP (ASN)", "City", "Probe ID"],
    cellLoc="left",
    colLoc="left",
    loc="center",
)
table.auto_set_font_size(False)
table.set_fontsize(8)
table.scale(1, 1.25)
for (row, col), cell in table.get_celld().items():
    cell.set_linewidth(0.4)
    if row == 0:
        cell.set_text_props(fontweight="bold")
        cell.set_facecolor("#dddddd")
    if row == len(ROWS) + 1:
        cell.set_text_props(fontweight="bold")

plt.tight_layout()
out_path = os.path.join(PAPER_FIGS, "fig_probe_panel.png")
plt.savefig(out_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"wrote {out_path}")
