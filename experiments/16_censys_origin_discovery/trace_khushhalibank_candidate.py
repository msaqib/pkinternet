#!/usr/bin/env python3
"""
Exp 16 -- RIPE Atlas verification for the khushhalibank.com.pk Censys candidate.

Censys cert search found 119.159.230.218 presenting a real, currently valid
*.khushhalibank.com.pk certificate (O=Khushhali Microfinance Bank Ltd,
issued by DigiCert), sitting on AS17557 (PTCL) in Bahawalpur, Punjab, with
no public DNS record. A direct HTTPS request completed the TLS handshake
(cert verified ok) but got connection-reset on the actual page request,
consistent with an origin firewalled to only accept traffic from the CDN.

This script runs the same live-probe traceroute check Exp13 used for other
candidates: trace to the raw IP from every live Pakistani RIPE Atlas probe,
same method as trace_other_cybernet_customers.py.

Usage (from repo root):
    python experiments/16_censys_origin_discovery/trace_khushhalibank_candidate.py
    python experiments/16_censys_origin_discovery/trace_khushhalibank_candidate.py --ip 117.20.24.53 --label khb-53-open
"""
import os
import sys
import csv
import time
import argparse
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "measurement"))
sys.path.insert(0, os.path.join(HERE, "..", "12_probe_mesh_panel"))

import pk_multi_probe as pk          # noqa: E402
import mesh_panel_monitor as mpm     # noqa: E402
from format_routes import format_file  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="119.159.230.218", help="target IP to traceroute")
parser.add_argument("--label", default="khushhalibank-candidate", help="short label for filenames/output")
parser.add_argument("--category", default="Khushhali Bank (Censys wildcard-cert candidate)",
                     help="description shown in output header")
parser.add_argument("--protocol", default="TCP", choices=["ICMP", "TCP"],
                     help="TCP (default) traces against a port the target actually answers on; "
                          "ICMP is the older default, useful only if a target blocks TCP too")
parser.add_argument("--port", type=int, default=443, help="port for TCP traceroute")
args = parser.parse_args()

TARGET = {
    "hostname": "khushhalibank-censys-candidate.pk",
    "label": args.label,
    "category": args.category,
    "resolved_ip": args.ip,
}

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_DIR = os.path.join(HERE, "results", f"{args.label}_{TIMESTAMP}")


def _f(x, default=1e18):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("=" * 70)
    print("  Exp 16 -- khushhalibank.com.pk Censys candidate verification")
    print("=" * 70)

    print("\n[1] Discovering live PK probes...")
    probes_map = mpm.discover_probes()
    print(f"  {len(probes_map)} live probe(s)")

    cost = len(probes_map) * 20
    print(f"\n[2] Scheduling {len(probes_map)} probes -> {TARGET['label']} "
          f"(~{cost:,} credits)...")

    scheduled = []
    for pid, info in sorted(probes_map.items()):
        probe = {
            "probe_id": pid, "asn_v4": info["asn"], "city": info["label"],
            "lat": None, "lon": None,
        }
        try:
            mid = pk.create_traceroute(pid, TARGET["resolved_ip"],
                                        f"{pid} to {TARGET['label']}",
                                        protocol=args.protocol, port=args.port)
            scheduled.append((mid, probe, TARGET))
        except Exception as e:
            print(f"    ERROR probe {pid} -> {TARGET['label']}: {e}")
        time.sleep(0.4)

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

    print(f"\n{'=' * 90}")
    print(f"  {TARGET['label']} ({TARGET['category']})")
    print(f"{'=' * 90}")
    for row in sorted(all_summaries, key=lambda r: _f(r["max_rtt_ms"])):
        reached = "yes" if str(row["destination_responded"]).lower() == "true" else "NO"
        print(f"  {row['probe_id']:>8}  {row['probe_city']:<16} reached={reached:>3} "
              f"hops={row['total_hops']:>3} max_rtt={row['max_rtt_ms']:>8}  "
              f"asns={row['asns_in_path']}  countries={row['countries_in_path']}")

    print(f"\n  scheduled={len(scheduled)}  completed={len(all_summaries)}")


if __name__ == "__main__":
    main()
