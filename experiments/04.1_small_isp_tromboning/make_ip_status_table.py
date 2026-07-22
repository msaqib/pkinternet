#!/usr/bin/env python3
"""
Exp 4.1 - build a hierarchical status table from the CANONICAL census CSV:
one row per (ISP -> block -> target IP -> source probe) with status
(trombone_hop / trombone_rtt / local / inconclusive), reached (reached the destination ISP's
network), and a tromboned flag. Reads the deduped census_*.csv (not the raw
checkpoint, which contains resume-duplicate measurements).

    python experiments/04.1_small_isp_tromboning/make_ip_status_table.py
Output: results/run_20260627_192918/ip_status_table_<ts>.csv
"""
import os, glob, csv, collections, ipaddress
from datetime import datetime, timezone

RUN = os.path.join(os.path.dirname(__file__), "results", "run_20260627_192918")
census = sorted(glob.glob(os.path.join(RUN, "census_*.csv")))[-1]

rows = []
for r in csv.DictReader(open(census, encoding="utf-8")):
    trombone = r["status"] in ("trombone_hop", "trombone_rtt")
    rows.append(dict(asn="AS" + r["asn"], isp=r["company"], block=r["prefix"],
                     target_ip=r["target_ip"], source=r["source"], status=r["status"],
                     reached=(r["reached_isp"] == "True"), tromboned=trombone,
                     exit=(r["exit_name"] or r["exit_cc"]) if trombone else "",
                     transit=r["transit"] if trombone else "", max_rtt=r["max_rtt"]))

rows.sort(key=lambda x: (x["isp"], ipaddress.ip_network(x["block"]).network_address,
                         ipaddress.ip_address(x["target_ip"]), str(x["source"])))
ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
out = os.path.join(RUN, f"ip_status_table_{ts}.csv")
cols = ["asn", "isp", "block", "target_ip", "source", "status", "reached", "tromboned", "exit", "transit", "max_rtt"]
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

st = collections.Counter(r["status"] for r in rows)
rc = collections.Counter(str(r["reached"]) for r in rows)
print(f"rows: {len(rows)}  (ISPs {len({r['isp'] for r in rows})}, blocks {len({r['block'] for r in rows})}, "
      f"IPs {len({r['target_ip'] for r in rows})})")
print("status:", dict(st), " reached:", dict(rc))
print("wrote", out)
