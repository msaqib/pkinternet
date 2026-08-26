#!/usr/bin/env python3
"""
Apply the paper's tromboning detector to the probe-to-probe mesh traceroutes.

Same five rules as analysis/final_classifier.py: a path is tromboned if any
responding hop resolves to a real non-PK country, is not private, is not on the
Shaw/Cogent artifact list, and has an RTT in [40, 500] ms.

    python experiments/11_probe_mesh/classify_mesh.py
"""
import json
import os
import socket
import sys

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
BASE = "https://atlas.ripe.net/api/v2"

FLOOR, CEIL = 40.0, 500.0
ARTIFACT = {"6327", "174"}
PRIV = ("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.3")


def cymru(ips):
    """Bulk IP-to-ASN/country via Team Cymru whois."""
    out = {}
    q = "begin\nverbose\n" + "\n".join(sorted(ips)) + "\nend\n"
    s = socket.socket(); s.settimeout(60); s.connect(("whois.cymru.com", 43))
    s.sendall(q.encode()); buf = b""
    while True:
        c = s.recv(8192)
        if not c:
            break
        buf += c
    s.close()
    for line in buf.decode(errors="replace").split("\n")[1:]:
        p = [x.strip() for x in line.split("|")]
        if len(p) >= 4:
            out[p[1]] = (p[0].split()[0] if p[0] and p[0] != "NA" else "", p[3])
    return out


def main():
    d = sorted(x for x in os.listdir(RESULTS) if x.startswith("mesh_"))[-1]
    outdir = os.path.join(RESULTS, d)
    meta = json.load(open(os.path.join(outdir, "measurements.json"), encoding="utf-8"))
    LAB = {int(k): v for k, v in meta["labels"].items()}

    paths = []
    for tgt_s, mid in meta["trace"].items():
        r = requests.get(f"{BASE}/measurements/{mid}/results/", timeout=60)
        for res in (r.json() if r.status_code == 200 else []):
            hops = []
            for h in res.get("result", []):
                pk = h.get("result", [])
                ip = next((x.get("from") for x in pk if x.get("from")), None)
                rr = [x["rtt"] for x in pk if isinstance(x.get("rtt"), (int, float))]
                hops.append((ip, min(rr) if rr else None))
            paths.append((res.get("prb_id"), int(tgt_s), hops))

    ips = {ip for _, _, hs in paths for ip, _ in hs if ip and not ip.startswith(PRIV)}
    print(f"{len(paths)} probe-to-probe paths, {len(ips)} distinct public hops")
    geo = cymru(ips)

    trom, local, exits = [], [], {}
    for src, tgt, hops in paths:
        hit = None
        for ip, rtt in hops:
            if not ip or ip.startswith(PRIV):
                continue
            asn, cc = geo.get(ip, ("", ""))
            if (cc and cc != "PK" and asn not in ARTIFACT
                    and rtt is not None and FLOOR <= rtt <= CEIL):
                hit = (ip, asn, cc, rtt)
                break
        if hit:
            trom.append((src, tgt, hit))
            exits[hit[2]] = exits.get(hit[2], 0) + 1
        else:
            local.append((src, tgt))

    n = len(paths)
    print(f"\nTROMBONED domestic probe-to-probe paths: {len(trom)} of {n} "
          f"({100*len(trom)/n:.0f}%)")
    print(f"exit countries: {exits}")
    print()
    for src, tgt, (ip, asn, cc, rtt) in sorted(trom, key=lambda x: LAB.get(x[0], "")):
        print(f"  {LAB.get(src, src):<3} to {LAB.get(tgt, tgt):<3}  exits via {cc} "
              f"at {ip:<16} AS{asn:<7} {rtt:.1f} ms")


if __name__ == "__main__":
    main()
