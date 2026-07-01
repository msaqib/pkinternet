#!/usr/bin/env python3
"""
Exp 1.4 Pass B — render readable traceroutes (routes_*.txt, Exp 03 style) for the
probe-64078 hosting traceroutes. Recovers hop data by re-fetching the account's
'exp1.4 hosting *' measurements from RIPE (no new credits) and flags foreign hops
(a PK-hosted site reached via a foreign hop = a hairpin).

    python experiments/01.4_pk100_hosting/render_pass_b_routes.py
"""
import os, sys, csv, json, re, requests
from datetime import datetime, timezone
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "measurement"))
import pk_multi_probe as pk
from ripe.atlas.sagan import TracerouteResult

OUT = os.path.join(HERE, "results")
FOREIGN_RTT = 40.0

meta = {r["ip"]: r for r in csv.DictReader(open(os.path.join(OUT, "pass_a_hosting.csv"), encoding="utf-8")) if r["ip"]}


def hop_label(ip):
    if not ip or pk.PRIVATE(ip):
        return ("", "RFC1918", "")
    a, _p, cc = pk.asn_for_ip(ip)
    if a:
        return (a, pk.asn_name(a) or "?", cc)
    _p2, cc2, name = pk.registry_lookup(ip)
    return ("", name or "?", cc2)


# 1) find the exp1.4 measurements on the account
msms = {}
url = "https://atlas.ripe.net/api/v2/measurements/my/"
params = {"description__startswith": "exp1.4 hosting", "fields": "id,description,target_ip", "page_size": 500}
while url:
    d = requests.get(url, headers=pk.HDR, params=params, timeout=40).json()
    for m in d.get("results", []):
        msms[m["id"]] = m
    url = d.get("next"); params = None
print(f"found {len(msms)} exp1.4 measurements")

raw = {}
lines = ["Exp 1.4 Pass B — traceroutes from probe 64078 (Transworld / TES-PL AS135407, Rawalpindi)",
         "PK100 hosting check. '<<< LEAVES PK' = a foreign hop (a PK-hosted site reached via a hairpin).", ""]
blocks = []
for mid, m in msms.items():
    try:
        res = requests.get(f"{pk.BASE}/measurements/{mid}/results/", headers=pk.HDR, timeout=25).json()
    except Exception:
        continue
    if not res:
        continue
    raw[str(mid)] = res
    pr = TracerouteResult.get(res[0])
    dom = m["description"].replace("exp1.4 hosting", "").strip()
    ip = pr.destination_address or m.get("target_ip", "")
    mrow = meta.get(ip, {})
    cat, host = mrow.get("category", "?"), mrow.get("host", "?")
    blk = [f" {dom}   ({cat}: {host[:38]})   ->   {ip}",
           f" SOURCE   probe 64078 - Transworld/TES-PL (AS135407), Rawalpindi",
           f" DEST RTT {pr.last_median_rtt}ms   reached={pr.destination_ip_responded}",
           "-" * 80,
           "  hop   rtt(ms)   ip                 asn       operator (country)"]
    for hop in pr.hops:
        hip = next((p.origin for p in hop.packets if p.origin), None)
        rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
        if not hip:
            blk.append(f"  {hop.index:>3}      *     (no response)"); continue
        a, name, cc = hop_label(hip)
        foreign = cc not in ("PK", "") and not pk.PRIVATE(hip) and rtt is not None and rtt >= FOREIGN_RTT and a != "6327"
        mark = "   <<< LEAVES PK" if foreign else ""
        blk.append(f"  {hop.index:>3}   {('%.1f'%rtt) if rtt is not None else '':>7}   {hip:<16} "
                   f"{('AS'+a) if a else '-':<9} {name[:28]}{(' ('+cc+')') if cc else ''}{mark}")
    blocks.append((dom, blk))

blocks.sort(key=lambda x: x[0])
for dom, blk in blocks:
    lines.append("=" * 80); lines += blk; lines.append("")

ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
open(os.path.join(OUT, f"routes_pass_b_{ts}.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
json.dump(raw, open(os.path.join(OUT, f"raw_pass_b_{ts}.json"), "w", encoding="utf-8"))
print(f"wrote routes_pass_b_{ts}.txt ({len(blocks)} traceroutes) + raw_pass_b_{ts}.json")
