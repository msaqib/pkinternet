#!/usr/bin/env python3
"""
15.1 Phase 1 - probe-type pilot.

Question: the 4.1 census had a MEDIAN HOP RESPONSE RATE OF 50%. Half of all routers
never replied. A responsiveness sweep cannot fix that; only the probe protocol can.
This measures ICMP vs TCP/80 vs UDP on identical targets from identical probes.

Cost: 20 targets x 15 probes x 3 protocols x 60 credits = 54,000 credits.
Account: .env at the repo root (main). Balance checked before firing.

  python fire_probe_type_pilot.py          # dry run, prints the plan and cost
  python fire_probe_type_pilot.py --fire   # actually creates the measurements
"""
import os,io,re,sys,json,ssl,time,datetime,urllib.request,urllib.error

HERE=os.path.dirname(os.path.abspath(__file__))
RES=HERE
ROOT=os.path.normpath(os.path.join(HERE,"..","..","..",".."))
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

# every connected PK probe as of 2026-09-08, plus the 4 disconnected ones.
# Atlas returns results only for probes that are up, and we are billed per result,
# so listing all 16 costs nothing extra and tests the roster at the same time.
PROBES=[1016126,1015679,7613,1016036,1016154,60223,64535,64078,
        65892,62224,1014872,64722,1016393,7764,1016143,65761,1017098,1017335,1016467]
PROTOCOLS=[("ICMP",{}),("TCP",{"port":80}),("UDP",{})]
TR_COST=60

def key():
    for line in io.open(os.path.join(ROOT,".env"),encoding="utf-8",errors="replace"):
        m=re.match(r'\s*RIPE_API_KEY\s*=\s*(.+)',line)
        if m: return m.group(1).strip().strip('"\'')
    sys.exit("no RIPE_API_KEY in .env at the repo root")

def api(path,payload=None,k=None):
    url=f"https://atlas.ripe.net/api/v2/{path}"
    data=json.dumps(payload).encode() if payload else None
    r=urllib.request.Request(url,data=data,
        headers={"Authorization":f"Key {k}","Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=90,context=ctx))

targets=[t["target"] for t in json.load(io.open(os.path.join(RES,"pilot_targets.json"),encoding="utf-8"))]
n=len(targets)*len(PROBES)*len(PROTOCOLS)
print(f"targets   : {len(targets)}")
print(f"probes    : {len(PROBES)} listed (only connected ones return results)")
print(f"protocols : {[p for p,_ in PROTOCOLS]}")
print(f"max results: {n:,}  ->  up to {n*TR_COST:,} credits (billed per RESULT, so less if probes are down)")

if "--fire" not in sys.argv:
    print("\nDRY RUN. re-run with --fire to create the measurements."); sys.exit(0)

K=key()
bal=api("credits/",k=K)["current_balance"]
print(f"\nbalance before: {bal:,}")
if bal < n*TR_COST:
    sys.exit("insufficient credits, aborting")

stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
created={}
for proto,extra in PROTOCOLS:
    defs=[dict(target=t,af=4,type="traceroute",protocol=proto,packets=3,paris=16,
               resolve_on_probe=False,is_oneoff=True,
               description=f"exp15.1 probe-type pilot {proto} {t}",**extra) for t in targets]
    payload=dict(definitions=defs,is_oneoff=True,
                 probes=[dict(type="probes",value=",".join(map(str,PROBES)),requested=len(PROBES))])
    try:
        r=api("measurements/",payload,K)
        created[proto]=r["measurements"]
        print(f"  {proto:5} -> {len(r['measurements'])} measurements created")
    except urllib.error.HTTPError as e:
        body=e.read().decode()[:300]
        print(f"  {proto:5} -> HTTP {e.code}: {body}")
        created[proto]=[]
    time.sleep(3)

out=dict(stamp=stamp,targets=targets,probes=PROBES,
         protocols=[p for p,_ in PROTOCOLS],measurements=created,
         balance_before=bal,balance_after=api("credits/",k=K)["current_balance"])
json.dump(out,io.open(os.path.join(RES,f"pilot_msms_{stamp}.json"),"w",encoding="utf-8"),indent=1)
print(f"\nbalance after : {out['balance_after']:,}  (spent {bal-out['balance_after']:,})")
print(f"wrote results/pilot_msms_{stamp}.json")
