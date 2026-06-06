#!/usr/bin/env python3
"""
Readable route formatter
========================
Turns a verbose per-hop `pk_grouped_*.csv` into a human-readable route report
where each traceroute is ONE block:

    - a header that states the SOURCE and DESTINATION once (no more repeating
      the destination on every hop row), and
    - the hop-by-hop route underneath (hop #, rtt, ip, asn, operator/country).

Usage (run from repo root):
    python scripts/measurement/format_routes.py                 # all grouped CSVs
    python scripts/measurement/format_routes.py path/to.csv ...  # specific files

For each input `pk_grouped_*.csv` it writes a sibling `*_routes.txt`.
"""

import csv
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo_utils import serving_location, ANYCAST_ASNS  # noqa: E402

RESULTS_GLOB = os.path.join(
    "experiments", "01_website_destinations", "results",
    "run_*", "pk_grouped_*.csv",
)


def short_operator(asn_name: str) -> str:
    """'ZCOMNETWORKS-AS-AP - Z COM NETWORKS, PK' -> 'Z COM NETWORKS'."""
    if not asn_name:
        return ""
    s = asn_name
    if " - " in s:
        s = s.split(" - ", 1)[1]
    head, _, tail = s.rpartition(", ")
    if head and len(tail.strip()) <= 3:   # strip trailing ', PK' / ', US'
        s = head
    return s.strip()


def describe_hop(row: dict) -> str:
    """One formatted line for a single hop."""
    hop = row["hop"]
    if row.get("is_timeout", "").lower() == "true" or row["hop_ip"] == "*":
        return f"  {hop:>3}      *     {'(no response)':<18}"

    rtt = row["rtt_ms"]
    try:
        rtt = f"{float(rtt):.1f}"
    except (ValueError, TypeError):
        rtt = "?"

    ip = row["hop_ip"]
    asn = row["hop_asn"]
    op = short_operator(row.get("hop_asn_name", ""))
    cc = row.get("hop_country", "")
    if row.get("is_private", "").lower() == "true":
        asn_str, who = "—", "(private/internal)"
    elif asn:
        asn_str = f"AS{asn}"
        who = f"{op} ({cc})" if cc else op
    elif op or cc:
        # No BGP origin AS, but RDAP registry gave us an operator/country hint.
        asn_str = "—"
        who = (f"{op} ({cc})" if op and cc else op or cc) + "  [registry]"
    else:
        asn_str, who = "—", "(unknown)"

    return f"  {hop:>3}  {rtt:>7}   {ip:<18} {asn_str:<9} {who}"


def format_trace(rows: list) -> str:
    """Render one measurement (list of hop rows) as a readable block."""
    first = rows[0]
    src_op = short_operator_from_asn(first["probe_asn"])
    dest_op = short_operator(first["target_asn_name"])
    dest_cc = first["target_country"]
    responded = first["destination_responded"].lower() == "true"
    reach = "reached, host replied" if responded else "host did NOT reply (trace incomplete)"

    lines = []
    lines.append("=" * 78)
    lines.append(f" {first['target_hostname']}   —   {first['target_label']}  ({first['target_category']})")
    src_label = f"{src_op} (AS{first['probe_asn']})" if src_op else f"AS{first['probe_asn']}"
    lines.append(f" SOURCE   probe {first['probe_id']} · {src_label} · {first['probe_city']}")
    lines.append(
        f" DEST     {first['target_ip']} · {dest_op} (AS{first['target_asn']})"
        f"{' · ' + dest_cc if dest_cc else ''} · {reach}"
    )

    # Actual location (not the ASN registration country). For anycast CDNs we can
    # only see where the probe ENTERS the CDN's network (the handoff), not where
    # HTTP is ultimately served — so we label it ENTERS, not SERVED. A real
    # (unicast) server genuinely is SERVED at its geolocated location.
    loc, via = serving_location(rows, first["target_asn"], first["target_ip"])
    if first["target_asn"] in ANYCAST_ASNS:
        if loc:
            lines.append(f" ENTERS   {loc}   ({ANYCAST_ASNS[first['target_asn']]} network — this probe's {via}; not necessarily where HTTP is served)")
        else:
            lines.append(f" ENTERS   (could not infer — trace filtered before the CDN; see RTT)")
    elif loc:
        lines.append(f" SERVED   {loc}   (server geolocation)")

    lines.append("-" * 78)
    lines.append(f"  hop   rtt(ms)   {'ip':<18} {'asn':<9} operator (country)")

    for row in rows:
        line = describe_hop(row)
        if row["hop_ip"] == first["target_ip"]:
            line += "   <<< DESTINATION"
        lines.append(line)

    lines.append("")
    return "\n".join(lines)


# Probe ASN -> friendly source operator (probe rows only carry the ASN number).
PROBE_ASN_NAMES = {
    "152605": "Z-Com",
    "23674": "Nayatel",
    "38193": "Transworld",
    "17557": "PTCL",
    "9541": "Cybernet",
    "9260": "Multinet",
    "45773": "PERN",
    "23888": "NTC",
    "38264": "Wateen",
}


def short_operator_from_asn(asn: str) -> str:
    return PROBE_ASN_NAMES.get(str(asn).strip(), "")


def format_file(path: str) -> str:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    # Group consecutive rows by measurement_id, preserving file order.
    traces, current, current_id = [], [], None
    for row in rows:
        mid = row["measurement_id"]
        if mid != current_id and current:
            traces.append(current)
            current = []
        current.append(row)
        current_id = mid
    if current:
        traces.append(current)

    out_name = os.path.basename(path).replace("pk_grouped_", "routes_").replace(".csv", ".txt")
    out_path = os.path.join(os.path.dirname(path), out_name)

    header = [
        f"Readable routes  —  {os.path.basename(path)}",
        f"{len(traces)} traceroutes  ·  destination shown once per block (in the DEST header)",
        "",
    ]
    body = "\n".join(header) + "\n" + "\n".join(format_trace(t) for t in traces)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return out_path


def main():
    paths = sys.argv[1:] or sorted(glob.glob(RESULTS_GLOB))
    if not paths:
        print("No grouped CSVs found. Run from the repo root (pkinternet/).")
        return
    for path in paths:
        out = format_file(path)
        print(f"  {path}\n   -> {out}")


if __name__ == "__main__":
    main()
