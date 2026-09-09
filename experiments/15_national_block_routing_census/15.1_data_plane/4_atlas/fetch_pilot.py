#!/usr/bin/env python3
"""
15.1 probe-type pilot - collect and analyse.

Polls the measurements created by fire_probe_type_pilot.py until they stop
returning new results, then writes:
  results/pilot_raw_<stamp>.json    every result, unmodified
  results/pilot_routes_<stamp>.txt  human-readable traceroutes (non-negotiable, MANUAL.md 3)
  results/pilot_report_<stamp>.md   the analysis
"""
import os,io,re,sys,json,ssl,time,glob,collections,urllib.request,datetime
HERE=os.path.dirname(os.path.abspath(__file__)); RES=HERE
ROOT=os.path.normpath(os.path.join(HERE,"..","..","..",".."))
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def key():
    for l in io.open(os.path.join(ROOT,".env"),encoding="utf-8",errors="replace"):
        m=re.match(r'\s*RIPE_API_KEY\s*=\s*(.+)',l)
        if m: return m.group(1).strip().strip('"\'')
K=key()
def api(p):
    r=urllib.request.Request(f"https://atlas.ripe.net/api/v2/{p}",headers={"Authorization":f"Key {K}"})
    return json.load(urllib.request.urlopen(r,timeout=90,context=ctx))

spec=json.load(io.open(sorted(glob.glob(os.path.join(RES,"pilot_msms_*.json")))[-1],encoding="utf-8"))
stamp=spec["stamp"]
tgt={t["target"]:t for t in json.load(io.open(os.path.join(RES,"pilot_targets.json"),encoding="utf-8"))}
allm=[(p,m) for p,ms in spec["measurements"].items() for m in ms]
print(f"{len(allm)} measurements, {len(tgt)} targets, {len(spec['probes'])} probes listed")

raw=collections.defaultdict(list); last=-1
for attempt in range(1,25):
    raw=collections.defaultdict(list)
    for proto,m in allm:
        try:
            for r in api(f"measurements/{m}/results/"): raw[proto].append(r)
        except Exception: pass
    n=sum(len(v) for v in raw.values())
    print(f"  poll {attempt}: {n} results", flush=True)
    if n and n==last: break
    last=n
    time.sleep(45)

json.dump({k:v for k,v in raw.items()},io.open(os.path.join(RES,f"pilot_raw_{stamp}.json"),"w",encoding="utf-8"))

def hops(r):
    out=[]
    for h in r.get("result",[]):
        pk=h.get("result",[])
        ip=next((p.get("from") for p in pk if p.get("from")),None)
        rt=[p["rtt"] for p in pk if p.get("rtt") is not None]
        out.append((h.get("hop"),ip,min(rt) if rt else None))
    return out

# readable routes
L=[f"Exp 15.1 probe-type pilot - {stamp}","'*' = no reply. Groups: A live under TCP/80 in 4.1, B dark but block live, C block all dark.",""]
rowsum=[]
for proto in ("ICMP","TCP","UDP"):
    for r in sorted(raw[proto],key=lambda x:(x.get("dst_addr") or "",x.get("prb_id") or 0)):
        hs=hops(r); dst=r.get("dst_addr"); prb=r.get("prb_id")
        ans=sum(1 for _,ip,_ in hs if ip); tot=len(hs)
        reached=any(ip==dst for _,ip,_ in hs)
        g=tgt.get(dst,{}).get("group","?")
        rowsum.append(dict(proto=proto,target=dst,probe=prb,group=g,hops=tot,
                           answered=ans,reached=reached,
                           frac=ans/tot if tot else 0))
        L.append("="*78)
        L.append(f" {proto}  probe {prb}  -> {dst}   [{g}]   {ans}/{tot} hops answered"
                 f"   reached={reached}")
        for hn,ip,rt in hs:
            L.append(f"   {hn:>3}  {'*' if not ip else ip:<17}{'' if rt is None else f'{rt:8.1f} ms'}")
io.open(os.path.join(RES,f"pilot_routes_{stamp}.txt"),"w",encoding="utf-8",newline="\n").write("\n".join(L)+"\n")
json.dump(rowsum,io.open(os.path.join(RES,f"pilot_summary_{stamp}.json"),"w",encoding="utf-8"),indent=1)
print(f"\nwrote pilot_raw / pilot_routes / pilot_summary for {stamp}  ({len(rowsum)} results)")
