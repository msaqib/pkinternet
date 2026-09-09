#!/usr/bin/env python3
"""
Per-ISP rollup of the whole 15.1 sweep: address space -> live hosts -> routes.

INPUTS
  1_universe/block_to_asn.json    every /24-equivalent -> announcing ASN
  1_universe/asn_holder.json      ASN -> registered holder name
  2_liveness/*.jsonl              one record per address CHECKED (m=[] means no answer)
  3_routes/local_routes.jsonl     one record per TRACE attempted
  3_routes/selected_traces.json   the traces that passed the selection gate

COLUMNS, and exactly what each one is
  blocks            /24-equivalents the network announces (or, for the unannounced
                    row, blocks in PK registry space nobody announces)
  probed            blocks in which at least one address was checked
  live blk          blocks where at least one address answered
  live hosts        distinct addresses that answered, either vantage
  blk>=8            blocks that reached 8 live hosts, the panel target
  traced            blocks in which at least one traceroute was attempted
  reached           traces where the last hop is the target itself
  sel blk / sel     blocks and targets that passed reached AND answered>=5

CAUTION  "live hosts" is a FLOOR, and the floors are not equally tight. Sampling is
         adaptive (8 per block, escalating to 64 only where something answered), so
         a block never yields more than 64 regardless of true occupancy. Per-network
         miss rates also differ: re-probing measured ~35% on PTCL against 22-25%
         elsewhere (SWEEP_FINDINGS 5C). Densities are comparable within a network
         over time, not between networks.

  python build_isp_summary.py    -> isp_summary.csv, ISP_SUMMARY.md
"""
import io, json, os, ipaddress, collections

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(H, "..")
def P(*p): return os.path.join(R, *p)

blocks = json.load(io.open(P("1_universe", "block_to_asn.json"), encoding="utf-8"))
holder = json.load(io.open(P("1_universe", "asn_holder.json"), encoding="utf-8"))
UNANN = "unannounced"
own = {b: (a or UNANN) for b, a in blocks.items()}

S = collections.defaultdict(lambda: dict(blocks=0, probed=set(), liveblk=set(), live=set(),
                                         checks=0, traced=set(), traces=0, reached=0,
                                         selblk=set(), sel=0, addrs=0))
for b, a in own.items():
    S[a]["blocks"] += 1
    S[a]["addrs"] += 256

def unit(ip):
    return str(ipaddress.ip_network(ip + "/24", strict=False))

live_per_block = collections.Counter()
for f in ("local_scan.jsonl", "pk_scan.jsonl", "topup_scan.jsonl"):
    p = P("2_liveness", f)
    if not os.path.exists(p): continue
    for l in io.open(p, encoding="utf-8"):
        try: d = json.loads(l)
        except Exception: continue
        u = unit(d["t"]); a = own.get(u)
        if a is None: continue                      # outside the universe, ignore
        s = S[a]; s["checks"] += 1; s["probed"].add(u)
        if d.get("m"):
            s["live"].add(d["t"]); s["liveblk"].add(u); live_per_block[u] += 1
for u, n in live_per_block.items():
    if n >= 8:
        a = own.get(u)
        if a: S[a].setdefault("blk8", set()).add(u)

p = P("3_routes", "local_routes.jsonl")
for l in io.open(p, encoding="utf-8"):
    try: d = json.loads(l)
    except Exception: continue
    u = unit(d["t"]); a = own.get(u)     # always the /24 unit: some early records
    if a is None: continue                # carry p as the announced /22 or /23
    s = S[a]; s["traces"] += 1; s["traced"].add(u)
    if d.get("reached"): s["reached"] += 1

for d in json.load(io.open(P("3_routes", "selected_traces.json"), encoding="utf-8")):
    u = unit(d["t"]); a = own.get(u)
    if a is None: continue
    S[a]["sel"] += 1; S[a]["selblk"].add(u)

rows = []
for a, s in S.items():
    b8 = len(s.get("blk8", ()))
    rows.append(dict(
        asn=a, name=(holder.get(a, f"AS{a}") if a != UNANN else "(registry space, announced by nobody)")[:44],
        blocks=s["blocks"], addrs=s["addrs"], checks=s["checks"],
        probed=len(s["probed"]), liveblk=len(s["liveblk"]), live=len(s["live"]), blk8=b8,
        traced=len(s["traced"]), traces=s["traces"], reached=s["reached"],
        selblk=len(s["selblk"]), sel=s["sel"],
        pct_live_blk=100*len(s["liveblk"])/max(len(s["probed"]), 1),
        pct_reach=100*s["reached"]/max(s["traces"], 1),
        pct_cov=100*len(s["selblk"])/max(len(s["liveblk"]), 1)))
rows.sort(key=lambda r: (-r["live"], -r["blocks"]))

import csv
with io.open(os.path.join(H, "isp_summary.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); [w.writerow(r) for r in rows]

T = {k: sum(r[k] for r in rows) for k in
     ("blocks", "addrs", "checks", "probed", "liveblk", "live", "blk8", "traced", "traces", "reached", "selblk", "sel")}
print(f"{'ASN':<9}{'network':<34}{'blocks':>7}{'probed':>7}{'live blk':>9}{'live hosts':>11}"
      f"{'blk>=8':>7}{'traced':>7}{'reached':>8}{'sel blk':>8}{'sel':>7}")
print("-"*114)
for r in rows[:35]:
    print(f"{('AS'+r['asn'] if r['asn']!=UNANN else '-'):<9}{r['name'][:33]:<34}{r['blocks']:>7,}{r['probed']:>7,}"
          f"{r['liveblk']:>9,}{r['live']:>11,}{r['blk8']:>7,}{r['traced']:>7,}{r['reached']:>8,}"
          f"{r['selblk']:>8,}{r['sel']:>7,}")
print("-"*114)
print(f"{'TOTAL':<43}{T['blocks']:>7,}{T['probed']:>7,}{T['liveblk']:>9,}{T['live']:>11,}"
      f"{T['blk8']:>7,}{T['traced']:>7,}{T['reached']:>8,}{T['selblk']:>8,}{T['sel']:>7,}")
print(f"\nnetworks with any live host: {sum(1 for r in rows if r['live']):,} of {len(rows):,}")
print(f"networks with a selected block: {sum(1 for r in rows if r['selblk']):,}")
json.dump(rows, io.open(os.path.join(H, "isp_summary.json"), "w", encoding="utf-8"), indent=1)
print("wrote isp_summary.csv / .json")
