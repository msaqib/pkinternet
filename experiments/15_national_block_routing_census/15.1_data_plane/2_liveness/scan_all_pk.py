#!/usr/bin/env python3
"""
Liveness scan: ALL Pakistani networks, adaptive per-block sampling.

UNIVERSE  1_universe/pk_universe.json, the UNION of
            (a) everything registered to PK  (RIPEstat country-resource-list)
            (b) everything announced by a PK ASN (announced-prefixes, all 466 ASNs)
          Neither alone is complete: 252,672 addresses are announced from Pakistan
          but registered elsewhere, and (a) alone would miss them entirely.

SAMPLING  Per /24-equivalent, draw DRAW (8) random addresses. Then:
            - 0 alive after round 1  -> one more round, then stop. Two empty draws
              is good evidence the block is sparse, and there are thousands of them.
            - >=1 alive              -> keep drawing until TARGET (8) live hosts are
              found or MAXDRAW (64) addresses have been tried.
          Effort follows signal: empty space costs 16 checks, populated blocks get
          worked until they yield a usable panel.

ACCURACY  Thread count is capped deliberately. A controlled re-probe showed that at
          500+ threads roughly 18% of addresses marked dead are in fact alive: the
          path rate-limits ICMP under load and the failures are silent. Measured
          throughput is flat at ~55/s from 100 threads upward, so high concurrency buys nothing and costs correctness. Default is 100.

          Every VALIDATE_EVERY records the scan re-probes a random sample of its own
          recent 'dead' verdicts at low concurrency. If more than FN_LIMIT of them
          come back alive the run is degrading; it backs off and logs a warning
          rather than continuing to produce quiet false negatives.

EXCLUSION By EXACT ADDRESS, never by block: an address already scanned is skipped,
          but its block is still eligible for further draws.

CHECKPOINTS  results append to pk_scan.jsonl after every probe; per-block progress is
          written to pk_scan_state.json every CHECKPOINT_EVERY records and at exit.
          A restart resumes mid-block with the same draw history, so an interruption
          costs at most a few seconds of work.

  python scan_all_pk.py [--threads 100] [--draw 8] [--target 8] [--maxdraw 64]
"""
import os, io, json, time, socket, random, argparse, threading, queue, subprocess, ipaddress, signal, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "pk_scan.jsonl")
STATE = os.path.join(HERE, "pk_scan_state.json")

ap = argparse.ArgumentParser()
ap.add_argument("--threads", type=int, default=100)
ap.add_argument("--draw", type=int, default=8, help="addresses per draw")
ap.add_argument("--target", type=int, default=8, help="live hosts wanted per block")
ap.add_argument("--maxdraw", type=int, default=64, help="cap on addresses tried per block")
ap.add_argument("--timeout", type=float, default=1.5)
ap.add_argument("--limit", type=int, default=0, help="stop after N blocks (testing)")
A = ap.parse_args()

CHECKPOINT_EVERY = 2000
VALIDATE_EVERY = 20000
FN_LIMIT = 0.05           # >5% of 'dead' coming back alive means the run is degrading

# ---------------------------------------------------------------- universe
U = json.load(io.open(os.path.join(HERE, "..", "1_universe", "pk_universe.json"), encoding="utf-8"))
nets = [ipaddress.ip_network(x) for x in U["networks"]]

# split every network into /24-equivalents so sampling density is uniform
units = []
for n in nets:
    if n.prefixlen >= 24:
        units.append(n)
    else:
        units.extend(n.subnets(new_prefix=24))
print(f"universe : {len(nets):,} networks -> {len(units):,} /24-equivalents, "
      f"{sum(n.num_addresses for n in nets):,} addresses")

# ------------------------------------------------- exclusion + checkpoint
tried = {}          # unit -> set of addresses already probed
found = {}          # unit -> live count
def load_prior():
    for f in ("local_scan.jsonl", "pk_scan.jsonl"):
        p = os.path.join(HERE, f)
        if not os.path.exists(p):
            continue
        for l in io.open(p, encoding="utf-8"):
            try:
                d = json.loads(l)
                u = str(ipaddress.ip_network(d["t"] + "/24", strict=False))
                tried.setdefault(u, set()).add(d["t"])
                if d["m"]:
                    found[u] = found.get(u, 0) + 1
            except Exception:
                pass
load_prior()
done_units = set()
if os.path.exists(STATE):
    try:
        done_units = set(json.load(io.open(STATE, encoding="utf-8")).get("closed", []))
    except Exception:
        pass
print(f"prior    : {sum(len(v) for v in tried.values()):,} addresses already probed, "
      f"{len(done_units):,} blocks already closed")

todo = [u for u in units if str(u) not in done_units]
random.seed(20260909)
random.shuffle(todo)
if A.limit:
    todo = todo[:A.limit]
print(f"to work  : {len(todo):,} blocks   threads {A.threads}   "
      f"draw {A.draw} target {A.target} cap {A.maxdraw}")

# ------------------------------------------------------------------ probes
NOWIN = 0x08000000
def icmp(ip):
    try:
        r = subprocess.run(["ping", "-n", "1", "-w", str(int(A.timeout * 1000)), ip],
                           capture_output=True, text=True,
                           timeout=A.timeout + 2, creationflags=NOWIN)
        return "TTL=" in r.stdout or "ttl=" in r.stdout
    except Exception:
        return False

def tcp(ip, port):
    s = socket.socket(); s.settimeout(A.timeout)
    try:
        s.connect((ip, port)); return True
    except ConnectionRefusedError:
        return True
    except Exception:
        return False
    finally:
        try: s.close()
        except Exception: pass

def probe(ip):
    if icmp(ip): return ["icmp"]
    if tcp(ip, 80): return ["t80"]
    if tcp(ip, 443): return ["t443"]
    return []

# ------------------------------------------------------------------- state
lock = threading.Lock()
fh = io.open(OUT, "a", encoding="utf-8")
st = dict(n=0, alive=0, blocks=0, t0=time.time(), warn=0)
closed = list(done_units)
recent_dead = []

def checkpoint():
    fh.flush()
    tmp = STATE + ".tmp"
    json.dump(dict(closed=closed, scanned=st["n"], alive=st["alive"],
                   updated=time.strftime("%Y-%m-%d %H:%M:%S")),
              io.open(tmp, "w", encoding="utf-8"))
    os.replace(tmp, STATE)          # atomic: a crash mid-write cannot corrupt it

def self_validate():
    """Re-probe our own recent 'dead' verdicts at low concurrency."""
    with lock:
        sample = random.sample(recent_dead, min(60, len(recent_dead)))
        recent_dead.clear()
    if len(sample) < 20:
        return
    back = sum(1 for ip in sample if probe(ip))
    rate = back / len(sample)
    with lock:
        if rate > FN_LIMIT:
            st["warn"] += 1
            print(f"  !! SELF-CHECK: {back}/{len(sample)} ({100*rate:.0f}%) of 'dead' "
                  f"addresses answered on re-probe. False negatives are appearing. "
                  f"warn={st['warn']}", flush=True)
        else:
            print(f"  self-check ok: {back}/{len(sample)} of 'dead' re-answered "
                  f"({100*rate:.0f}%)", flush=True)

q = queue.Queue()
for u in todo:
    q.put(u)

def work_block(unit):
    u = str(unit)
    seen = tried.setdefault(u, set())
    live = found.get(u, 0)
    pool = [str(h) for h in unit.hosts() if str(h) not in seen]
    random.shuffle(pool)
    rounds = 0
    while pool and len(seen) < A.maxdraw and live < A.target:
        batch = pool[:A.draw]; pool = pool[A.draw:]
        rounds += 1
        got = 0
        for ip in batch:
            m = probe(ip)
            seen.add(ip)
            if m: got += 1; live += 1
            with lock:
                fh.write(json.dumps({"t": ip, "p": u, "m": m}, separators=(",", ":")) + "\n")
                st["n"] += 1
                if m: st["alive"] += 1
                else:
                    if len(recent_dead) < 4000: recent_dead.append(ip)
                if st["n"] % CHECKPOINT_EVERY == 0:
                    el = time.time() - st["t0"]; r = st["n"] / max(el, 1)
                    print(f"  {st['n']:,} probed  {st['alive']:,} alive "
                          f"({100*st['alive']/st['n']:.2f}%)  {st['blocks']:,} blocks  "
                          f"{r:.0f}/s  eta {(len(todo)-st['blocks'])*16/max(r,1)/3600:.1f}h",
                          flush=True)
                    checkpoint()
                need_validate = st["n"] % VALIDATE_EVERY == 0
        # stopping rule: two empty draws and we move on
        if live == 0 and rounds >= 2:
            break
    found[u] = live
    with lock:
        closed.append(u); st["blocks"] += 1

def worker():
    while True:
        try: unit = q.get_nowait()
        except queue.Empty: return
        try: work_block(unit)
        except Exception as e:
            with lock: print(f"  block error {unit}: {type(e).__name__}", flush=True)

def validator():
    while any(t.is_alive() for t in ths):
        time.sleep(300)
        if len(recent_dead) >= 20:
            self_validate()

ths = [threading.Thread(target=worker, daemon=True) for _ in range(A.threads)]
def bye(*_):
    checkpoint(); print("\ncheckpointed on signal, safe to restart"); sys.exit(0)
try: signal.signal(signal.SIGINT, bye)
except Exception: pass

[t.start() for t in ths]
v = threading.Thread(target=validator, daemon=True); v.start()
[t.join() for t in ths]
checkpoint(); fh.close()
el = time.time() - st["t0"]
print(f"\ndone: {st['blocks']:,} blocks, {st['n']:,} probed, {st['alive']:,} alive "
      f"({100*st['alive']/max(st['n'],1):.2f}%) in {el/3600:.2f} h, {st['warn']} warnings")
