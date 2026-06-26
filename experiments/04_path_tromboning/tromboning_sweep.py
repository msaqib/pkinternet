#!/usr/bin/env python3
"""
Exp 04 — Phase 1: tromboning sweep over an ISP's prefixes.
==========================================================
For each announced /24 of the target ISP (from enumerate_prefixes.py), launch a
TCP Paris traceroute (port 80, like the source `tcptraceroute` observation) from a
chosen probe, then flag any path that leaves Pakistan (a foreign hop) = tromboning.

Stack: ripe-atlas-cousteau (create/fetch), ripe-atlas-sagan (parse),
pk_multi_probe (Cymru + RDAP enrichment, incl. unannounced foreign-IXP hops).

    python experiments/04_path_tromboning/tromboning_sweep.py 38710
    python experiments/04_path_tromboning/tromboning_sweep.py 38710 --probe 1015679 --per-prefix 1

Output: results/run_<ts>/tromboning_<ts>.csv + routes_<ts>.txt + raw_<ts>.json
"""
import os, sys, csv, json, time, ipaddress
from datetime import datetime, timezone

from ripe.atlas.cousteau import Traceroute, AtlasSource, AtlasCreateRequest, AtlasResultsRequest
from ripe.atlas.sagan import TracerouteResult

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "scripts", "measurement"))
import pk_multi_probe as pk   # API_KEY (from .env), asn_for_ip, asn_name, registry_lookup, PRIVATE

HERE = os.path.dirname(__file__)
PROBE_DEFAULT = 1015679          # Nova (AS136174) — where tromboning was first seen
LDI = {"17557": "PTCL", "38193": "Transworld"}   # the two int'l gateways
LAUNCH_DELAY = 0.5               # polite spacing between create calls (s)
CONTROL_IP = "115.186.61.254"    # Dr. Saqib's observed tromboning IP (positive control)

# A hop can only truly be abroad if its RTT is physically plausible for abroad:
# PK -> Singapore ~60ms, -> Gulf ~30-50ms. Anything flagged "foreign" below this
# floor is a mis-geolocation or a known artifact (e.g. the Nova probe's Shaw CPE
# hop 70.70.x / AS6327, which CLAUDE.md documents is physically in Pakistan at
# ~1.5ms). The RTT gate + artifact list keep those from masking the real exit.
FOREIGN_RTT_FLOOR = 40.0
ARTIFACT_ASN = {"6327"}          # Shaw (Nova-probe CPE, physically in PK)
# RTT backstop: tromboning is provable from the RTT profile even when the foreign
# hop doesn't reply (it was a `*`) or its ASN/geo lookup fails. Domestic PK RTT
# tops out ~40ms; PK->Singapore ~60-90ms, ->Europe ~100-130ms.
JUMP_THRESH = 60.0   # a +60ms step between consecutive hops = an int'l leg
HIGH_RTT    = 70.0   # any hop RTT >=70ms means the packet left PK
LOCAL_CEIL  = 45.0   # a path whose max RTT stays under this never left PK


def hop_geo(ip):
    """(asn, name, country) — Cymru, then RDAP registry fallback for unannounced
    foreign-IXP hops (e.g. *.equinix.com that Cymru can't resolve)."""
    if not ip or pk.PRIVATE(ip):
        return ("", "RFC1918", "")
    asn, _p, cc = pk.asn_for_ip(ip)
    if asn:
        return (asn, pk.asn_name(asn) or "?", cc)
    _p2, cc2, name = pk.registry_lookup(ip)
    return ("", name or "?", cc2)


def targets_for(asn, per_prefix, live=False):
    """Pick target IP(s) per /24. --live uses the responsiveness-sweep output
    (one confirmed-live IP per prefix); otherwise spread mid-block hosts."""
    if live:
        path = os.path.join(HERE, "results", f"live_AS{asn}.csv")
        if not os.path.exists(path):
            sys.exit(f"missing {path} — run responsiveness_sweep.py {asn} first")
        out = [(r["prefix"], r["live_ip"])
               for r in csv.DictReader(open(path, encoding="utf-8")) if r["live_ip"]]
        return out
    path = os.path.join(HERE, "results", f"targets_AS{asn}.csv")
    if not os.path.exists(path):
        sys.exit(f"missing {path} — run enumerate_prefixes.py {asn} first")
    out = []
    for r in csv.DictReader(open(path, encoding="utf-8")):
        net = ipaddress.ip_network(r["prefix"], strict=False)
        # spread per_prefix hosts across the block, avoiding .0/.255
        n = net.num_addresses
        offs = [max(1, n * k // (per_prefix + 1)) for k in range(1, per_prefix + 1)]
        for o in offs:
            out.append((r["prefix"], str(net.network_address + o)))
    return out


def main():
    args = sys.argv[1:]
    if not args or not args[0].lstrip("AS").isdigit():
        sys.exit("usage: tromboning_sweep.py <ASN> [--probe ID] [--per-prefix N]")
    asn = args[0].lstrip("AS")
    probe = int(args[args.index("--probe") + 1]) if "--probe" in args else PROBE_DEFAULT
    per_prefix = int(args[args.index("--per-prefix") + 1]) if "--per-prefix" in args else 1
    if not pk.API_KEY or pk.API_KEY == "your-api-key-here":
        sys.exit("RIPE_API_KEY not loaded from .env")

    # --reparse <run_dir>: rebuild CSV/routes from saved raw_*.json, no new measurements
    if "--reparse" in args:
        run_dir = args[args.index("--reparse") + 1]
        rawf = next(f for f in os.listdir(run_dir) if f.startswith("raw_"))
        raw_in = json.load(open(os.path.join(run_dir, rawf), encoding="utf-8"))
        ts = rawf[len("raw_"):-len(".json")]
        jobs, results = [], {}
        for k, v in raw_in.items():
            prefix, ip, mid = k.rsplit(":", 2); mid = int(mid)
            jobs.append((prefix, ip, mid)); results[mid] = v
        print(f"Re-parsing {len(jobs)} saved traceroutes from {run_dir}")
        write_outputs(jobs, results, asn, probe, run_dir, ts)
        return

    targets = targets_for(asn, per_prefix, live="--live" in args)
    targets.append(("control", CONTROL_IP))
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(HERE, "results", f"run_{ts}")
    os.makedirs(run_dir, exist_ok=True)

    print(f"AS{asn}: {len(targets)} targets, TCP/80 Paris traceroute from probe {probe}")
    src = AtlasSource(type="probes", value=str(probe), requested=1)
    jobs = []   # (prefix, ip, msm_id)
    for prefix, ip in targets:
        tr = Traceroute(af=4, target=ip, protocol="TCP", port=80, paris=16,
                        packets=3, description=f"exp04 tromboning AS{asn} {prefix}")
        try:
            ok, resp = AtlasCreateRequest(key=pk.API_KEY, measurements=[tr],
                                          sources=[src], is_oneoff=True).create()
            if ok:
                mid = resp["measurements"][0]; jobs.append((prefix, ip, mid))
                print(f"  {prefix:20} {ip:16} #{mid}")
            else:
                print(f"  {prefix:20} {ip:16} FAILED: {str(resp)[:90]}")
        except Exception as e:
            print(f"  {prefix:20} {ip:16} ERROR: {str(e)[:90]}")
        time.sleep(LAUNCH_DELAY)

    # ---- poll for results ----
    print(f"\nPolling {len(jobs)} measurements...", end="", flush=True)
    pending = {mid for _, _, mid in jobs}
    results = {}
    deadline = time.time() + 420
    while pending and time.time() < deadline:
        time.sleep(12); print(".", end="", flush=True)
        for mid in list(pending):
            ok, res = AtlasResultsRequest(msm_id=mid).create()
            if ok and res:
                results[mid] = res; pending.discard(mid)
    print(f" done ({len(results)}/{len(jobs)} returned)")

    write_outputs(jobs, results, asn, probe, run_dir, ts)


def write_outputs(jobs, results, asn, probe, run_dir, ts):
    # ---- parse + tag + write ----
    raw = {}
    rows = []
    lines = [f"Exp 04 path-tromboning sweep — AS{asn} from probe {probe}",
             f"TCP/80 Paris traceroute, {len(jobs)} prefixes. trombrne = a hop outside PK.",
             ""]
    for prefix, ip, mid in jobs:
        res = results.get(mid)
        if not res:
            rows.append(dict(prefix=prefix, target_ip=ip, reached="", trombones="",
                             note="no result", measurement_id=mid))
            continue
        raw[f"{prefix}:{ip}:{mid}"] = res
        pr = TracerouteResult.get(res[0])
        # walk hops, enrich, find first foreign hop + track the RTT profile
        exit_hop = exit_ip = exit_name = exit_cc = transit_asn = transit_name = ""
        hop_lines = []
        prev_pk_asn = prev_pk_name = ""
        reached_isp = False
        max_rtt = 0.0; prev_rtt = None; max_jump = 0.0; jump_asn = jump_name = ""
        dest_rtt = pr.last_median_rtt
        for hop in pr.hops:
            ip_h = next((p.origin for p in hop.packets if p.origin), None)
            rtt_h = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
            if not ip_h:
                hop_lines.append(f"  {hop.index:>3}      *     (no response)"); continue
            a, name, cc = hop_geo(ip_h)
            asn_s = f"AS{a}" if a else "-"
            if a == asn:
                reached_isp = True
            # RTT profile (all real RTTs are evidence; the artifact hop is low so harmless)
            if rtt_h is not None:
                max_rtt = max(max_rtt, rtt_h)
                if prev_rtt is not None and rtt_h - prev_rtt > max_jump:
                    max_jump = rtt_h - prev_rtt; jump_asn, jump_name = prev_pk_asn, prev_pk_name
                prev_rtt = rtt_h
            # truly-foreign requires a plausible foreign RTT (speed-of-light gate)
            # and excludes the documented in-PK artifact ASNs.
            foreign = (cc not in ("PK", "") and not pk.PRIVATE(ip_h)
                       and a not in ARTIFACT_ASN
                       and rtt_h is not None and rtt_h >= FOREIGN_RTT_FLOOR)
            mark = ""
            if foreign and not exit_hop:
                exit_hop, exit_ip, exit_name, exit_cc = hop.index, ip_h, name, cc
                transit_asn, transit_name = prev_pk_asn, prev_pk_name
                mark = "  <<< LEAVES PK"
            # track last in-PK (or low-RTT, i.e. physically-PK) hop with an ASN
            if a and a not in ARTIFACT_ASN and (cc == "PK" or
                    (rtt_h is not None and rtt_h < FOREIGN_RTT_FLOOR)):
                prev_pk_asn, prev_pk_name = a, name
            hop_lines.append(f"  {hop.index:>3}   {('%.1f'%rtt_h) if rtt_h is not None else '   ':>7}"
                             f"   {ip_h:<16} {asn_s:<9} {name[:30]}{(' ('+cc+')') if cc else ''}{mark}")

        # ---- verdict ----
        evidence = ""
        if exit_hop:
            evidence = "foreign_hop"
        elif max_jump >= JUMP_THRESH or max_rtt >= HIGH_RTT:
            # RTT backstop: left PK even though the foreign hop is invisible/unresolved
            exit_name = "(foreign hop not visible — RTT evidence)"
            exit_cc = "?"; transit_asn, transit_name = jump_asn, jump_name
            evidence = f"rtt_jump={max_jump:.0f} max_rtt={max_rtt:.0f}"
        trombones = bool(exit_hop) or evidence.startswith("rtt")
        status = ("trombone" if trombones else
                  "local" if (reached_isp or (max_rtt and max_rtt < LOCAL_CEIL))
                  else "inconclusive")
        rows.append(dict(prefix=prefix, target_ip=ip,
                         reached=pr.destination_ip_responded, trombones=trombones,
                         status=status, evidence=evidence,
                         exit_hop=exit_hop, exit_ip=exit_ip, exit_name=exit_name[:40],
                         exit_country=exit_cc, transit_asn=transit_asn,
                         transit_name=(LDI.get(transit_asn) or transit_name[:24]),
                         max_rtt_ms=round(max_rtt, 1) if max_rtt else "",
                         dest_rtt_ms=round(dest_rtt, 1) if dest_rtt else "",
                         n_hops=len(pr.hops), note="", measurement_id=mid))
        # routes block
        lines.append("=" * 78)
        flag = f"TROMBONES via {exit_name[:24]} ({exit_cc})" if trombones else "stays in PK"
        lines.append(f" {prefix}  ->  {ip}   [{flag}]")
        lines.append(f" reached={pr.destination_ip_responded}  dest_rtt={dest_rtt}  msm={mid}")
        lines.append("-" * 78)
        lines.append("  hop   rtt(ms)   ip                 asn       operator (country)")
        lines += hop_lines
        lines.append("")

    # write outputs
    cols = ["prefix", "target_ip", "reached", "trombones", "status", "evidence",
            "exit_hop", "exit_ip", "exit_name", "exit_country", "transit_asn",
            "transit_name", "max_rtt_ms", "dest_rtt_ms", "n_hops", "note",
            "measurement_id"]
    csv_path = os.path.join(run_dir, f"tromboning_{ts}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    with open(os.path.join(run_dir, f"routes_{ts}.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    json.dump(raw, open(os.path.join(run_dir, f"raw_{ts}.json"), "w", encoding="utf-8"))

    # summary
    got = [r for r in rows if r["trombones"] != ""]
    tr = [r for r in got if r["trombones"]]
    loc = [r for r in got if r.get("status") == "local"]
    inc = [r for r in got if r.get("status") == "inconclusive"]
    print(f"\n=== AS{asn} sweep summary ===")
    if got:
        n = len(got)
        print(f"  {n} traceroutes with data:")
        print(f"    trombone abroad : {len(tr):>2}  ({100*len(tr)/n:.0f}%)")
        print(f"    stayed local    : {len(loc):>2}  ({100*len(loc)/n:.0f}%)  (reached AS{asn}, or never exceeded ~{LOCAL_CEIL:.0f}ms)")
        print(f"    inconclusive    : {len(inc):>2}  ({100*len(inc)/n:.0f}%)  (no foreign hop, but RTT signal ambiguous)")
    exits = {}
    for r in tr:
        k = f"{r['exit_name']} ({r['exit_country']})"; exits[k] = exits.get(k, 0) + 1
    for k, count in sorted(exits.items(), key=lambda x: -x[1]):
        print(f"    exit via {k}: {count}")
    transits = {}
    for r in tr:
        k = r["transit_name"] or "?"; transits[k] = transits.get(k, 0) + 1
    if transits:
        print("  handed off abroad by: " + ", ".join(f"{k}×{v}" for k, v in transits.items()))
    print(f"  wrote {csv_path}")


if __name__ == "__main__":
    main()
