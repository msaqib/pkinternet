#!/usr/bin/env python3
"""
Exp 4.1: render the TROMBONING traceroutes from the census raw into a readable
routes_*.txt (Exp 03/04 style), one block per hairpinning trace, with the hop
where it leaves Pakistan flagged. Reads the latest run's raw checkpoint.

    python experiments/04.1_small_isp_tromboning/render_tromboning_routes.py
"""
import os, sys, json, glob, csv
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(__file__))
import census_sweep as cs
from ripe.atlas.sagan import TracerouteResult

R = os.path.join(os.path.dirname(__file__), "results")
RUN = "run_20260627_192918"
SRC = {1016126: "ptcl.khi", 1015679: "nova.lhe", 7613: "zcom.lhe",
       1016036: "cybernet.hrp", 1016154: "cybernet.khi", 60223: "nayatel.isb", 64535: "orbit.fsd"}

ip2blk = {}
for b in csv.DictReader(open(os.path.join(R, "blocks_all.csv"), encoding="utf-8")):
    for ip in cs.block_ips(b["prefix"], 8):
        ip2blk[ip] = (b["asn"], b["company"], b["prefix"])

# frozen verdicts from the canonical census CSV (re-classifying raw drifts, because
# hop_geo does live ASN/geo lookups) -> key (source_id, target_ip) -> census row
frozen = {}
for cr in csv.DictReader(open(glob.glob(os.path.join(R, RUN, "census_*.csv"))[0], encoding="utf-8")):
    frozen[(int(cr["source_id"]), cr["target_ip"])] = cr

raw = json.load(open(glob.glob(os.path.join(R, RUN, "raw_*.json"))[0], encoding="utf-8"))

# dedup resume-duplicate measurements (raw has ~190 dup (probe,target) entries), keep last
last = {}
for res in raw.values():
    for r in res:
        last[(r.get("prb_id"), r.get("dst_addr"))] = r

items = []   # (company, asn, prefix, ip, prb, census-verdict, result)
for r in last.values():
    ip = r.get("dst_addr"); prb = r.get("prb_id")
    v = frozen.get((prb, ip))
    if v is None or ip not in ip2blk:
        continue
    if v["status"] in ("trombone_hop", "trombone_rtt"):
        asn, comp, prefix = ip2blk[ip]
        items.append((comp, asn, prefix, ip, prb, v, r))

items.sort(key=lambda x: (x[0], x[2], x[3], str(x[4])))   # by ISP, prefix, ip, probe

lines = [f"Exp 4.1 — TROMBONING traceroutes (small-ISP census, complete {RUN})",
         f"{len(items)} hairpinning traces. '<<< LEAVES PK' marks where the packet exits Pakistan.",
         "VERDICT is TROMBONE_HOP (a foreign hop actually resolved, RTT>=40ms - hard evidence) or "
         "TROMBONE_RTT (no foreign hop seen; inferred from RTT jump>=60ms OR max hop RTT>=70ms alone).", ""]
for comp, asn, prefix, ip, prb, v, r in items:
    pr = TracerouteResult.get(r)
    lines.append("=" * 80)
    lines.append(f" {comp[:44]} (AS{asn})   ->   {ip}    [block {prefix}]")
    lines.append(f" SOURCE   probe {prb} - {SRC.get(prb, prb)}")
    lines.append(f" VERDICT  {v['status'].upper()}   reached={v['reached_isp']}   "
                 f"exit={v['exit_name'] or '?'} ({v['exit_cc']})   "
                 f"transit={v['transit']}   maxRTT={v['max_rtt']}ms   evidence={v['evidence']}")
    lines.append("-" * 80)
    lines.append("  hop   rtt(ms)   ip                 asn       operator (country)")
    for hop in pr.hops:
        ipx = next((p.origin for p in hop.packets if p.origin), None)
        rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
        if not ipx:
            lines.append(f"  {hop.index:>3}      *     (no response)"); continue
        a, name, ccx = cs.hop_geo(ipx)
        foreign = (ccx not in ("PK", "") and not cs.pk.PRIVATE(ipx) and a not in cs.ARTIFACT_ASN
                   and rtt is not None and cs.FOREIGN_RTT_FLOOR <= rtt <= cs.QUEUE_CEIL)
        mark = "   <<< LEAVES PK" if foreign else ""
        rtts = ("%.1f" % rtt) if rtt is not None else ""
        lines.append(f"  {hop.index:>3}   {rtts:>7}   {ipx:<16} {('AS'+a) if a else '-':<9} "
                     f"{name[:28]}{(' ('+ccx+')') if ccx else ''}{mark}")
    lines.append("")

ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
out = os.path.join(R, RUN, f"routes_tromboning_{ts}.txt")
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"wrote {out}  ({len(items)} tromboning traces)")
