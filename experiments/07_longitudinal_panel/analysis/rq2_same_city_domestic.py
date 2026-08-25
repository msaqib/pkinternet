#!/usr/bin/env python3
"""
New-RQ2 same-city domestic-content cut: median RTT and tromboning rate to
Pakistani-hosted sites, per ISP, held to a single city, mirroring the same-city
CDN comparison already computed in rq2_rq3_rq4_final.py's city_stats() (RQ4).

Uses the raw min-of-N ping RTT (results/b panel CSV, same source and EXCLUDE
set as rq2_rq3_rq4_final.py) rather than ratio_corrected.csv, since that file
drops any probe-site pair under 30km (the ratio denominator blows up there),
which would silently exclude many of the exact short-distance same-city pairs
this comparison needs. Tromboning rate comes from final_classified_rounds.csv,
same source as every other RQ1/RQ3 number.

Run final_classifier.py first (produces final_classified_rounds.csv).
Writes rq2_same_city_domestic.csv here.
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RESULTS = os.path.join(EXP, "results")

EXCLUDE = {1015491, 7764}

KARACHI = {1016126: "PTCL", 1016143: "Cybernet", 1016154: "Cybernet", 64722: "TES"}
LAHORE = {1015679: "Nova", 62224: "Transworld", 7613: "Zcom", 65892: "Nayatel"}

trace = pd.read_csv(os.path.join(HERE, "final_classified_rounds.csv"))
pk_targets = set(trace.target.unique())

ping = pd.read_csv(os.path.join(RESULTS, "b", "panel_20260718_200355.csv"))
ping = ping[ping["kind"] == "ping"].dropna(subset=["rtt_min"]).copy()
ping = ping[~ping["probe_id"].isin(EXCLUDE)]
ping = ping[ping.target.isin(pk_targets)].copy()

min_rtt = ping.groupby(["probe_id", "target"])["rtt_min"].min().reset_index()


def rtt_stats(probes, label):
    d = min_rtt[min_rtt.probe_id.isin(probes)].copy()
    d["isp_label"] = d.probe_id.map(probes)
    g = d.groupby("isp_label").agg(
        median_rtt=("rtt_min", "median"),
        n_pairs=("rtt_min", "size"),
    ).sort_values("median_rtt")
    print(f"\n{label} -- median RTT to Pakistani-hosted sites, by ISP:")
    print(g.round(1))
    if len(g) > 1:
        print(f"spread: {(g.median_rtt.max() / g.median_rtt.min()):.1f}x")
    return g


def trombone_stats(probes, label):
    d = trace[trace.probe_id.isin(probes)].copy()
    d["isp_label"] = d.probe_id.map(probes)
    g = d.groupby("isp_label").agg(
        trombone_rate=("trombone", "mean"),
        n_rounds=("trombone", "size"),
    ).sort_values("trombone_rate")
    g["trombone_rate"] = (g["trombone_rate"] * 100).round(1)
    print(f"\n{label} -- tromboning rate to Pakistani-hosted sites, by ISP:")
    print(g)
    return g


results = []
for probes, label in [(KARACHI, "Karachi"), (LAHORE, "Lahore")]:
    r = rtt_stats(probes, label)
    t = trombone_stats(probes, label)
    combo = r.join(t, how="outer")
    combo["city"] = label
    results.append(combo.reset_index())

out = pd.concat(results, ignore_index=True)
out.to_csv(os.path.join(HERE, "rq2_same_city_domestic.csv"), index=False)
print("\nwrote rq2_same_city_domestic.csv")
