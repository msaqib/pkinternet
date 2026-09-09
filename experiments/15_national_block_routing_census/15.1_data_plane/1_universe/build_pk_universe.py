#!/usr/bin/env python3
"""
Build the ALL-PAKISTAN scan universe.

Two sources, unioned, because neither alone is complete:
  1. RIPEstat country-resource-list PK  - everything REGISTERED to Pakistan
  2. announced-prefixes for every PK ASN - everything Pakistani networks ROUTE

(2) catches space registered abroad but announced from Pakistan. In the small-ISP
universe, 113 of 778 blocks fall in that category, so (1) alone would miss them.
(1) catches space registered to PK that nobody currently announces.

Writes pk_universe.json: the deduplicated, collapsed network list.
"""
import json,ssl,io,sys,time,collections,ipaddress,urllib.request,threading,queue
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def get(u,tries=3):
    for i in range(tries):
        try: return json.load(urllib.request.urlopen(u,timeout=90,context=ctx))["data"]
        except Exception:
            if i==tries-1: return None
            time.sleep(2)

d=get("https://stat.ripe.net/data/country-resource-list/data.json?resource=PK")
asns=[a for a in d["resources"]["asn"]]
reg=[]
for p in d["resources"]["ipv4"]:
    try:
        if "-" in p:
            a,b=p.split("-")
            reg+=list(ipaddress.summarize_address_range(ipaddress.ip_address(a),ipaddress.ip_address(b)))
        else: reg.append(ipaddress.ip_network(p,strict=False))
    except Exception: pass
print(f"registry : {len(reg):,} networks, {sum(n.num_addresses for n in reg):,} addresses")
print(f"PK ASNs  : {len(asns):,}  - querying announced-prefixes for each")

ann=[]; lock=threading.Lock(); q=queue.Queue(); [q.put(a) for a in asns]
errs=[]; n=[0]
def w():
    while True:
        try: a=q.get_nowait()
        except queue.Empty: return
        r=get(f"https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{a}")
        with lock:
            n[0]+=1
            if r is None: errs.append(a)
            else:
                for p in r.get("prefixes",[]):
                    px=p["prefix"]
                    if ":" in px: continue
                    try: ann.append(ipaddress.ip_network(px,strict=False))
                    except Exception: pass
            if n[0]%50==0: print(f"   {n[0]}/{len(asns)} ASNs",flush=True)
ths=[threading.Thread(target=w) for _ in range(12)]
[t.start() for t in ths]; [t.join() for t in ths]
print(f"announced: {len(ann):,} prefixes from {len(asns)-len(errs)} ASNs ({len(errs)} errors)")

merged=list(ipaddress.collapse_addresses(reg+ann))
tot=sum(nn.num_addresses for nn in merged)
print(f"\nUNION, collapsed: {len(merged):,} networks, {tot:,} addresses")
big=[nn for nn in merged if nn.prefixlen<8]
if big: print(f"   WARNING: {len(big)} networks larger than /8 - check: {[str(x) for x in big][:5]}")
json.dump(dict(networks=[str(x) for x in merged],asns=asns,errors=errs,
               registry_addrs=sum(x.num_addresses for x in reg),
               total_addrs=tot),
          io.open("pk_universe.json","w",encoding="utf-8"),indent=1)
print("wrote pk_universe.json")
