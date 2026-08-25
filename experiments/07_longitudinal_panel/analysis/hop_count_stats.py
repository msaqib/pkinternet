#!/usr/bin/env python3
"""
Median hop count per ISP and per site class, under the strict rule that a traceroute only
counts if the destination itself replied and the hop count is below 255.

Traces where the destination never answers give a path length that reflects how far the
probe could see, not how far the packet travelled. Excluding them removes the ICMP-filtered
probes from this statistic rather than explaining their short paths away.

Reports both the strict figure and the permissive one (last hop that replied, whether or
not it was the destination) so the effect of the filter is visible.

    python experiments/07_longitudinal_panel/analysis/hop_count_stats.py
"""
import collections
import gzip
import json
import os
import statistics as st

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RES = os.path.join(EXP, "results")
EXCLUDE = {1015491, 7764}


def main():
    m = pd.read_csv(os.path.join(HERE, "probe_label_map.csv")).set_index("probe_id")
    cls = pd.read_csv(os.path.join(HERE, "targets_corrected.csv")) \
        .set_index("target")["cls_corrected"].to_dict()
    meas = json.load(open(os.path.join(RES, "a", "measurements.json"), encoding="utf-8"))
    msm = {v: k for k, v in meas["trace"].items()}
    print("loading raw archive...")
    arch = json.load(gzip.open(os.path.join(RES, "a", "raw_a_20260718_201113.json.gz"),
                               "rt", encoding="utf-8"))

    strict_isp, loose_isp = collections.defaultdict(list), collections.defaultdict(list)
    strict_cls = collections.defaultdict(list)
    seen, kept = collections.Counter(), collections.Counter()

    for mid, rds in arch.items():
        if not mid.isdigit():
            continue
        tgt = msm.get(int(mid))
        c = cls.get(tgt, "?")
        for rd in rds:
            p = rd.get("prb_id")
            if p in EXCLUDE or p not in m.index:
                continue
            isp = m.loc[p].isp
            dst = rd.get("dst_addr")
            res = rd.get("result", [])
            seen[isp] += 1

            last, dst_hop = None, None
            for i, hh in enumerate(res):
                ips = [x.get("from") for x in hh.get("result", []) if x.get("from")]
                if not ips:
                    continue
                last = i + 1
                if dst and dst in ips and dst_hop is None:
                    dst_hop = i + 1
            if last:
                loose_isp[isp].append(last)
            # strict: destination replied, and the hop index is a real TTL below 255
            if dst_hop is not None and dst_hop < 255:
                strict_isp[isp].append(dst_hop)
                strict_cls[c].append(dst_hop)
                kept[isp] += 1

    L = {r.isp: r.label[0] for _, r in m.iterrows()}
    print("\nMEDIAN HOP COUNT, all 98 sites")
    print("%-5s %-11s %8s %8s %10s %9s"
          % ("ISP", "operator", "strict", "loose", "kept", "of total"))
    for isp in sorted(strict_isp, key=lambda k: st.median(strict_isp[k])):
        print("%-5s %-11s %8.0f %8.0f %10d %8.0f%%"
              % (L.get(isp, "?"), isp, st.median(strict_isp[isp]),
                 st.median(loose_isp[isp]), kept[isp], 100 * kept[isp] / seen[isp]))
    for isp in sorted(set(loose_isp) - set(strict_isp)):
        print("%-5s %-11s %8s %8.0f %10d %8.0f%%"
              % (L.get(isp, "?"), isp, "none", st.median(loose_isp[isp]),
                 0, 0.0))

    allv = [x for v in strict_isp.values() for x in v]
    print("\noverall strict median: %.0f  (%d rounds, %.0f%% of all traces retained)"
          % (st.median(allv), len(allv), 100 * len(allv) / sum(seen.values())))
    print("\nby site class, strict:")
    for k in sorted(strict_cls):
        print("   %-10s %2.0f   (n=%d)" % (k, st.median(strict_cls[k]), len(strict_cls[k])))


if __name__ == "__main__":
    main()
