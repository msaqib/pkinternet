#!/usr/bin/env python3
"""
Every IP the tromboning classifier ever labelled foreign, with the incremental RTT that
hop adds over the last responding hop before it, and a check against known foreign IXP
peering LANs.

Outputs, both written next to this script:
  foreign_hops.csv   one row per distinct foreign-classified IP
  foreign_hops.txt   readable summary, IXP matches first

Incremental RTT is (RTT of this hop) minus (RTT of the nearest preceding responding,
non-private hop) in the same trace. It is a noisy quantity: return paths differ per hop
and routers vary in how fast they generate ICMP, so a fraction of increments are negative.
The negative share is reported so the noise floor is visible rather than assumed away.

    python experiments/07_longitudinal_panel/analysis/foreign_hop_audit.py
"""
import collections
import csv
import gzip
import json
import os
import statistics as st

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RES = os.path.join(EXP, "results")

FLOOR, CEIL = 40.0, 500.0
ARTIFACT = {"6327", "174"}
PRIV = ("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.3")
EXCLUDE_PROBES = {1015491, 7764}

# Known peering-LAN prefixes of foreign exchanges, from PeeringDB/Euro-IX published ranges.
IXP_LANS = [
    ("27.111.228.0/22", "Equinix Singapore"),
    ("103.16.102.0/23", "SGIX Singapore"),
    ("218.100.52.0/23", "Megaport Singapore"),
    ("123.255.90.0/23", "HKIX Hong Kong"),
    ("103.247.139.0/24", "BBIX Hong Kong"),
    ("80.81.192.0/21", "DE-CIX Frankfurt"),
    ("80.249.208.0/21", "AMS-IX Amsterdam"),
    ("195.66.224.0/21", "LINX London"),
    ("206.126.236.0/22", "Equinix Ashburn"),
    ("206.223.116.0/22", "Equinix Chicago"),
    ("198.32.176.0/24", "Equinix Palo Alto"),
    ("185.1.0.0/16", "Euro-IX allocation, various European exchanges"),
    ("196.60.96.0/22", "NAPAfrica Johannesburg"),
    ("91.210.16.0/23", "UAE-IX Dubai"),
]


def in_net(ip, cidr):
    net, bits = cidr.split("/")
    bits = int(bits)
    try:
        a = [int(x) for x in ip.split(".")]
        b = [int(x) for x in net.split(".")]
    except ValueError:
        return False
    if len(a) != 4 or len(b) != 4:
        return False
    ia = (a[0] << 24) | (a[1] << 16) | (a[2] << 8) | a[3]
    ib = (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]
    mask = (0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF
    return (ia & mask) == (ib & mask)


def ixp_of(ip):
    for cidr, name in IXP_LANS:
        if in_net(ip, cidr):
            return name, cidr
    return "", ""


def main():
    lut, org = {}, {}
    h = pd.read_csv(os.path.join(HERE, "hop_annotations.csv"))
    for _, r in h.iterrows():
        lut[r.ip] = (str(int(r.asn)) if pd.notna(r.asn) else "",
                     r.cc if pd.notna(r.cc) else "")
    cym = json.load(open(os.path.join(HERE, "_cymru_bulk_result.json"), encoding="utf-8"))
    for ip, v in cym.items():
        if v.get("asn") and v["asn"] != "NA":
            lut[ip] = (v["asn"], v.get("country", ""))
        if v.get("as_name"):
            org[ip] = v["as_name"]
    rd = json.load(open(os.path.join(HERE, "_rdap_result.json"), encoding="utf-8"))
    for ip, v in rd.items():
        if v.get("country"):
            lut[ip] = (lut.get(ip, ("", ""))[0], v["country"])
        if v.get("name") and ip not in org:
            org[ip] = v["name"]

    hg = pd.read_csv(os.path.join(HERE, "hop_geo.csv"))
    city = {r.ip: (str(r.city) if pd.notna(r.city) else "") for _, r in hg.iterrows()}

    cls = pd.read_csv(os.path.join(HERE, "targets_corrected.csv")) \
        .set_index("target")["cls_corrected"]
    pk = set(cls[cls == "Pakistan"].index)
    meas = json.load(open(os.path.join(RES, "a", "measurements.json"), encoding="utf-8"))
    msm_of = {v: k for k, v in meas["trace"].items()}

    print("loading raw archive...")
    arch = json.load(gzip.open(os.path.join(RES, "a", "raw_a_20260718_201113.json.gz"),
                               "rt", encoding="utf-8"))

    hits = collections.defaultdict(list)     # ip -> [incremental rtt]
    absol = collections.defaultdict(list)    # ip -> [absolute rtt]
    exits = collections.Counter()            # ip -> times it was the FIRST foreign hop
    seen = collections.Counter()             # ip -> times it qualified at all
    probes = collections.defaultdict(set)
    no_prev = collections.Counter()

    for mid, rds in arch.items():
        if not mid.isdigit() or msm_of.get(int(mid)) not in pk:
            continue
        for rd_ in rds:
            prb = rd_.get("prb_id")
            if prb in EXCLUDE_PROBES:
                continue
            hops = []
            for hh in rd_.get("result", []):
                p = hh.get("result", [])
                ip = next((x.get("from") for x in p if x.get("from")), None)
                rr = [x["rtt"] for x in p if isinstance(x.get("rtt"), (int, float))]
                hops.append((ip, min(rr) if rr else None))

            first = True
            for i, (ip, rtt) in enumerate(hops):
                if not ip or rtt is None or ip.startswith(PRIV):
                    continue
                asn, cc = lut.get(ip, ("", ""))
                if not (cc and cc != "PK" and asn not in ARTIFACT
                        and FLOOR <= rtt <= CEIL):
                    continue
                seen[ip] += 1
                probes[ip].add(prb)
                absol[ip].append(rtt)
                prev = None
                for j in range(i - 1, -1, -1):
                    pip, pv = hops[j]
                    if pip and pv is not None and not pip.startswith(PRIV):
                        prev = pv
                        break
                if prev is None:
                    no_prev[ip] += 1
                else:
                    hits[ip].append(rtt - prev)
                if first:
                    exits[ip] += 1
                    first = False

    rows = []
    for ip in sorted(seen, key=lambda x: -seen[x]):
        inc = sorted(hits[ip])
        a = sorted(absol[ip])
        asn, cc = lut.get(ip, ("", ""))
        name, cidr = ixp_of(ip)
        rows.append({
            "ip": ip,
            "asn": asn,
            "registered_cc": cc,
            "org": org.get(ip, ""),
            "geoip_city": city.get(ip, ""),
            "times_qualified": seen[ip],
            "times_first_foreign_hop": exits[ip],
            "n_probes": len(probes[ip]),
            "rtt_median_ms": round(st.median(a), 1) if a else "",
            "rtt_min_ms": round(a[0], 1) if a else "",
            "rtt_max_ms": round(a[-1], 1) if a else "",
            "incr_rtt_median_ms": round(st.median(inc), 1) if inc else "",
            "incr_rtt_p10_ms": round(inc[int(0.10 * len(inc))], 1) if inc else "",
            "incr_rtt_p90_ms": round(inc[int(0.90 * len(inc))], 1) if inc else "",
            "incr_negative_pct": round(100 * sum(1 for x in inc if x < 0) / len(inc), 1) if inc else "",
            "incr_samples": len(inc),
            "no_preceding_hop": no_prev[ip],
            "ixp_peering_lan": name,
            "ixp_prefix": cidr,
        })

    out_csv = os.path.join(HERE, "foreign_hops.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    tot_q = sum(seen.values())
    tot_e = sum(exits.values())
    all_inc = [x for v in hits.values() for x in v]
    ixp_rows = [r for r in rows if r["ixp_peering_lan"]]

    lines = []
    lines.append("FOREIGN-CLASSIFIED HOPS, Exp 07 panel, Pakistani-hosted targets")
    lines.append("=" * 78)
    lines.append("distinct IPs classified foreign          : %d" % len(rows))
    lines.append("hop observations qualifying as foreign   : %d" % tot_q)
    lines.append("of which were the FIRST foreign hop      : %d (these drive the verdicts)" % tot_e)
    lines.append("")
    lines.append("INCREMENTAL RTT over the preceding responding hop")
    lines.append("  samples %d   median %.1f ms   p10 %.1f   p90 %.1f"
                 % (len(all_inc), st.median(all_inc),
                    sorted(all_inc)[int(0.10 * len(all_inc))],
                    sorted(all_inc)[int(0.90 * len(all_inc))]))
    lines.append("  negative increments: %.1f%%  (next hop answered FASTER than the one before it,")
    lines[-1] = lines[-1] % (100 * sum(1 for x in all_inc if x < 0) / len(all_inc))
    lines.append("   which is impossible as a distance, so this is the noise floor of the measure)")
    lines.append("")
    lines.append("FOREIGN IXP PEERING-LAN MATCHES")
    if ixp_rows:
        for r in ixp_rows:
            lines.append("  %-16s %-28s %s  (%d observations, %d as exit)"
                         % (r["ip"], r["ixp_peering_lan"], r["ixp_prefix"],
                            r["times_qualified"], r["times_first_foreign_hop"]))
        lines.append("  %d of %d distinct IPs, %d of %d observations"
                     % (len(ixp_rows), len(rows),
                        sum(r["times_qualified"] for r in ixp_rows), tot_q))
    else:
        lines.append("  none of the foreign-classified IPs falls in a peering LAN we checked")
    lines.append("")
    lines.append("TOP 25 BY OBSERVATION COUNT")
    lines.append("%-16s %-7s %-4s %-8s %8s %9s %9s  %s"
                 % ("ip", "asn", "cc", "obs", "rtt_med", "incr_med", "neg%", "org / ixp"))
    for r in rows[:25]:
        lines.append("%-16s %-7s %-4s %-8d %8s %9s %8s%%  %s"
                     % (r["ip"], "AS" + r["asn"], r["registered_cc"], r["times_qualified"],
                        r["rtt_median_ms"], r["incr_rtt_median_ms"], r["incr_negative_pct"],
                        (r["ixp_peering_lan"] or r["org"])[:38]))

    out_txt = os.path.join(HERE, "foreign_hops.txt")
    open(out_txt, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nwrote %s" % os.path.relpath(out_csv, EXP))
    print("wrote %s" % os.path.relpath(out_txt, EXP))


if __name__ == "__main__":
    main()
