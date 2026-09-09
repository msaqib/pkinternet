#!/usr/bin/env python3
"""
Exp 15.1 - vantage fingerprints, derived from traceroutes alone.

Every characteristic below is measured from the probe's own traces. No external
metadata, no assumptions about what network it sits in. Read-only over the 4.1
archive; no network, no credits.

Why: the 4.1 census used one global detour threshold for seven probes whose
domestic baselines range from 3.0 to 47.7 ms. A probe is not a neutral observer,
and these are the properties that make it non-neutral.
"""
import os,io,re,json,collections,statistics as stx,ipaddress

HERE=os.path.dirname(os.path.abspath(__file__))
RUN=os.path.normpath(os.path.join(HERE,"..","..","..",
    "04.1_small_isp_tromboning","results","run_20260627_192918"))
CACHE=os.path.normpath(os.path.join(HERE,"..","..","..",
    "07_longitudinal_panel","analysis",".cache_hop_asn.json"))
HOP=re.compile(r'^\s*(\d+)\s+(\*|[\d.]+)\s*(\d+\.\d+\.\d+\.\d+)?')
asn={}
try: asn=json.load(io.open(CACHE,encoding="utf-8"))
except Exception: pass
SENTINEL=255          # Atlas reports a final pseudo-hop 255; it is not a real router
def cgnat(ip):
    try: return ipaddress.ip_address(ip) in ipaddress.ip_network("100.64.0.0/10")
    except ValueError: return False
def private(ip):
    try: return not ipaddress.ip_address(ip).is_global
    except ValueError: return True

V=collections.defaultdict(lambda: dict(
    traces=0, reached=0, hoptot=0, hopans=0, priv=0, pub=0,
    first_rtt=[], first_pub_depth=[], hopcount=[], answered_frac=[], nopub=0, cg=0,
    upstream=collections.Counter(), asns=set(), maxrtt=[], gw=collections.Counter()))

txt=io.open(os.path.join(RUN,"routes_all_20260703_112939.txt"),encoding="utf-8",errors="replace").read()
for b in txt.split("="*80):
    s=re.search(r'probe\s+\d+\s+-\s+(\S+)',b)
    r=re.search(r'reached=(\S+)',b); mx=re.search(r'maxRTT=([\d.]+)',b)
    if not (s and r): continue
    v=V[s.group(1)]; v["traces"]+=1
    if r.group(1)=="True": v["reached"]+=1
    if mx: v["maxrtt"].append(float(mx.group(1)))
    hs=[]
    for ln in b.splitlines():
        m=HOP.match(ln)
        if m and int(m.group(1))!=SENTINEL:
            hs.append((int(m.group(1)), m.group(3), None if m.group(2)=="*" else float(m.group(2))))
    if not hs: continue
    v["hopcount"].append(len(hs))
    ans=[h for h in hs if h[1]]
    v["hoptot"]+=len(hs); v["hopans"]+=len(ans)
    v["answered_frac"].append(len(ans)/len(hs))
    if ans:
        v["gw"][ans[0][1]]+=1
        if ans[0][2] is not None: v["first_rtt"].append(ans[0][2])
    for hn,ip,rt in ans:
        if cgnat(ip): v["cg"]+=1
        if private(ip): v["priv"]+=1
        else:
            v["pub"]+=1
            a=asn.get(ip,{}).get("asn")
            if a: v["asns"].add(a)
    pub=[h for h in ans if not private(h[1])]
    if not pub: v["nopub"]+=1
    if pub:
        v["first_pub_depth"].append(pub[0][0])
        a=asn.get(pub[0][1],{}).get("holder")
        if a: v["upstream"][a[:26]]+=1

def med(x): return stx.median(x) if x else float("nan")
print("VANTAGE FINGERPRINTS  (all measured from the probe's own traceroutes)\n")
hdr=("probe","traces","reach%","hop ans%","priv%","CGNAT%","NO public hop%","hops","maxRTT")
print(f"{hdr[0]:15}{hdr[1]:>7}{hdr[2]:>8}{hdr[3]:>10}{hdr[4]:>8}{hdr[5]:>8}{hdr[6]:>16}{hdr[7]:>6}{hdr[8]:>9}")
for name in sorted(V, key=lambda k: -V[k]["hopans"]/max(V[k]["hoptot"],1)):
    v=V[name]; tot=max(v["hoptot"],1); ansd=max(v["priv"]+v["pub"],1)
    print(f"{name:15}{v['traces']:>7}{100*v['reached']/v['traces']:>7.1f}%"
          f"{100*v['hopans']/tot:>9.1f}%{100*v['priv']/ansd:>7.1f}%{100*v['cg']/ansd:>7.1f}%"
          f"{100*v['nopub']/v['traces']:>15.1f}%"
          f"{med(v['hopcount']):>6.0f}{med(v['maxrtt']):>9.1f}")
print("\nTRANSIT, as seen in the data plane (first public AS on the path):")
for name in sorted(V):
    v=V[name]; top=v["upstream"].most_common(3)
    tot=sum(v["upstream"].values()) or 1
    s=" | ".join(f"{h} {100*c/tot:.0f}%" for h,c in top)
    print(f"   {name:15}{len(v['asns']):>4} distinct ASNs   {s}")
print("\nGATEWAY (first replying hop), and whether it is the same device every time:")
for name in sorted(V):
    v=V[name]; g=v["gw"].most_common(1)
    tot=sum(v["gw"].values()) or 1
    if g: print(f"   {name:15}{g[0][0]:<17}{100*g[0][1]/tot:5.1f}% of traces   "
                f"({len(v['gw'])} distinct first hops)")
