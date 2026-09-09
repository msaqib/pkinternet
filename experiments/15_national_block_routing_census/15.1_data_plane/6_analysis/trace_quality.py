#!/usr/bin/env python3
"""
Exp 15.1 — trace-quality census over the frozen Exp 4.1 archive.

Answers, from existing data only (read-only, no network, no credits):
  1. Which ISPs' blocks responded at all?
  2. How many CLEAR traceroutes per vantage, per ISP, per block?
  3. Are there enough clear targets per block to seed Exp 16.1?

CLEAR is defined as: the trace reached the destination ISP's AS, at least
MIN_ANSWERED of its hops replied, and no more than MAX_PRIVATE of the replying
hops were RFC1918. Thresholds are reported, not hidden, so they can be moved.
"""
import os, io, re, csv, sys, collections

RUN = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
      "..","..","..","04.1_small_isp_tromboning",
      "results","run_20260627_192918"))
MIN_ANSWERED, MAX_PRIVATE = 0.80, 0.50
HOP = re.compile(r'^\s*(\d+)\s+(\*|[\d.]+)\s*(\d+\.\d+\.\d+\.\d+)?')
PRIV = ("10.","192.168.","172.16.","172.17.","172.18.","172.19.","172.2","172.30.","172.31.")

meta = {}
for r in csv.DictReader(io.open(os.path.join(RUN,"census_20260627_192918.csv"),encoding="utf-8")):
    meta[(r["source"], r["target_ip"])] = (r["company"], r["prefix"], r["asn"])

traces = []
txt = io.open(os.path.join(RUN,"routes_all_20260703_112939.txt"),encoding="utf-8",errors="replace").read()
for b in txt.split("="*80):
    s = re.search(r'probe\s+\d+\s+-\s+(\S+)', b)
    t = re.search(r'->\s+(\d+\.\d+\.\d+\.\d+)', b)
    v = re.search(r'reached=(\S+)', b)
    if not (s and t and v): continue
    tot=ans=priv=0
    for ln in b.splitlines():
        m = HOP.match(ln)
        if not m: continue
        tot += 1
        if m.group(3):
            ans += 1
            if m.group(3).startswith(PRIV): priv += 1
    if not tot: continue
    key = (s.group(1), t.group(1))
    company, prefix, asn = meta.get(key, ("?","?","?"))
    clear = (v.group(1)=="True" and ans/tot >= MIN_ANSWERED and priv/max(ans,1) <= MAX_PRIVATE)
    traces.append(dict(vantage=s.group(1), target=t.group(1), company=company, prefix=prefix,
                       asn=asn, reached=v.group(1)=="True", answered=ans/tot,
                       private=priv/max(ans,1), clear=clear))

print(f"traces {len(traces)}   CLEAR = reached AND >={MIN_ANSWERED:.0%} hops answered "
      f"AND <={MAX_PRIVATE:.0%} private\n")

# 1 — per ISP
print("="*94)
print("1. PER DESTINATION ISP")
print("="*94)
isp = collections.defaultdict(lambda: dict(n=0, reached=0, clear=0, blocks=set(),
                                           bl_reached=set(), bl_clear=set(), tg_clear=set()))
for t in traces:
    d = isp[t["company"][:34]]
    d["n"] += 1; d["blocks"].add(t["prefix"])
    if t["reached"]: d["reached"] += 1; d["bl_reached"].add(t["prefix"])
    if t["clear"]:   d["clear"]   += 1; d["bl_clear"].add(t["prefix"]); d["tg_clear"].add(t["target"])
rows = sorted(isp.items(), key=lambda x: -x[1]["clear"])
print(f"{'ISP':36}{'probes':>8}{'reach%':>8}{'clear':>7}{'clear%':>8}{'blocks':>8}{'blk+':>6}{'IPs+':>6}")
for name, d in rows[:22]:
    print(f"{name:36}{d['n']:8}{100*d['reached']/d['n']:7.1f}%{d['clear']:7}"
          f"{100*d['clear']/d['n']:7.1f}%{len(d['blocks']):8}{len(d['bl_clear']):6}{len(d['tg_clear']):6}")
dead = [n for n,d in isp.items() if d["clear"]==0]
print(f"\nISPs with ZERO clear traces: {len(dead)} of {len(isp)}")

# 2 — per vantage
print("\n"+"="*94)
print("2. PER VANTAGE")
print("="*94)
van = collections.defaultdict(lambda: dict(n=0, reached=0, clear=0, isps=set(), tg=set()))
for t in traces:
    d = van[t["vantage"]]
    d["n"] += 1
    if t["reached"]: d["reached"] += 1
    if t["clear"]: d["clear"] += 1; d["isps"].add(t["company"]); d["tg"].add(t["target"])
print(f"{'vantage':16}{'probes':>8}{'reach%':>8}{'clear':>8}{'clear%':>8}{'ISPs+':>7}{'IPs+':>7}")
for v, d in sorted(van.items(), key=lambda x: -x[1]["clear"]):
    print(f"{v:16}{d['n']:8}{100*d['reached']/d['n']:7.1f}%{d['clear']:8}"
          f"{100*d['clear']/d['n']:7.1f}%{len(d['isps']):7}{len(d['tg']):7}")

# 3 — per block, and the 16.1 seed question
print("\n"+"="*94)
print("3. PER BLOCK  — can we seed Exp 16.1?")
print("="*94)
blk = collections.defaultdict(lambda: collections.defaultdict(set))
for t in traces:
    if t["clear"]: blk[t["prefix"]][t["target"]].add(t["vantage"])
per_n = collections.Counter()
for p, tg in blk.items(): per_n[len(tg)] += 1
allb = {t["prefix"] for t in traces}
print(f"blocks probed: {len(allb)};  with >=1 clear target: {len(blk)}")
print("\ndistinct CLEAR targets per block:")
for k in sorted(per_n): print(f"   {k:3} clear target(s): {per_n[k]:4} blocks")
for bar in (1,2,4,8):
    n = sum(v for k,v in per_n.items() if k>=bar)
    print(f"   blocks with >={bar} clear targets: {n:4}  ({100*n/len(allb):.1f}% of probed)")
print("\nclear targets by how many vantages saw them clearly:")
cv = collections.Counter()
for p, tg in blk.items():
    for t, vs in tg.items(): cv[len(vs)] += 1
for k in sorted(cv, reverse=True): print(f"   clear from {k} of 7 vantages: {cv[k]:5} targets")
print("\nbest blocks (most clear targets):")
best = sorted(blk.items(), key=lambda x: -len(x[1]))[:12]
for p, tg in best:
    co = next((t["company"][:26] for t in traces if t["prefix"]==p), "?")
    mv = max(len(v) for v in tg.values())
    print(f"   {p:20}{co:28}{len(tg):3} clear targets, best seen by {mv}/7 vantages")
