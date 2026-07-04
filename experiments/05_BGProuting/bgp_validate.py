#!/usr/bin/env python3
"""
BGP Validation Script
Validates observed traceroute AS paths against historical BGP routing tables
using the RIPEstat bgp-state API.

Usage:
    python3 bgp_validate.py

Output:
    findings/bgp_validation_results.csv
"""

import pandas as pd
import requests
import time
from datetime import datetime

# ── CONFIG ───────────────────────────────────────────────────────────────────
FACT_TRACE = "experiments/03_longitudinal_routing/results/run_20260612_48h/normalized/fact_trace.csv"
DIM_PROBE  = "experiments/03_longitudinal_routing/results/run_20260612_48h/normalized/dim_probe.csv"
DIM_SITE   = "experiments/03_longitudinal_routing/results/run_20260612_48h/normalized/dim_site.csv"
OUTPUT     = "findings/bgp_validation_results.csv"
SLEEP_SEC  = 0.5   # rate limit: 2 requests/sec max
# ─────────────────────────────────────────────────────────────────────────────


def fetch_bgp_state(ip, timestamp):
    """
    Query RIPEstat bgp-state API for the BGP routing table entry
    for a given IP at a given timestamp.
    Returns list of AS path lists, or empty list on failure.
    NOTE: This uses the RIPEstat Data API, which is FREE and does NOT
    consume any RIPE Atlas credits.
    """
    url = "https://stat.ripe.net/data/bgp-state/data.json"
    params = {
        "resource":  ip,
        "timestamp": timestamp,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        routes = data.get("data", {}).get("bgp_state", [])
        paths = [route.get("path", []) for route in routes if "path" in route]
        return paths
    except Exception as e:
        print(f"    !! API error for {ip} at {timestamp}: {e}")
        return []


def observed_asns(asns_in_path_str):
    """
    Parse the observed AS path string from fact_trace.
    e.g. "152605 > 38193 > 58453 > 13335" -> [152605, 38193, 58453, 13335]
    Returns empty list if NaN or unparseable.
    """
    if pd.isna(asns_in_path_str) or not str(asns_in_path_str).strip():
        return []
    try:
        return [int(x.strip()) for x in str(asns_in_path_str).split(">")]
    except Exception:
        return []


def validate_path(observed, bgp_paths, isp, site, trace_time):
    """
    Check if the observed AS path is consistent with any BGP-advertised path.
    Prints a clear comparison so you can see exactly what's being checked.
    Returns 'consistent', 'partial', 'no_match', or 'no_data'.
    """
    if not observed:
        print(f"    [SKIP] {isp} -> {site} at {trace_time}: no observed AS path (ICMP blocked or timeout)")
        return "no_data"

    if not bgp_paths:
        print(f"    [SKIP] {isp} -> {site} at {trace_time}: RIPEstat returned no BGP paths")
        return "no_data"

    dest_asn = observed[-1]
    obs_str  = " > ".join(str(a) for a in observed)

    print(f"\n    ISP:      {isp}")
    print(f"    Site:     {site}")
    print(f"    Time:     {trace_time}")
    print(f"    Observed: {obs_str}")
    print(f"    BGP paths from RIPEstat ({len(bgp_paths)} total):")
    for i, p in enumerate(bgp_paths[:3]):  # show first 3 BGP paths max
        print(f"      [{i+1}] {' > '.join(str(a) for a in p)}")
    if len(bgp_paths) > 3:
        print(f"      ... and {len(bgp_paths)-3} more")

    for bgp_path in bgp_paths:
        if dest_asn in bgp_path:
            observed_transit = set(observed[1:-1])
            bgp_transit      = set(bgp_path)
            overlap          = observed_transit & bgp_transit
            if overlap:
                print(f"    RESULT: CONSISTENT (shared transit ASNs: {overlap})")
                return "consistent"
            else:
                print(f"    RESULT: PARTIAL (destination ASN {dest_asn} found in BGP, but no shared transit ASNs)")
                return "partial"

    print(f"    RESULT: NO MATCH (destination ASN {dest_asn} not found in any BGP path)")
    return "no_match"


def main():
    print("=" * 60)
    print("  BGP Path Validation — RIPEstat Historical Check")
    print("  (Uses RIPEstat Data API — FREE, no Atlas credits used)")
    print("=" * 60)

    print("\n[1] Loading and joining tables...")
    fact_trace = pd.read_csv(FACT_TRACE)
    dim_probe  = pd.read_csv(DIM_PROBE)
    dim_site   = pd.read_csv(DIM_SITE)
    traces = fact_trace.merge(dim_probe, on="probe_id").merge(dim_site, on="site_id")
    print(f"    Loaded {len(traces)} trace rows")

    # group by (target_ip, hour) to minimize API calls
    traces['hour_str'] = pd.to_datetime(traces['trace_time'], utc=True)\
                           .dt.floor('h')\
                           .dt.strftime('%Y-%m-%dT%H:%M:%S')

    valid_traces = traces.dropna(subset=['asns_in_path'])
    unique_combos = valid_traces.groupby(['target_ip', 'hour_str'])\
                                .first()\
                                .reset_index()[['target_ip', 'hour_str', 'target_hostname']]

    print(f"    Rows with observable AS paths: {len(valid_traces)}")
    print(f"    Unique (IP, hour) combos to query: {len(unique_combos)}")
    print(f"    Estimated time: ~{len(unique_combos) * SLEEP_SEC / 60:.1f} minutes\n")

    # Step 2 — query RIPEstat for each unique (ip, hour) combo
    print("[2] Querying RIPEstat BGP historical state...")
    cache = {}
    for i, row in unique_combos.iterrows():
        ip   = row['target_ip']
        ts   = row['hour_str']
        site = row['target_hostname']
        key  = (ip, ts)

        print(f"  [{i+1}/{len(unique_combos)}] {site} ({ip}) at {ts}... ", end="", flush=True)
        paths = fetch_bgp_state(ip, ts)
        cache[key] = paths
        print(f"{len(paths)} BGP paths returned")
        time.sleep(SLEEP_SEC)

    # Step 3 — validate each trace row
    print(f"\n[3] Validating {len(traces)} trace rows against BGP data...")
    results = []
    shown   = set()  # only print full comparison once per unique (isp, site, hour)

    for _, row in traces.iterrows():
        ip   = row['target_ip']
        ts   = row.get('hour_str', '')
        obs  = observed_asns(row.get('asns_in_path'))
        bgp  = cache.get((ip, ts), [])
        isp  = row['isp']
        site = row['target_hostname']
        t    = row['trace_time']

        # only print detailed comparison once per (isp, site, hour) to avoid spam
        key = (isp, site, ts)
        if key not in shown:
            verdict = validate_path(obs, bgp, isp, site, t)
            shown.add(key)
        else:
            # silent validation for repeat combos
            if not obs or not bgp:
                verdict = "no_data"
            else:
                dest_asn = obs[-1]
                verdict  = "no_match"
                for bgp_path in bgp:
                    if dest_asn in bgp_path:
                        overlap = set(obs[1:-1]) & set(bgp_path)
                        verdict = "consistent" if overlap else "partial"
                        break

        results.append({
            'trace_id':        row['trace_id'],
            'trace_time':      row['trace_time'],
            'isp':             isp,
            'target_hostname': site,
            'target_ip':       ip,
            'observed_path':   row.get('asns_in_path', ''),
            'bgp_paths_found': len(bgp),
            'validation':      verdict,
        })

    # Step 4 — save and summarize
    out = pd.DataFrame(results)
    out.to_csv(OUTPUT, index=False)

    print(f"\n[4] Results saved to {OUTPUT}")
    print("\n=== Validation Summary ===")
    print(out['validation'].value_counts())
    print("\n=== By ISP ===")
    print(out.groupby(['isp', 'validation']).size().unstack(fill_value=0))
    print("\n=== By Site ===")
    print(out.groupby(['target_hostname', 'validation']).size().unstack(fill_value=0))
    print("=" * 60)


if __name__ == "__main__":
    main()