#!/usr/bin/env python3
"""
Exp 13 -- follow-up: does the EFU Life pattern generalize to other Cybernet
customers with their own ASN?

Cybernet's own BGP neighbor list turned up ~10 Pakistani companies (banks,
a fintech, a utility, brokerages) with the identical structural setup as EFU
Life: their own ASN, single-homed to Cybernet only. A cheap BGP check
(cybernet_prefix_scope_check.md's method) split them 7/10 "no domestic peer
visible" (same as EFU Life) vs 3/10 "domestic peer visible" (HBL Bank,
K-Electric, Samba Bank, via PTCL/Transworld). This script is the traceroute
follow-up: one target from each group, live, to check whether traceroute
confirms or contradicts that BGP split -- exactly the same kind of check that
caught the Cybernet-core-block visibility-gap artifact earlier in this
experiment.

IMPORTANT: none of these companies' public websites resolve into their own
Cybernet-connected block -- hbl.com and nayapay.com both sit behind Cloudflare
/ Imperva, unrelated third-party CDNs. Targeting the public website would test
the CDN, not Cybernet. Targets here are the company's own announced prefix
directly (first usable address), found via `announced-prefixes` for each ASN.
No live hostname could be found inside these blocks (no PTR anywhere checked),
so traceroute is aimed at the bare block; that's fine methodologically, a
traceroute shows every real intermediate hop regardless of whether the final
address answers.

Targets:
    HBL Bank     AS137513  103.111.84.1   (BGP: domestic peer visible, PTCL+Transworld)
    NayaPay      AS139067  103.210.224.1  (BGP: no domestic peer visible, like EFU Life)
    DataCheck    AS132872  103.141.43.1   (BGP: no domestic peer visible, like EFU Life)

Usage (from repo root):
    python experiments/13_efulife_live_snapshot/trace_other_cybernet_customers.py
"""
import os
import sys
import csv
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "measurement"))
sys.path.insert(0, os.path.join(HERE, "..", "12_probe_mesh_panel"))

import pk_multi_probe as pk          # noqa: E402
import mesh_panel_monitor as mpm     # noqa: E402
from format_routes import format_file  # noqa: E402

TARGETS = [
    {"hostname": "hbl-bank-as137513.pk", "label": "hbl-bank",
     "category": "Bank (Cybernet customer, BGP: domestic peer visible)",
     "resolved_ip": "103.111.84.1"},
    {"hostname": "nayapay-as139067.pk", "label": "nayapay",
     "category": "Fintech (Cybernet customer, BGP: no domestic peer visible)",
     "resolved_ip": "103.210.224.1"},
    {"hostname": "datacheck-as132872.pk", "label": "datacheck",
     "category": "DataCheck (Cybernet customer, BGP: no domestic peer visible)",
     "resolved_ip": "103.141.43.1"},
]

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_DIR = os.path.join(HERE, "results", f"other_customers_{TIMESTAMP}")


def _f(x, default=1e18):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("=" * 70)
    print("  Exp 13 follow-up -- other Cybernet-hosted PK companies")
    print("=" * 70)

    print("\n[1] Discovering live PK probes...")
    probes_map = mpm.discover_probes()
    print(f"  {len(probes_map)} live probe(s)")

    cost = len(probes_map) * len(TARGETS) * 20
    print(f"\n[2] Scheduling {len(probes_map)} probes x {len(TARGETS)} targets "
          f"(~{cost:,} credits)...")

    scheduled = []
    for target in TARGETS:
        for pid, info in sorted(probes_map.items()):
            probe = {
                "probe_id": pid, "asn_v4": info["asn"], "city": info["label"],
                "lat": None, "lon": None,
            }
            try:
                mid = pk.create_traceroute(pid, target["resolved_ip"],
                                            f"{pid}→{target['label']}")
                scheduled.append((mid, probe, target))
            except Exception as e:
                print(f"    ERROR probe {pid} -> {target['label']}: {e}")
            time.sleep(0.4)
        print(f"    scheduled all probes -> {target['label']}")

    print(f"\n[3] Waiting for {len(scheduled)} measurement(s)...")
    completed = pk.wait_for_all([mid for mid, _, _ in scheduled], timeout=600)

    print(f"\n[4] Fetching + enriching results...")
    all_grouped, all_summaries = [], []
    for mid, probe, target in scheduled:
        if mid not in completed:
            continue
        try:
            raw = pk.fetch_result(mid)
            hop_rows, sum_row, grouped_rows = pk.flatten(mid, probe, target, raw)
            all_grouped.extend(grouped_rows)
            if sum_row:
                all_summaries.append(sum_row)
        except Exception as e:
            print(f"    ERROR fetching measurement {mid}: {e}")

    all_grouped.sort(key=lambda x: (x["target_label"], x["probe_id"], x["hop"] or 0))
    grouped_file = os.path.join(RESULTS_DIR, f"grouped_{TIMESTAMP}.csv")
    summary_file = os.path.join(RESULTS_DIR, f"summary_{TIMESTAMP}.csv")

    with open(grouped_file, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=pk.GROUPED_FIELDS)
        w.writeheader()
        w.writerows(all_grouped)

    with open(summary_file, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=pk.SUMMARY_FIELDS)
        w.writeheader()
        w.writerows(all_summaries)

    routes_path = format_file(grouped_file)
    print(f"\n  Grouped CSV -> {grouped_file}")
    print(f"  Summary CSV -> {summary_file}")
    print(f"  Readable    -> {routes_path}")

    for target in TARGETS:
        rows = [r for r in all_summaries if r["target_label"] == target["label"]]
        print(f"\n{'=' * 90}")
        print(f"  {target['label']} ({target['category']})")
        print(f"{'=' * 90}")
        for row in sorted(rows, key=lambda r: _f(r["max_rtt_ms"])):
            reached = "yes" if str(row["destination_responded"]).lower() == "true" else "NO"
            print(f"  {row['probe_id']:>8}  {row['probe_city']:<16} reached={reached:>3} "
                  f"hops={row['total_hops']:>3} max_rtt={row['max_rtt_ms']:>8}  "
                  f"asns={row['asns_in_path']}  countries={row['countries_in_path']}")

    print(f"\n  scheduled={len(scheduled)}  completed={len(all_summaries)}")


if __name__ == "__main__":
    main()
