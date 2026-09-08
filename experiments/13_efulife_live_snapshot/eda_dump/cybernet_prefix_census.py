#!/usr/bin/env python3
"""
Exp 13 -- Cybernet prefix census: does AS9541 (Cybernet) peer domestically with
any Pakistani ISP for its OWN announced address space, or only internationally?

Follow-up to the EFU Life investigation. EFU Life (AS141008) is reachable from
non-Cybernet Pakistani ISPs only via an international hairpin (GSL Networks in
Singapore, then a Zain Omantel block) -- Cybernet never announces a domestic
peer for that specific prefix. This script checks whether that's specific to
EFU Life's customer block, or true of Cybernet's own announced space generally,
by running the same "who sits immediately upstream of AS9541" check across
every prefix Cybernet itself announces (its 957 own blocks -- for regular
customers without their own ASN, NOT EFU Life's block, which EFU Life itself
announces under its own ASN with Cybernet only as transit).

IMPORTANT CAVEAT (see cybernet_prefix_scope_check.md): this is a CONTROL-PLANE
check only (BGP looking-glass, backed by RIS). RIS/RouteViews only see BGP
announcements from networks that peer directly with their own collectors --
mostly large international carriers. A small, domestic-only Pakistani ISP can
have a perfectly real, working link to Cybernet that never touches anything
RIS is listening to, and this script would report that block as having "0"
domestic peers even though it's actually reachable domestically. A "0" here
means "no domestic peer visible from RIS's vantage points," not "provably no
domestic peer exists." Only cross-checking with an actual traceroute (DATA
PLANE, real packets) can settle that for any specific block -- this script
alone cannot.

Method: one HTTP GET per prefix to RIPEstat's `looking-glass` data call (a
public, keyless API backed by RIS's collector network), rate-limited to be a
polite user of a free public service. For each prefix, every currently-visible
AS-path is parsed; the AS immediately to the left of "9541" in each path (i.e.
the network handing traffic off *into* Cybernet) is recorded and checked
against a hardcoded list of Pakistani ISP ASNs from this project's records.

Usage (from repo root):
    python experiments/13_efulife_live_snapshot/cybernet_prefix_census.py

Output:
    results/cybernet_prefix_census_<timestamp>.csv
    one row per Cybernet-announced prefix: total AS-paths seen, how many of
    those go through a Pakistani ASN immediately before Cybernet, and which.
"""
import csv
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, "results")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_FILE = os.path.join(RESULTS_DIR, f"cybernet_prefix_census_{TIMESTAMP}.csv")

CYBERNET_ASN = "9541"
REQUEST_DELAY_SEC = 0.35   # politeness delay between requests to the free RIPEstat API

# Pakistani ISP ASNs tracked elsewhere in this project (mesh_panel_monitor.py's
# PK_ASN map, format_routes.py's PROBE_ASN_NAMES, and the Globalping check).
PK_ASNS = {
    "17557": "PTCL", "38193": "Transworld", "23674": "Nayatel", "136174": "Nova",
    "152605": "Zcom", "135407": "TES", "151983": "Orbit", "150683": "Fasttel",
    "45773": "PERN", "9260": "Multinet", "23888": "NTC", "38264": "Wateen",
    "147302": "Falcon", "154578": "LeapDigital", "45814": "Fariya",
    "150750": "INCABLE", "9387": "SharpTelecom",
}


def fetch_cybernet_prefixes():
    """All prefixes AS9541 currently announces as origin (RIPEstat, no auth needed)."""
    url = ("https://stat.ripe.net/data/announced-prefixes/data.json"
           f"?resource=AS{CYBERNET_ASN}&starttime=2026-08-01T00:00:00&endtime=2026-09-02T00:00:00")
    with urllib.request.urlopen(url, timeout=20) as r:
        d = json.load(r)
    return [p["prefix"] for p in d["data"]["prefixes"]]


def check_prefix(prefix):
    """Return (total_paths_seen, pk_hit_count, sorted set of PK ISP names hit)."""
    url = f"https://stat.ripe.net/data/looking-glass/data.json?resource={prefix}"
    for attempt in range(2):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                d = json.load(r)
            break
        except Exception:
            if attempt == 1:
                return None
            time.sleep(1)

    total = 0
    pk_hits = []
    for rrc in d.get("data", {}).get("rrcs", []):
        for peer in rrc.get("peers", []):
            path = peer.get("as_path")
            if not path:
                continue
            parts = path.split()
            if CYBERNET_ASN not in parts:
                continue
            total += 1
            idx = parts.index(CYBERNET_ASN)
            if idx > 0 and parts[idx - 1] in PK_ASNS:
                pk_hits.append(PK_ASNS[parts[idx - 1]])
    return total, len(pk_hits), sorted(set(pk_hits))


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("Fetching Cybernet's currently-announced prefix list...")
    prefixes = fetch_cybernet_prefixes()
    print(f"  {len(prefixes)} prefixes")

    with open(OUT_FILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["prefix", "total_paths", "pk_paths", "pk_asns"])

        errors = 0
        for i, prefix in enumerate(prefixes):
            result = check_prefix(prefix)
            if result is None:
                w.writerow([prefix, "ERROR", "", ""])
                errors += 1
            else:
                total, pk_count, pk_names = result
                w.writerow([prefix, total, pk_count, ";".join(pk_names)])
            f.flush()

            if (i + 1) % 50 == 0:
                print(f"  {i + 1}/{len(prefixes)} checked, {errors} errors so far")

            time.sleep(REQUEST_DELAY_SEC)

    print(f"\nDone. {len(prefixes)} prefixes checked, {errors} errors.")
    print(f"Results -> {OUT_FILE}")


if __name__ == "__main__":
    main()
