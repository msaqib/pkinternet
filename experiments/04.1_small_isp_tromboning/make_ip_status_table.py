#!/usr/bin/env python3
"""
Exp 4.1 — build a hierarchical status table from the census checkpoint:
one row per (ISP -> block -> target IP -> source probe) with status
(trombone / local / inconclusive) and reached (did the destination reply).

    python experiments/04.1_small_isp_tromboning/make_ip_status_table.py
Output: results/run_20260627_192918/ip_status_table_<ts>.csv
"""
import os, sys, json, glob, csv, shutil, collections
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(__file__))
import census_sweep as cs
from ripe.atlas.sagan import TracerouteResult

R = os.path.join(os.path.dirname(__file__), "results")
RUN = os.path.join(R, "run_20260627_192918")

# ip -> (asn, company, prefix)
ip2blk = {}
for b in csv.DictReader(open(os.path.join(R, "blocks_all.csv"), encoding="utf-8")):
    for ip in cs.block_ips(b["prefix"], 8):
        ip2blk[ip] = (b["asn"], b["company"], b["prefix"])

# snapshot the (live-written) checkpoint before reading
src = glob.glob(os.path.join(RUN, "raw_*.json"))[0]
snap = src + ".snap"
shutil.copy(src, snap)
raw = json.load(open(snap, encoding="utf-8"))
os.remove(snap)

rows = []
for res in raw.values():
    for r in res:
        ip = r.get("dst_addr")
        if ip not in ip2blk:
            continue
        asn, comp, prefix = ip2blk[ip]
        try:
            v = cs.classify(r, asn)
            reached = TracerouteResult.get(r).destination_ip_responded
        except Exception:
            continue
        rows.append(dict(asn="AS" + asn, isp=comp, block=prefix, target_ip=ip,
                         source=cs.SOURCES.get(r.get("prb_id"), r.get("prb_id")),
                         status=v["status"], reached=reached,
                         exit=(v["exit_name"] or v["exit_cc"]) if v["status"] == "trombone" else "",
                         transit=v["transit"] if v["status"] == "trombone" else "",
                         max_rtt=v["max_rtt"]))

import ipaddress
rows.sort(key=lambda x: (x["isp"], ipaddress.ip_network(x["block"]).network_address,
                         ipaddress.ip_address(x["target_ip"]), str(x["source"])))
ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
out = os.path.join(RUN, f"ip_status_table_{ts}.csv")
cols = ["asn", "isp", "block", "target_ip", "source", "status", "reached", "exit", "transit", "max_rtt"]
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

st = collections.Counter(r["status"] for r in rows)
rc = collections.Counter(str(r["reached"]) for r in rows)
print(f"rows: {len(rows)}  (ISPs {len({r['isp'] for r in rows})}, blocks {len({r['block'] for r in rows})}, "
      f"IPs {len({r['target_ip'] for r in rows})})")
print("status:", dict(st), " reached:", dict(rc))
print("wrote", out)
