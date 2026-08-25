#!/usr/bin/env python3
"""
Independent re-run of RQ1's IXP-crossing scan, straight from the raw archive.

Answers two questions the paper depends on and prints both:

  1. Do the Data Cleaning row counts reproduce? (218,480 raw / 200,292 cleaned /
     75,600 Pakistani-class, for the final 98-site sample.)
  2. Does any hop in any traceroute fall inside either exchange's peering LAN?
     PIE Karachi  58.181.127.0/24
     PKIX Lahore  100.128.0.0/24
     (Prefixes from experiments/08_CDN/CheckPIE.py and CheckPKIX.py.)

Reports both the whole archive and the final 98-site sample, since the archive
still contains toptop.net and youth.cn, the two sites dropped from the sample
(see analysis/evidence_sweep_findings.md section 5).

Read-only: reads the gzipped archive and two CSVs, writes nothing.

    python experiments/07_longitudinal_panel/analysis/ixp_crossing_scan.py
"""
import gzip
import ipaddress
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RESULTS = os.path.join(EXP, "results")

PEERING_LANS = {
    "PIE Karachi": ipaddress.ip_network("58.181.127.0/24"),
    "PKIX Lahore": ipaddress.ip_network("100.128.0.0/24"),
}

EXCLUDE_PROBES = {1015491, 7764}   # mislabelled duplicate; no valid traceroute responses
DROPPED_SITES = {"toptop.net", "youth.cn"}
RAW = os.path.join(RESULTS, "a", "raw_a_20260718_201113.json.gz")


def main():
    meas = json.load(open(os.path.join(RESULTS, "a", "measurements.json"), encoding="utf-8"))
    msm_to_target = {v: k for k, v in meas["trace"].items()}

    cls = pd.read_csv(os.path.join(HERE, "targets_corrected.csv")).set_index("target")["cls_corrected"]
    pk_targets = set(cls[cls == "Pakistan"].index)
    print(f"Pakistani-class targets (targets_corrected.csv): {len(pk_targets)}")

    print("loading raw archive...")
    with gzip.open(RAW, "rt", encoding="utf-8") as f:
        archive = json.load(f)

    # counters: [whole archive, final 98-site sample]
    raw = [0, 0]
    cleaned = [0, 0]
    pk = [0, 0]
    hops_seen = [0, 0]
    routers = [set(), set()]
    lan_hits = {name: [0, 0] for name in PEERING_LANS}

    for msm_id_str, rounds in archive.items():
        if not msm_id_str.isdigit():
            continue
        target = msm_to_target.get(int(msm_id_str))
        scopes = (0,) if target in DROPPED_SITES else (0, 1)
        is_pk = target in pk_targets

        for rd in rounds:
            for s in scopes:
                raw[s] += 1
            if rd.get("prb_id") in EXCLUDE_PROBES:
                continue
            ips = [
                next((p.get("from") for p in hop.get("result", []) if p.get("from")), None)
                for hop in rd.get("result", [])
            ]
            if not ips:
                continue
            for s in scopes:
                cleaned[s] += 1
                if is_pk:
                    pk[s] += 1
            for ip in ips:
                if not ip:
                    continue
                for s in scopes:
                    hops_seen[s] += 1
                    routers[s].add(ip)
                try:
                    addr = ipaddress.ip_address(ip)
                except ValueError:
                    continue
                for name, net in PEERING_LANS.items():
                    if addr in net:
                        for s in scopes:
                            lan_hits[name][s] += 1

    labels = ("whole archive (100 sites)", "final sample (98 sites)")
    for s, label in enumerate(labels):
        print()
        print(f"--- {label} ---")
        print(f"  raw traceroute rounds:                 {raw[s]:,}")
        print(f"  after excluding {sorted(EXCLUDE_PROBES)}, non-empty: {cleaned[s]:,}")
        print(f"  of those, Pakistani-class:             {pk[s]:,}")
        print(f"  distinct responding routers:           {len(routers[s]):,}")
        print(f"  responding hop observations:           {hops_seen[s]:,}")
        for name, net in PEERING_LANS.items():
            print(f"  hops inside {name} {net}: {lan_hits[name][s]}")


if __name__ == "__main__":
    main()
