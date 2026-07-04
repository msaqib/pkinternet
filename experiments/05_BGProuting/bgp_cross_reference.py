#!/usr/bin/env python3
"""
BGP Cross-Reference Validation
Validates observed AS paths from bgp_validation_results.csv against
actual peer tables from bgp.he.net.

Logic:
For each unique observed path, check if each transit ASN in that path
is explainable by the probe ISP's known peers (or their upstream's peers).
If yes → consistent. If no → flag for review.
"""

import pandas as pd
from collections import defaultdict

# ── Peer tables from bgp.he.net (fetched June 2026) ──────────────────────────
# Format: ASN → set of known peers
# For smaller ISPs that only have 1-2 upstreams, we also include
# the upstream's peers (since traffic flows through them)

DIRECT_PEERS = {
    # PTCL (AS17557) — large ISP, direct international peers
    17557: {8529, 7473, 8966, 3491, 1299, 174, 3356, 6461, 58682, 6939, 2914},

    # Transworld/TWA (AS38193) — direct international peers
    38193: {6762, 8529, 174, 3356, 7473, 8966, 58453, 3320, 138423, 6461,
            13335,  # Cloudflare — Transworld directly peers with Cloudflare!
            9260},  # Multinet — local Pakistani peer

    # Nayatel (AS23674) — only 2 peers: PTCL and Transworld
    23674: {17557, 38193},

    # Cybernet (AS9541) — known peers from traceroute + public data
    9541:  {1299, 8529, 6939, 38193, 174, 3356, 13335},

    # Zcom (AS152605) — uses Transworld as primary upstream
    152605: {38193},

    # Nova (AS136174) — uses Shaw Canada (AS6327) as upstream
    136174: {6327},
}

# For ISPs that only have Pakistani upstreams (Nayatel, Zcom, Nova),
# they can also reach anything their upstream can reach.
# So we need upstream's peers too.
UPSTREAM_PEERS = {
    23674:  DIRECT_PEERS[38193],   # Nayatel uses Transworld → inherits TWA's peers
    152605: DIRECT_PEERS[38193],   # Zcom uses Transworld → inherits TWA's peers
    136174: DIRECT_PEERS[17557] | DIRECT_PEERS[38193],  # Nova uses Shaw → inherits both
}

# ASN to name mapping for readable output
ASN_NAMES = {
    1299:   "Arelion/Telia (Sweden)",
    2914:   "NTT (Japan)",
    3320:   "Deutsche Telekom (Germany)",
    3356:   "Lumen/Level3 (US/UK)",
    3491:   "PCCW Global (HK)",
    6327:   "Shaw Communications (Canada)",
    6461:   "Zayo (US)",
    6762:   "Telecom Italia Sparkle (Italy)",
    6939:   "Hurricane Electric (US)",
    7473:   "SingTel (Singapore)",
    8529:   "Zain Omantel (Oman)",
    8966:   "Etisalat (UAE)",
    9260:   "Multinet Pakistan",
    13335:  "Cloudflare",
    17557:  "PTCL",
    20940:  "Akamai",
    23674:  "Nayatel",
    30148:  "Sucuri (US)",
    38193:  "Transworld",
    45102:  "Alibaba",
    58453:  "China Mobile International (HK)",
    9541:   "Cybernet",
    136174: "Nova",
    152605: "Zcom",
    19551:  "Incapsula/Imperva (US)",
    4845:   "Alibaba/Singapore",
}

ISP_ASN = {
    'ptcl':       17557,
    'transworld': 38193,
    'nayatel':    23674,
    'cybernet':   9541,
    'zcom':       152605,
    'nova':       136174,
}


def parse_path(path_str):
    if pd.isna(path_str) or not str(path_str).strip():
        return []
    try:
        return [int(x.strip()) for x in str(path_str).split(">")]
    except Exception:
        return []


def get_all_known_peers(probe_asn):
    """Get all ASNs reachable via this probe's peers (direct + upstream)."""
    peers = set(DIRECT_PEERS.get(probe_asn, set()))
    peers |= set(UPSTREAM_PEERS.get(probe_asn, set()))
    # Also add the upstream's peers recursively one level
    for p in list(peers):
        peers |= set(DIRECT_PEERS.get(p, set()))
    return peers


def validate_path_against_peers(observed_path, probe_asn, isp_name):
    """
    Check each transit ASN in observed path against known peers.
    Returns (verdict, details)
    """
    if len(observed_path) <= 1:
        return "no_transit", "only destination ASN visible"

    # transit = everything except first (probe ISP) and last (destination)
    # but first ASN might be the probe itself or might already be transit
    transit_asns = observed_path[1:-1] if len(observed_path) > 2 else []
    dest_asn = observed_path[-1]

    if not transit_asns:
        # direct connection: probe ISP → destination
        # check if destination is in known peers
        all_peers = get_all_known_peers(probe_asn)
        if dest_asn in all_peers or dest_asn in DIRECT_PEERS.get(probe_asn, set()):
            return "consistent_direct", f"direct peer to AS{dest_asn} ({ASN_NAMES.get(dest_asn, 'unknown')})"
        else:
            return "unverified_direct", f"no record of direct peering with AS{dest_asn}"

    all_peers = get_all_known_peers(probe_asn)
    unverified = []
    verified = []

    for asn in transit_asns:
        name = ASN_NAMES.get(asn, f"AS{asn}")
        if asn in all_peers:
            verified.append(f"AS{asn} ({name}) ✅")
        else:
            unverified.append(f"AS{asn} ({name}) ❓")

    if not unverified:
        return "consistent", f"all transit ASNs verified: {', '.join(verified)}"
    elif not verified:
        return "unverified", f"no transit ASNs in peer table: {', '.join(unverified)}"
    else:
        return "partial_verified", f"verified: {', '.join(verified)} | unverified: {', '.join(unverified)}"


def main():
    print("Loading BGP validation results...")
    df = pd.read_csv('findings/bgp_validation_results.csv')

    # Get unique observed paths per ISP
    unique_paths = df[df['observed_path'].notna() & df['validation'].isin(['partial', 'no_match'])]\
        .groupby(['isp', 'target_hostname', 'observed_path'])\
        .size().reset_index(name='count')\
        .sort_values(['isp', 'count'], ascending=[True, False])

    print(f"\nValidating {len(unique_paths)} unique (ISP, site, path) combinations\n")
    print("=" * 70)

    results = []
    for _, row in unique_paths.iterrows():
        isp = row['isp']
        site = row['target_hostname']
        path_str = row['observed_path']
        count = row['count']
        path = parse_path(path_str)
        probe_asn = ISP_ASN.get(isp)

        if not probe_asn or not path:
            continue

        verdict, details = validate_path_against_peers(path, probe_asn, isp)

        print(f"ISP: {isp:<12} Site: {site:<20} Count: {count}")
        print(f"  Path:    {path_str}")
        print(f"  Verdict: {verdict.upper()}")
        print(f"  Details: {details}")
        print()

        results.append({
            'isp': isp,
            'site': site,
            'observed_path': path_str,
            'count': count,
            'verdict': verdict,
            'details': details,
        })

    out = pd.DataFrame(results)
    out.to_csv('findings/bgp_peer_validation.csv', index=False)

    print("=" * 70)
    print("\n=== Summary ===")
    print(out['verdict'].value_counts())
    print("\n=== By ISP ===")
    print(out.groupby(['isp', 'verdict']).size().unstack(fill_value=0))
    print("\nSaved to findings/bgp_peer_validation.csv")


if __name__ == "__main__":
    main()