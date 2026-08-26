#!/usr/bin/env python3
"""
RQ2/RQ3/RQ4 numbers under the final 5-rule detector. Run final_classifier.py first
(produces final_classified_rounds.csv, required input here). Read-only against the
panel results and cdn.csv; writes rq2_merged.csv, rq3_qualified_pairs.csv,
rq3_site_rate.csv here, prints every number used in
running_draft_final_detector_corrections.md.
"""
import os, json
import collections
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RESULTS = os.path.join(EXP, "results")

EXCLUDE = {1015491, 7764}

trace = pd.read_csv(os.path.join(HERE, "final_classified_rounds.csv"))

# ================================ RQ2 ================================
print("=" * 60, "\nRQ2\n", "=" * 60)
trace["endtime"] = pd.to_datetime(trace["endtime"], unit="s", errors="coerce")
if trace["endtime"].isna().mean() > 0.5:
    trace["endtime"] = pd.to_datetime(trace["endtime"])
trace = trace.sort_values("endtime")

ping = pd.read_csv(os.path.join(RESULTS, "b", "panel_20260718_200355.csv"))
ping = ping[ping["kind"] == "ping"].dropna(subset=["rtt_min"]).copy()
ping = ping[~ping["probe_id"].isin(EXCLUDE)]
pk_targets = set(trace.target.unique())
ping = ping[ping.target.isin(pk_targets)].copy()
ping["ts_utc"] = pd.to_datetime(ping["ts_utc"])

rows = []
for (pid, tgt), pgrp in ping.groupby(["probe_id", "target"]):
    tgrp = trace[(trace.probe_id == pid) & (trace.target == tgt)]
    if tgrp.empty:
        continue
    pgrp = pgrp.sort_values("ts_utc")
    tgrp = tgrp.sort_values("endtime")
    m = pd.merge_asof(pgrp, tgrp[["endtime", "trombone"]], left_on="ts_utc", right_on="endtime",
                       direction="nearest", tolerance=pd.Timedelta("40min"))
    rows.append(m)
merged = pd.concat(rows, ignore_index=True).dropna(subset=["trombone"])
merged["trombone"] = merged["trombone"].astype(bool)
merged.to_csv(os.path.join(HERE, "rq2_merged.csv"), index=False)

print(f"merged ping rows: {len(merged)}")
print(merged.groupby("trombone")["rtt_min"].agg(["median", "mean", "count"]))

g = merged.groupby(["probe_id", "target", "trombone"])["rtt_min"].median().unstack().dropna()
g["delta"] = g[True] - g[False]
print(f"\nflip pairs (both states, RTT in both): {len(g)}")
print(f"median delta: {g.delta.median():.2f} ms, mean delta: {g.delta.mean():.2f} ms")

merged["hour_pkt"] = (merged["ts_utc"] + pd.Timedelta(hours=5)).dt.hour
hourly = merged.groupby("hour_pkt")["trombone"].mean() * 100
merged["date_pkt"] = (merged["ts_utc"] + pd.Timedelta(hours=5)).dt.date
daily = merged.groupby("date_pkt")["trombone"].mean() * 100
print(f"\nhourly range: {hourly.min():.1f} - {hourly.max():.1f}")
print(f"daily range: {daily.min():.1f} - {daily.max():.1f}")

# ================================ RQ3 ================================
print("\n" + "=" * 60, "\nRQ3\n", "=" * 60)
pair_counts = trace.groupby(["probe_id", "target"]).size()
qualified = pair_counts[pair_counts >= 50].index
sub = trace.set_index(["probe_id", "target"]).loc[qualified].reset_index()
sub.to_csv(os.path.join(HERE, "rq3_qualified_pairs.csv"), index=False)

pair_rate = sub.groupby(["probe_id", "target"])["trombone"].mean()
n_local = (pair_rate == 0).sum()
n_hairpin = (pair_rate == 1).sum()
n_flap = ((pair_rate > 0) & (pair_rate < 1)).sum()
print(f"qualified pairs (>=50 rounds): {len(pair_rate)}")
print(f"local: {n_local} ({n_local/len(pair_rate)*100:.1f}%)  "
      f"hairpinned: {n_hairpin} ({n_hairpin/len(pair_rate)*100:.1f}%)  "
      f"flapping: {n_flap} ({n_flap/len(pair_rate)*100:.1f}%)")
ever = n_hairpin + n_flap
print(f"ever-trombone: {ever}, also-local ({n_flap}/{ever}): {n_flap/ever*100:.1f}%")

site_rate = sub.groupby("target")["trombone"].agg(["mean", "max", "min"])
site_rate.to_csv(os.path.join(HERE, "rq3_site_rate.csv"))
n_sites = len(site_rate)
n_ever_site = (site_rate["max"] > 0).sum()
n_flap_site = ((site_rate["max"] > 0) & (site_rate["min"] == 0)).sum()
n_gt90 = (site_rate["mean"] > 0.9).sum()
print(f"sites: {n_sites}, ever hairpinned: {n_ever_site}, flap: {n_flap_site}, >90% hairpinned: {n_gt90}")


def is_subseq_or_proj(a, b):
    def nn(lst):
        return [x for x in lst if x]
    A, B = nn(a), nn(b)

    def subseq(x, y):
        it = iter(y)
        return all(v in it for v in x)
    return subseq(A, B) or subseq(B, A)


sub2 = sub.copy()
sub2["as_path"] = sub2["as_path"].apply(json.loads)

divergence_hops = []
genuine_transitions = 0
total_transitions = 0
pairs_with_reroute = 0
n_pairs = 0

for (pid, tgt), grp in sub2.sort_values("endtime").groupby(["probe_id", "target"]):
    grp = grp.reset_index(drop=True)
    n_pairs += 1
    pair_has_reroute = False
    for i in range(1, len(grp)):
        prev, cur = grp.loc[i - 1], grp.loc[i]
        if not is_subseq_or_proj(prev.as_path, cur.as_path):
            pair_has_reroute = True
        if prev.trombone == cur.trombone:
            continue
        total_transitions += 1
        p_path, c_path = prev.as_path, cur.as_path
        maxlen = max(len(p_path), len(c_path))
        first_diff = None
        for h in range(maxlen):
            pv = p_path[h] if h < len(p_path) else None
            cv = c_path[h] if h < len(c_path) else None
            if pv != cv:
                first_diff = h + 1
                break
        if first_diff:
            divergence_hops.append(first_diff)
        if not is_subseq_or_proj(p_path, c_path):
            genuine_transitions += 1
    if pair_has_reroute:
        pairs_with_reroute += 1

c = collections.Counter(divergence_hops)
in_3_5 = sum(v for h, v in c.items() if 3 <= h <= 5)
print(f"\nverdict-flip transitions: {total_transitions}, resolvable divergences: {len(divergence_hops)}")
print(f"pct at hops 3-5: {in_3_5}/{len(divergence_hops)} = {in_3_5/len(divergence_hops)*100:.1f}%")
print(f"genuine reroutes / transitions: {genuine_transitions}/{total_transitions} = "
      f"{genuine_transitions/total_transitions*100:.1f}%")
print(f"pairs with >=1 genuine reroute: {pairs_with_reroute}/{n_pairs} = "
      f"{pairs_with_reroute/n_pairs*100:.1f}%")

# ================================ RQ4 ================================
print("\n" + "=" * 60, "\nRQ4\n", "=" * 60)
cdn = pd.read_csv(os.path.join(HERE, "cdn.csv"))
KARACHI = {1016126: "PTCL", 1016143: "Cybernet", 1016154: "Cybernet", 64722: "TES"}
LAHORE = {1015679: "Nova", 62224: "Transworld", 7613: "Zcom", 65892: "Nayatel"}


def city_stats(probes, label):
    d = cdn[cdn.probe_id.isin(probes)].copy()
    d["isp_label"] = d.probe_id.map(probes)
    g = d.groupby("isp_label").agg(
        median_rtt=("min_rtt_ms", "median"),
        pct_local=("pop_class", lambda s: (s == "local").mean() * 100),
    ).sort_values("median_rtt")
    print(f"\n{label}:")
    print(g.round(1))
    print(f"spread: {(g.median_rtt.max()/g.median_rtt.min()):.1f}x")
    return g


city_stats(KARACHI, "Karachi")
city_stats(LAHORE, "Lahore")
