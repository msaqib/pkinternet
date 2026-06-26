#!/usr/bin/env python3
"""
Exp 04 helper: TCP/80 Paris traceroute to one target from several named probes,
with the same tromboning verdict logic as tromboning_sweep.py. For RQ4 — does a
prefix trombone from every vantage, or only via a particular transit?

    python experiments/04_path_tromboning/trace_from_probes.py 115.186.61.254 62224 1016126
"""
import os, sys, time
from ripe.atlas.cousteau import Traceroute, AtlasSource, AtlasCreateRequest, AtlasResultsRequest
from ripe.atlas.sagan import TracerouteResult

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "scripts", "measurement"))
import pk_multi_probe as pk
from tromboning_sweep import (hop_geo, FOREIGN_RTT_FLOOR, ARTIFACT_ASN,
                              JUMP_THRESH, HIGH_RTT)

LABELS = {62224: "transworld.lhe (AS38193)", 7764: "ptcl.lhe (AS17557)",
          1016126: "ptcl.khi (AS17557)", 1015679: "nova.lhe (AS136174)",
          60223: "nayatel.isb (AS23674)", 7613: "zcom.lhe (AS152605)"}


def main():
    target = sys.argv[1]
    probes = [int(x) for x in sys.argv[2:]]
    if not pk.API_KEY or pk.API_KEY == "your-api-key-here":
        sys.exit("RIPE_API_KEY not loaded from .env")

    jobs = []
    for pid in probes:
        tr = Traceroute(af=4, target=target, protocol="TCP", port=80, paris=16,
                        packets=3, description=f"exp04 rq4 {pid} to {target}")
        ok, resp = AtlasCreateRequest(key=pk.API_KEY, measurements=[tr],
                                      sources=[AtlasSource(type="probes", value=str(pid),
                                                           requested=1)],
                                      is_oneoff=True).create()
        if ok:
            jobs.append((pid, resp["measurements"][0]))
            print(f"  {LABELS.get(pid, pid)}  #{resp['measurements'][0]}")
        time.sleep(1)

    pending = {m for _, m in jobs}; results = {}; deadline = time.time() + 300
    print("polling...", end="", flush=True)
    while pending and time.time() < deadline:
        time.sleep(10); print(".", end="", flush=True)
        for _, m in list(jobs):
            if m in pending:
                ok, res = AtlasResultsRequest(msm_id=m).create()
                if ok and res:
                    results[m] = res; pending.discard(m)
    print()

    for pid, mid in jobs:
        res = results.get(mid)
        print("\n" + "=" * 74)
        print(f" {LABELS.get(pid, pid)}  ->  {target}   (msm {mid})")
        if not res:
            print("   no result"); continue
        pr = TracerouteResult.get(res[0])
        exit_cc = ""; max_rtt = 0.0; prev_rtt = None; max_jump = 0.0; transit = ""
        prev_pk = ""
        print("-" * 74)
        for hop in pr.hops:
            ip = next((p.origin for p in hop.packets if p.origin), None)
            rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
            if not ip:
                print(f"  {hop.index:>3}      *"); continue
            a, name, cc = hop_geo(ip)
            if rtt is not None:
                max_rtt = max(max_rtt, rtt)
                if prev_rtt is not None and rtt - prev_rtt > max_jump:
                    max_jump = rtt - prev_rtt; transit = prev_pk
                prev_rtt = rtt
            foreign = (cc not in ("PK", "") and not pk.PRIVATE(ip) and a not in ARTIFACT_ASN
                       and rtt is not None and rtt >= FOREIGN_RTT_FLOOR)
            mark = "  <<< LEAVES PK" if foreign and not exit_cc else ""
            if foreign and not exit_cc:
                exit_cc = cc; transit = prev_pk
            if a and a not in ARTIFACT_ASN and (cc == "PK" or (rtt is not None and rtt < FOREIGN_RTT_FLOOR)):
                prev_pk = pk.asn_name(a).split(" ")[0] if a else prev_pk
            print(f"  {hop.index:>3}  {('%.1f'%rtt) if rtt is not None else ' ':>7}  "
                  f"{ip:<16} {('AS'+a) if a else '-':<9} {name[:28]}{(' ('+cc+')') if cc else ''}{mark}")
        trombone = bool(exit_cc) or max_jump >= JUMP_THRESH or max_rtt >= HIGH_RTT
        verdict = (f"TROMBONES (exit {exit_cc or '?'}, max {max_rtt:.0f}ms, "
                   f"jump {max_jump:.0f}ms, via {transit})" if trombone
                   else f"LOCAL (max {max_rtt:.0f}ms)")
        print(f"  => {verdict}")


if __name__ == "__main__":
    main()
