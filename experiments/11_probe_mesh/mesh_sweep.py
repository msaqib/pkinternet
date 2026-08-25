#!/usr/bin/env python3
"""
Exp 11 -- probe-to-probe mesh.
===============================
Every currently-connected PK probe traceroutes + pings every OTHER connected PK
probe (all directed pairs, N*(N-1)). Answers RQ2 directly with real inter-ISP
measurements instead of inferring peering quality from website hairpinning, and
because both directions of every pair are measured, it also surfaces routing
asymmetry the same way the Shaw/Nova artifact and PTCL<->Transworld findings did.

RIPE Atlas has no "probe X -> probe Y" target type -- a measurement always
targets an IP/hostname. So each probe's own public address_v4 (from the public
/api/v2/probes/ endpoint, no API key/login required) is used as the
traceroute/ping destination, sourced from every OTHER probe.

Live status + address_v4 are fetched fresh every run (never hardcoded --
probe IPs can rotate, e.g. Nayatel's CGNAT gateway). Only probes currently
"Connected" with a usable public IPv4 are included. As of 2026-08-24 that's
13 of the 19 known-roster probes (see CLAUDE.md probe tables) -- run with
--list to see the live set before spending credits.

    python experiments/11_probe_mesh/mesh_sweep.py --list       # just show who's in
    python experiments/11_probe_mesh/mesh_sweep.py               # launch + poll + parse
    python experiments/11_probe_mesh/mesh_sweep.py --reparse results/run_TS

Output: results/run_<ts>/mesh_<ts>.csv + routes_<ts>.txt + raw_<ts>.json

Quota note: each destination probe receives N-1 inbound traceroutes + N-1
inbound pings. RIPE caps one-off measurements at 25 per target -- with 13
probes that's 12 inbound of each type, safely under the cap. Re-check this
guard if the connected roster grows past ~26.
"""
import os, sys, csv, json, time
from datetime import datetime, timezone

import requests
from ripe.atlas.cousteau import (Traceroute, Ping, AtlasSource,
                                  AtlasCreateRequest, AtlasResultsRequest)
from ripe.atlas.sagan import TracerouteResult, PingResult

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "scripts", "measurement"))
import pk_multi_probe as pk   # API_KEY, asn_for_ip, asn_name, registry_lookup, PRIVATE

HERE = os.path.dirname(__file__)
RIPE_PROBES_API = "https://atlas.ripe.net/api/v2/probes/"

# Full known PK roster (CLAUDE.md probe tables) -- filtered to Connected +
# usable IPv4 at runtime, never trusted as-is.
KNOWN_IDS = [1015679, 1015210, 62224, 60223, 7613, 1016036, 1016143, 1016126,
             1016153, 1016154, 64535, 7764, 64078, 64722, 65892, 1014872,
             1015491, 1016393, 1016431]

# (isp, city) for labeling only -- from CLAUDE.md's probe roster tables.
PROBE_LABEL = {
    1015679: ("nova", "lhe"), 1015210: ("ptcl", "khi"), 62224: ("transworld", "lhe"),
    60223: ("nayatel", "isb"), 7613: ("zcom", "lhe"), 1016036: ("cybernet", "hrp"),
    1016143: ("cybernet", "khi"), 1016126: ("ptcl", "khi"), 1016153: ("tes", "khi"),
    1016154: ("cybernet", "khi"), 64535: ("orbit", "fsd"), 7764: ("ptcl", "lhe"),
    64078: ("tes", "lhe"), 64722: ("tes", "khi"), 65892: ("nayatel", "lhe"),
    1014872: ("fasttel", "isb"), 1015491: ("zcom", "?"), 1016393: ("ptcl", "npj"),
    1016431: ("ntc", "khi"),
}
# Hide the path (traceroute) as source AND now as destination too -- their own
# address_v4 will still resolve, but hops leading TO them may go dark near the
# end. Ping RTT is still valid. See CLAUDE.md "Known measurement artifacts".
ICMP_FILTERED = {62224, 7764}

LAUNCH_DELAY = 0.4     # polite spacing between create() calls
BATCH_SIZE = 40        # concurrent one-off measurements per chunk (well under the 100/account cap)
BATCH_WAIT = 20        # seconds between chunks
POLL_INTERVAL = 12
POLL_DEADLINE_S = 900

# Same RTT-physics tromboning thresholds as Exp 04 / 4.1 (CLAUDE.md "Detector methodology").
FOREIGN_RTT_FLOOR = 40.0
JUMP_THRESH = 60.0
HIGH_RTT = 70.0
LOCAL_CEIL = 45.0
ARTIFACT_ASN = {"6327"}   # Shaw/Nova CPE, physically in PK -- exclude from country analysis


def label(pid):
    m = PROBE_LABEL.get(pid)
    return f"{m[0]}.{m[1]}" if m else str(pid)


def fetch_active_probes():
    """Live status + address_v4 for KNOWN_IDS via RIPE's public API (no key needed).
    Returns {id: {"ip": ..., "asn": ...}}, Connected + usable-IPv4 only."""
    r = requests.get(RIPE_PROBES_API, params={
        "id__in": ",".join(map(str, KNOWN_IDS)), "page_size": 100,
        "fields": "id,status,asn_v4,address_v4"}, timeout=25)
    r.raise_for_status()
    out = {}
    for p in r.json()["results"]:
        st = (p.get("status") or {}).get("name")
        ip = p.get("address_v4")
        if st == "Connected" and ip:
            out[p["id"]] = {"ip": ip, "asn": p.get("asn_v4")}
    return out


def hop_geo(ip):
    if not ip or pk.PRIVATE(ip):
        return ("", "RFC1918", "")
    asn, _p, cc = pk.asn_for_ip(ip)
    if asn:
        return (asn, pk.asn_name(asn) or "?", cc)
    _p2, cc2, name = pk.registry_lookup(ip)
    return ("", name or "?", cc2)


def classify_trace(pr):
    """Same RTT-physics tromboning detector as Exp 04/4.1 -- foreign hop with a
    physically-plausible RTT, or an RTT jump/ceiling backstop when the foreign hop
    doesn't reply. Returns (verdict_dict, hop_lines)."""
    exit_hop = exit_ip = exit_name = exit_cc = transit_asn = transit_name = ""
    hop_lines = []
    prev_pk_asn = prev_pk_name = ""
    max_rtt = 0.0; prev_rtt = None; max_jump = 0.0; jump_asn = jump_name = ""
    for hop in pr.hops:
        ip_h = next((pkt.origin for pkt in hop.packets if pkt.origin), None)
        rtt_h = min([pkt.rtt for pkt in hop.packets if pkt.rtt is not None], default=None)
        if not ip_h:
            hop_lines.append(f"  {hop.index:>3}      *     (no response)")
            continue
        a, name, cc = hop_geo(ip_h)
        asn_s = f"AS{a}" if a else "-"
        if rtt_h is not None:
            max_rtt = max(max_rtt, rtt_h)
            if prev_rtt is not None and rtt_h - prev_rtt > max_jump:
                max_jump = rtt_h - prev_rtt; jump_asn, jump_name = prev_pk_asn, prev_pk_name
            prev_rtt = rtt_h
        foreign = (cc not in ("PK", "") and not pk.PRIVATE(ip_h) and a not in ARTIFACT_ASN
                   and rtt_h is not None and rtt_h >= FOREIGN_RTT_FLOOR)
        mark = ""
        if foreign and not exit_hop:
            exit_hop, exit_ip, exit_name, exit_cc = hop.index, ip_h, name, cc
            transit_asn, transit_name = prev_pk_asn, prev_pk_name
            mark = "  <<< LEAVES PK"
        if a and a not in ARTIFACT_ASN and (cc == "PK" or (rtt_h is not None and rtt_h < FOREIGN_RTT_FLOOR)):
            prev_pk_asn, prev_pk_name = a, name
        hop_lines.append(f"  {hop.index:>3}   {('%.1f' % rtt_h) if rtt_h is not None else '   ':>7}"
                         f"   {ip_h:<16} {asn_s:<9} {name[:30]}{(' (' + cc + ')') if cc else ''}{mark}")
    evidence = ""
    if exit_hop:
        evidence = "foreign_hop"
    elif max_jump >= JUMP_THRESH or max_rtt >= HIGH_RTT:
        exit_name = "(foreign hop not visible -- RTT evidence)"
        exit_cc = "?"; transit_asn, transit_name = jump_asn, jump_name
        evidence = f"rtt_jump={max_jump:.0f} max_rtt={max_rtt:.0f}"
    trombones = bool(exit_hop) or evidence.startswith("rtt")
    status = ("trombone_hop" if exit_hop else "trombone_rtt" if trombones else
              "local" if (max_rtt and max_rtt < LOCAL_CEIL) else "inconclusive")
    verdict = dict(status=status, evidence=evidence, exit_hop=exit_hop, exit_ip=exit_ip,
                   exit_name=exit_name[:40], exit_country=exit_cc, transit_asn=transit_asn,
                   transit_name=transit_name[:24],
                   max_rtt_ms=round(max_rtt, 1) if max_rtt else "", n_hops=len(pr.hops))
    return verdict, hop_lines


def build_pairs(active):
    ids = sorted(active)
    return [(i, j) for i in ids for j in ids if i != j]


def launch(jobs_spec, kind, key):
    """jobs_spec: list of (src_id, dst_id, dst_ip). Returns list of (kind, src, dst, dst_ip, mid)."""
    out = []
    for i in range(0, len(jobs_spec), BATCH_SIZE):
        chunk = jobs_spec[i:i + BATCH_SIZE]
        for src, dst, dst_ip in chunk:
            if kind == "trace":
                m = Traceroute(af=4, target=dst_ip, protocol="TCP", port=80, paris=16,
                               packets=3, description=f"exp11 mesh {src}->{dst}")
            else:
                m = Ping(af=4, target=dst_ip, packets=3, description=f"exp11 mesh {src}->{dst}")
            src_obj = AtlasSource(type="probes", value=str(src), requested=1)
            try:
                ok, resp = AtlasCreateRequest(key=key, measurements=[m],
                                              sources=[src_obj], is_oneoff=True).create()
                if ok:
                    mid = resp["measurements"][0]
                    out.append((kind, src, dst, dst_ip, mid))
                    print(f"  [{kind}] {label(src):>14} -> {label(dst):<14} {dst_ip:16} #{mid}")
                else:
                    print(f"  [{kind}] {label(src):>14} -> {label(dst):<14} FAILED: {str(resp)[:80]}")
            except Exception as e:
                print(f"  [{kind}] {label(src):>14} -> {label(dst):<14} ERROR: {str(e)[:80]}")
            time.sleep(LAUNCH_DELAY)
        if i + BATCH_SIZE < len(jobs_spec):
            print(f"  ... batch wait {BATCH_WAIT}s ...")
            time.sleep(BATCH_WAIT)
    return out


def poll(jobs):
    pending = {mid for *_, mid in jobs}
    results = {}
    deadline = time.time() + POLL_DEADLINE_S
    print(f"\nPolling {len(jobs)} measurements...", end="", flush=True)
    while pending and time.time() < deadline:
        time.sleep(POLL_INTERVAL); print(".", end="", flush=True)
        for mid in list(pending):
            ok, res = AtlasResultsRequest(msm_id=mid).create()
            if ok and res:
                results[mid] = res; pending.discard(mid)
    print(f" done ({len(results)}/{len(jobs)} returned)")
    return results


def main():
    args = sys.argv[1:]
    active = fetch_active_probes()
    if "--list" in args:
        print(f"{len(active)} probes currently Connected with a public IPv4:")
        for pid, info in sorted(active.items()):
            print(f"  {pid:>8}  {label(pid):<16} AS{info['asn']:<8} {info['ip']}")
        return

    if not pk.API_KEY or pk.API_KEY == "your-api-key-here":
        sys.exit("RIPE_API_KEY not loaded from .env")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(HERE, "results", f"run_{ts}")

    if "--reparse" in args:
        run_dir = args[args.index("--reparse") + 1]
        rawf = next(f for f in os.listdir(run_dir) if f.startswith("raw_"))
        raw_in = json.load(open(os.path.join(run_dir, rawf), encoding="utf-8"))
        ts = rawf[len("raw_"):-len(".json")]
        jobs, results = [], {}
        for k, v in raw_in.items():
            kind, src, dst, dst_ip, mid = k.split(":"); mid = int(mid)
            jobs.append((kind, int(src), int(dst), dst_ip, mid)); results[mid] = v
        print(f"Re-parsing {len(jobs)} saved results from {run_dir}")
        write_outputs(jobs, results, run_dir, ts)
        return

    os.makedirs(run_dir, exist_ok=True)
    pairs = build_pairs(active)
    n = len(active)
    print(f"{n} connected probes -> {len(pairs)} directed pairs "
          f"({len(pairs)} traceroutes + {len(pairs)} pings = {2 * len(pairs)} measurements)")
    if n - 1 > 25:
        print(f"WARNING: each target gets {n - 1} inbound measurements per kind -- "
              f"approaching RIPE's 25-one-off-per-target cap")

    trace_spec = [(i, j, active[j]["ip"]) for i, j in pairs]
    ping_spec = [(i, j, active[j]["ip"]) for i, j in pairs]

    print("\n--- launching traceroutes ---")
    jobs = launch(trace_spec, "trace", pk.API_KEY)
    print("\n--- launching pings ---")
    jobs += launch(ping_spec, "ping", pk.API_KEY)

    results = poll(jobs)
    write_outputs(jobs, results, run_dir, ts)


def write_outputs(jobs, results, run_dir, ts):
    raw = {}
    rows = []
    route_lines = [f"Exp 11 probe mesh -- {ts}", ""]

    for kind, src, dst, dst_ip, mid in jobs:
        res = results.get(mid)
        key = f"{kind}:{src}:{dst}:{dst_ip}:{mid}"
        if not res:
            rows.append(dict(kind=kind, src_probe=src, src_label=label(src),
                             dst_probe=dst, dst_label=label(dst), dst_ip=dst_ip,
                             status="no_result", measurement_id=mid))
            continue
        raw[key] = res

        if kind == "ping":
            pg = PingResult.get(res[0])
            rows.append(dict(kind="ping", src_probe=src, src_label=label(src),
                             dst_probe=dst, dst_label=label(dst), dst_ip=dst_ip,
                             status="ok" if pg.packets_received else "no_reply",
                             rtt_min_ms=round(pg.rtt_min, 1) if pg.rtt_min is not None else "",
                             rtt_avg_ms=round(pg.rtt_average, 1) if pg.rtt_average is not None else "",
                             packets_sent=pg.packets_sent, packets_received=pg.packets_received,
                             measurement_id=mid))
            continue

        pr = TracerouteResult.get(res[0])
        verdict, hop_lines = classify_trace(pr)
        rows.append(dict(kind="trace", src_probe=src, src_label=label(src),
                         dst_probe=dst, dst_label=label(dst), dst_ip=dst_ip,
                         status=verdict["status"], evidence=verdict["evidence"],
                         exit_name=verdict["exit_name"], exit_country=verdict["exit_country"],
                         transit_name=verdict["transit_name"], max_rtt_ms=verdict["max_rtt_ms"],
                         dest_rtt_ms=round(pr.last_median_rtt, 1) if pr.last_median_rtt else "",
                         n_hops=verdict["n_hops"], reached=pr.destination_ip_responded,
                         measurement_id=mid))
        route_lines.append("=" * 78)
        flag = f"TROMBONES via {verdict['exit_name'][:24]} ({verdict['exit_country']})" \
               if verdict["status"].startswith("trombone") else "stays in PK"
        route_lines.append(f" {label(src)} ({src}) -> {label(dst)} ({dst}, {dst_ip})   [{flag}]")
        route_lines.append(f" reached={pr.destination_ip_responded}  msm={mid}")
        route_lines.append("-" * 78)
        route_lines += hop_lines
        route_lines.append("")

    cols = ["kind", "src_probe", "src_label", "dst_probe", "dst_label", "dst_ip",
            "status", "evidence", "exit_name", "exit_country", "transit_name",
            "max_rtt_ms", "dest_rtt_ms", "n_hops", "reached",
            "rtt_min_ms", "rtt_avg_ms", "packets_sent", "packets_received",
            "measurement_id"]
    csv_path = os.path.join(run_dir, f"mesh_{ts}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    with open(os.path.join(run_dir, f"routes_{ts}.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(route_lines) + "\n")
    json.dump(raw, open(os.path.join(run_dir, f"raw_{ts}.json"), "w", encoding="utf-8"))

    # ---- symmetry check: for each unordered pair, compare i->j vs j->i ----
    by_pair = {}
    for r in rows:
        if r["kind"] != "trace":
            continue
        k = frozenset((r["src_probe"], r["dst_probe"]))
        by_pair.setdefault(k, {})[r["src_probe"]] = r
    asym = []
    for k, dirs in by_pair.items():
        if len(dirs) != 2:
            continue
        a, b = dirs.values()
        if a["status"] != b["status"]:
            asym.append((a, b))

    trace_rows = [r for r in rows if r["kind"] == "trace" and r["status"] != "no_result"]
    tr = [r for r in trace_rows if r["status"].startswith("trombone")]
    print(f"\n=== Exp 11 mesh summary ===")
    print(f"  {len(trace_rows)} traceroutes with data")
    if trace_rows:
        print(f"    trombone abroad : {len(tr):>3}  ({100*len(tr)/len(trace_rows):.0f}%)")
    print(f"  {len(asym)} pairs with an ASYMMETRIC verdict (local one way, trombone the other):")
    for a, b in asym:
        print(f"    {a['src_label']} -> {a['dst_label']}: {a['status']}   |   "
              f"{b['src_label']} -> {b['dst_label']}: {b['status']}")
    print(f"  wrote {csv_path}")


if __name__ == "__main__":
    main()
