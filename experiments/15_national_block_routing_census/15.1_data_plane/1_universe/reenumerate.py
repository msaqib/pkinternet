#!/usr/bin/env python3
"""
15.1 Phase A - re-enumerate the block universe.

Re-pulls announced-prefixes for every FLL ASN in the 4.1 roster and diffs against the
2026-06-27 snapshot. Free, no API key, no measurement credits. Read-only w.r.t. experiment 04.1.

  python reenumerate.py            # writes blocks_YYYYMMDD.csv + universe_diff.txt
"""
import os,io,csv,json,ssl,sys,time,collections,urllib.request,datetime
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
OLD=os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
    "..","..","..","04.1_small_isp_tromboning","results"))
TODAY=datetime.date.today().strftime("%Y%m%d")

old=collections.defaultdict(set); company={}
for r in csv.DictReader(io.open(os.path.join(OLD,"blocks_all.csv"),encoding="utf-8")):
    old[r["asn"]].add(r["prefix"])
for r in csv.DictReader(io.open(os.path.join(OLD,"isp_summary.csv"),encoding="utf-8")):
    company[r["asn"]]=r["company"]
asns=sorted(old, key=lambda a:-len(old[a]))
print(f"roster: {len(asns)} ASNs, {sum(len(v) for v in old.values())} blocks in the 2026-06-27 snapshot")

new={}; errs=[]
for i,a in enumerate(asns,1):
    url=f"https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{a}"
    for attempt in (1,2):
        try:
            d=json.load(urllib.request.urlopen(url,timeout=45,context=ctx))
            new[a]={p["prefix"] for p in d["data"]["prefixes"] if ":" not in p["prefix"]}
            break
        except Exception as e:
            if attempt==2: errs.append((a,str(e)[:50])); new[a]=None
            time.sleep(2)
    print(f"  [{i:2}/{len(asns)}] AS{a:<7} {company.get(a,'?')[:30]:32} "
          f"{'ERR' if new[a] is None else len(new[a])}", flush=True)

rows=[]; add=collections.defaultdict(list); rem=collections.defaultdict(list)
for a in asns:
    if new[a] is None: continue
    for p in sorted(new[a]-old[a]): add[a].append(p)
    for p in sorted(old[a]-new[a]): rem[a].append(p)
    for p in sorted(new[a]):
        import ipaddress
        n=ipaddress.ip_network(p,strict=False)
        rows.append(dict(asn=a,company=company.get(a,"?"),prefix=p,
                         prefix_len=n.prefixlen,num_addresses=n.num_addresses))
with io.open(f"blocks_{TODAY}.csv","w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["asn","company","prefix","prefix_len","num_addresses"])
    w.writeheader(); w.writerows(rows)

tot_old=sum(len(v) for v in old.values()); tot_new=len(rows)
eq24=sum(max(1,r["num_addresses"]//256) for r in rows)
L=[f"15.1 Phase A - block universe refresh, {TODAY}",
   f"queried {len(asns)} ASNs via RIPEstat announced-prefixes; {len(errs)} errors","",
   f"blocks: {tot_old} (2026-06-27)  ->  {tot_new} (today)   net {tot_new-tot_old:+d}",
   f"/24-equivalents today: {eq24}",
   f"ASNs gaining blocks: {sum(1 for a in add if add[a])}   losing: {sum(1 for a in rem if rem[a])}",""]
for a in asns:
    if add[a] or rem[a]:
        L.append(f"AS{a} {company.get(a,'?')[:34]}  +{len(add[a])} / -{len(rem[a])}")
        for p in add[a][:6]: L.append(f"    + {p}")
        for p in rem[a][:6]: L.append(f"    - {p}")
if errs: L+=["","ERRORS:"]+[f"  AS{a}: {e}" for a,e in errs]
io.open("universe_diff.txt","w",encoding="utf-8",newline="\n").write("\n".join(L)+"\n")
print("\n".join(L[:8]))
print(f"\nwrote blocks_{TODAY}.csv ({tot_new} rows) and universe_diff.txt")
