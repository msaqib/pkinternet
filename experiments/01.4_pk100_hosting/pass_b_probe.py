#!/usr/bin/env python3
"""
Exp 1.4 — Pass B: ICMP Paris traceroute to the PK100 sites from ONE probe
(64078, Transworld/TES-PL, Rawalpindi), to get the RTT + serving location from a
real Pakistani vantage. Reads Pass A's resolved IPs.

    python experiments/01.4_pk100_hosting/pass_b_probe.py
Output: results/pass_b_probe.csv
"""
import os, sys, csv, json, time
from datetime import datetime, timezone
from ripe.atlas.cousteau import Traceroute, AtlasSource, AtlasCreateRequest, AtlasResultsRequest
from ripe.atlas.sagan import TracerouteResult
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "measurement"))
import pk_multi_probe as pk

PROBE = 64078                       # Transworld / TES-PL (AS135407), Rawalpindi
OUT = os.path.join(HERE, "results")
MAX_INFLIGHT = 90


def rtt_bucket(rtt):
    if rtt is None: return "no-reply"
    if rtt < 10:  return "same-city (<10ms)"
    if rtt < 50:  return "in-PK (<50ms)"
    if rtt < 100: return "regional (50-100ms)"
    if rtt < 150: return "abroad (100-150ms)"
    return "far (>150ms)"


def main():
    if not pk.API_KEY or pk.API_KEY == "your-api-key-here":
        sys.exit("RIPE_API_KEY not loaded")
    targets = [(r["domain"], r["ip"], r["category"], r["host"])
               for r in csv.DictReader(open(os.path.join(OUT, "pass_a_hosting.csv"), encoding="utf-8"))
               if r["ip"]]
    print(f"Pass B: {len(targets)} traceroutes from probe {PROBE} (Transworld)")

    jobs = {}   # mid -> (domain, ip, cat, host)
    src = AtlasSource(type="probes", value=str(PROBE), requested=1)
    for dom, ip, cat, host in targets:
        tr = Traceroute(af=4, target=ip, protocol="ICMP", paris=16, packets=3,
                        description=f"exp1.4 hosting {dom}"[:80])
        try:
            ok, resp = AtlasCreateRequest(key=pk.API_KEY, measurements=[tr], sources=[src], is_oneoff=True).create()
            if ok: jobs[resp["measurements"][0]] = (dom, ip, cat, host)
        except Exception as e:
            print(f"  ! {dom}: {str(e)[:60]}")
        time.sleep(0.3)

    print(f"  launched {len(jobs)}; polling...")
    pend = set(jobs); res = {}; deadline = time.time() + 420
    while pend and time.time() < deadline:
        time.sleep(15)
        for mid in list(pend):
            try:
                r = AtlasResultsRequest(msm_id=mid).create()
                if r[0] and r[1]:
                    res[mid] = r[1]; pend.discard(mid)
            except Exception:
                pass

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rows = []
    raw = {}
    routes = ["Exp 1.4 Pass B — traceroutes from probe 64078 (Transworld/TES-PL AS135407, Rawalpindi)",
              "PK100 hosting check. '<<< LEAVES PK' = a foreign hop (a PK-hosted site reached via a hairpin).", ""]
    for mid, (dom, ip, cat, host) in jobs.items():
        r = res.get(mid)
        if not r:
            rows.append(dict(domain=dom, ip=ip, category=cat, host=host, dest_rtt="",
                             bucket="no-result", reached="", last_hop="", last_asn="")); continue
        raw[str(mid)] = r
        pr = TracerouteResult.get(r[0])
        dest_rtt = pr.last_median_rtt
        last_ip = last_asn = ""
        routes.append("=" * 80)
        routes.append(f" {dom}   ({cat}: {host[:38]})   ->   {ip}")
        routes.append(f" SOURCE   probe 64078 - Transworld/TES-PL (AS135407), Rawalpindi")
        routes.append(f" DEST RTT {dest_rtt}ms   reached={pr.destination_ip_responded}")
        routes.append("-" * 80)
        routes.append("  hop   rtt(ms)   ip                 asn       operator (country)")
        for hop in pr.hops:
            hip = next((p.origin for p in hop.packets if p.origin), None)
            rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
            if not hip:
                routes.append(f"  {hop.index:>3}      *     (no response)"); continue
            if pk.PRIVATE(hip):
                a, name, cc = "", "RFC1918", ""
            else:
                a, _p, cc = pk.asn_for_ip(hip); name = pk.asn_name(a) if a else pk.registry_lookup(hip)[2]
                last_ip = hip; last_asn = ("AS" + a) if a else ""
            foreign = cc not in ("PK", "") and not pk.PRIVATE(hip) and rtt is not None and rtt >= 40 and a != "6327"
            routes.append(f"  {hop.index:>3}   {('%.1f'%rtt) if rtt is not None else '':>7}   {hip:<16} "
                          f"{('AS'+a) if a else '-':<9} {(name or '')[:28]}{(' ('+cc+')') if cc else ''}"
                          f"{'   <<< LEAVES PK' if foreign else ''}")
        routes.append("")
        rows.append(dict(domain=dom, ip=ip, category=cat, host=host,
                         dest_rtt=round(dest_rtt, 1) if dest_rtt else "",
                         bucket=rtt_bucket(dest_rtt), reached=pr.destination_ip_responded,
                         last_hop=last_ip, last_asn=last_asn))
        print(f"  {dom:26} {cat:9} rtt={str(rows[-1]['dest_rtt']):7} {rows[-1]['bucket']}")

    cols = ["domain", "ip", "category", "host", "dest_rtt", "bucket", "reached", "last_hop", "last_asn"]
    with open(os.path.join(OUT, "pass_b_probe.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    # ALWAYS emit the readable routes txt + raw for any traceroute run
    open(os.path.join(OUT, f"routes_pass_b_{ts}.txt"), "w", encoding="utf-8").write("\n".join(routes) + "\n")
    json.dump(raw, open(os.path.join(OUT, f"raw_pass_b_{ts}.json"), "w", encoding="utf-8"))

    import collections
    got = [r for r in rows if r["dest_rtt"] != ""]
    print(f"\n=== Pass B (from Transworld, {len(got)}/{len(rows)} reached) ===")
    for k, c in collections.Counter(r["bucket"] for r in rows).most_common():
        print(f"  {k:22} {c}")
    if got:
        import statistics
        print(f"  median dest RTT (PK-hosted): "
              f"{statistics.median([r['dest_rtt'] for r in got if r['category']=='Pakistan' and isinstance(r['dest_rtt'],(int,float))]):.0f} ms")
    print(f"  wrote {os.path.join(OUT,'pass_b_probe.csv')}")


if __name__ == "__main__":
    main()
