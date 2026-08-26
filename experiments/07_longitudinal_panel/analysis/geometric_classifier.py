#!/usr/bin/env python3
"""
Geometric tromboning detector: replaces the flat 40 ms RTT gate with a per-hop
physics check against the hop's own geolocated coordinates.

Preconditions, a hop failing any of these is skipped and carries no information:
  - it replied
  - it is a public address
  - its RTT is <= 500 ms (above that, ICMP-error-generation artifact)

Rules, a hop is CONFIRMED FOREIGN only if both hold:
  1. location  its coordinates fall outside the Pakistan boundary polygon
  2. physics   RTT >= 2 * geodesic(probe, hop) / v_fibre

A hop with no coordinates is not confirmed foreign. A round is tromboned if at
least one hop is confirmed foreign. Exit country is the country polygon that
contains the coordinates, not the registration record.

    python experiments/07_longitudinal_panel/analysis/geometric_classifier.py
"""
import collections
import gzip
import json
import math
import os

import pandas as pd
from shapely.geometry import Point, shape
from shapely.prepared import prep

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RES = os.path.join(EXP, "results")
GEO = os.path.join(EXP, "..", "..", "data", "ne50_countries.geojson")
PK_TOLERANCE_DEG = 0.25   # ~25 km, absorbs Natural Earth coastline simplification
                          # (Karachi city centre sits 0.2 km outside the raw polygon)

V_FIBER = 204.218          # km/ms
QUEUE_CEIL = 500.0         # ms
EXCLUDE_PROBES = {1015491, 7764}
LEGACY_ARTIFACT = {"6327", "174"}   # Shaw, Cogent, for the redundancy check only


def haversine_km(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    x = (math.sin(math.radians(c - a) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def load_countries():
    fc = json.load(open(GEO, encoding="utf-8"))
    raw = {f["properties"]["iso"]: shape(f["geometry"]) for f in fc["features"]}
    prepped = {k: prep(v) for k, v in raw.items()}
    pk_buffered = prep(raw["PAK"].buffer(PK_TOLERANCE_DEG))
    return prepped, pk_buffered


def main():
    countries, pk_poly = load_countries()

    hg = pd.read_csv(os.path.join(HERE, "hop_geo.csv"))
    hopxy, hopasn = {}, {}
    for _, r in hg.iterrows():
        if pd.notna(r.lat) and pd.notna(r.lon):
            hopxy[r.ip] = (float(r.lat), float(r.lon))
        hopasn[r.ip] = str(int(r.asn)) if pd.notna(r.asn) else ""

    pxy = {int(k): (v["lat"], v["lon"]) for k, v in
           json.load(open(os.path.join(HERE, ".cache_probe_geo.json"), encoding="utf-8")).items()}

    cls = pd.read_csv(os.path.join(HERE, "targets_corrected.csv")).set_index("target")["cls_corrected"]
    pk_targets = set(cls[cls == "Pakistan"].index)
    meas = json.load(open(os.path.join(RES, "a", "measurements.json"), encoding="utf-8"))
    msm_of = {v: k for k, v in meas["trace"].items()}
    targets_meta = pd.read_csv(os.path.join(EXP, "targets.csv")).set_index("target")
    sector_of = targets_meta["cisa_sector"].to_dict()

    # resolve each geolocated hop to the country polygon that contains it
    hop_cc, outside = {}, {}
    for ip, (la, lo) in hopxy.items():
        p = Point(lo, la)
        outside[ip] = not pk_poly.covers(p)
        hop_cc[ip] = next((iso for iso, poly in countries.items() if poly.covers(p)), "??")

    print("loading raw archive...")
    arch = json.load(gzip.open(os.path.join(RES, "a", "raw_a_20260718_201113.json.gz"),
                               "rt", encoding="utf-8"))

    rows = []
    cov = collections.Counter()
    artifact_still_needed = collections.Counter()
    for mid, rds in arch.items():
        if not mid.isdigit():
            continue
        tgt = msm_of.get(int(mid))
        if tgt not in pk_targets:
            continue
        for rd in rds:
            prb = rd.get("prb_id")
            if prb in EXCLUDE_PROBES or prb not in pxy:
                continue
            hops = []
            for hh in rd.get("result", []):
                p = hh.get("result", [])
                ip = next((x.get("from") for x in p if x.get("from")), None)
                rr = [x["rtt"] for x in p if isinstance(x.get("rtt"), (int, float))]
                hops.append((ip, min(rr) if rr else None))
            if not hops:
                continue

            exit_cc, exit_ip = "", ""
            for ip, rtt in hops:
                if not ip or rtt is None or rtt > QUEUE_CEIL:
                    continue
                if ip.startswith(("192.168.", "10.", "172.16.", "172.17.", "172.18.",
                                  "172.19.", "172.2", "172.3")):
                    continue
                if ip not in hopxy:
                    cov["no_coords"] += 1
                    continue
                cov["located"] += 1
                if not outside[ip]:
                    continue
                d = haversine_km(pxy[prb][0], pxy[prb][1], hopxy[ip][0], hopxy[ip][1])
                if rtt >= 2 * d / V_FIBER:
                    exit_cc, exit_ip = hop_cc[ip], ip
                    if hopasn.get(ip) in LEGACY_ARTIFACT:
                        artifact_still_needed[hopasn[ip]] += 1
                    break
            rows.append({"target": tgt, "probe_id": prb, "sector": sector_of.get(tgt, "?"),
                         "trombone": bool(exit_cc), "exit_cc": exit_cc, "exit_ip": exit_ip})

    d = pd.DataFrame(rows)
    n, t = len(d), int(d.trombone.sum())
    print(f"\nPK-class rounds       : {n:,}")
    print(f"confirmed tromboned   : {t:,}  ({100*t/n:.2f}%)   [flat-gate detector: 4,170 / 5.52%]")
    print(f"hop coverage          : {cov['located']:,} located, {cov['no_coords']:,} without coords "
          f"({100*cov['no_coords']/(cov['located']+cov['no_coords']):.0f}% unlocatable)")
    print(f"Shaw/Cogent hops that still pass the physics rule: "
          f"{dict(artifact_still_needed) or 'none, the artifact list is redundant'}")
    print("\nexit country, from coordinates:")
    for cc, c in d[d.trombone].exit_cc.value_counts().items():
        print(f"   {cc:<4} {c:>6,}")
    print("\nby sector:")
    g = d.groupby("sector")["trombone"].agg(n="size", k="sum")
    g["rate"] = (100 * g.k / g.n).round(2)
    print(g.sort_values("rate", ascending=False).to_string())

    out = os.path.join(HERE, "geometric_classified_rounds.csv")
    d.to_csv(out, index=False)
    print(f"\nwrote {os.path.basename(out)}")


if __name__ == "__main__":
    main()
