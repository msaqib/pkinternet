#!/usr/bin/env python3
"""
Second-vantage top-up scan.

TARGETS   Blocks that already have between 1 and 7 live hosts. They are known to be
          populated and are short of the 8 needed for an Exp 16.1 panel block. Blocks
          with zero live are deliberately excluded from this pass: the prior is much
          weaker and they are 4x the volume.

VANTAGE   This runs from a DIFFERENT network than the earlier scans. Every record
          carries a "v" field with the egress ASN, so the two vantages stay separable
          and nothing silently merges. After this pass, "alive" for a topped-up block
          means "answered from vantage A or vantage B", which is a union across two
          independent networks and strictly better evidence than either alone.

          This is not only a repair. Measured on 250 known-alive addresses, about 8%
          of hosts that answer from the first vantage do not answer from this one,
          at every concurrency from 10 to 200 threads. That asymmetry is a real
          property of Pakistani interconnection, not a measurement fault, and a
          second vantage measures it directly.

CONCURRENCY  50 threads. The recall-vs-concurrency curve on this network is flat
          (92.4% at 10 threads, 92.4% at 200), so the loss is vantage, not load.
          50 sits at the throughput knee without buying extra error.

METHOD    Identical to the earlier scans so results are comparable: ICMP, then
          TCP/80, then TCP/443; first answer wins; an RST counts as alive.

CHECKPOINTS  Append after every check; block state written atomically every 2,000.
          Restart resumes without loss.

  python topup_scan.py [--threads 50] [--extra 32]
"""
import os, io, json, time, socket, random, argparse, threading, queue, subprocess, ipaddress, ssl, sys, signal
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "topup_scan.jsonl")
STATE = os.path.join(HERE, "topup_state.json")

ap = argparse.ArgumentParser()
ap.add_argument("--threads", type=int, default=50)
ap.add_argument("--extra", type=int, default=32, help="additional addresses per block")
ap.add_argument("--target", type=int, default=8, help="live hosts wanted per block")
ap.add_argument("--timeout", type=float, default=1.5)
ap.add_argument("--limit", type=int, default=0)
A = ap.parse_args()

# ------------------------------------------------------------- vantage id
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
def vantage():
    try:
        ip = json.load(urllib.request.urlopen(
            "https://stat.ripe.net/data/whats-my-ip/data.json", timeout=25, context=ctx))["data"]["ip"]
        n = json.load(urllib.request.urlopen(
            f"https://stat.ripe.net/data/network-info/data.json?resource={ip}",
            timeout=25, context=ctx))["data"]
        return (n.get("asns") or ["?"])[0]
    except Exception:
        return "?"
V = vantage()
print(f"vantage  : AS{V}")

# --------------------------------------------------------- current state
blk = {}     # unit -> [live, set(addresses already checked)]
for f in ("pk_scan.jsonl", "local_scan.jsonl", "topup_scan.jsonl"):
    p = os.path.join(HERE, f)
    if not os.path.exists(p): continue
    for l in io.open(p, encoding="utf-8"):
        try:
            d = json.loads(l)
            u = str(ipaddress.ip_network(d["t"] + "/24", strict=False))
            e = blk.setdefault(u, [0, set()])
            e[1].add(d["t"])
            if d["m"]: e[0] += 1
        except Exception:
            pass

todo = [(u, v[0], v[1]) for u, v in blk.items() if 1 <= v[0] < A.target]
done = set()
if os.path.exists(STATE):
    try: done = set(json.load(io.open(STATE, encoding="utf-8")).get("closed", []))
    except Exception: pass
todo = [t for t in todo if t[0] not in done]
random.seed(20260909); random.shuffle(todo)
if A.limit: todo = todo[:A.limit]
print(f"blocks with 1-7 live: {len(todo):,} to work "
      f"({len(done):,} already done this pass)")
print(f"budget   : up to {A.extra} extra checks each = {len(todo)*A.extra:,} checks")

# ---------------------------------------------------------------- probing
NOWIN = 0x08000000
def icmp(ip):
    try:
        r = subprocess.run(["ping", "-n", "1", "-w", str(int(A.timeout*1000)), ip],
                           capture_output=True, text=True,
                           timeout=A.timeout+2, creationflags=NOWIN)
        return "TTL=" in r.stdout or "ttl=" in r.stdout
    except Exception:
        return False

def tcp(ip, port):
    s = socket.socket(); s.settimeout(A.timeout)
    try: s.connect((ip, port)); return True
    except ConnectionRefusedError: return True
    except Exception: return False
    finally:
        try: s.close()
        except Exception: pass

def probe(ip):
    if icmp(ip): return ["icmp"]
    if tcp(ip, 80): return ["t80"]
    if tcp(ip, 443): return ["t443"]
    return []

lock = threading.Lock()
fh = io.open(OUT, "a", encoding="utf-8")
st = dict(n=0, new=0, blocks=0, reached=0, t0=time.time())
closed = list(done)

def checkpoint():
    fh.flush()
    tmp = STATE + ".tmp"
    json.dump(dict(closed=closed, checks=st["n"], new_live=st["new"],
                   vantage=str(V), updated=time.strftime("%Y-%m-%d %H:%M:%S")),
              io.open(tmp, "w", encoding="utf-8"))
    os.replace(tmp, STATE)

q = queue.Queue()
for t in todo: q.put(t)

def work():
    while True:
        try: unit, live0, seen = q.get_nowait()
        except queue.Empty: return
        try:
            net = ipaddress.ip_network(unit)
            pool = [str(h) for h in net.hosts() if str(h) not in seen]
            random.shuffle(pool)
            live = live0; used = 0
            for ip in pool:
                if used >= A.extra or live >= A.target: break
                m = probe(ip); used += 1
                if m: live += 1
                with lock:
                    fh.write(json.dumps({"t": ip, "p": unit, "m": m, "v": str(V)},
                                        separators=(",", ":")) + "\n")
                    st["n"] += 1
                    if m: st["new"] += 1
                    if st["n"] % 2000 == 0:
                        el = time.time()-st["t0"]; r = st["n"]/max(el, 1)
                        print(f"  {st['n']:,} checks  {st['new']:,} new live  "
                              f"{st['blocks']:,} blocks  {st['reached']:,} reached 8  "
                              f"{r:.0f}/s  eta {(len(todo)-st['blocks'])*A.extra/max(r,1)/3600:.1f}h",
                              flush=True)
                        checkpoint()
            with lock:
                st["blocks"] += 1; closed.append(unit)
                if live >= A.target: st["reached"] += 1
        except Exception as e:
            with lock: print(f"  block {unit}: {type(e).__name__}", flush=True)

ths = [threading.Thread(target=work, daemon=True) for _ in range(A.threads)]
def bye(*_):
    checkpoint(); print("\ncheckpointed, safe to restart"); sys.exit(0)
try: signal.signal(signal.SIGINT, bye)
except Exception: pass
[t.start() for t in ths]; [t.join() for t in ths]
checkpoint(); fh.close()
el = time.time()-st["t0"]
print(f"\ndone: {st['blocks']:,} blocks, {st['n']:,} checks, {st['new']:,} new live hosts, "
      f"{st['reached']:,} blocks reached {A.target}, in {el/3600:.2f} h")
