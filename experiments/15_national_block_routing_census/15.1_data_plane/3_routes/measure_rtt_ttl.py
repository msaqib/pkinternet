#!/usr/bin/env python3
"""
Measure RTT for routers that answer TTL-exceeded but ignore direct pings.

WHY A SECOND TOOL
  measure_rtt.py pings each address directly. 76 of the 516 foreign addresses never
  answer an echo request, including `182.45.51.22`, which alone carries 37% of the
  tromboning count. Those routers are visible ONLY as TTL-exceeded replies inside a
  traceroute, so the only way to measure them is to reproduce the hop that found them:
  send repeated packets at the exact TTL, toward a target whose path crosses them.

METHOD
  For each unimproved address, take up to MAXPATHS (target, ttl) pairs from the
  selected traces where that address answered, then SEARCH a window of TTLs around
  the recorded one for the hop that actually answers from that address, and burst
  there.

  THE WINDOW IS NOT OPTIONAL. Hop numbers are relative to the measuring machine's own
  position, and ours moved: during the sweep the first hop was silent and the gateway
  sat at TTL 2, while today the gateway answers at TTL 1. Every recorded hop number is
  therefore one too high. A first version of this tool trusted the recorded TTL and
  measured 7 of 76 addresses, because it kept landing on the router one step further
  along. Searching for the address instead of trusting its index fixes that, and is
  robust to any future change in where the measuring machine sits.

  Reports the MINIMUM, for the same reason as measure_rtt.py: queuing and slow ICMP
  generation only add to a round trip, so the minimum of a clean burst is the closest
  approach to the physical path cost.

  Low concurrency on purpose. The inflation being corrected is our own contention.

  python measure_rtt_ttl.py [--packets 25] [--threads 6]
"""
import os, io, json, time, socket, struct, ctypes, argparse, threading, queue, collections, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--packets", type=int, default=25, help="probes per (target, ttl) pair")
ap.add_argument("--threads", type=int, default=6)
ap.add_argument("--maxpaths", type=int, default=3, help="distinct paths to try per address")
ap.add_argument("--window", type=int, default=3, help="TTLs to search either side of the recorded hop")
ap.add_argument("--timeout", type=int, default=1000)
ap.add_argument("--gap", type=float, default=0.05)
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--all", action="store_true",
                help="measure EVERY foreign address in-path, not only those that ignore echo")
A = ap.parse_args()
OUT = os.path.join(HERE, "rtt_foreign_ttl.json")   # set below if --all

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
DATA = b"exp15ttl"
BUFSZ = ctypes.sizeof(ICMP_ECHO_REPLY) + len(DATA) + 64

if A.all:
    OUT = os.path.join(HERE, "rtt_inpath.json")
ann = json.load(io.open(os.path.join(HERE, "selected_annotated.json"), encoding="utf-8"))
HOME = ("PK", "PRIV", "CGN", "??")

direct = {}
p = os.path.join(HERE, "rtt_foreign.json")
if os.path.exists(p):
    direct = json.load(io.open(p, encoding="utf-8"))

# where each foreign address was seen: (target, ttl)
seen = collections.defaultdict(list)
meta = {}
for r in ann:
    for i, h in enumerate(r["path"]):
        if h and h["cc"] not in HOME:
            seen[h["ip"]].append((r["target"], i + 1))
            meta[h["ip"]] = dict(cc=h["cc"], asn=h.get("asn"),
                                 holder=(h.get("holder") or "")[:40], kind=h.get("kind"))

# In-path is the only correct method: the RTT must come from a packet travelling
# toward the ORIGINAL destination, exactly as it did when the sweep saw this hop.
# Pinging a router directly measures a different thing: routers deprioritise packets
# addressed to themselves, and the route TO a router need not match the route THROUGH
# it. --all re-measures every foreign address this way so nothing rests on direct echo.
todo = list(seen) if A.all else [ip for ip in seen if not direct.get(ip, {}).get("n")]
if A.limit:
    todo = todo[:A.limit]
print(f"addresses needing TTL measurement: {len(todo)} "
      f"(of {len(seen)} foreign; the rest answered direct echo)")
print(f"{A.packets} probes x up to {A.maxpaths} paths each, {A.threads} threads\n")

res, lock, q = {}, threading.Lock(), queue.Queue()
for ip in todo:
    q.put(ip)
stt = dict(n=0, ok=0, t0=time.time())


def probe_at_ttl(handle, target, ttl, want, n, timeout, gap):
    """n probes toward target at this TTL. Keep only replies from `want`."""
    dst = struct.unpack("<I", socket.inet_aton(target))[0]
    hits, others = [], collections.Counter()
    for _ in range(n):
        buf = ctypes.create_string_buffer(BUFSZ)
        opt = IP_OPTION_INFORMATION(ttl, 0, 0, 0, None)
        if iph.IcmpSendEcho(handle, dst, DATA, len(DATA), ctypes.byref(opt),
                            buf, BUFSZ, timeout):
            r = ICMP_ECHO_REPLY.from_buffer_copy(buf)
            src = socket.inet_ntoa(struct.pack("<I", r.Address))
            if src == want:
                hits.append(int(r.RoundTripTime))
            else:
                others[src] += 1
        time.sleep(gap)
    return hits, others


def find_ttl(handle, target, want, ttl0, window, timeout, gap):
    """Which TTL currently reaches `want` on the way to `target`? Search outward from
    the recorded hop, nearest first, so the common one-hop drift is found immediately."""
    order = [ttl0]
    for d in range(1, window+1):
        order += [ttl0-d, ttl0+d]
    for ttl in order:
        if ttl < 1:
            continue
        hits, _ = probe_at_ttl(handle, target, ttl, want, 1, timeout, gap)
        if hits:
            return ttl
    return None


def work():
    h = ctypes.c_void_p(iph.IcmpCreateFile())
    while True:
        try:
            ip = q.get_nowait()
        except queue.Empty:
            return
        allhits, drift, used, found_at = [], collections.Counter(), 0, None
        for target, ttl in seen[ip][:A.maxpaths]:
            real = find_ttl(h, target, ip, ttl, A.window, A.timeout, A.gap)
            used += 1
            if real is None:
                continue
            found_at = dict(target=target, recorded_ttl=ttl, actual_ttl=real)
            hits, others = probe_at_ttl(h, target, real, ip, A.packets, A.timeout, A.gap)
            allhits += hits
            drift += others
            if len(allhits) >= A.packets:
                break
        with lock:
            stt["n"] += 1
            if allhits:
                stt["ok"] += 1
                s = sorted(allhits)
                res[ip] = dict(n=len(s), paths=used, min=s[0], p25=s[len(s)//4],
                               median=st.median(s), max=s[-1], spread=s[len(s)//4]-s[0],
                               drift=sum(drift.values()), at=found_at, **meta[ip])
            else:
                res[ip] = dict(n=0, paths=used, drift=sum(drift.values()),
                               drift_top=drift.most_common(2), **meta[ip])
            if stt["n"] % 10 == 0:
                el = time.time()-stt["t0"]
                print(f"  {stt['n']}/{len(todo)}  {stt['ok']} measured  "
                      f"eta {(len(todo)-stt['n'])/max(stt['n']/max(el,1),.01)/60:.0f} min", flush=True)
                json.dump(res, io.open(OUT+".tmp", "w", encoding="utf-8"))
                os.replace(OUT+".tmp", OUT)


ths = [threading.Thread(target=work, daemon=True) for _ in range(A.threads)]
[t.start() for t in ths]
[t.join() for t in ths]
json.dump(res, io.open(OUT, "w", encoding="utf-8"))
got = [v for v in res.values() if v.get("n")]
print(f"\ndone in {(time.time()-stt['t0'])/60:.1f} min")
print(f"  measured : {len(got)} of {len(todo)}")
print(f"  no reply : {len(todo)-len(got)}  (path moved, or the router stopped answering)")
if got:
    print(f"  median dispersion p25-min: {st.median([v['spread'] for v in got]):.0f} ms")
print(f"wrote {os.path.basename(OUT)}")
