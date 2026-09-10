#!/usr/bin/env python3
"""
Measure RTT properly, for addresses the sweep only ever sampled once.

WHY THIS EXISTS
  local_trace.py was built to answer two topological questions, "did it reach" and
  "how complete is the path". It sends ONE packet per TTL and ran at 120 threads.
  RoundTripTime came back for free and was recorded, but a single sample under heavy
  concurrency is not a latency measurement. Measured consequences on that data:
    - one fixed router address spans 4 ms to 853 ms
    - 22% of adjacent hop pairs show RTT FALLING deeper into the path, which distance
      cannot do
  So every latency rule built on it collapsed. This pass fixes the input rather than
  retuning thresholds to fit bad data.

WHAT IT DOES DIFFERENTLY
  1. MANY PACKETS per address, not one.
  2. LOW CONCURRENCY. The inflation is our own contention, so 8 threads, not 120.
  3. Reports the MINIMUM as the propagation estimate. Queuing, rate limiting and
     ICMP generation delay only ever ADD to a round trip, never subtract, so over a
     burst the minimum is the closest approach to the physical path cost. Median is
     the wrong estimator for distance: it carries the queuing.
  4. Keeps the full sample so dispersion is visible. An address whose min and p25 sit
     far apart is being rate limited, and that is worth knowing rather than averaging.

  WHY MIN IS SAFE HERE, when RULES.md R2 insists on a median.
  R2 takes its samples from DIFFERENT traces spread over hours, where a single fast
  reading can come from a routing change or a mislabelled hop, so one lucky packet
  must not falsify a country. Here the samples are a controlled burst to ONE address
  over a few seconds. That is a measurement, not a coincidence, and `spread` below
  lets a caller reject bursts that look unstable.

  python measure_rtt.py --what foreign      # the 516 addresses that decide verdicts
  python measure_rtt.py --what routers      # every intermediate router
  python measure_rtt.py --what destinations # every target, for the R4 baseline
  python measure_rtt.py --what all
"""
import os, io, json, time, socket, struct, ctypes, argparse, threading, queue, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--what", default="foreign",
                choices=["foreign", "routers", "destinations", "all"])
ap.add_argument("--packets", type=int, default=30, help="echoes per address")
ap.add_argument("--threads", type=int, default=8, help="keep this LOW; contention is the bug")
ap.add_argument("--timeout", type=int, default=1000)
ap.add_argument("--gap", type=float, default=0.05, help="seconds between packets to one address")
ap.add_argument("--limit", type=int, default=0)
A = ap.parse_args()
OUT = os.path.join(HERE, f"rtt_{A.what}.json")

iph = ctypes.windll.iphlpapi
class IP_OPTION_INFORMATION(ctypes.Structure):
    _fields_ = [("Ttl", ctypes.c_ubyte), ("Tos", ctypes.c_ubyte),
                ("Flags", ctypes.c_ubyte), ("OptionsSize", ctypes.c_ubyte),
                ("OptionsData", ctypes.c_void_p)]
class ICMP_ECHO_REPLY(ctypes.Structure):
    _fields_ = [("Address", ctypes.c_uint32), ("Status", ctypes.c_ulong),
                ("RoundTripTime", ctypes.c_ulong), ("DataSize", ctypes.c_ushort),
                ("Reserved", ctypes.c_ushort), ("Data", ctypes.c_void_p),
                ("Options", IP_OPTION_INFORMATION)]
iph.IcmpCreateFile.restype = ctypes.c_void_p
iph.IcmpSendEcho.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p,
                             ctypes.c_ushort, ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_ulong, ctypes.c_ulong]
iph.IcmpSendEcho.restype = ctypes.c_ulong
DATA = b"exp15rtt"
BUFSZ = ctypes.sizeof(ICMP_ECHO_REPLY) + len(DATA) + 64


def burst(handle, ip, n, timeout, gap):
    """n echoes to one address. Returns the RTTs that came back."""
    dst = struct.unpack("<I", socket.inet_aton(ip))[0]
    out = []
    for _ in range(n):
        buf = ctypes.create_string_buffer(BUFSZ)
        if iph.IcmpSendEcho(handle, dst, DATA, len(DATA), None, buf, BUFSZ, timeout):
            r = ICMP_ECHO_REPLY.from_buffer_copy(buf)
            if r.Status == 0:
                out.append(int(r.RoundTripTime))
        time.sleep(gap)
    return out


ann = json.load(io.open(os.path.join(HERE, "selected_annotated.json"), encoding="utf-8"))
HOME = ("PK", "PRIV", "CGN", "??")
dests, routers, foreign, meta = set(), set(), set(), {}
for r in ann:
    dests.add(r["target"])
    for h in r["path"]:
        if not h:
            continue
        meta[h["ip"]] = dict(cc=h["cc"], asn=h.get("asn"),
                             holder=(h.get("holder") or "")[:40], kind=h.get("kind"))
        if h["ip"] != r["target"]:
            routers.add(h["ip"])
        if h["cc"] not in HOME:
            foreign.add(h["ip"])
targets = {"foreign": foreign, "routers": routers, "destinations": dests,
           "all": foreign | routers | dests}[A.what]
targets = sorted(targets)
if A.limit:
    targets = targets[:A.limit]

print(f"measuring {len(targets):,} addresses, {A.packets} packets each, "
      f"{A.threads} threads, {A.gap*1000:.0f} ms apart")
print(f"estimated {len(targets)*A.packets*(A.gap+0.08)/A.threads/60:.0f} min\n")

res, lock, q = {}, threading.Lock(), queue.Queue()
for t in targets:
    q.put(t)
st_ = dict(n=0, ok=0, t0=time.time())


def work():
    h = ctypes.c_void_p(iph.IcmpCreateFile())
    while True:
        try:
            ip = q.get_nowait()
        except queue.Empty:
            return
        v = burst(h, ip, A.packets, A.timeout, A.gap)
        with lock:
            st_["n"] += 1
            if v:
                st_["ok"] += 1
                s = sorted(v)
                res[ip] = dict(n=len(v), sent=A.packets,
                               min=s[0], p25=s[len(s)//4], median=st.median(s), max=s[-1],
                               spread=s[len(s)//4]-s[0], loss=round(1-len(v)/A.packets, 3),
                               **meta.get(ip, {}))
            else:
                res[ip] = dict(n=0, sent=A.packets, loss=1.0, **meta.get(ip, {}))
            if st_["n"] % 50 == 0:
                el = time.time()-st_["t0"]
                print(f"  {st_['n']:,}/{len(targets):,}  {st_['ok']:,} answered  "
                      f"{st_['n']/max(el,1)*60:.0f}/min  "
                      f"eta {(len(targets)-st_['n'])/max(st_['n']/max(el,1),.01)/60:.0f} min",
                      flush=True)
                json.dump(res, io.open(OUT+".tmp", "w", encoding="utf-8"))
                os.replace(OUT+".tmp", OUT)


ths = [threading.Thread(target=work, daemon=True) for _ in range(A.threads)]
[t.start() for t in ths]
[t.join() for t in ths]
json.dump(res, io.open(OUT, "w", encoding="utf-8"))
got = [v for v in res.values() if v.get("n")]
print(f"\ndone in {(time.time()-st_['t0'])/60:.1f} min")
print(f"  answered direct echo : {len(got):,} of {len(targets):,}")
print(f"  silent to direct echo: {len(targets)-len(got):,}  "
      f"(these answer TTL-exceeded but not echo; their RTT stays unimproved)")
if got:
    print(f"  median of the per-address MINIMUM: {st.median([v['min'] for v in got]):.0f} ms")
    print(f"  median dispersion (p25 - min)    : {st.median([v['spread'] for v in got]):.0f} ms")
print(f"wrote {os.path.basename(OUT)}")
