#!/usr/bin/env python3
"""
Exp 13 -- reconfirm: fresh live traceroute to MCB Arif Habib and HBL Bank,
from every currently-connected Pakistani probe.

Why: the original other_companies_and_hbl_report.html findings for these two
were never saved as raw measurement data anywhere in this repo (checked, not
present). MCB Arif Habib in particular is the closest thing found to a second
EFU-Life-style hairpin, PTCL's path reportedly went 14 hops / 181ms through
NTT -> Telecom Italia Sparkle -> Cogent, genuinely international, unlike the
low-RTT Cogent artifact ruled out for K-Electric. But the destination itself
never replied, so it's unconfirmed. This script re-runs both live and saves
raw results this time.

MCB Arif Habib's ASN/block was looked up fresh for this script (not in any
committed file): AS136427 (MCBAH-AS-AP), block 103.87.162.0/24. No live host
confirmed inside that block (same caveat as the original companies), so the
target is the first usable address, same convention as trace_other_cybernet_
customers.py.

HBL Bank uses the known-live address from chosen_targets.json (103.111.84.5),
not the earlier .1 fallback, since .5 actually answers.

Usage (from repo root):
    python experiments/13_efulife_live_snapshot/reconfirm_mcb_hbl.py
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
    {"hostname": "mcb-arif-habib-as136427.pk", "label": "mcb-arif-habib",
     "category": "Brokerage (Cybernet customer, unconfirmed PTCL int'l detour)",
     "resolved_ip": "103.87.162.1"},
    {"hostname": "hbl-bank-as137513.pk", "label": "hbl-bank",
     "category": "Bank (Cybernet customer, Cybernet-only detour via PIE hostname)",
     "resolved_ip": "103.111.84.5"},
]

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_DIR = os.path.join(HERE, "results", f"reconfirm_{TIMESTAMP}")


def _f(x, default=1e18):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("=" * 70)
    print("  Exp 13 reconfirm -- MCB Arif Habib + HBL Bank")
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
