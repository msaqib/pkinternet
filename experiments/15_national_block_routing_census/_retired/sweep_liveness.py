#!/usr/bin/env python3
"""
15.1 Phase B - liveness sweep.

Finds which destination addresses in Pakistani small-ISP space are actually alive.

DESIGN, and why:
  TCP/80 traceroute, 1 packet, 96 addresses per /24-equivalent, from ONE probe.
  * TCP not ICMP: in the probe-type pilot TCP reached 34/35 targets and ICMP only 14.
    Twenty targets answered TCP but not ICMP; none the other way. An ICMP sweep would
    miss ~60% of live hosts.
  * 1 packet not 3: measured cost is 20 credits vs 60, and liveness needs one reply.
  * 96 addresses: at the 4.1 TCP base rate of 11% that yields ~10.6 live per block,
    clearing the 8-target bar 16.1 needs.
  * one probe: liveness is a property of the target, not the vantage.
  A 1-packet traceroute also returns the path, so this doubles as a first-pass census.

Resumable. State in results/sweep_state.json; re-running continues where it stopped.

  python sweep_liveness.py --probe 7613 --batches 1     # validate throughput
  python sweep_liveness.py --probe 7613                 # run to completion
"""
import os,io,re,sys,csv,json,ssl,time,glob,ipaddress,argparse,datetime,collections
import urllib.request,urllib.error
HERE=os.path.dirname(os.path.abspath(__file__)); RES=os.path.join(HERE,"results")
ROOT=os.path.normpath(os.path.join(HERE,"..","..",".."))
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
PER_EQ24=96; BATCH=90; COST=20      # BATCH stays under Atlas's 100-concurrent cap
ap=argparse.ArgumentParser()
ap.add_argument("--probe",required=True); ap.add_argument("--batches",type=int,default=0)
ap.add_argument("--per",type=int,default=PER_EQ24)
A=ap.parse_args()

def key():
    for l in io.open(os.path.join(ROOT,".env"),encoding="utf-8",errors="replace"):
        m=re.match(r'\s*RIPE_API_KEY\s*=\s*(.+)',l)
        if m: return m.group(1).strip().strip('"\'')
K=key()
def api(p,payload=None):
    r=urllib.request.Request(f"https://atlas.ripe.net/api/v2/{p}",
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization":f"Key {K}","Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=120,context=ctx))

def targets_for(prefix, per):
    net=ipaddress.ip_network(prefix,strict=False)
    n=net.num_addresses
    k=max(1,int(per*max(1,n//256)))
    if n<=k+2: offs=list(range(1,n-1))
    else: offs=[max(1,n*i//(k+1)) for i in range(1,k+1)]
    return [str(net.network_address+o) for o in sorted(set(offs))]

blocks=list(csv.DictReader(io.open(os.path.join(HERE,"phase_a","blocks_20260908.csv"),encoding="utf-8")))
plan=[]
for b in blocks:
    for t in targets_for(b["prefix"],A.per):
        plan.append((b["asn"],b["prefix"],t))
print(f"universe: {len(blocks)} blocks -> {len(plan):,} targets at {A.per}/24-eq")
print(f"estimated cost: {len(plan)*COST:,} credits ({100*len(plan)*COST/78_048_141:.2f}% of balance)")

SF=os.path.join(RES,"sweep_state.json")
state=json.load(io.open(SF,encoding="utf-8")) if os.path.exists(SF) else dict(done=[],msms=[],probe=A.probe,per=A.per)
done=set(state["done"])
todo=[p for p in plan if p[2] not in done]
print(f"already dispatched: {len(done):,}   remaining: {len(todo):,}")
if not todo: sys.exit("nothing to do")

t0=time.time(); sent=0; nb=0
for i in range(0,len(todo),BATCH):
    chunk=todo[i:i+BATCH]
    defs=[dict(target=t,af=4,type="traceroute",protocol="TCP",port=80,packets=1,paris=16,
               max_hops=32,resolve_on_probe=False,is_oneoff=True,
               description=f"exp15.1 liveness {pfx} {t}") for _,pfx,t in chunk]
    try:
        r=api("measurements/",dict(definitions=defs,is_oneoff=True,
              probes=[dict(type="probes",value=str(A.probe),requested=1)]))
        state["msms"].extend(r["measurements"]); state["done"].extend(t for _,_,t in chunk)
        sent+=len(chunk); nb+=1
        json.dump(state,io.open(SF,"w",encoding="utf-8"))
        el=time.time()-t0
        print(f"  batch {nb}: +{len(chunk)} ({sent:,} sent, {el:.0f}s, {sent/max(el,1)*3600:,.0f}/hr)",flush=True)
    except urllib.error.HTTPError as e:
        body=e.read().decode()[:200]
        print(f"  batch {nb+1} HTTP {e.code}: {body}",flush=True)
        if e.code in (429,403):
            print("  rate limited - backing off 120s"); time.sleep(120); continue
        time.sleep(30); continue
    except Exception as e:
        # transient DNS/socket failures must not kill a multi-hour run
        print(f"  batch {nb+1} {type(e).__name__}: {str(e)[:80]} - retrying in 60s",flush=True)
        time.sleep(60); continue
    if A.batches and nb>=A.batches: break
    time.sleep(20)
print(f"\ndispatched {sent:,} this run; {len(state['done']):,} of {len(plan):,} total")
print(f"state saved to results/sweep_state.json")
