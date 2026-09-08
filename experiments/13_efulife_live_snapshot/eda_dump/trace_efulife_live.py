#!/usr/bin/env python3
"""
Exp 13 -- EFU Life live snapshot: one traceroute per currently-live PK probe.

Follow-up to the Exp 07 case study (`case_study_efulife_cybernet_gatekeeper.md`,
prompted by Dr. Saqib's observation that efulife.com's routing "trombones from
different places and is sometimes local"). That case study was built from the
7-day panel's archived rounds; this script re-checks it live, right now, with
whichever PK probes RIPE currently reports Connected -- one one-off traceroute
per probe, no periodic scheduling.

Probe discovery reuses Exp 07/12's exact method (RIPE API, country_code=PK,
status=Connected -- see `experiments/12_probe_mesh_panel/notes.md`, "Which live
source"). Everything else -- measurement creation, hop/ASN enrichment, CSV
shape, readable route formatting -- reuses `scripts/measurement/pk_multi_probe.py`
and `format_routes.py` as-is; this script is just a thin driver: one target,
all live probes, one round.

Usage (from repo root):
    python experiments/13_efulife_live_snapshot/trace_efulife_live.py
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

TARGET_HOSTNAME = "efulife.com"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_DIR = os.path.join(HERE, "results", f"run_{TIMESTAMP}")


def _f(x, default=1e18):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("=" * 70)
    print("  Exp 13 -- EFU Life live snapshot")
    print("=" * 70)

    print("\n[1] Discovering live PK probes (RIPE, country_code=PK, Connected)...")
    probes_map = mpm.discover_probes()
    print(f"  {len(probes_map)} live probe(s):")
    for pid, info in sorted(probes_map.items()):
        flag = "  [ICMP-filtered]" if pid in mpm.ICMP_FILTERED else ""
        print(f"    {pid:>8}  {info['label']:<18} AS{info['asn']}{flag}")

    print(f"\n[2] Resolving {TARGET_HOSTNAME}...")
    ip, err = pk.resolve(TARGET_HOSTNAME)
    if err:
        print(f"  DNS resolution failed: {err}")
        return
    print(f"  {TARGET_HOSTNAME} -> {ip}")

    target = {
        "hostname": TARGET_HOSTNAME,
        "label": "efulife",
        "category": "Financial Services (n=1 case study)",
        "resolved_ip": ip,
    }

    cost = len(probes_map) * 20
    print(f"\n[3] Scheduling {len(probes_map)} one-off traceroute(s) "
          f"(~{cost:,} credits)...")
    scheduled = []
    for pid, info in sorted(probes_map.items()):
        probe = {
            "probe_id": pid,
            "asn_v4": info["asn"],
            "city": info["label"],
            "lat": None,
            "lon": None,
        }
        try:
            mid = pk.create_traceroute(pid, ip, f"{pid}→efulife")
            scheduled.append((mid, probe))
            print(f"    probe {pid:>8} ({info['label']:<18}) -> measurement {mid}")
        except Exception as e:
            print(f"    ERROR probe {pid}: {e}")
        time.sleep(0.5)

    print(f"\n[4] Waiting for {len(scheduled)} measurement(s)...")
    completed = pk.wait_for_all([mid for mid, _ in scheduled], timeout=600)

    print(f"\n[5] Fetching + enriching results...")
    all_hop_rows, all_grouped, all_summaries = [], [], []
    for mid, probe in scheduled:
        if mid not in completed:
            print(f"    skip measurement {mid} (probe {probe['probe_id']}) -- no result")
            continue
        try:
            raw = pk.fetch_result(mid)
            hop_rows, sum_row, grouped_rows = pk.flatten(mid, probe, target, raw)
            all_hop_rows.extend(hop_rows)
            all_grouped.extend(grouped_rows)
            if sum_row:
                all_summaries.append(sum_row)
        except Exception as e:
            print(f"    ERROR fetching measurement {mid}: {e}")

    all_grouped.sort(key=lambda x: (x["probe_id"], x["hop"] or 0))
    grouped_file = os.path.join(RESULTS_DIR, f"pk_grouped_efulife_{TIMESTAMP}.csv")
    summary_file = os.path.join(RESULTS_DIR, f"pk_summary_efulife_{TIMESTAMP}.csv")

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

    print("\n" + "=" * 100)
    print("  HEADLINE -- one traceroute per live probe, sorted by RTT (fast/direct first)")
    print("=" * 100)
    header = f"{'probe':>8}  {'ISP':<18} {'reached':>7} {'hops':>5} {'max_rtt_ms':>11}  asns_in_path / countries_in_path"
    print(header)
    print("-" * len(header))
    for row in sorted(all_summaries, key=lambda r: _f(r["max_rtt_ms"])):
        reached = "yes" if str(row["destination_responded"]).lower() == "true" else "NO"
        print(
            f"{row['probe_id']:>8}  {row['probe_city']:<18} {reached:>7} "
            f"{row['total_hops']:>5} {row['max_rtt_ms']:>11}  "
            f"{row['asns_in_path']}  /  {row['countries_in_path']}"
        )

    skipped = len(scheduled) - len(all_summaries)
    print(f"\n  scheduled={len(scheduled)}  completed={len(all_summaries)}  skipped={skipped}")
    print("=" * 100)


if __name__ == "__main__":
    main()
