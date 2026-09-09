#!/usr/bin/env python3
"""
Measure this scan's false-negative rate AS A FUNCTION OF WHEN a check happened.

pk_scan.jsonl is append-only, so line position is a proxy for scan time. The run's
own self-checks reported rates from 2% to 17%, so a single headline error figure
would be misleading. This splits the file into deciles, re-probes a random sample of
'dead' verdicts from each, and reports the rate per decile.

If the rate is flat, the error is uniform and per-ISP comparisons are safe (target
order was shuffled, so every ISP is spread across all deciles equally).
If it spikes, the affected windows have to be identified before the data is used.

  python validate_scan.py [--per 120]
"""
import io,json,socket,subprocess,threading,queue,random,argparse,time
ap=argparse.ArgumentParser(); ap.add_argument("--per",type=int,default=120); A=ap.parse_args()
rows=[]
for i,l in enumerate(io.open("pk_scan.jsonl",encoding="utf-8")):
    d=json.loads(l)
    if not d["m"]: rows.append((i,d["t"]))
N=sum(1 for _ in io.open("pk_scan.jsonl",encoding="utf-8"))
print(f"{N:,} checks, {len(rows):,} marked dead")
D=10; edges=[i*N//D for i in range(D+1)]
buckets=[[t for pos,t in rows if edges[k]<=pos<edges[k+1]] for k in range(D)]
random.seed(31)
sample=[(k,ip) for k in range(D) for ip in random.sample(buckets[k],min(A.per,len(buckets[k])))]
print(f"re-probing {len(sample):,} dead addresses, {A.per} per decile, at 40 threads\n")
NOWIN=0x08000000
def probe(ip,to=2.0):
    try:
        r=subprocess.run(["ping","-n","1","-w",str(int(to*1000)),ip],capture_output=True,
                         text=True,timeout=to+2,creationflags=NOWIN)
        if "TTL=" in r.stdout or "ttl=" in r.stdout: return True
    except Exception: pass
    for p in (80,443):
        s=socket.socket(); s.settimeout(to)
        try: s.connect((ip,p)); return True
        except ConnectionRefusedError: return True
        except Exception: pass
        finally:
            try: s.close()
            except Exception: pass
    return False
q=queue.Queue(); [q.put(x) for x in sample]
hit=[0]*D; tot=[0]*D; lock=threading.Lock()
def w():
    while True:
        try: k,ip=q.get_nowait()
        except queue.Empty: return
        r=probe(ip)
        with lock:
            tot[k]+=1
            if r: hit[k]+=1
t0=time.time()
ths=[threading.Thread(target=w) for _ in range(40)]
[t.start() for t in ths]; [t.join() for t in ths]
print(f"{'decile':>7}{'checks in it':>15}{'resampled':>11}{'came back alive':>17}{'rate':>8}")
for k in range(D):
    print(f"{k+1:>7}{len(buckets[k]):>15,}{tot[k]:>11}{hit[k]:>17}{100*hit[k]/max(tot[k],1):>7.1f}%")
o=sum(hit)/max(sum(tot),1)
print(f"\noverall false-negative rate: {100*o:.1f}%  ({sum(hit)}/{sum(tot)})  in {time.time()-t0:.0f}s")
r=[100*hit[k]/max(tot[k],1) for k in range(D)]
print(f"spread across deciles: min {min(r):.1f}%  max {max(r):.1f}%")
