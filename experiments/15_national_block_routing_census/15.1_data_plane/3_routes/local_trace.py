#!/usr/bin/env python3
"""
15.1 Phase B2 - local route sweep over the live hosts from local_scan.py.

Windows filters inbound ICMP before it reaches raw sockets, so a hand-rolled raw
tracer receives nothing. `tracert` works but costs ~28s per target. This uses the
Windows IcmpSendEcho API that ping and tracert themselves use: a completed trace
takes ~0.3s, and silent hops cost ~1.2s each, capped by early-stop.

Emits, per target, the two numbers the final selection needs:
    reached   the last hop equals the target
    frac      share of TTLs that answered   (route completeness)

Windows cannot map hops with TCP: it does not surface the ICMP TTL-exceeded to a TCP
socket, and inbound ICMP never reaches a raw socket either (both verified). So the
path is always mapped with ICMP, and TCP is used only to confirm the destination.

That split is sound because the PATH is a property of routing, not of probe type. A
host that answers only TCP still has its route mapped to the last ICMP-speaking
router; only the final hop is missing, and `tcp_ok` supplies it. Three fields let the
selection weigh this:
    reached   ICMP echo came back from the target itself
    tcp_ok    a TCP connect or RST confirmed the target is up
    frac      share of TTLs that answered  (route completeness)

  python local_trace.py [--threads 120] [--maxttl 30] [--stop 5] [--limit N]
"""
import os,io,json,time,socket,struct,ctypes,random,argparse,threading,queue
HERE=os.path.dirname(os.path.abspath(__file__)); RES=HERE
ap=argparse.ArgumentParser()
ap.add_argument("--threads",type=int,default=120)
ap.add_argument("--maxttl",type=int,default=30)
ap.add_argument("--stop",type=int,default=5,help="give up after this many consecutive silent hops")
ap.add_argument("--timeout",type=int,default=1000)
ap.add_argument("--limit",type=int,default=0)
A=ap.parse_args()
OUT=os.path.join(RES,"local_routes.jsonl")

iph=ctypes.windll.iphlpapi
class IP_OPTION_INFORMATION(ctypes.Structure):
    _fields_=[("Ttl",ctypes.c_ubyte),("Tos",ctypes.c_ubyte),("Flags",ctypes.c_ubyte),
              ("OptionsSize",ctypes.c_ubyte),("OptionsData",ctypes.c_void_p)]
class ICMP_ECHO_REPLY(ctypes.Structure):
    _fields_=[("Address",ctypes.c_uint32),("Status",ctypes.c_ulong),("RoundTripTime",ctypes.c_ulong),
              ("DataSize",ctypes.c_ushort),("Reserved",ctypes.c_ushort),
              ("Data",ctypes.c_void_p),("Options",IP_OPTION_INFORMATION)]
iph.IcmpCreateFile.restype=ctypes.c_void_p
iph.IcmpCloseHandle.argtypes=[ctypes.c_void_p]
iph.IcmpSendEcho.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_ushort,
                           ctypes.POINTER(IP_OPTION_INFORMATION),ctypes.c_void_p,
                           ctypes.c_ulong,ctypes.c_ulong]
iph.IcmpSendEcho.restype=ctypes.c_ulong
DATA=b"exp15.1r"; BUFSZ=ctypes.sizeof(ICMP_ECHO_REPLY)+len(DATA)+64

def tcp_confirm(ip,ports,to=2.0):
    """A connect OR an RST both prove the host is up."""
    for p in ports:
        s=socket.socket(); s.settimeout(to)
        try:
            s.connect((ip,p)); return p
        except ConnectionRefusedError: return p
        except Exception: pass
        finally:
            try: s.close()
            except Exception: pass
    return None

def trace(handle,target,maxttl,stopafter,timeout):
    dst=struct.unpack("<I",socket.inet_aton(target))[0]
    hops=[]; silent=0
    for ttl in range(1,maxttl+1):
        buf=ctypes.create_string_buffer(BUFSZ)
        opt=IP_OPTION_INFORMATION(ttl,0,0,0,None)
        n=iph.IcmpSendEcho(handle,dst,DATA,len(DATA),ctypes.byref(opt),buf,BUFSZ,timeout)
        if n==0:
            hops.append(None); silent+=1
            if silent>=stopafter: break
            continue
        r=ICMP_ECHO_REPLY.from_buffer_copy(buf)
        addr=socket.inet_ntoa(struct.pack("<I",r.Address))
        hops.append([addr,int(r.RoundTripTime)]); silent=0
        if r.Status==0: break            # echo reply: destination reached
    while hops and hops[-1] is None: hops.pop()
    return hops

live=[]
for _f in ("local_scan.jsonl","pk_scan.jsonl","topup_scan.jsonl"):
    _p=os.path.join(HERE,"..","2_liveness",_f)
    if not os.path.exists(_p): continue
    for _l in io.open(_p,encoding="utf-8"):
        _d=json.loads(_l)
        if _d["m"]: live.append(_d)
done=set()
if os.path.exists(OUT):
    for l in io.open(OUT,encoding="utf-8"):
        try: done.add(json.loads(l)["t"])
        except Exception: pass
todo=[d for d in live if d["t"] not in done]
random.seed(20260909); random.shuffle(todo)
if A.limit: todo=todo[:A.limit]
print(f"live hosts {len(live):,}   traced {len(done):,}   to trace {len(todo):,}   threads {A.threads}")
if not todo: raise SystemExit("nothing to do")

q=queue.Queue(); [q.put(d) for d in todo]
lock=threading.Lock(); fh=io.open(OUT,"a",encoding="utf-8")
st=dict(n=0,reached=0,t0=time.time(),miss=0)
HALT=threading.Event()

def link_up():
    """Is the local link actually working? Checked before believing a run of failures."""
    for host in ("1.1.1.1","8.8.8.8"):
        s_=socket.socket(); s_.settimeout(3)
        try:
            s_.connect((host,53 if host=="8.8.8.8" else 80)); return True
        except Exception: pass
        finally:
            try: s_.close()
            except Exception: pass
    return False
def work():
    h=iph.IcmpCreateFile()
    while True:
        if HALT.is_set(): break
        try: d=q.get_nowait()
        except queue.Empty: break
        try:
            hops=trace(h,d["t"],A.maxttl,A.stop,A.timeout)
        except Exception as e:
            with lock:
                st["err"]=st.get("err",0)+1
                if st["err"]<=3: print(f"  trace error {d.get('t')}: {type(e).__name__}",flush=True)
            continue
        ans=sum(1 for x in hops if x)
        reached=bool(hops) and hops[-1] is not None and hops[-1][0]==d["t"]
        # confirm the destination over TCP when ICMP did not reach it and the
        # liveness scan had found it on a TCP port
        tcp_ok=None
        if not reached:
            ports=[p for p,f in ((80,"t80"),(443,"t443")) if f in d["m"]] or [80,443]
            tcp_ok=tcp_confirm(d["t"],ports)
        with lock:
            fh.write(json.dumps({"t":d["t"],"p":d["p"],"a":d.get("a"),"m":d["m"],"v":d.get("v"),
                                 "reached":reached,"tcp_ok":tcp_ok,"ttls":len(hops),"answered":ans,
                                 "frac":round(ans/len(hops),3) if hops else 0,
                                 "h":hops},separators=(",",":"))+"\n")
            st["n"]+=1; st["reached"]+=reached
            # a long run of unreached targets usually means OUR link died, not that
            # 300 hosts vanished. Verify before writing thousands of false verdicts.
            st["miss"] = 0 if reached else st["miss"]+1
            if st["miss"]>=150:
                if not link_up():
                    print("  !! LINK DOWN - halting. Re-run when connectivity returns. "
                          "results so far are kept and will not be re-traced.",flush=True)
                    HALT.set()
                else:
                    st["miss"]=0
            if st["n"]%200==0:
                fh.flush(); el=time.time()-st["t0"]; r=st["n"]/max(el,1)
                print(f"  {st['n']:,}/{len(todo):,}  reached {st['reached']:,} "
                      f"({100*st['reached']/st['n']:.0f}%)  {r:.1f}/s  "
                      f"eta {(len(todo)-st['n'])/max(r,.01)/60:.0f} min",flush=True)
    iph.IcmpCloseHandle(h)
ths=[threading.Thread(target=work,daemon=True) for _ in range(A.threads)]
[t.start() for t in ths]; [t.join() for t in ths]
fh.flush(); fh.close()
el=time.time()-st["t0"]
print(f"\ndone: {st['n']:,} traced, {st['reached']:,} reached ({100*st['reached']/max(st['n'],1):.0f}%), {el/60:.1f} min")
