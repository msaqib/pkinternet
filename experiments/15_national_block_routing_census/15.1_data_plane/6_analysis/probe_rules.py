#!/usr/bin/env python3
"""
Exp 15.1 - per-probe baseline rules, learned from each probe's own traces.

A probe is not a neutral observer. Before any tromboning verdict, we learn what is
NORMAL for that probe and subtract it. Two rule families:

  RULE 1  FIXTURES. An address that appears in most of a probe's traces is part of
          that probe's own access path, not part of the route to any destination.
          A fixture that is foreign-registered, answers at local RTT, and adds
          almost nothing across the hop is an ARTEFACT of that probe.

  RULE 2  RTT SPINE. Each probe has a characteristic RTT staircase by hop index.
          The steps are its own access network. Anything above the spine is the
          thing we are actually trying to measure.

Read-only over the 4.1 archive. No network, no credits.
"""
import os,io,re,json,collections,statistics as stx,ipaddress
HERE=os.path.dirname(os.path.abspath(__file__))
RUN=os.path.normpath(os.path.join(HERE,"..","..","..",
    "04.1_small_isp_tromboning","results","run_20260627_192918"))
CACHE=os.path.normpath(os.path.join(HERE,"..","..","..",
    "07_longitudinal_panel","analysis",".cache_hop_asn.json"))
HOP=re.compile(r'^\s*(\d+)\s+(\*|[\d.]+)\s*(\d+\.\d+\.\d+\.\d+)?')
SENT=255
geo={}
try: geo=json.load(io.open(CACHE,encoding="utf-8"))
except Exception: pass
def pub(ip):
    try: return ipaddress.ip_address(ip).is_global
    except ValueError: return False

traces=collections.defaultdict(int)
seen=collections.defaultdict(lambda: collections.defaultdict(list))     # probe -> ip -> [rtt]
delta=collections.defaultdict(lambda: collections.defaultdict(list))    # probe -> ip -> [inter-hop delta]
spine=collections.defaultdict(lambda: collections.defaultdict(list))    # probe -> hop idx -> [rtt]
txt=io.open(os.path.join(RUN,"routes_all_20260703_112939.txt"),encoding="utf-8",errors="replace").read()
for b in txt.split("="*80):
    s=re.search(r'probe\s+\d+\s+-\s+(\S+)',b)
    if not s: continue
    v=s.group(1); traces[v]+=1
    hs=[]
    for ln in b.splitlines():
        m=HOP.match(ln)
        if m and int(m.group(1))!=SENT and m.group(3):
            hs.append((int(m.group(1)),m.group(3),None if m.group(2)=="*" else float(m.group(2))))
    prev=None
    for idx,ip,rtt in hs:
        if rtt is None: continue
        seen[v][ip].append(rtt); spine[v][idx].append(rtt)
        if prev is not None: delta[v][ip].append(rtt-prev)
        prev=rtt

print("RULE 1 - FIXTURES: addresses on >=50% of a probe's traces\n")
print(f"{'probe':14}{'address':17}{'seen':>7}{'% traces':>10}{'med RTT':>9}{'med step':>10}  registry")
arte=[]
for v in sorted(seen):
    for ip,rtts in sorted(seen[v].items(), key=lambda x:-len(x[1])):
        frac=len(rtts)/traces[v]
        if frac<0.5: continue
        d=delta[v].get(ip,[])
        g=geo.get(ip,{}); cc=g.get("cc",""); holder=(g.get("holder") or "")[:26]
        tag="private" if not pub(ip) else (cc or "?")
        mark=""
        if pub(ip) and cc and cc!="PK" and stx.median(rtts)<10 and (not d or abs(stx.median(d))<5):
            mark="  <== ARTEFACT"; arte.append((v,ip,cc,holder))
        print(f"{v:14}{ip:17}{len(rtts):>7}{100*frac:>9.0f}%{stx.median(rtts):>9.1f}"
              f"{(stx.median(d) if d else 0):>10.1f}  {tag:8}{holder}{mark}")
print(f"\nRule 1 flags {len(arte)} probe-specific artefacts:")
for v,ip,cc,h in arte: print(f"   {v:14}{ip:17}registered {cc}  {h}")

print("\n\nRULE 2 - RTT SPINE: each probe's characteristic staircase (median RTT by hop index)\n")
idxs=list(range(1,11))
print(f"{'probe':14}"+"".join(f"{i:>7}" for i in idxs)+"   <- hop index")
for v in sorted(spine):
    cells=[]
    for i in idxs:
        r=spine[v].get(i,[])
        cells.append(f"{stx.median(r):>7.1f}" if len(r)>=30 else f"{'-':>7}")
    print(f"{v:14}"+"".join(cells))
print("\nthe STEP between consecutive hops (what each hop costs this probe):")
print(f"{'probe':14}"+"".join(f"{f'{i}->{i+1}':>8}" for i in idxs[:-1]))
for v in sorted(spine):
    cells=[]
    for i in idxs[:-1]:
        a,b2=spine[v].get(i,[]),spine[v].get(i+1,[])
        cells.append(f"{stx.median(b2)-stx.median(a):>8.1f}" if len(a)>=30 and len(b2)>=30 else f"{'-':>8}")
    print(f"{v:14}"+"".join(cells))
