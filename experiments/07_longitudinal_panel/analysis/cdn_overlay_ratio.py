#!/usr/bin/env python3
"""
Recompute the CDN latency ratio using the overlay floor defined in the Methodology.

    ratio(p,s,t) = r_{p,s,t} / min_q ( d_{p,q}/102 + r_0(q,s) )

r_0(q,s) is the lowest RTT probe q ever measured to site s; d_{p,q} is the great-circle
distance between probes p and q, so d_{p,q}/102 is the round-trip f-latency between them.
The floor is the better of reaching the site directly or tunnelling to another probe and
reusing its access.

Two variants are computed because the Methodology text and the arithmetic disagree:

  q_excl_p   q ranges over probes OTHER than p, as the text currently says
  q_incl_p   q ranges over all probes including p, with d_{p,p} = 0

Only the second is a floor. Excluding q = p forbids a probe from using its own direct
path, so a probe with strong local access beats its own floor; that produces ratios below
1, which is impossible by definition. Both are written so the difference is visible.

Replaces the ratio_vs_best column of cdn.csv, which was r divided by the global minimum
across all probes and carried no distance term at all.

    python experiments/07_longitudinal_panel/analysis/cdn_overlay_ratio.py
"""
import json
import math
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = 102.109      # km per ms of round-trip fibre: d/V2 = 2d/204.218


def km(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    x = (math.sin(math.radians(c - a) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def main():
    pxy = {int(k): (v["lat"], v["lon"]) for k, v in
           json.load(open(os.path.join(HERE, ".cache_probe_geo.json"), encoding="utf-8")).items()}
    d = pd.read_csv(os.path.join(HERE, "cdn.csv"))

    r0 = {(int(r.probe_id), r.site): r.min_rtt_ms for _, r in d.iterrows()}
    probes = sorted({p for p, _ in r0 if p in pxy})
    dist = {(a, b): (0.0 if a == b else km(pxy[a][0], pxy[a][1], pxy[b][0], pxy[b][1]))
            for a in probes for b in probes}

    excl, incl, old = [], [], []
    for _, r in d.iterrows():
        p = int(r.probe_id)
        if p not in pxy:
            excl.append(float("nan")); incl.append(float("nan")); old.append(float("nan"))
            continue
        peers = [q for q in probes if (q, r.site) in r0]
        fe = min(dist[(p, q)] / V2 + r0[(q, r.site)] for q in peers if q != p)
        fi = min(dist[(p, q)] / V2 + r0[(q, r.site)] for q in peers)
        excl.append(r.min_rtt_ms / fe)
        incl.append(r.min_rtt_ms / fi)
        old.append(r.min_rtt_ms / min(r0[(q, r.site)] for q in peers))

    d["ratio_overlay_q_excl_p"] = [round(x, 3) for x in excl]
    d["ratio_overlay_q_incl_p"] = [round(x, 3) for x in incl]
    d["ratio_vs_best_old"] = [round(x, 3) for x in old]
    out = os.path.join(HERE, "cdn_overlay.csv")
    d.to_csv(out, index=False)

    print("%d probe-CDN pairs\n" % len(d))
    print("%-24s %8s %8s %8s %8s %8s"
          % ("floor", "median", "p75", "p90", "max", "below 1"))
    for col, lab in (("ratio_vs_best_old", "old, global minimum"),
                     ("ratio_overlay_q_excl_p", "overlay, q != p"),
                     ("ratio_overlay_q_incl_p", "overlay, q incl p")):
        s = d[col].dropna()
        print("%-24s %8.2f %8.2f %8.2f %8.2f %8d"
              % (lab, s.median(), s.quantile(.75), s.quantile(.9), s.max(), int((s < 1).sum())))

    M = {"cybernet": "A", "fasttel": "B", "nayatel": "C", "orbit": "E",
         "ptcl": "F", "tes": "G", "transworld": "H"}
    print("\nMEDIAN RATIO PER ISP, the numbers \\S4.3 quotes")
    print("%-12s %-6s %10s %10s" % ("isp", "letter", "old", "overlay"))
    g = d.groupby("isp")[["ratio_vs_best_old", "ratio_overlay_q_incl_p"]].median()
    for isp, row in g.sort_values("ratio_overlay_q_incl_p").iterrows():
        print("%-12s %-6s %10.2f %10.2f"
              % (isp, "ISP " + M.get(isp, "?"), row.ratio_vs_best_old,
                 row.ratio_overlay_q_incl_p))
    print("\nwrote %s" % os.path.basename(out))


if __name__ == "__main__":
    main()
