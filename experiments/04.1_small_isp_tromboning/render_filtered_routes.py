#!/usr/bin/env python3
"""
Exp 4.1 — render readable traceroutes for a filtered set of (target_ip, source)
rows (e.g. the reached=True AND tromboned=True subset). Reads the filter CSV +
the census raw checkpoint. Exp 03 style, with reached + '<<< LEAVES PK' markers.

    python experiments/04.1_small_isp_tromboning/render_filtered_routes.py \
        results/run_20260627_192918/filtered_reached_tromboned.csv
"""
import os, sys, json, glob, csv, shutil
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(__file__))
import census_sweep as cs
from ripe.atlas.sagan import TracerouteResult

R = os.path.join(os.path.dirname(__file__), "results")
RUN = os.path.join(R, "run_20260627_192918")
FILTER = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RUN, "filtered_reached_tromboned.csv")

ip2blk = {}
for b in csv.DictReader(open(os.path.join(R, "blocks_all.csv"), encoding="utf-8")):
    for ip in cs.block_ips(b["prefix"], 8):
        ip2blk[ip] = (b["asn"], b["company"], b["prefix"])

want = {(r["target_ip"], r["source"]) for r in csv.DictReader(open(FILTER, encoding="utf-8"))}
print(f"{len(want)} (ip, source) traces to render")

src = glob.glob(os.path.join(RUN, "raw_*.json"))[0]
snap = src + ".snap2"; shutil.copy(src, snap)
raw = json.load(open(snap, encoding="utf-8")); os.remove(snap)

items = []
for res in raw.values():
    for r in res:
        ip = r.get("dst_addr"); lbl = cs.SOURCES.get(r.get("prb_id"), r.get("prb_id"))
        if (ip, str(lbl)) in want and ip in ip2blk:
            items.append((ip, str(lbl), r))
items.sort(key=lambda x: (ip2blk[x[0]][1], x[0], x[1]))

lines = [f"Exp 4.1 — filtered traceroutes: reached=True AND tromboned=True ({len(items)} traces)",
         "Live hosts reached via an international hairpin. '<<< LEAVES PK' = the exit hop.", ""]
for ip, lbl, r in items:
    asn, comp, prefix = ip2blk[ip]
    v = cs.classify(r, asn)
    pr = TracerouteResult.get(r)
    lines.append("=" * 80)
    lines.append(f" {comp[:44]} (AS{asn})   ->   {ip}    [block {prefix}]")
    lines.append(f" SOURCE   probe {r.get('prb_id')} - {lbl}")
    lines.append(f" VERDICT  TROMBONE   reached={pr.destination_ip_responded}   "
                 f"exit={v['exit_name'] or '?'} ({v['exit_cc']})   transit={v['transit']}   "
                 f"maxRTT={v['max_rtt']}ms   evidence={v['evidence']}")
    lines.append("-" * 80)
    lines.append("  hop   rtt(ms)   ip                 asn       operator (country)")
    for hop in pr.hops:
        hip = next((p.origin for p in hop.packets if p.origin), None)
        rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
        if not hip:
            lines.append(f"  {hop.index:>3}      *     (no response)"); continue
        a, name, cc = cs.hop_geo(hip)
        foreign = (cc not in ("PK", "") and not cs.pk.PRIVATE(hip) and a not in cs.ARTIFACT_ASN
                   and rtt is not None and cs.FOREIGN_RTT_FLOOR <= rtt <= cs.QUEUE_CEIL)
        lines.append(f"  {hop.index:>3}   {('%.1f'%rtt) if rtt is not None else '':>7}   {hip:<16} "
                     f"{('AS'+a) if a else '-':<9} {name[:28]}{(' ('+cc+')') if cc else ''}"
                     f"{'   <<< LEAVES PK' if foreign else ''}")
    lines.append("")

ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
out = os.path.join(RUN, f"routes_filtered_reached_tromboned_{ts}.txt")
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"wrote {out} ({len(items)} traces)")
