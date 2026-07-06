#!/usr/bin/env python3
"""
Exp 4.1: render EVERY census traceroute (local + trombone + inconclusive) into one
readable routes_all_*.txt, grouped by ISP -> block -> IP -> probe. Verdicts are the
census's FROZEN classification (from census_*.csv), not a re-classification. Per-hop
shows IP + RTT + an RTT-based exit marker (no live ASN/geo lookup, so it renders fast
over all ~18k traces); full per-hop operator names are in routes_tromboning /
routes_filtered_reached_tromboned.

    python experiments/04.1_small_isp_tromboning/render_all_routes.py
"""
import os, sys, json, glob, csv, collections
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

# frozen verdicts from the canonical census CSV -> key (source_id, target_ip)
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
counts = collections.Counter()
for r in last.values():
    ip = r.get("dst_addr"); prb = r.get("prb_id")
    v = frozen.get((prb, ip))
    if v is None or ip not in ip2blk:
        continue
    asn, comp, prefix = ip2blk[ip]
    counts[v["status"]] += 1
    items.append((comp, asn, prefix, ip, prb, v, r))

items.sort(key=lambda x: (x[0], x[2], x[3], str(x[4])))   # by ISP, prefix, ip, probe

lines = [f"Exp 4.1 — ALL census traceroutes (small-ISP census, complete {RUN})",
         f"{len(items)} traces  (local {counts['local']}, trombone {counts['trombone']}, "
         f"inconclusive {counts['inconclusive']}).  Verdicts = the census's frozen classification.",
         "'<<< high RTT' marks a hop >=40ms (likely off-PK). Per-hop operator names are in "
         "routes_tromboning_*.txt / routes_filtered_reached_tromboned_*.txt.", ""]
for comp, asn, prefix, ip, prb, v, r in items:
    pr = TracerouteResult.get(r)
    lines.append("=" * 80)
    lines.append(f" {comp[:44]} (AS{asn})   ->   {ip}    [block {prefix}]")
    lines.append(f" SOURCE   probe {prb} - {SRC.get(prb, prb)}")
    extra = (f"   exit={v['exit_name'] or '?'} ({v['exit_cc']})   transit={v['transit']}"
             if v["status"] == "trombone" else "")
    lines.append(f" VERDICT  {v['status'].upper()}   reached={v['reached_isp']}   "
                 f"maxRTT={v['max_rtt']}ms{extra}   evidence={v['evidence']}")
    lines.append("-" * 80)
    lines.append("  hop   rtt(ms)   ip")
    for hop in pr.hops:
        ipx = next((p.origin for p in hop.packets if p.origin), None)
        rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
        if not ipx:
            lines.append(f"  {hop.index:>3}      *     (no response)"); continue
        mark = ("   <<< high RTT" if (rtt is not None and not cs.pk.PRIVATE(ipx)
                and cs.FOREIGN_RTT_FLOOR <= rtt <= cs.QUEUE_CEIL) else "")
        rtts = ("%.1f" % rtt) if rtt is not None else ""
        lines.append(f"  {hop.index:>3}   {rtts:>7}   {ipx:<16}{mark}")
    lines.append("")

ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
out = os.path.join(R, RUN, f"routes_all_{ts}.txt")
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"wrote {out}  ({len(items)} traces: {dict(counts)})")
