#!/usr/bin/env python3
"""
Exp 4.1 — Phase 1-3: complete small-ISP tromboning census.
==========================================================
For every announced block (from enumerate_small_isps.py), TCP/80 Paris-traceroute
K spread IPs per block from each source probe; classify each with the Exp 04
RTT-physics detector; aggregate into per-ISP rates + a source x destination matrix,
carrying per-block live-host density (for the Q2 population weighting).

Reuses cousteau (create/fetch), sagan (parse), and the Exp 04 detector helpers.

    # pilot a few ISPs first (cheap), then the full run:
    python experiments/04.1_small_isp_tromboning/census_sweep.py --asns 151648,150387,152684
    python experiments/04.1_small_isp_tromboning/census_sweep.py            # full: all 747 blocks
    python experiments/04.1_small_isp_tromboning/census_sweep.py --ips 8 --sources 1016126,60223
"""
import os, sys, csv, json, time, ipaddress, argparse, glob
from datetime import datetime, timezone
from collections import defaultdict
import requests
from ripe.atlas.sagan import TracerouteResult

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "measurement"))
sys.path.insert(0, os.path.join(HERE, "..", "04_path_tromboning"))
import pk_multi_probe as pk
from tromboning_sweep import (hop_geo, FOREIGN_RTT_FLOOR, ARTIFACT_ASN,
                              JUMP_THRESH, HIGH_RTT, LOCAL_CEIL)

OUT = os.path.join(HERE, "results")
LDI = {"17557": "PTCL", "38193": "Transworld"}
QUEUE_CEIL = 500.0          # RTT above this = queuing / ICMP-gen artifact, not distance
MAX_INFLIGHT = 95           # under RIPE's 100-concurrent one-off cap
LAUNCH_DELAY = 0.4

# 7 path-visible connected probes (see notes.md). label: isp.city
SOURCES = {
    1016126: "ptcl.khi", 1015679: "nova.lhe", 7613: "zcom.lhe",
    1016036: "cybernet.hrp", 1016154: "cybernet.khi",
    60223: "nayatel.isb", 64535: "orbit.fsd",
}


def block_ips(prefix, k):
    net = ipaddress.ip_network(prefix, strict=False)
    n = net.num_addresses
    if n <= k + 2:
        offs = list(range(1, n - 1))
    else:
        offs = [max(1, n * i // (k + 1)) for i in range(1, k + 1)]
    return [str(net.network_address + o) for o in offs]


def classify(res, isp_asn):
    """Exp 04 RTT-physics detector -> dict(status, evidence, exit_cc, exit_name,
    transit, max_rtt, reached_isp)."""
    pr = TracerouteResult.get(res)
    exit_cc = exit_name = transit = ""
    max_rtt = 0.0; prev = None; max_jump = 0.0; prev_pk = ""; reached = False
    for hop in pr.hops:
        ip = next((p.origin for p in hop.packets if p.origin), None)
        rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
        if not ip:
            continue
        a, name, cc = hop_geo(ip)
        if a == isp_asn:
            reached = True
        if rtt is not None and rtt <= QUEUE_CEIL:      # ignore queuing spikes
            max_rtt = max(max_rtt, rtt)
            if prev is not None and rtt - prev > max_jump:
                max_jump = rtt - prev; transit = prev_pk
            prev = rtt
        elif rtt is not None and prev is None:
            prev = min(rtt, QUEUE_CEIL)
        foreign = (cc not in ("PK", "") and not pk.PRIVATE(ip) and a not in ARTIFACT_ASN
                   and rtt is not None and FOREIGN_RTT_FLOOR <= rtt <= QUEUE_CEIL)
        if foreign and not exit_cc:
            exit_cc, exit_name, transit = cc, name[:24], prev_pk
        if a and a not in ARTIFACT_ASN and (cc == "PK" or (rtt is not None and rtt < FOREIGN_RTT_FLOOR)):
            prev_pk = LDI.get(a, a)
    if exit_cc:
        ev = "foreign_hop"; trombone = True
    elif max_jump >= JUMP_THRESH or max_rtt >= HIGH_RTT:
        ev = f"rtt(jump={max_jump:.0f},max={max_rtt:.0f})"; trombone = True; exit_cc = "?"
    else:
        ev = ""; trombone = False
    status = ("trombone" if trombone else
              "local" if (reached or (max_rtt and max_rtt < LOCAL_CEIL)) else "inconclusive")
    return dict(status=status, evidence=ev, exit_cc=exit_cc, exit_name=exit_name,
                transit=transit or "?", max_rtt=round(max_rtt, 1) if max_rtt else "",
                reached_isp=reached)


def create_one(ip, asn, prefix, srcval, nsrc):
    """One multi-probe one-off TCP/80 Paris traceroute. Direct requests (TIMED, so a
    hung call can't freeze the run, unlike cousteau's un-timed fetch)."""
    payload = {"definitions": [{"target": ip, "description": f"exp41 AS{asn} {prefix}"[:80],
               "type": "traceroute", "af": 4, "protocol": "TCP", "port": 80, "paris": 16,
               "first_hop": 1, "max_hops": 32, "packets": 3, "size": 48}],
               "probes": [{"type": "probes", "value": srcval, "requested": nsrc}],
               "is_oneoff": True}
    r = requests.post(f"{pk.BASE}/measurements/", headers=pk.HDR, json=payload, timeout=25)
    r.raise_for_status()
    return r.json()["measurements"][0]


def fetch_one(mid):
    try:
        r = requests.get(f"{pk.BASE}/measurements/{mid}/results/", headers=pk.HDR, timeout=25)
        return r.json() if r.ok else []
    except Exception:
        return []


def launch_poll(jobs_spec, sources, run_dir, ts, seed_raw):
    """One multi-probe measurement per IP, batched under the cap. Resumable: starts
    from seed_raw and checkpoints the merged raw after every batch. All HTTP is timed,
    so no single call can freeze the loop."""
    raw = dict(seed_raw)
    srcval = ",".join(str(s) for s in sources); nsrc = len(sources)
    n = len(jobs_spec); nb = (n + MAX_INFLIGHT - 1) // MAX_INFLIGHT
    raw_path = os.path.join(run_dir, f"raw_{ts}.json")
    for i in range(0, n, MAX_INFLIGHT):
        batch = jobs_spec[i:i + MAX_INFLIGHT]
        print(f"  batch {i//MAX_INFLIGHT+1}/{nb}: launching {len(batch)}...", flush=True)
        live = set()
        for asn, comp, prefix, ip in batch:
            try:
                live.add(create_one(ip, asn, prefix, srcval, nsrc))
            except Exception as e:
                print(f"    ! create {ip}: {str(e)[:60]}")
            time.sleep(LAUNCH_DELAY)
        pend = set(live); deadline = time.time() + 300
        while pend and time.time() < deadline:
            time.sleep(15)
            for mid in list(pend):
                res = fetch_one(mid)
                if res and len(res) >= nsrc:                    # all probes reported
                    raw[str(mid)] = res; pend.discard(mid)
        for mid in list(pend):                                  # deadline: take partials
            res = fetch_one(mid)
            if res:
                raw[str(mid)] = res
        json.dump(raw, open(raw_path, "w", encoding="utf-8"))   # checkpoint
        print(f"    checkpoint: {len(raw)} measurements", flush=True)
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asns", help="comma list of ASNs to limit to (pilot)")
    ap.add_argument("--ips", type=int, default=8)
    ap.add_argument("--sources", help="comma list of probe ids (default the 7)")
    ap.add_argument("--resume", help="path to a run dir; skip IPs already in its raw")
    args = ap.parse_args()
    if not pk.API_KEY or pk.API_KEY == "your-api-key-here":
        sys.exit("RIPE_API_KEY not loaded from .env")

    sources = ([int(x) for x in args.sources.split(",")] if args.sources else list(SOURCES))
    only = set(args.asns.split(",")) if args.asns else None

    blocks = [r for r in csv.DictReader(open(os.path.join(OUT, "blocks_all.csv"), encoding="utf-8"))
              if (only is None or r["asn"] in only)]
    if not blocks:
        sys.exit("no blocks (run enumerate_small_isps.py, or check --asns)")

    # resume from an existing run dir (skip IPs already measured), or start fresh
    if args.resume:
        run_dir = args.resume
        rfs = sorted(glob.glob(os.path.join(run_dir, "raw_*.json")))
        seed_raw = json.load(open(rfs[-1], encoding="utf-8")) if rfs else {}
        ts = os.path.basename(rfs[-1])[len("raw_"):-len(".json")] if rfs else \
            datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        done_ips = {r.get("dst_addr") for res in seed_raw.values() for r in res if r.get("dst_addr")}
        print(f"  RESUME {run_dir}: {len(seed_raw)} measurements done, {len(done_ips)} IPs covered")
    else:
        seed_raw = {}; done_ips = set()
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(OUT, f"run_{ts}"); os.makedirs(run_dir, exist_ok=True)

    ip2blk = {}
    jobs = []
    for b in blocks:
        for ip in block_ips(b["prefix"], args.ips):
            ip2blk[ip] = (b["asn"], b["company"], b["prefix"])
            if ip not in done_ips:
                jobs.append((b["asn"], b["company"], b["prefix"], ip))
    print(f"Exp 4.1 census: {len(blocks)} blocks x {args.ips} IPs, {len(jobs)} measurements "
          f"remaining x {len(sources)} probes (~{len(jobs)*len(sources)*20:,} credits)")

    raw = launch_poll(jobs, sources, run_dir, ts, seed_raw)

    # build per-(probe, block, ip) results from the full merged raw
    results = {}
    for res in raw.values():
        for r in res:
            ip = r.get("dst_addr")
            if ip in ip2blk:
                _, _, prefix = ip2blk[ip]
                results[(r.get("prb_id"), prefix, ip)] = r

    # classify
    bmeta = {b["prefix"]: b for b in blocks}
    rows = []
    for (pid, prefix, ip), res in results.items():
        try:
            v = classify(res, bmeta[prefix]["asn"])
        except Exception:
            continue
        rows.append(dict(source=SOURCES.get(pid, pid), source_id=pid,
                         asn=bmeta[prefix]["asn"], company=bmeta[prefix]["company"],
                         prefix=prefix, target_ip=ip, **v))
    cols = ["source", "source_id", "asn", "company", "prefix", "target_ip",
            "status", "evidence", "exit_cc", "exit_name", "transit", "max_rtt", "reached_isp"]
    with open(os.path.join(run_dir, f"census_{ts}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow({c: r.get(c, "") for c in cols})
    json.dump(raw, open(os.path.join(run_dir, f"raw_{ts}.json"), "w", encoding="utf-8"))

    # ---- aggregates ----
    # per-block density + per-block consistency (within source, do all IPs agree?)
    by_block = defaultdict(lambda: defaultdict(list))   # (asn,prefix)->source->[status]
    for r in rows:
        by_block[(r["asn"], r["prefix"])][r["source"]].append(r["status"])
    # per-ISP trombone rate (block trombones from a source if ANY ip trombones)
    isp = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # asn->source->[tromb_blocks, total_blocks]
    consistency = [0, 0]   # [consistent_blocks, total_block-source pairs with >1 ip]
    for (asn, prefix), srcs in by_block.items():
        for s, statuses in srcs.items():
            t = sum(1 for x in statuses if x == "trombone")
            isp[asn][s][1] += 1
            if t: isp[asn][s][0] += 1
            if len(statuses) > 1:
                consistency[1] += 1
                if len(set(statuses)) == 1: consistency[0] += 1

    with open(os.path.join(run_dir, "isp_tromboning.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["asn", "company", "source", "trombone_blocks", "total_blocks", "pct"])
        for asn in sorted(isp):
            comp = next(b["company"] for b in blocks if b["asn"] == asn)
            for s in sorted(isp[asn]):
                tb, tot = isp[asn][s]
                w.writerow([asn, comp, s, tb, tot, f"{100*tb/tot:.0f}" if tot else 0])

    # ---- summary ----
    print(f"\n=== Exp 4.1 census summary ({len(rows)} traceroutes w/ data) ===")
    st = defaultdict(int)
    for r in rows: st[r["status"]] += 1
    print("  per-traceroute:", dict(st))
    if consistency[1]:
        print(f"  intra-block consistency: {consistency[0]}/{consistency[1]} "
              f"({100*consistency[0]/consistency[1]:.0f}%) of (block,source) had all IPs agree")
    print("  per source: trombone blocks / total")
    persrc = defaultdict(lambda: [0, 0])
    for asn in isp:
        for s in isp[asn]:
            persrc[s][0] += isp[asn][s][0]; persrc[s][1] += isp[asn][s][1]
    for s in sorted(persrc):
        tb, tot = persrc[s]
        print(f"    {s:14} {tb:>4}/{tot:<4}  ({100*tb/tot:.0f}%)" if tot else f"    {s}: 0")
    print(f"  wrote {run_dir}/census_{ts}.csv + isp_tromboning.csv")


if __name__ == "__main__":
    main()
