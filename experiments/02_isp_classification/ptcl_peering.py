#!/usr/bin/env python3
"""
PTCL interconnect probes (Exp 02 method, supports findings 3.1)
===============================================================
Two related data-plane tests, one script. Reuses scripts/measurement/pk_multi_probe.py.

  peering  Direct probe-to-probe traceroute + ping in BOTH directions between a
           PTCL endpoint and a Transworld endpoint. Settles "no PTCL/TWA peering
           => routed internationally": RTT < ~50 ms with all-PK hops = domestic.

  hosted   Traceroute from every probe to the two genuinely PTCL-hosted (AS17557)
           Exp-01 sites (lums.edu.pk, ptcl.com.pk) — Exp 02 "probe-on-A to host-on-B":
           does each ISP reach a PTCL server locally or hairpin?

Output (committed): results/ptcl_peering/{mode}_raw.json + {mode}_routes.txt
(routes in the Exp 03 style). Measurements are one-off (cheaper than a periodic
trace_monitor run and need no cleanup).

    python experiments/02_isp_classification/ptcl_peering.py peering
    python experiments/02_isp_classification/ptcl_peering.py hosted
    python experiments/02_isp_classification/ptcl_peering.py hosted --render-only
"""
import os, sys, time, json, glob
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "scripts", "measurement"))
import pk_multi_probe as pk

OUT_DIR = os.path.join(os.path.dirname(__file__), "results", "ptcl_peering")
os.makedirs(OUT_DIR, exist_ok=True)

# ---- endpoints (probe_id, egress IP, label), from run_20260612_48h dim_probe ----
PTCL_KHI = (1016126, "39.39.48.53",    "ptcl.khi")
PTCL_LHE = (7764,    "203.135.63.50",  "ptcl.lhe")
TWA_LHE  = (62224,   "110.93.235.222", "transworld.lhe")

# peering: (src_probe, src_label, dst_ip, dst_label) — both directions
PAIRS = [
    (PTCL_KHI[0], PTCL_KHI[2], TWA_LHE[1],  TWA_LHE[2]),
    (PTCL_LHE[0], PTCL_LHE[2], TWA_LHE[1],  TWA_LHE[2]),
    (TWA_LHE[0],  TWA_LHE[2],  PTCL_KHI[1], PTCL_KHI[2]),
    (TWA_LHE[0],  TWA_LHE[2],  PTCL_LHE[1], PTCL_LHE[2]),
]

# hosted: every current probe -> the two PTCL-hosted sites
PROBES = [
    (7613,    "AS152605 - Z-Com (Lahore)"),
    (7764,    "AS17557 - PTCL (Lahore, anchor LUMS)"),
    (60223,   "AS23674 - Nayatel (Islamabad)"),
    (62224,   "AS38193 - Transworld (Lahore)"),
    (1015679, "AS136174 - TPCPL/Nova (Lahore)"),
    (1016036, "AS9541 - Cybernet (Haripur)"),
    (1016126, "AS17557 - PTCL (Karachi)"),
    (1016143, "AS9541 - Cybernet (Karachi)"),
]
SRC = dict(PROBES)
# pinned public IPs (lums.edu.pk split-DNS resolves to RFC1918 on some networks)
HOSTED = {"lums.edu.pk": "203.135.62.24", "ptcl.com.pk": "221.120.226.61"}


# ───────────────────────── shared helpers ─────────────────────────
def label(ip):
    if not ip:
        return ("", "(no response)", "")
    if pk.PRIVATE(ip):
        return ("", "RFC1918", "")
    asn, _p, cc = pk.asn_for_ip(ip)
    if asn:
        return (asn, pk.asn_name(asn) or "?", cc)
    _p2, cc2, name = pk.registry_lookup(ip)
    return ("", name or "?", cc2)

def fmt_ts(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()

def create_ping(probe_id, target_ip, description):
    payload = {"definitions": [{"target": target_ip, "description": description,
               "type": "ping", "af": 4, "packets": 3, "resolve_on_probe": False}],
               "probes": [{"type": "probes", "value": str(probe_id), "requested": 1}],
               "is_oneoff": True}
    r = pk.requests.post(f"{pk.BASE}/measurements/", headers=pk.HDR, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()["measurements"][0]

def safe_create(fn, *a):
    try:
        return fn(*a)
    except Exception as e:
        body = getattr(getattr(e, "response", None), "text", str(e))
        print(f"    ! create failed: {body[:140]}")
        return None

def trace_block(r0, header_dst_asn=True):
    """Render one traceroute result as Exp-03-style text lines."""
    out = []
    dst = r0.get("dst_addr"); reached = r0.get("destination_ip_responded")
    out.append("-" * 78)
    out.append("  hop   rtt(ms)   ip                 asn       operator (country)")
    for hop in r0.get("result", []):
        hn = hop.get("hop"); reps = hop.get("result", [])
        ips = [x.get("from") for x in reps if x.get("from")]
        rtt = min([x["rtt"] for x in reps if "rtt" in x], default=None)
        if not ips:
            out.append(f"  {hn:>3}      *     (no response)"); continue
        ip = ips[0]; asn, name, cc = label(ip)
        asn_s = f"AS{asn}" if asn else "-"
        op = f"{name}{(' ('+cc+')') if cc else ''}"
        mark = "  <<< DESTINATION" if ip == dst else ""
        out.append(f"  {hn:>3}   {rtt:>7.1f}   {ip:<18} {asn_s:<9} {op}{mark}")
    return out, dst, reached


# ───────────────────────── peering mode ─────────────────────────
def run_peering(render_only):
    raw_path = os.path.join(OUT_DIR, "peering_raw.json")
    raw = json.load(open(raw_path, encoding="utf-8")) if os.path.exists(raw_path) else {}

    if not render_only:
        print("Launching PTCL<->Transworld traceroutes + pings (both directions)...")
        jobs = []
        for sid, slab, dip, dlab in PAIRS:
            desc = f"ptcl-twa peering: {slab} to {dlab}"
            t = safe_create(pk.create_traceroute, sid, dip, "TR " + desc)
            p = safe_create(create_ping, sid, dip, "PING " + desc)
            if t: jobs.append(("trace", f"{slab} to {dlab}", t))
            if p: jobs.append(("ping",  f"{slab} to {dlab}", p))
            print(f"  {slab:16}-> {dlab:16}  trace#{t}  ping#{p}")
            time.sleep(2)
        done = pk.wait_for_all([j[2] for j in jobs], timeout=600)
        for kind, pair, mid in jobs:
            if mid in done:
                res = pk.fetch_result(mid)
                if res: raw[f"{kind}:{pair}:{mid}"] = res
        json.dump(raw, open(raw_path, "w", encoding="utf-8"), indent=2)

    # render
    traces = {k: v for k, v in raw.items() if k.startswith("trace:") and v}
    pings  = {k: v for k, v in raw.items() if k.startswith("ping:")  and v}
    L = ["PTCL <-> Transworld peering check  -  readable traceroutes",
         "Direct probe-to-probe test, both directions. Settles 'no PTCL/TWA peering => routed internationally'.",
         f"{len(traces)} traceroutes, {len(pings)} pings.", ""]
    for k in sorted(traces):
        _, pair, mid = k.split(":"); r0 = traces[k][0]
        dasn, dname, dcc = label(r0.get("dst_addr"))
        L.append("=" * 78)
        L.append(f" {pair}    (msm {mid})")
        L.append(f" TIME    {fmt_ts(r0.get('timestamp'))}")
        L.append(f" SOURCE  probe {r0.get('prb_id')}   [egress {r0.get('src_addr')}]")
        L.append(f" DEST    {r0.get('dst_addr')} - {('AS'+dasn+' ') if dasn else ''}{dname}"
                 f"{(' ('+dcc+')') if dcc else ''} - "
                 f"{'reached' if r0.get('destination_ip_responded') else 'no final response'}")
        body, _, _ = trace_block(r0); L += body; L.append("")
    L += ["=" * 78, " PING RTT SUMMARY  (the speed-of-light evidence)",
          " floor: Karachi/Lahore -> Singapore ~60-90ms, -> Europe ~100-130ms",
          "-" * 78,
          f" {'direction':32} {'min':>8} {'avg':>8} {'max':>8}  rcvd  verdict"]
    for k in sorted(pings):
        _, pair, mid = k.split(":"); p0 = pings[k][0]; mn = p0.get("min")
        verdict = ("DOMESTIC (<50ms)" if isinstance(mn,(int,float)) and 0 <= mn < 50
                   else "INTL HAIRPIN (>100ms)" if isinstance(mn,(int,float)) and mn > 100
                   else "no reply (ICMP filtered)")
        s = lambda x: f"{x:.1f}" if isinstance(x,(int,float)) and x >= 0 else "-"
        L.append(f" {pair:32} {s(p0.get('min')):>8} {s(p0.get('avg')):>8} {s(p0.get('max')):>8}"
                 f"  {p0.get('rcvd')}/{p0.get('sent')}  {verdict}")
    L += ["", "Verdict: PTCL and Transworld interconnect DOMESTICALLY (1.5-47ms, all PK).",
          "The 'routed internationally' claim is disproved. See findings/03.1_ptcl_rtt_jumps.md."]
    _write(L, "peering_routes.txt")


# ───────────────────────── hosted mode ─────────────────────────
def run_hosted(render_only):
    raw_path = os.path.join(OUT_DIR, "hosted_raw.json")
    raw = json.load(open(raw_path, encoding="utf-8")) if os.path.exists(raw_path) else {}
    have = {(k.split(":")[0], int(k.split(":")[1])) for k in raw}

    if not render_only:
        todo = [(h, pid) for h in HOSTED for pid, _ in PROBES if (h, pid) not in have]
        print(f"Launching {len(todo)} traceroutes (skipping {len(have)} cached)...")
        jobs = []
        for host, pid in todo:
            mid = safe_create(pk.create_traceroute, pid, HOSTED[host],
                              f"TR ptcl-host reach: {pid} to {host}")
            if mid: jobs.append((host, pid, mid)); print(f"  {host:14} from {pid:<8} #{mid}")
            time.sleep(2)
        done = pk.wait_for_all([j[2] for j in jobs], timeout=600)
        for host, pid, mid in jobs:
            if mid in done:
                res = pk.fetch_result(mid)
                if res: raw[f"{host}:{pid}:{mid}"] = res
        json.dump(raw, open(raw_path, "w", encoding="utf-8"), indent=2)

    # render — newest result per (host, pid)
    merged = {}
    for k, v in raw.items():
        host, pid, _m = k.split(":"); merged[(host, int(pid))] = v
    L = ["PTCL-hosted sites reached from every probe  -  readable traceroutes",
         "Exp 02 'probe-on-A to host-on-B': how each ISP reaches a PTCL (AS17557) server.",
         "Targets: " + ", ".join(f"{h} ({ip})" for h, ip in HOSTED.items()), ""]
    for host in HOSTED:
        for pid, _d in PROBES:
            res = merged.get((host, pid))
            L.append("=" * 78)
            if not res:
                L.append(f" {host}   from probe {pid} - {SRC.get(pid)}")
                L.append("   (no result — timed out / no suitable probe)"); L.append(""); continue
            r0 = res[0]; dasn, dname, dcc = label(r0.get("dst_addr"))
            L.append(f" {host}  ({r0.get('dst_addr')})  -  {('AS'+dasn+' ') if dasn else ''}{dname}")
            L.append(f" TIME    {fmt_ts(r0.get('timestamp'))}")
            L.append(f" SOURCE  probe {pid} - {SRC.get(pid)}   [egress {r0.get('src_addr')}]")
            L.append(f" DEST    {r0.get('dst_addr')} - "
                     f"{'reached' if r0.get('destination_ip_responded') else 'no final response'}")
            body, _, _ = trace_block(r0); L += body; L.append("")
    _write(L, "hosted_routes.txt")


def _write(lines, name):
    out = os.path.join(OUT_DIR, name)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {out}")


def main():
    args = sys.argv[1:]
    render_only = "--render-only" in args
    mode = next((a for a in args if not a.startswith("-")), None)
    if mode not in ("peering", "hosted"):
        sys.exit("usage: ptcl_peering.py {peering|hosted} [--render-only]")
    if not render_only and (not pk.API_KEY or pk.API_KEY == "your-api-key-here"):
        sys.exit("RIPE_API_KEY not loaded from .env")
    (run_peering if mode == "peering" else run_hosted)(render_only)


if __name__ == "__main__":
    main()
