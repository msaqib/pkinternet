#!/usr/bin/env python3
"""
Exp 4.1 — Phase 0: enumerate the COMPLETE block universe of all small (FLL) ISPs.
=================================================================================
Reads the FLL licensee roster (data/pk_isp_fll_list.csv), and for every ISP with a
usable ASN, pulls its currently-announced IPv4 prefixes from RIPEstat (no key, no
credits). Writes the full destination universe + a per-ISP summary, and prints a
cost estimate for a complete TCP-traceroute sweep.

    python experiments/04.1_small_isp_tromboning/enumerate_small_isps.py

Output: results/blocks_all.csv   (one row per announced prefix = one block)
        results/isp_summary.csv  (one row per ISP)
"""
import os, csv, time, ipaddress
import requests

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..", "..")
FLL = os.path.join(ROOT, "data", "pk_isp_fll_list.csv")
OUT = os.path.join(HERE, "results")
RIPESTAT = "https://stat.ripe.net/data/announced-prefixes/data.json"
UA = {"User-Agent": "pkinternet-exp4.1/0.1"}

# sweep parameters (for the cost estimate only; the actual sweep script uses these)
IPS_PER_BLOCK = 8
SOURCE_PROBES = 7
CREDITS_PER_TRACEROUTE = 20


def announced_v4(asn):
    try:
        r = requests.get(RIPESTAT, params={"resource": f"AS{asn}"}, headers=UA, timeout=30)
        r.raise_for_status()
        out = []
        for p in r.json()["data"]["prefixes"]:
            try:
                net = ipaddress.ip_network(p["prefix"], strict=False)
            except ValueError:
                continue
            if net.version == 4:
                out.append(net)
        return out
    except Exception as e:
        print(f"    ! AS{asn} failed: {e}")
        return []


def main():
    os.makedirs(OUT, exist_ok=True)
    # company + asn (dedupe ASNs, keep first company name)
    isps = {}
    for r in csv.DictReader(open(FLL, encoding="utf-8")):
        a = (r.get("asn") or "").strip().lstrip("AS")
        if a.isdigit() and a not in isps:
            isps[a] = r.get("company_name", "").strip()

    blocks_rows = []
    isp_rows = []
    tot_blocks = tot_addrs = tot_24eq = 0
    print(f"Enumerating {len(isps)} FLL ISP ASNs via RIPEstat...")
    for asn, name in sorted(isps.items(), key=lambda x: int(x[0])):
        nets = announced_v4(asn)
        addrs = sum(n.num_addresses for n in nets)
        eq24 = sum(max(1, n.num_addresses // 256) for n in nets)
        tot_blocks += len(nets); tot_addrs += addrs; tot_24eq += eq24
        isp_rows.append(dict(asn=asn, company=name, prefixes=len(nets),
                             addresses=addrs, eq_24=eq24))
        for n in nets:
            blocks_rows.append(dict(asn=asn, company=name, prefix=str(n),
                                    prefix_len=n.prefixlen, num_addresses=n.num_addresses))
        print(f"  AS{asn:<8} {name[:38]:38} {len(nets):>4} prefixes, {addrs:>7,} addrs")
        time.sleep(0.2)

    with open(os.path.join(OUT, "blocks_all.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["asn", "company", "prefix", "prefix_len", "num_addresses"])
        w.writeheader(); w.writerows(blocks_rows)
    with open(os.path.join(OUT, "isp_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["asn", "company", "prefixes", "addresses", "eq_24"])
        w.writeheader()
        for row in sorted(isp_rows, key=lambda x: -x["eq_24"]): w.writerow(row)

    live = [r for r in isp_rows if r["prefixes"] > 0]
    traces = tot_blocks * IPS_PER_BLOCK * SOURCE_PROBES
    print("\n" + "=" * 64)
    print(f"  ISPs with announced prefixes : {len(live)} / {len(isps)}")
    print(f"  announced blocks (prefixes)  : {tot_blocks:,}")
    print(f"  /24-equivalents              : {tot_24eq:,}")
    print(f"  total addresses              : {tot_addrs:,}")
    print(f"\n  COMPLETE sweep cost estimate ({IPS_PER_BLOCK} IPs/block x {SOURCE_PROBES} sources):")
    print(f"    traceroutes/pass : {traces:,}")
    print(f"    credits/pass     : ~{traces * CREDITS_PER_TRACEROUTE:,}")
    print(f"  wrote results/blocks_all.csv ({tot_blocks} blocks), results/isp_summary.csv")
    print("=" * 64)
    print("\n  Largest small ISPs by /24-equivalents:")
    for r in sorted(isp_rows, key=lambda x: -x["eq_24"])[:10]:
        print(f"    AS{r['asn']:<8} {r['company'][:36]:36} {r['eq_24']:>5} /24-eq")


if __name__ == "__main__":
    main()
