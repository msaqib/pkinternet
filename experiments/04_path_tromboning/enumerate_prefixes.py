#!/usr/bin/env python3
"""
Exp 04 — Phase 0: enumerate an ISP's announced BGP prefixes (target universe).
==============================================================================
Pulls the prefixes an ASN currently announces from the RIPEstat data API
(no key needed) and writes a target list — the principled answer to "which IPs
do we probe, and why". Each announced prefix is one sampling unit for the
tromboning sweep (Phase 1).

    python experiments/04_path_tromboning/enumerate_prefixes.py 38710
    python experiments/04_path_tromboning/enumerate_prefixes.py 38710 --sample 1

--sample N adds N candidate target IP(s) per prefix (the .1 ... offsets), a
convenience for the Phase-1 responsiveness sweep; pass 0 to list prefixes only.
Output: results/targets_AS<asn>.csv
"""
import sys, os, csv, ipaddress
import requests

RIPESTAT = "https://stat.ripe.net/data/announced-prefixes/data.json"
ASNAME   = "https://stat.ripe.net/data/as-overview/data.json"
OUT_DIR  = os.path.join(os.path.dirname(__file__), "results")


def announced_prefixes(asn):
    r = requests.get(RIPESTAT, params={"resource": f"AS{asn}"}, timeout=30,
                     headers={"User-Agent": "pkinternet-exp04/0.1"})
    r.raise_for_status()
    return [p["prefix"] for p in r.json()["data"]["prefixes"]]


def as_name(asn):
    try:
        r = requests.get(ASNAME, params={"resource": f"AS{asn}"}, timeout=15,
                         headers={"User-Agent": "pkinternet-exp04/0.1"})
        return r.json()["data"].get("holder", "")
    except Exception:
        return ""


def main():
    args = [a for a in sys.argv[1:]]
    if not args or not args[0].lstrip("AS").isdigit():
        sys.exit("usage: enumerate_prefixes.py <ASN> [--sample N]")
    asn = args[0].lstrip("AS")
    sample = 1
    if "--sample" in args:
        sample = int(args[args.index("--sample") + 1])

    holder = as_name(asn)
    prefixes = announced_prefixes(asn)

    # IPv4 only for Exp 04; sort by size (largest blocks first)
    nets = []
    for p in prefixes:
        try:
            net = ipaddress.ip_network(p, strict=False)
        except ValueError:
            continue
        if net.version == 4:
            nets.append(net)
    nets.sort(key=lambda n: (-n.num_addresses, int(n.network_address)))

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"targets_AS{asn}.csv")
    total_addrs = 0
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["asn", "as_name", "prefix", "prefix_len", "num_addresses",
                    "sample_targets"])
        for net in nets:
            total_addrs += net.num_addresses
            samples = []
            if sample and net.num_addresses > sample + 2:
                hosts = net.network_address
                # spread a few candidate IPs across the block (.1, midpoints)
                offs = [1] + [net.num_addresses * k // (sample + 1)
                              for k in range(1, sample)] if sample > 1 else [1]
                for o in offs[:sample]:
                    samples.append(str(net.network_address + o))
            w.writerow([asn, holder, str(net), net.prefixlen,
                        net.num_addresses, " ".join(samples)])

    # summary
    bylen = {}
    for n in nets:
        bylen[n.prefixlen] = bylen.get(n.prefixlen, 0) + 1
    print(f"AS{asn}  {holder}")
    print(f"  {len(nets)} IPv4 prefixes announced, {total_addrs:,} addresses total")
    print("  by prefix length: " +
          ", ".join(f"/{k}×{v}" for k, v in sorted(bylen.items())))
    print(f"  wrote {out}")
    print("\n  largest blocks:")
    for n in nets[:8]:
        print(f"    {str(n):20} {n.num_addresses:>8,} addrs")


if __name__ == "__main__":
    main()
