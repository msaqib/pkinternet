#!/usr/bin/env python3
"""
RIPE Atlas — Pakistan Multi-Probe Website Measurement
======================================================
Runs ICMP Paris traceroutes from specified RIPE Atlas probes
to Pakistani websites to determine hosting location and routing.

Requirements: pip install requests dnspython

Usage (run from repo root):
    python scripts/measurement/pk_multi_probe.py

Before running:
    1. Set RUN_NAME in CONFIG
    2. Set RIPE_API_KEY environment variable
    3. Add probe IDs to PROBES list
    4. Set BATCH_SIZE (10 for test, None for all 100)

Results saved to:
    experiments/01_website_destinations/results/{RUN_NAME}/
"""

import requests
import csv
import time
import socket
import sys
import dns.resolver
import os
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo_utils import serving_location   # actual destination location helper

load_dotenv()

# ─────────────────────────────────────────────────────
#  CONFIG — edit before running
# ─────────────────────────────────────────────────────

API_KEY        = os.environ.get("RIPE_API_KEY", "your-api-key-here")

# ── RUN NAME — edit before each run ───────────────────
# Results will be saved to:
# experiments/01_website_destinations/results/{RUN_NAME}/
RUN_NAME       = "run_20260604_batch11"
# ─────────────────────────────────────────────────────

# Path to websites list — relative to repo root
# Run this script from the repo root:
# python scripts/measurement/pk_multi_probe.py
WEBSITES_FILE  = "data/pk_websites_list.csv"

# ── PROBES — edit this list manually ──────────────────
# Format: (probe_id, asn, city, description)
PROBES = [
    (1015679, 136174, "Pakistan", "LocalInternetProj01 (Transworld)"),
    (1015210,  17557, "Pakistan", "AS17557 (PTCL)"),
    (  62224,  38193, "Pakistan", "Zartash-Office (Transworld)"),
    (  60223,  23674, "Pakistan", "PK_Inara (Nayatel)"),
    (   7613, 152605, "Pakistan", "Z COM Networks Private Limited"),
]
# ─────────────────────────────────────────────────────

# Slice of the target list to run in this batch
# BATCH_START: 0-indexed offset into the CSV (0 = first target)
# BATCH_SIZE:  how many targets to run (None = all remaining)
# Examples:
#   targets  1-20  →  BATCH_START = 0,  BATCH_SIZE = 20
#   targets 21-40  →  BATCH_START = 20, BATCH_SIZE = 20
#   targets 41-end →  BATCH_START = 40, BATCH_SIZE = None
BATCH_START    = 90
BATCH_SIZE     = 10

# Wait between probe batches (seconds)
BATCH_WAIT     =30

# How long to wait for measurements to complete (seconds)
RESULT_TIMEOUT = 3600

# Output paths — built from RUN_NAME automatically
TIMESTAMP      = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_DIR    = os.path.join(
    "experiments", "01_website_destinations", "results", RUN_NAME
)
GROUPED_FILE   = os.path.join(RESULTS_DIR, f"pk_grouped_{TIMESTAMP}.csv")
SUMMARY_FILE   = os.path.join(RESULTS_DIR, f"pk_summary_{TIMESTAMP}.csv")

# ─────────────────────────────────────────────────────
#  API SETUP
# ─────────────────────────────────────────────────────

BASE = "https://atlas.ripe.net/api/v2"
HDR  = {
    "Authorization": f"Key {API_KEY}",
    "Content-Type":  "application/json",
}

# ─────────────────────────────────────────────────────
#  STEP 1 — DISCOVER PAKISTANI PROBES
# ─────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────
#  STEP 2 — LOAD TARGET WEBSITES
# ─────────────────────────────────────────────────────

def load_targets(filepath, batch_start=0, batch_size=None):
    """
    Read targets from CSV file.
    Format: hostname, label, category
    """
    targets = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                targets.append({
                    "hostname": parts[0],
                    "label":    parts[1],
                    "category": parts[2],
                })

    targets = targets[batch_start:]
    if batch_size:
        targets = targets[:batch_size]
    return targets


# ─────────────────────────────────────────────────────
#  STEP 3 — DNS RESOLUTION
# ─────────────────────────────────────────────────────

def resolve(hostname):
    """Resolve hostname to IP. Returns (ip, error)."""
    try:
        return socket.gethostbyname(hostname), None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────
#  STEP 4 — ASN LOOKUP (Team Cymru DNS)
# ─────────────────────────────────────────────────────

_asn_cache  = {}
_name_cache = {}

def asn_for_ip(ip):
    """Returns (asn, prefix, country) for an IP via Team Cymru."""
    if ip in _asn_cache:
        return _asn_cache[ip]
    try:
        rev = ".".join(reversed(ip.split(".")))
        ans = dns.resolver.resolve(f"{rev}.origin.asn.cymru.com", "TXT", lifetime=5)
        for r in ans:
            p = [x.strip() for x in str(r).strip('"').split("|")]
            asn     = p[0].strip().split()[0]
            prefix  = p[1].strip() if len(p) > 1 else ""
            country = p[2].strip() if len(p) > 2 else ""
            _asn_cache[ip] = (asn, prefix, country)
            return asn, prefix, country
    except Exception:
        pass
    _asn_cache[ip] = (None, "", "")
    return None, "", ""

def asn_name(asn):
    """Returns org name for an ASN via Team Cymru."""
    if not asn or asn in _name_cache:
        return _name_cache.get(asn, "")
    try:
        ans = dns.resolver.resolve(f"AS{asn}.asn.cymru.com", "TXT", lifetime=5)
        for r in ans:
            p = [x.strip() for x in str(r).strip('"').split("|")]
            name = p[4].strip() if len(p) > 4 else p[-1].strip()
            _name_cache[asn] = name
            return name
    except Exception:
        pass
    _name_cache[asn] = ""
    return ""


_reg_cache = {}

def registry_lookup(ip):
    """Fallback for IPs that Team Cymru can't resolve because their prefix is
    not announced in BGP (e.g. an ISP's internal backbone interfaces).

    Queries RDAP (via the rdap.org redirector → the correct RIR) for the
    *allocation* record, which exists even when the prefix isn't routed.
    Returns (prefix, country, name). The numeric origin AS is usually absent
    from RDAP IP objects, so callers should treat a registry result as an
    operator/country hint, not a BGP origin — it is left with an empty hop_asn.
    """
    if ip in _reg_cache:
        return _reg_cache[ip]
    result = ("", "", "")
    try:
        r = requests.get(
            f"https://rdap.org/ip/{ip}",
            headers={"Accept": "application/rdap+json"},
            timeout=8,
        )
        if r.ok:
            d = r.json()
            name    = (d.get("name") or "").strip()
            country = (d.get("country") or "").strip()
            prefix  = ""
            cidrs   = d.get("cidr0_cidrs") or []
            if cidrs:
                c = cidrs[0]
                net = c.get("v4prefix") or c.get("v6prefix")
                if net:
                    prefix = f"{net}/{c.get('length', '')}"
            result = (prefix, country, name)
    except Exception:
        pass
    _reg_cache[ip] = result
    return result


# ─────────────────────────────────────────────────────
#  STEP 5 — CREATE TRACEROUTE MEASUREMENT
# ─────────────────────────────────────────────────────

def create_traceroute(probe_id, target_ip, description):
    payload = {
        "definitions": [{
            "target":           target_ip,
            "description":      description,
            "type":             "traceroute",
            "protocol":         "ICMP",
            "af":               4,
            "paris":            16,
            "first_hop":        1,
            "max_hops":         32,
            "size":             48,
            "dont_fragment":    True,
            "resolve_on_probe": False,
        }],
        "probes": [{
            "type":      "probes",
            "value":     str(probe_id),
            "requested": 1,
        }],
        "is_oneoff": True,
    }
    r = requests.post(f"{BASE}/measurements/", headers=HDR, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()["measurements"][0]


# ─────────────────────────────────────────────────────
#  STEP 6 — WAIT FOR RESULT
# ─────────────────────────────────────────────────────

def wait_for_all(msm_ids, timeout=180):
    """
    Poll all measurements simultaneously until all are Stopped.
    Much faster than waiting for each one sequentially.
    """
    pending  = set(msm_ids)
    done     = set()   # reached "Stopped" — has results
    failed   = set()   # terminal failure (e.g. No suitable probes) — no results
    deadline = time.time() + timeout

    print(f"  Polling {len(pending)} measurements", end="", flush=True)

    while pending and time.time() < deadline:
        for mid in list(pending):
            try:
                r = requests.get(
                    f"{BASE}/measurements/{mid}/",
                    headers=HDR, timeout=10
                )
                r.raise_for_status()
                status = r.json().get("status", {})
                sid, sname = status.get("id", 0), status.get("name", "")
                # RIPE status ids: <4 = still running (Specified/Scheduled/Ongoing);
                # >=4 = terminal (4 Stopped, 5 Forced, 6 No suitable probes, 7 Failed).
                if sid >= 4 or sname == "Stopped":
                    pending.remove(mid)
                    (done if sname == "Stopped" else failed).add(mid)
            except Exception:
                pass
        if pending:
            print(".", end="", flush=True)
            time.sleep(10)

    if failed:
        print(f"\n  {len(failed)} measurement(s) failed (e.g. offline probe / no suitable probes) — skipping them")
    print(f"  done ({len(done)} completed, {len(failed)} failed, {len(pending)} timed out)")
    return done


def fetch_result(msm_id):
    """Fetch results for a single completed measurement."""
    r = requests.get(
        f"{BASE}/measurements/{msm_id}/results/",
        headers=HDR, timeout=15
    )
    r.raise_for_status()
    return r.json()


# ─────────────────────────────────────────────────────
#  STEP 7 — FLATTEN RESULT TO ROWS
# ─────────────────────────────────────────────────────

PRIVATE = lambda ip: ip.startswith((
    "192.168.", "10.", "172.16.", "172.17.", "172.18.",
    "172.19.", "172.2", "172.3"
))

HOP_FIELDS = [
    "measurement_id",
    "probe_id",
    "probe_asn",
    "probe_city",
    "probe_lat",
    "probe_lon",
    "target_label",
    "target_category",
    "target_hostname",
    "target_ip",
    "target_asn",
    "target_asn_name",
    "target_country",
    "destination_responded",
    "hop",
    "hop_ip",
    "rtt_ms",
    "hop_asn",
    "hop_prefix",
    "hop_country",
    "hop_asn_name",
    "is_private",
    "is_timeout",
    "timestamp",
]

SUMMARY_FIELDS = [
    "measurement_id",
    "probe_id",
    "probe_asn",
    "probe_city",
    "target_label",
    "target_category",
    "target_hostname",
    "target_ip",
    "target_asn",
    "target_asn_name",
    "target_country",
    "dest_location",
    "location_via",
    "destination_responded",
    "total_hops",
    "timeout_hops",
    "max_rtt_ms",
    "asns_in_path",
    "countries_in_path",
    "timestamp",
]

# Grouped file — sorted website → probe → hop
# Column order: source (probe) → hops → target (destination)
GROUPED_FIELDS = [
    # ── target/website (what we are measuring) ──
    "target_hostname",
    "target_label",
    "target_category",
    # ── source (where we are measuring from) ──
    "probe_id",
    "probe_asn",
    "probe_city",
    # ── hops (the path) ──
    "hop",
    "hop_ip",
    "rtt_ms",
    "hop_asn",
    "hop_prefix",
    "hop_country",
    "hop_asn_name",
    "is_private",
    "is_timeout",
    # ── destination (what we reached) ──
    "target_ip",
    "target_asn",
    "target_asn_name",
    "target_country",
    "destination_responded",
    # ── metadata ──
    "measurement_id",
    "timestamp",
]


def flatten(msm_id, probe, target, raw_results):
    hop_rows  = []
    sum_row   = {}
    ts        = datetime.utcnow().isoformat()

    t_ip  = target.get("resolved_ip", "")
    t_asn, t_prefix, t_cc = asn_for_ip(t_ip) if t_ip else (None, "", "")
    t_name = asn_name(t_asn) if t_asn else ""

    for result in raw_results:
        responded  = result.get("destination_ip_responded", False)
        hops       = result.get("result", [])
        real_count = 0
        tmout_count= 0
        max_rtt    = 0
        all_asns   = []
        all_cc     = []

        for hop in hops:
            hop_num = hop.get("hop")
            replies = hop.get("result", [])
            chosen  = next((r for r in replies if "from" in r), None)

            if chosen is None:
                tmout_count += 1
                hop_rows.append({
                    "measurement_id":       msm_id,
                    "probe_id":             probe["probe_id"],
                    "probe_asn":            probe["asn_v4"],
                    "probe_city":           probe["city"],
                    "probe_lat":            probe["lat"],
                    "probe_lon":            probe["lon"],
                    "target_label":         target["label"],
                    "target_category":      target["category"],
                    "target_hostname":      target["hostname"],
                    "target_ip":            t_ip,
                    "target_asn":           t_asn or "",
                    "target_asn_name":      t_name,
                    "target_country":       t_cc,
                    "destination_responded":responded,
                    "hop":                  hop_num,
                    "hop_ip":               "*",
                    "rtt_ms":               "",
                    "hop_asn":              "",
                    "hop_prefix":           "",
                    "hop_country":          "",
                    "hop_asn_name":         "",
                    "is_private":           False,
                    "is_timeout":           True,
                    "timestamp":            ts,
                })
                continue

            real_count += 1
            ip  = chosen["from"]
            rtt = chosen.get("rtt", 0)
            max_rtt = max(max_rtt, rtt)

            if PRIVATE(ip):
                h_asn, h_prefix, h_cc, h_name = "", "", "", "RFC1918"
                is_private = True
            else:
                h_asn, h_prefix, h_cc = asn_for_ip(ip)
                h_name    = asn_name(h_asn) if h_asn else ""
                is_private = False
                # BGP had no origin AS (unannounced internal prefix) — fall back
                # to the RDAP registry allocation for an operator/country hint.
                if not h_asn:
                    r_prefix, r_cc, r_name = registry_lookup(ip)
                    h_prefix = h_prefix or r_prefix
                    h_cc     = h_cc or r_cc
                    h_name   = h_name or r_name

            if h_asn and h_asn not in all_asns:
                all_asns.append(h_asn)
            if h_cc and h_cc not in all_cc:
                all_cc.append(h_cc)

            hop_rows.append({
                "measurement_id":        msm_id,
                "probe_id":              probe["probe_id"],
                "probe_asn":             probe["asn_v4"],
                "probe_city":            probe["city"],
                "probe_lat":             probe["lat"],
                "probe_lon":             probe["lon"],
                "target_label":          target["label"],
                "target_category":       target["category"],
                "target_hostname":       target["hostname"],
                "target_ip":             t_ip,
                "target_asn":            t_asn or "",
                "target_asn_name":       t_name,
                "target_country":        t_cc,
                "destination_responded": responded,
                "hop":                   hop_num,
                "hop_ip":                ip,
                "rtt_ms":                rtt,
                "hop_asn":               h_asn or "",
                "hop_prefix":            h_prefix,
                "hop_country":           h_cc,
                "hop_asn_name":          h_name,
                "is_private":            is_private,
                "is_timeout":            False,
                "timestamp":             ts,
            })

        # Actual serving location (handoff geolocation for anycast CDNs, server
        # IP geolocation for unicast) — not the ASN's registration country.
        dest_location, location_via = serving_location(hop_rows, t_asn or "", t_ip)

        sum_row = {
            "measurement_id":       msm_id,
            "probe_id":             probe["probe_id"],
            "probe_asn":            probe["asn_v4"],
            "probe_city":           probe["city"],
            "target_label":         target["label"],
            "target_category":      target["category"],
            "target_hostname":      target["hostname"],
            "target_ip":            t_ip,
            "target_asn":           t_asn or "",
            "target_asn_name":      t_name,
            "target_country":       t_cc,
            "dest_location":        dest_location,
            "location_via":         location_via,
            "destination_responded":responded,
            "total_hops":           real_count,
            "timeout_hops":         tmout_count,
            "max_rtt_ms":           max_rtt,
            "asns_in_path":         " > ".join(all_asns),
            "countries_in_path":    " > ".join(all_cc),
            "timestamp":            ts,
        }

    # Build grouped rows — same data, sorted probe→target→hop
    # Destination info on every row, no probe lat/lon
    grouped_rows = sorted(
        [
            {
                "probe_id":             r["probe_id"],
                "probe_asn":            r["probe_asn"],
                "probe_city":           r["probe_city"],
                "target_label":         r["target_label"],
                "target_category":      r["target_category"],
                "target_hostname":      r["target_hostname"],
                "target_ip":            r["target_ip"],
                "target_asn":           r["target_asn"],
                "target_asn_name":      r["target_asn_name"],
                "target_country":       r["target_country"],
                "destination_responded":r["destination_responded"],
                "hop":                  r["hop"],
                "hop_ip":               r["hop_ip"],
                "rtt_ms":               r["rtt_ms"],
                "hop_asn":              r["hop_asn"],
                "hop_prefix":           r["hop_prefix"],
                "hop_country":          r["hop_country"],
                "hop_asn_name":         r["hop_asn_name"],
                "is_private":           r["is_private"],
                "is_timeout":           r["is_timeout"],
                "measurement_id":       r["measurement_id"],
                "timestamp":            r["timestamp"],
            }
            for r in hop_rows
        ],
        key=lambda x: (x["target_hostname"], x["probe_id"], x["hop"] or 0)
    )

    return hop_rows, sum_row, grouped_rows


# ─────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  RIPE Atlas — Pakistan Multi-Probe Measurement")
    print("=" * 60)

    # Create results folder if it doesn't exist
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print(f"  Results folder: {RESULTS_DIR}")

    # Credits check
    r = requests.get(f"{BASE}/credits/", headers=HDR, timeout=10)
    d = r.json()
    balance = d.get("current_balance", "?")
    print(f"\n  Credits available: {balance:,}" if isinstance(balance, int) else f"\n  Credits: {balance}")

    # Load probes from manual config
    print("\n[1] Probes loaded from config...")
    probes = [
        {
            "probe_id":    pid,
            "asn_v4":      asn,
            "city":        city,
            "description": desc,
            "lat":         None,
            "lon":         None,
        }
        for pid, asn, city, desc in PROBES
    ]
    print(f"  {len(probes)} probe(s) configured:")
    for p in probes:
        print(f"    Probe {p['probe_id']:<10} AS{p['asn_v4']:<8} {p['city']:<15} {p['description']}")

    # Load targets
    print(f"\n[2] Loading targets from {WEBSITES_FILE}...")
    targets = load_targets(WEBSITES_FILE, BATCH_START, BATCH_SIZE)
    print(f"  Loaded {len(targets)} targets")

    # Estimate credit cost
    cost = len(probes) * len(targets) * 20
    print(f"\n  Estimated credit cost: {cost:,} credits")
    print(f"  ({len(probes)} probes × {len(targets)} targets × 20 credits)")

    confirm = input("\n  Proceed? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("  Aborted.")
        return

    # Resolve all hostnames first
    print("\n[3] Resolving hostnames...")
    resolved = []
    for t in targets:
        ip, err = resolve(t["hostname"])
        if err:
            print(f"  ✗ {t['label']:<25} {t['hostname']} — {err}")
        else:
            t["resolved_ip"] = ip
            resolved.append(t)
            print(f"  ✓ {t['label']:<25} {t['hostname']} → {ip}")

    # Schedule measurements
    print(f"\n[4] Scheduling measurements ({len(probes)} probes x {len(resolved)} targets)...")
    scheduled = []

    for probe in probes:
        for t in resolved:
            try:
                mid = create_traceroute(
                    probe["probe_id"],
                    t["resolved_ip"],
                    f"{probe['probe_id']}→{t['label']}"
                )
                scheduled.append((mid, probe, t))
                print(f"  Probe {probe['probe_id']} - {t['label']:<20} ID: {mid}")
                time.sleep(0.3)  # gentle rate limiting
            except requests.HTTPError as e:
                print(f"  ERROR Probe {probe['probe_id']} - {t['label']}: {e.response.status_code}")

        time.sleep(BATCH_WAIT)

    # Wait for ALL measurements in parallel — one poll loop for everything
    print(f"\n[5] Waiting for all {len(scheduled)} measurements to complete...")
    all_msm_ids = [mid for mid, _, _ in scheduled]
    completed   = wait_for_all(all_msm_ids, RESULT_TIMEOUT)

    # Fetch and process results — ONLY for measurements that actually completed.
    # Failed ones (e.g. a disconnected probe → "No suitable probes") have no
    # results; skipping them avoids slow empty fetches and keeps the output a
    # faithful record of the measurements that really ran.
    skipped = [(mid, p, t) for mid, p, t in scheduled if mid not in completed]
    if skipped:
        print(f"\n  Skipping {len(skipped)} measurement(s) with no results "
              f"(disconnected probe / no suitable probes):")
        for _mid, p, t in skipped:
            print(f"    Probe {p['probe_id']} -> {t['label']}")

    print(f"\n[5b] Fetching results for {len(completed)} completed measurement(s)...")
    all_hop_rows = []
    all_grouped  = []
    all_summaries= []

    for msm_id, probe, t in scheduled:
        if msm_id not in completed:
            continue   # failed/incomplete — nothing to fetch
        print(f"  Probe {probe['probe_id']} -> {t['label']}", end="")
        try:
            raw = fetch_result(msm_id)
            print(f" ({len(raw)} result(s))")

            hop_rows, sum_row, grouped_rows = flatten(msm_id, probe, t, raw)
            all_hop_rows.extend(hop_rows)
            all_grouped.extend(grouped_rows)
            if sum_row:
                all_summaries.append(sum_row)

        except Exception as e:
            print(f" ERROR: {e}")

    # Save CSVs
    print(f"\n[6] Saving files...")

    # Sort grouped by probe → target → hop before saving
    all_grouped.sort(key=lambda x: (
        x["target_hostname"],
        x["probe_id"],
        x["hop"] or 0
    ))
    with open(GROUPED_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=GROUPED_FIELDS)
        writer.writeheader()
        writer.writerows(all_grouped)
    print(f"  Grouped CSV → {GROUPED_FILE}")

    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(all_summaries)
    print(f"  Summary CSV → {SUMMARY_FILE}")

    # [6b] Generate the readable per-trace route report (best-effort).
    # Hop ASNs are already enriched live above via registry_lookup(), so this
    # just renders the grouped CSV into routes_*.txt. A failure here must not
    # lose the measurement data, hence the try/except.
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from format_routes import format_file as _format_routes
        routes_path = _format_routes(GROUPED_FILE)
        print(f"  Readable routes → {routes_path}")
    except Exception as e:
        print(f"  (skipped readable routes — run format_routes.py manually: {e})")


    print(f"\n  Scheduled          : {len(scheduled)}")
    print(f"  Completed (in CSV) : {len(all_summaries)}")
    print(f"  Skipped (no result): {len(skipped)}")
    print(f"  Total hop rows     : {len(all_hop_rows)}")
    print("=" * 60)


if __name__ == "__main__":
    main()