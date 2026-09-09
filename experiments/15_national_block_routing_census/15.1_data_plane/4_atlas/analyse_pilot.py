#!/usr/bin/env python3
"""15.1 probe-type pilot - analysis. Excludes Atlas's hop-255 sentinel."""
import os,io,json,glob,collections,statistics as stx,ipaddress
RES=os.path.dirname(os.path.abspath(__file__))
SENT=255
raw=json.load(io.open(sorted(glob.glob(os.path.join(RES,"pilot_raw_*.json")))[-1],encoding="utf-8"))
tg={t["target"]:t for t in json.load(io.open(os.path.join(RES,"pilot_targets.json"),encoding="utf-8"))}
def pub(ip):
    try: return ipaddress.ip_address(ip).is_global
    except ValueError: return False
rows=[]
for proto,res in raw.items():
    for r in res:
        dst=r.get("dst_addr"); prb=r.get("prb_id")
        if not dst: continue
        hs=[]
        for h in r.get("result",[]):
            if h.get("hop")==SENT: continue
            pk=h.get("result",[])
            ip=next((p.get("from") for p in pk if p.get("from")),None)
            rt=[p["rtt"] for p in pk if p.get("rtt") is not None]
            hs.append((ip,min(rt) if rt else None))
        if not hs: continue
        ans=[h for h in hs if h[0]]
        rows.append(dict(proto=proto,target=dst,probe=prb,
                         group=tg.get(dst,{}).get("group","?"),
                         tot=len(hs),ans=len(ans),
                         pub=sum(1 for ip,_ in ans if pub(ip)),
                         reached=any(ip==dst for ip,_ in hs)))
print(f"results analysed: {len(rows)}\n")
print("="*72); print("1. PROTOCOL COMPARISON  (4.1 used TCP/80 and got 50% hop response)"); print("="*72)
print(f"{'protocol':10}{'results':>9}{'hop answered':>14}{'reached':>10}{'public hops':>13}")
for p in ("ICMP","TCP","UDP"):
    g=[r for r in rows if r["proto"]==p]
    if not g: continue
    ha=100*sum(r["ans"] for r in g)/max(sum(r["tot"] for r in g),1)
    rc=100*sum(r["reached"] for r in g)/len(g)
    pb=100*sum(r["pub"] for r in g)/max(sum(r["ans"] for r in g),1)
    print(f"{p:10}{len(g):>9}{ha:>13.1f}%{rc:>9.1f}%{pb:>12.1f}%")
print("\n"+"="*72); print("2. THE CONTROL: do dark targets answer under another protocol?"); print("="*72)
print(f"{'group':22}{'ICMP':>18}{'TCP':>18}{'UDP':>18}")
for grp,lab in (("A_live","A live under TCP/80"),("B_dark_live_block","B dark, block live"),
                ("C_dark_block","C dark, block dark")):
    cells=[]
    for p in ("ICMP","TCP","UDP"):
        g=[r for r in rows if r["proto"]==p and r["group"]==grp]
        cells.append(f"{100*sum(r['reached'] for r in g)/len(g):.0f}% reached" if g else "-")
    print(f"{lab:22}{cells[0]:>18}{cells[1]:>18}{cells[2]:>18}")
print("\ntargets newly reached by a protocol that TCP/80 could not reach:")
by=collections.defaultdict(lambda: collections.defaultdict(bool))
for r in rows:
    if r["reached"]: by[r["target"]][r["proto"]]=True
new=[(t,d) for t,d in by.items() if tg.get(t,{}).get("group","").startswith(("B","C")) and any(d.values())]
for t,d in sorted(new):
    print(f"   {t:17} {tg[t]['company'][:30]:32}{','.join(sorted(k for k in d if d[k]))}")
print(f"   -> {len(new)} of {sum(1 for t in tg if tg[t]['group'].startswith(('B','C')))} previously-dark targets now reachable")
print("\n"+"="*72); print("3. PER PROBE, best protocol"); print("="*72)
print(f"{'probe':>9}{'results':>9}{'ICMP ans%':>11}{'TCP ans%':>10}{'UDP ans%':>10}{'best':>7}{'reach%':>8}")
for prb in sorted({r["probe"] for r in rows}):
    cells={}
    for p in ("ICMP","TCP","UDP"):
        g=[r for r in rows if r["probe"]==prb and r["proto"]==p]
        cells[p]=100*sum(r["ans"] for r in g)/max(sum(r["tot"] for r in g),1) if g else 0
    tot=[r for r in rows if r["probe"]==prb]
    best=max(cells,key=cells.get)
    rc=100*sum(r["reached"] for r in tot)/len(tot)
    print(f"{prb:>9}{len(tot):>9}{cells['ICMP']:>10.1f}%{cells['TCP']:>9.1f}%{cells['UDP']:>9.1f}%{best:>7}{rc:>7.1f}%")
