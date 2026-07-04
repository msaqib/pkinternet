#!/usr/bin/env python3
"""Merge all batch CSVs from the full census run into single combined files."""

import csv
import glob
import os

RESULTS_DIR = "experiments/01_website_destinations/results/run_20260617_full_census"

def merge_summary(pattern, output_name):
    """Summary: one row per (site, probe) — dedupe keeping latest."""
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, pattern)))
    print(f"Merging {len(files)} files matching {pattern}...")

    all_rows = []
    fieldnames = None
    for fpath in files:
        with open(fpath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if fieldnames is None:
                fieldnames = reader.fieldnames
            for row in reader:
                all_rows.append(row)

    seen = {}
    for row in all_rows:
        key = (row.get("target_hostname"), row.get("probe_id"))
        seen[key] = row
    deduped = list(seen.values())

    out_path = os.path.join(RESULTS_DIR, output_name)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped)

    print(f"  Wrote {len(deduped)} rows (deduped from {len(all_rows)}) -> {out_path}")
    return deduped


def merge_grouped(pattern, output_name):
    """Grouped: one row per HOP — dedupe by (site, probe, hop), not just (site, probe)."""
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, pattern)))
    print(f"Merging {len(files)} files matching {pattern}...")

    all_rows = []
    fieldnames = None
    for fpath in files:
        with open(fpath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if fieldnames is None:
                fieldnames = reader.fieldnames
            for row in reader:
                all_rows.append(row)

    seen = {}
    for row in all_rows:
        key = (row.get("target_hostname"), row.get("probe_id"), row.get("hop"))
        seen[key] = row
    deduped = list(seen.values())

    deduped.sort(key=lambda r: (
        r.get("target_hostname", ""),
        r.get("probe_id", ""),
        int(r.get("hop") or 0)
    ))

    out_path = os.path.join(RESULTS_DIR, output_name)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped)

    print(f"  Wrote {len(deduped)} rows (deduped from {len(all_rows)}) -> {out_path}")
    return deduped


if __name__ == "__main__":
    summary = merge_summary("pk_summary_*.csv", "MERGED_summary.csv")
    grouped = merge_grouped("pk_grouped_*.csv", "MERGED_grouped.csv")

    unique_sites = set(r["target_hostname"] for r in summary)
    print(f"\nUnique sites covered: {len(unique_sites)}")