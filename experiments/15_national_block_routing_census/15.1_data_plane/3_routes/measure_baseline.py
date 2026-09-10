#!/usr/bin/env python3
"""
Measure this vantage's real domestic baseline, cleanly.

WHY  RULES.md derives a "domestic ceiling" of 34.2 ms as line-of-sight x 2.1 / c.
     That 2.1 is Bozkurt's rule of thumb for TYPICAL latency, not an upper bound.
     The same paper reports that only 11% of real fibre links have RTTs within 25%
     of what their cable length predicts, and that even servers in the SAME city
     often sit 10 to 30 ms apart. So 34.2 ms cannot be used as "anything above this
     left the country", and a baseline derived from geometry is the wrong tool.

     This measures the baseline instead: clean minimum RTT to Pakistani destinations
     the topological detector calls domestic. Self-calibrating, and it does not care
     whether Pakistan's real inflation is 2x or 4x.

     Destinations are pinged directly, which is correct HERE and only here: the
     destination is the endpoint of the path, so a direct echo measures the same
     thing the trace's final hop measures. Intermediate routers must never be
     measured this way (see measure_rtt_ttl.py).

  python measure_baseline.py [--n 400] [--packets 10] [--threads 8]
"""
import io, json, os, time, socket, struct, ctypes, random, argparse, threading, queue, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=400, help="destinations to sample")
ap.add_argument("--packets", type=int, default=10)
ap.add_argument("--threads", type=int, default=8)
ap.add_argument("--timeout", type=int, default=1000)
ap.add_argument("--gap", type=float, default=0.05)
ap.add_argument("--seed", type=int, default=7)
A = ap.parse_args()
OUT = os.path.join(HERE, "rtt_baseline_sample.json")

iph = ctypes.windll.iphlpapi
class OPT(ctypes.Structure):
    _fields_ = [("Ttl", ctypes.c_ubyte), ("Tos", ctypes.c_ubyte), ("Flags", ctypes.c_ubyte),
                ("OptionsSize", ctypes.c_ubyte), ("OptionsData", ctypes.c_void_p)]
class REP(ctypes.Structure):
    _fields_ = [("Address", ctypes.c_uint32), ("Status", ctypes.c_ulong),
                ("RoundTripTime", ctypes.c_ulong), ("DataSize", ctypes.c_ushort),
                ("Reserved", ctypes.c_ushort), ("Data", ctypes.c_void_p), ("Options", OPT)]
iph.IcmpCreateFile.restype = ctypes.c_void_p
iph.IcmpSendEcho.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_ushort,
                             ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong]
iph.IcmpSendEcho.restype = ctypes.c_ulong
DATA = b"exp15bas"
BUFSZ = ctypes.sizeof(REP) + len(DATA) + 64

ann = json.load(io.open(os.path.join(HERE, "selected_annotated.json"), encoding="utf-8"))
pool = [r["target"] for r in ann if r["reached"]]
random.seed(A.seed)
targets = random.sample(pool, min(A.n, len(pool)))
print(f"sampling {len(targets)} of {len(pool):,} reached destinations, "
      f"{A.packets} packets each, {A.threads} threads")

res, lock, q = {}, threading.Lock(), queue.Queue()
for t in targets:
    q.put(t)
n = [0]

def work():
    h = ctypes.c_void_p(iph.IcmpCreateFile())
    while True:
        try:
            ip = q.get_nowait()
        except queue.Empty:
            return
        dst = struct.unpack("<I", socket.inet_aton(ip))[0]
        v = []
        for _ in range(A.packets):
            buf = ctypes.create_string_buffer(BUFSZ)
            if iph.IcmpSendEcho(h, dst, DATA, len(DATA), None, buf, BUFSZ, A.timeout):
                r = REP.from_buffer_copy(buf)
                if r.Status == 0:
                    v.append(int(r.RoundTripTime))
            time.sleep(A.gap)
        with lock:
            n[0] += 1
            if v:
                s = sorted(v)
                res[ip] = dict(n=len(s), min=s[0], median=st.median(s), max=s[-1],
                               spread=s[len(s)//4]-s[0])
            if n[0] % 50 == 0:
                print(f"  {n[0]}/{len(targets)}  {len(res)} answered", flush=True)

ths = [threading.Thread(target=work, daemon=True) for _ in range(A.threads)]
[t.start() for t in ths]
[t.join() for t in ths]
json.dump(res, io.open(OUT, "w", encoding="utf-8"))
print(f"answered {len(res)} of {len(targets)}; wrote {os.path.basename(OUT)}")
