#!/usr/bin/env python3
"""
15.1 Phase B - collect the liveness sweep.

Atlas has no bulk result endpoint (msm_id__in returns 405), so each measurement is
fetched individually, in parallel. Resumable: already-fetched ids are skipped, so
this can be killed and restarted safely.

Writes results/sweep_results.jsonl, one compact record per line:
  {t: target, a: alive, n: hops, k: hops answered, h: [[ip,rtt],...]}

  python collect_sweep.py [--threads 16]
"""
import os,io,re,json,ssl,sys,time,threading,queue,argparse,urllib.request,urllib.error
HERE=os.path.dirname(os.path.abspath(__file__)); RES=os.path.join(HERE,"results")
ROOT=os.path.normpath(os.path.join(HERE,"..","..",".."))
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
ap=argparse.ArgumentParser(); ap.add_argument("--threads",type=int,default=16)
ap.add_argument("--limit",type=int,default=0); A=ap.parse_args()
K=[re.match(r'\s*RIPE_API_KEY\s*=\s*(.+)',l).group(1).strip().strip('"\'')
   for l in io.open(os.path.join(ROOT,".env"),encoding="utf-8",errors="replace")
   if re.match(r'\s*RIPE_API_KEY\s*=',l)][0]
OUT=os.path.join(RES,"sweep_results.jsonl")
DONE=os.path.join(RES,"sweep_collected.json")

st=json.load(io.open(os.path.join(RES,"sweep_state.json"),encoding="utf-8"))
msms=st["msms"]
done=set(json.load(io.open(DONE,encoding="utf-8"))) if os.path.exists(DONE) else set()
todo=[m for m in msms if m not in done]
if A.limit: todo=todo[:A.limit]
print(f"measurements: {len(msms):,}   already collected: {len(done):,}   to fetch: {len(todo):,}")
if not todo: sys.exit("nothing to fetch")

q=queue.Queue(); [q.put(m) for m in todo]
lock=threading.Lock(); fh=io.open(OUT,"a",encoding="utf-8")
stats=dict(ok=0,err=0,alive=0,pending=0,t0=time.time())

def work():
    while True:
        try: m=q.get_nowait()
        except queue.Empty: return
        for attempt in (1,2,3):
            try:
                r=urllib.request.Request(f"https://atlas.ripe.net/api/v2/measurements/{m}/results/",
                                         headers={"Authorization":f"Key {K}"})
                rs=json.load(urllib.request.urlopen(r,timeout=60,context=ctx))
                for x in rs:
                    dst=x.get("dst_addr")
                    if not dst: continue
                    hops=[]; alive=False; n=0; k=0
                    for h in x.get("result",[]):
                        if h.get("hop")==255: continue
                        n+=1
                        pk=[p for p in h.get("result",[]) if isinstance(p,dict)]
                        ip=next((p.get("from") for p in pk if p.get("from")),None)
                        rt=[p["rtt"] for p in pk if p.get("rtt") is not None]
                        if ip:
                            k+=1; hops.append([ip, round(min(rt),1) if rt else None])
                            if ip==dst: alive=True
                    with lock:
                        fh.write(json.dumps(dict(t=dst,a=alive,n=n,k=k,h=hops),
                                            separators=(",",":"))+"\n")
                        stats["ok"]+=1
                        if alive: stats["alive"]+=1
                # only mark collected when the measurement actually returned results.
                # an empty list means it has not finished running yet; marking it done
                # would skip it permanently on the next pass.
                if rs:
                    with lock: done.add(m)
                else:
                    with lock: stats['pending']+=1
                break
            except urllib.error.HTTPError as e:
                if e.code==429: time.sleep(20); continue
                with lock: stats["err"]+=1
                break
            except Exception:
                if attempt==3:
                    with lock: stats["err"]+=1
                else: time.sleep(5)
        q.task_done()

ths=[threading.Thread(target=work,daemon=True) for _ in range(A.threads)]
[t.start() for t in ths]
last=0
while any(t.is_alive() for t in ths):
    time.sleep(20)
    with lock:
        el=time.time()-stats["t0"]; n=stats["ok"]
        if n!=last:
            print(f"  {n:,} results  ({stats['alive']:,} alive, {stats['pending']:,} not ready, {stats['err']} err)  "
                  f"{n/max(el,1):.0f}/s  eta {(len(todo)-len(done))/max(n/max(el,1),0.1)/60:.0f} min",flush=True)
            last=n
            fh.flush(); json.dump(sorted(done),io.open(DONE,"w",encoding="utf-8"))
fh.flush(); fh.close(); json.dump(sorted(done),io.open(DONE,"w",encoding="utf-8"))
print(f"\ndone: {stats['ok']:,} results, {stats['alive']:,} alive, {stats['err']} errors")
