#!/usr/bin/env python3
"""
15.1 Phase B (revised) - local liveness scan.

Replaces the Atlas sweep, which was the wrong tool: Atlas caps at 100 simultaneous
measurements, so 207,616 addresses would take ~3 days and 1.5M credits for a SINGLE
vantage's view. A local scan does all of them in under an hour for nothing.

Validated against Atlas ground truth on 174 addresses:
    Atlas alive (54)     -> local finds 49  (91%)
    Atlas no-reply (120) -> local finds 3   (2% false positive)

Method: ICMP first (45/54 on the validation set, the strongest single signal), then
TCP/80 and TCP/443 only for non-responders. A TCP RST counts as alive: the port is
shut but the host answered. Union of the three.

This is a LOWER BOUND on liveness. ~9% of Atlas-reachable hosts do not answer us,
because reachability depends on the source network - which is the project's thesis.

Politeness: target order is shuffled, so no single block or ISP is hammered.
Resumable: results/local_scan.jsonl is append-only, re-running skips what is done.

  python local_scan.py --threads 200 [--limit N]
"""
import os,io,csv,json,time,socket,random,argparse,threading,queue,subprocess,ipaddress
HERE=os.path.dirname(os.path.abspath(__file__)); RES=HERE
ap=argparse.ArgumentParser()
ap.add_argument("--threads",type=int,default=200)
ap.add_argument("--limit",type=int,default=0)
ap.add_argument("--timeout",type=float,default=1.5)
A=ap.parse_args()
OUT=os.path.join(RES,"local_scan.jsonl")

blocks=list(csv.DictReader(io.open(os.path.join(HERE,"..","1_universe","blocks_20260908.csv"),encoding="utf-8")))
targets=[]
for b in blocks:
    net=ipaddress.ip_network(b["prefix"],strict=False)
    for h in net.hosts():
        targets.append((str(h),b["prefix"],b["asn"]))
random.seed(20260909); random.shuffle(targets)          # politeness + unbiased partial runs
done=set()
if os.path.exists(OUT):
    for l in io.open(OUT,encoding="utf-8"):
        try: done.add(json.loads(l)["t"])
        except Exception: pass
todo=[t for t in targets if t[0] not in done]
if A.limit: todo=todo[:A.limit]
print(f"universe : {len(targets):,} addresses in {len(blocks)} blocks")
print(f"done     : {len(done):,}   to scan: {len(todo):,}   threads: {A.threads}")

def tcp(ip,port):
    s=socket.socket(); s.settimeout(A.timeout)
    try: s.connect((ip,port)); s.close(); return True
    except ConnectionRefusedError: return True     # RST: port shut, host alive
    except Exception: return False
    finally:
        try: s.close()
        except Exception: pass
CREATE_NO_WINDOW=0x08000000
def icmp(ip):
    try:
        r=subprocess.run(["ping","-n","1","-w",str(int(A.timeout*1000)),ip],
                         capture_output=True,text=True,timeout=A.timeout+2,
                         creationflags=CREATE_NO_WINDOW)
        return "TTL=" in r.stdout or "ttl=" in r.stdout
    except Exception: return False

q=queue.Queue(); [q.put(t) for t in todo]
lock=threading.Lock(); fh=io.open(OUT,"a",encoding="utf-8")
st=dict(n=0,alive=0,t0=time.time())
def work():
    while True:
        try: ip,pfx,asn=q.get_nowait()
        except queue.Empty: return
        m=[]
        if icmp(ip): m.append("icmp")
        else:
            if tcp(ip,80): m.append("t80")
            elif tcp(ip,443): m.append("t443")
        with lock:
            fh.write(json.dumps({"t":ip,"p":pfx,"a":asn,"m":m},separators=(",",":"))+"\n")
            st["n"]+=1
            if m: st["alive"]+=1
            if st["n"]%2000==0:
                el=time.time()-st["t0"]; r=st["n"]/max(el,1)
                fh.flush()
                print(f"  {st['n']:,}/{len(todo):,}  alive {st['alive']:,} "
                      f"({100*st['alive']/st['n']:.1f}%)  {r:.0f}/s  "
                      f"eta {(len(todo)-st['n'])/max(r,1)/60:.0f} min",flush=True)
ths=[threading.Thread(target=work,daemon=True) for _ in range(A.threads)]
[t.start() for t in ths]; [t.join() for t in ths]
fh.flush(); fh.close()
el=time.time()-st["t0"]
print(f"\ndone: {st['n']:,} scanned, {st['alive']:,} alive ({100*st['alive']/max(st['n'],1):.1f}%) in {el/60:.1f} min")
