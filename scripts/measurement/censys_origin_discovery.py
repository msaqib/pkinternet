#!/usr/bin/env python3
"""
Censys cert-CN origin discovery
================================
For each financial-institution domain in a target CSV, searches Censys for
hosts presenting a TLS certificate whose common name matches that domain
(exact) or "*.domain" (wildcard cert). The point: sites that look "abroad"
or "CDN" from the outside (Cloudflare/AWS CloudFront/Sucuri etc.) may still
have a real local Pakistani server behind the CDN, terminating TLS with the
same certificate. That server usually has no public DNS record of its own,
so it doesn't show up in a normal hosting check, but Censys's internet-wide
port-443 cert scan finds it anyway.

This script only does discovery + filtering. It does NOT confirm domestic
reachability, that still needs a real ping/traceroute from a Pakistani
vantage point (RIPE Atlas / Globalping), same as Exp 13's BGP-found IPs
were confirmed. Treat this script's output as a candidate list to verify,
not a final answer.

Requirements: pip install censys-platform python-dotenv
Auth: needs CENSYS_PAT and CENSYS_ORG_ID in .env (Censys Platform ->
Account -> Personal Access Tokens). Free-tier Censys accounts can run
host/cert search; you do not need a paid plan for this.

Usage (run from repo root):
    python scripts/measurement/censys_origin_discovery.py
    python scripts/measurement/censys_origin_discovery.py --targets data/financial_institutions_targets.csv
    python scripts/measurement/censys_origin_discovery.py --domain hbl.com --debug

Results saved to:
    experiments/15_censys_origin_discovery/results/censys_candidates_{timestamp}.csv
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

CENSYS_PAT = os.environ.get("CENSYS_PAT", "")
CENSYS_ORG_ID = os.environ.get("CENSYS_ORG_ID", "")

PK_ASN_FILE = "data/pk_asn_names.json"
DEFAULT_TARGETS_FILE = "data/financial_institutions_targets.csv"
RESULTS_DIR = "experiments/15_censys_origin_discovery/results"

FIELDS = [
    "host.ip",
    "host.location.country",
    "host.location.city",
    "host.autonomous_system.asn",
    "host.autonomous_system.name",
    "host.services.port",
    "host.services.cert.parsed.subject.common_name",
    "host.services.cert.parsed.validity_period.not_after",
]

OUTPUT_FIELDS = [
    "domain", "query_type", "ip", "asn", "as_name", "is_pk_asn",
    "country", "city", "port", "cert_common_name", "cert_not_after",
    "cert_expired",
]


def load_targets(filepath):
    with open(filepath, newline="") as f:
        return list(csv.DictReader(f))


def load_pk_asns():
    if not os.path.exists(PK_ASN_FILE):
        print(f"  [warn] {PK_ASN_FILE} not found, is_pk_asn will be blank for everything")
        return {}
    with open(PK_ASN_FILE) as f:
        return json.load(f)


def cert_is_expired(not_after):
    if not not_after:
        return None
    try:
        expiry = datetime.fromisoformat(not_after.replace("Z", "+00:00"))
        return expiry < datetime.now(timezone.utc)
    except ValueError:
        return None


def extract_hits(res, debug=False):
    """
    The censys-platform SDK is a generated client; the exact attribute path
    of the parsed response isn't pinned down in public docs at the time this
    was written. Try the likely shapes, and fall back to dumping the raw
    object so a human can see what's actually there.
    """
    candidates = []

    for attr_path in (
        lambda r: r.result.hits,
        lambda r: r.search_query_response.result.hits,
        lambda r: r.object.result.hits,
    ):
        try:
            hits = attr_path(res)
            if hits is not None:
                return hits
        except AttributeError:
            continue

    # pydantic model fallback
    for dump_method in ("model_dump", "dict"):
        if hasattr(res, dump_method):
            try:
                data = getattr(res, dump_method)()
                hits = (
                    data.get("result", {}).get("hits")
                    or data.get("search_query_response", {}).get("result", {}).get("hits")
                )
                if hits is not None:
                    return hits
            except Exception:
                continue

    if debug:
        print("  [debug] could not locate hits in response, dumping raw object:")
        print(repr(res)[:4000])

    return candidates


def search_censys(sdk, query, debug=False):
    try:
        res = sdk.global_data.search(
            search_query_input_body={
                "fields": FIELDS,
                "page_size": 50,
                "query": query,
            }
        )
    except Exception as e:
        print(f"  [error] Censys query failed: {e}")
        return []
    return extract_hits(res, debug=debug)


def flatten_hit(hit, domain, query_type, pk_asns):
    """
    hit is expected to be a dict-like nested structure matching FIELDS.
    Exact nesting depends on the API response shape; handle both nested
    dict and flat dotted-key shapes defensively.
    """
    def get(path, default=None):
        # try dotted-key flat access first
        if path in hit:
            return hit[path]
        # try nested dict walk
        cur = hit
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur

    ip = get("host.ip") or get("ip")
    asn = get("host.autonomous_system.asn") or get("autonomous_system.asn")
    as_name = get("host.autonomous_system.name") or get("autonomous_system.name")
    country = get("host.location.country") or get("location.country")
    city = get("host.location.city") or get("location.city")
    port = get("host.services.port") or get("services.port")
    cn = get("host.services.cert.parsed.subject.common_name") or get(
        "services.cert.parsed.subject.common_name"
    )
    not_after = get("host.services.cert.parsed.validity_period.not_after") or get(
        "services.cert.parsed.validity_period.not_after"
    )

    asn_key = str(asn).lstrip("AS") if asn else None

    return {
        "domain": domain,
        "query_type": query_type,
        "ip": ip,
        "asn": asn,
        "as_name": as_name,
        "is_pk_asn": bool(pk_asns.get(asn_key)) if asn_key else None,
        "country": country,
        "city": city,
        "port": port,
        "cert_common_name": cn,
        "cert_not_after": not_after,
        "cert_expired": cert_is_expired(not_after) if not_after else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", default=DEFAULT_TARGETS_FILE, help="CSV with a 'domain' column")
    parser.add_argument("--domain", help="run for a single domain instead of the targets file")
    parser.add_argument("--sleep", type=float, default=1.0, help="seconds between Censys queries")
    parser.add_argument("--debug", action="store_true", help="dump raw response shape on parse failure")
    args = parser.parse_args()

    if not CENSYS_PAT:
        sys.exit(
            "CENSYS_PAT not set. Add it to .env (Censys account -> Personal "
            "Access Tokens)."
        )
    if not CENSYS_ORG_ID:
        print(
            "  [warn] CENSYS_ORG_ID not set, running under free-account "
            "permissions instead of an org."
        )

    try:
        from censys_platform import SDK
    except ImportError:
        sys.exit("censys-platform not installed. Run: pip install censys-platform")

    if args.domain:
        targets = [{"domain": args.domain, "name": args.domain}]
    else:
        targets = load_targets(args.targets)

    pk_asns = load_pk_asns()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(RESULTS_DIR, f"censys_candidates_{timestamp}.csv")

    rows = []
    seen_ips_per_domain = {}

    sdk_kwargs = {"personal_access_token": CENSYS_PAT}
    if CENSYS_ORG_ID:
        sdk_kwargs["organization_id"] = CENSYS_ORG_ID

    with SDK(**sdk_kwargs) as sdk:
        for target in targets:
            domain = target["domain"].strip()
            print(f"[{domain}]")
            seen_ips_per_domain.setdefault(domain, set())

            queries = [
                ("exact_or_subdomain", f'host.services.cert.parsed.subject.common_name: "{domain}"'),
                ("wildcard", f'host.services.cert.parsed.subject.common_name: "*.{domain}"'),
            ]

            for query_type, query in queries:
                hits = search_censys(sdk, query, debug=args.debug)
                print(f"  {query_type}: {len(hits)} hit(s)")
                for hit in hits:
                    row = flatten_hit(hit, domain, query_type, pk_asns)
                    if row["ip"] in seen_ips_per_domain[domain]:
                        continue
                    seen_ips_per_domain[domain].add(row["ip"])
                    rows.append(row)
                time.sleep(args.sleep)

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    pk_hits = [r for r in rows if r["is_pk_asn"]]
    print(f"\nWrote {len(rows)} candidate row(s) to {output_file}")
    print(f"{len(pk_hits)} of those are on a known Pakistani ASN, review those first.")


if __name__ == "__main__":
    main()
