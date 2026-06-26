#!/usr/bin/env python3
"""
Exp 04 — Phase 1a: responsiveness sweep (find a live IP per /24).
================================================================
The tromboning sweep gave 62% "inconclusive" because a fixed .128 target is
usually not a live host, so the TCP traceroute went dark before reaching the ISP.
This is the TASS "scan once, then focus" step: ping a few candidate IPs per
announced /24 from the probe, keep the most responsive one, and write a refined
live-target list that `tromboning_sweep.py --live` then traceroutes.

ICMP ping is cheap; caveat: a host that drops ICMP but answers TCP/80 is missed,
so this is a *lower bound* on live hosts — good enough to complete most paths.

    python experiments/04_path_tromboning/responsiveness_sweep.py 38710
    python experiments/04_path_tromboning/responsiveness_sweep.py 38710 --probe 1015679

Output: results/live_AS<asn>.csv  (prefix, live_ip, rcvd, sent, min_rtt, note)
"""
import os, sys, csv, time, ipaddress
from ripe.atlas.cousteau import Ping, AtlasSource, AtlasCreateRequest, AtlasResultsRequest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "scripts", "measurement"))
import pk_multi_probe as pk

HERE = os.path.dirname(__file__)
PROBE_DEFAULT = 1015679
CAND_OFFSETS = [1, 85, 170, 254]   # spread candidates per /24
MAX_INFLIGHT = 90                  # stay under RIPE's 100 concurrent one-off cap
LAUNCH_DELAY = 0.35


def candidates(asn):
    path = os.path.join(HERE, "results", f"targets_AS{asn}.csv")
    if not os.path.exists(path):
        sys.exit(f"missing {path} — run enumerate_prefixes.py {asn} first")
    out = []   # (prefix, ip)
    for r in csv.DictReader(open(path, encoding="utf-8")):
        net = ipaddress.ip_network(r["prefix"], strict=False)
        for o in CAND_OFFSETS:
            if o < net.num_addresses - 1:
                out.append((r["prefix"], str(net.network_address + o)))
    return out


def ping_batch(probe, batch):
    """Launch a batch of one-off pings; return {ip: result_dict}."""
    src = AtlasSource(type="probes", value=str(probe), requested=1)
    ids = {}   # mid -> ip
    for prefix, ip in batch:
        p = Ping(af=4, target=ip, packets=3, description=f"exp04 sweep {ip}")
        try:
            ok, resp = AtlasCreateRequest(key=pk.API_KEY, measurements=[p],
                                          sources=[src], is_oneoff=True).create()
            if ok:
                ids[resp["measurements"][0]] = ip
        except Exception as e:
            print(f"    ! {ip} create failed: {str(e)[:80]}")
        time.sleep(LAUNCH_DELAY)
    # poll
    out, pending, deadline = {}, set(ids), time.time() + 240
    while pending and time.time() < deadline:
        time.sleep(10)
        for mid in list(pending):
            ok, res = AtlasResultsRequest(msm_id=mid).create()
            if ok and res:
                out[ids[mid]] = res[0]; pending.discard(mid)
    return out


def main():
    args = sys.argv[1:]
    if not args or not args[0].lstrip("AS").isdigit():
        sys.exit("usage: responsiveness_sweep.py <ASN> [--probe ID]")
    asn = args[0].lstrip("AS")
    probe = int(args[args.index("--probe") + 1]) if "--probe" in args else PROBE_DEFAULT
    if not pk.API_KEY or pk.API_KEY == "your-api-key-here":
        sys.exit("RIPE_API_KEY not loaded from .env")

    cands = candidates(asn)
    print(f"AS{asn}: pinging {len(cands)} candidates "
          f"({len(CAND_OFFSETS)}/prefix) from probe {probe}, batches of {MAX_INFLIGHT}")

    results = {}
    for i in range(0, len(cands), MAX_INFLIGHT):
        batch = cands[i:i + MAX_INFLIGHT]
        print(f"  batch {i//MAX_INFLIGHT + 1}: {len(batch)} pings...", flush=True)
        results.update(ping_batch(probe, batch))

    # pick best candidate per prefix: most packets received, then lowest min RTT
    best = {}   # prefix -> (ip, rcvd, sent, min_rtt)
    for prefix, ip in cands:
        r = results.get(ip)
        if not r:
            continue
        rcvd, sent = r.get("rcvd", 0), r.get("sent", 0)
        mn = r.get("min", -1)
        mn = mn if isinstance(mn, (int, float)) and mn >= 0 else 9999
        cur = best.get(prefix)
        if rcvd > 0 and (cur is None or (rcvd, -mn) > (cur[1], -cur[3])):
            best[prefix] = (ip, rcvd, sent, mn)

    # write live list (one row per prefix; empty live_ip if no responder)
    out = os.path.join(HERE, "results", f"live_AS{asn}.csv")
    all_prefixes = sorted({p for p, _ in cands},
                          key=lambda x: ipaddress.ip_network(x).network_address)
    live_n = 0
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["prefix", "live_ip", "rcvd", "sent", "min_rtt", "note"])
        for prefix in all_prefixes:
            if prefix in best:
                ip, rcvd, sent, mn = best[prefix]
                w.writerow([prefix, ip, rcvd, sent, mn, ""])
                live_n += 1
            else:
                w.writerow([prefix, "", 0, len(CAND_OFFSETS) * 3, "", "no ICMP responder"])
    print(f"\n=== AS{asn} responsiveness ===")
    print(f"  {live_n}/{len(all_prefixes)} prefixes have a live (ICMP) IP")
    print(f"  wrote {out}")
    print(f"  next: python {os.path.basename(__file__).replace('responsiveness_sweep','tromboning_sweep')} {asn} --live")


if __name__ == "__main__":
    main()
