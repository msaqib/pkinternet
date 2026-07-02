#!/usr/bin/env python3
"""
Exp 06 - submarine-outage routing monitor (SMW5 fault, Jul 2026).

Periodic ICMP Paris traceroute + ping every 15 min for 12 h, from all 4 connected
PTCL/Transworld probes to a balanced CDN / Abroad / PK target sample. Server-side
periodic measurements (survive laptop sleep, tiny footprint, no clash with the census).

    python experiments/06_submarine_outage/outage_monitor.py schedule   # start
    python experiments/06_submarine_outage/outage_monitor.py fetch       # results -> CSV + routes txt
    python experiments/06_submarine_outage/outage_monitor.py stop        # stop early

Analysis (fetch): per (probe, target, round) we record end-to-end RTT and the
per-hop RTT deltas, flag the max-delta hop (the link that introduces the delay),
and mark 2-3x spikes vs the per-series baseline (first rounds). International RTT
should spike while local RTT stays flat - the submarine-cut signature.
"""
import os, sys, csv, json, glob, socket, shutil, collections
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results"); os.makedirs(OUT, exist_ok=True)
MJSON = os.path.join(OUT, "measurements.json")

sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "measurement"))
import pk_multi_probe as pk
sys.path.insert(0, os.path.join(HERE, "..", "04.1_small_isp_tromboning"))
import census_sweep as cs
from ripe.atlas.cousteau import (Traceroute, Ping, AtlasSource, AtlasCreateRequest,
                                 AtlasStopRequest, AtlasResultsRequest)
from ripe.atlas.sagan import TracerouteResult, PingResult

INTERVAL = 900          # 15 minutes
DURATION_H = 12         # 12 hours

# All 14 connected Pakistani probes (PTCL/Transworld = the affected LDIs; rest = other
# ISPs / controls). Snapshot 2026-07-03.
PROBES = {
    7764:    "ptcl.anchor (AS17557)",
    1015210: "ptcl (AS17557)",
    1016126: "ptcl.khi (AS17557)",
    62224:   "transworld (AS38193)",
    64078:   "tes.transworld-retail (AS135407)",
    1016036: "cybernet (AS9541)",
    1016143: "cybernet (AS9541)",
    1016154: "cybernet (AS9541)",
    60223:   "nayatel (AS23674)",
    65892:   "nayatel (AS23674)",
    1015679: "nova/tpcpl (AS136174)",
    1014872: "fasttel (AS150683)",
    64535:   "orbit (AS151983)",
    7613:    "zcom.anchor (AS152605)",
}

# Balanced CDN / Abroad / PK sample (liveness-checked 2026-07-03). Resolved at schedule.
TARGETS = [
    ("CDN",      "telenor.com.pk",       "Cloudflare"),
    ("CDN",      "shophive.com",         "Cloudflare"),
    ("CDN",      "aku.edu",              "Microsoft/Azure"),
    ("CDN",      "express.com.pk",       "Cloudflare"),
    ("CDN",      "outfitters.com.pk",    "Cloudflare"),
    ("CDN",      "telemart.pk",          "Cloudflare"),
    ("Abroad",   "wateen.com",           "Hostinger"),
    ("Abroad",   "daraz.pk",             "Alibaba-CN"),
    ("Abroad",   "alfatah.com.pk",       "Hostinger"),
    ("Abroad",   "dailypakistan.com.pk", "Hetzner"),
    ("Abroad",   "sapphireonline.pk",    "EDNS"),
    ("Abroad",   "balochistan.gov.pk",   "Oracle"),
    ("Pakistan", "isra.edu.pk",          "GESNET-PK"),
    ("Pakistan", "punjab.gov.pk",        "PITB-Punjab"),
    ("Pakistan", "nab.gov.pk",           "Cybernet-PK"),
    ("Pakistan", "pbs.gov.pk",           "NTC-PK"),
    ("Pakistan", "maju.edu.pk",          "Wateen-PK"),
    ("Pakistan", "yansrhr.org",          "LDN-PK"),
]


def resolve(host):
    try:
        return socket.gethostbyname(host)
    except Exception:
        return None


def schedule():
    if os.path.exists(MJSON):
        print("measurements.json already exists - stop/remove it before re-scheduling."); return
    src = AtlasSource(type="probes", value=",".join(str(p) for p in PROBES), requested=len(PROBES))
    start = datetime.utcnow() + timedelta(minutes=1)
    stop = start + timedelta(hours=DURATION_H)
    meta = {"created": start.isoformat() + "Z", "stop": stop.isoformat() + "Z",
            "interval_s": INTERVAL, "probes": PROBES, "trace": {}, "ping": {}, "target_ip": {},
            "target_cat": {}, "target_host": {}}
    for cat, host, hoster in TARGETS:
        ip = resolve(host)
        if not ip:
            print(f"  skip {host} (no DNS)"); continue
        meta["target_ip"][host] = ip; meta["target_cat"][host] = cat; meta["target_host"][host] = hoster
        for kind, spec in (
            ("trace", Traceroute(af=4, target=ip, protocol="ICMP", paris=16, packets=3,
                                 interval=INTERVAL, description=f"exp06 smw5 trace {cat} {host}")),
            ("ping",  Ping(af=4, target=ip, packets=3, interval=INTERVAL,
                          description=f"exp06 smw5 ping {cat} {host}")),
        ):
            ok, resp = AtlasCreateRequest(key=pk.API_KEY, measurements=[spec], sources=[src],
                                          is_oneoff=False, start_time=start, stop_time=stop).create()
            if ok:
                mid = resp["measurements"][0]; meta[kind][host] = mid
                print(f"  {kind:5} {cat:8} {host:24} -> msm {mid}")
            else:
                print(f"  FAIL {kind} {host}: {resp}")
    json.dump(meta, open(MJSON, "w"), indent=2)
    n = len(meta["trace"]) + len(meta["ping"])
    print(f"\nscheduled {n} periodic measurements x {len(PROBES)} probes, every {INTERVAL//60} min "
          f"until {stop:%Y-%m-%d %H:%M} UTC\nsaved {MJSON}")


def stop():
    meta = json.load(open(MJSON))
    for kind in ("trace", "ping"):
        for host, mid in meta[kind].items():
            try:
                AtlasStopRequest(msm_id=mid, key=pk.API_KEY).create(); print(f"  stopped {mid} ({host})")
            except Exception as e:
                print(f"  {mid}: {e}")


def _hop_rtts(pr):
    """list of (index, min_rtt, ip, asn, name, cc) for responding hops."""
    out = []
    for hop in pr.hops:
        hip = next((p.origin for p in hop.packets if p.origin), None)
        rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
        if hip and rtt is not None:
            a, name, ccc = cs.hop_geo(hip)
            out.append((hop.index, rtt, hip, a, name, ccc))
    return out


def fetch():
    meta = json.load(open(MJSON))
    start = meta["created"].rstrip("Z")
    rows = []            # per (probe, target, round)
    traces = []          # for routes txt: (cat, host, label, sagan result, verdict)
    for host, mid in meta["trace"].items():
        cat = meta["target_cat"][host]; ip = meta["target_ip"][host]
        try:
            ok, results = AtlasResultsRequest(msm_id=mid, start=start).create()
        except Exception as e:
            print(f"  {host}: {e}"); continue
        if not ok:
            continue
        for r in results:
            lbl = PROBES.get(r.get("prb_id"), r.get("prb_id"))
            try:
                pr = TracerouteResult.get(r); v = cs.classify(r, "0")
            except Exception:
                continue
            hops = _hop_rtts(pr)
            # consecutive-hop RTT delta -> the link that introduces the most delay
            best = (0.0, "", "")
            for (i0, r0, ip0, a0, n0, c0), (i1, r1, ip1, a1, n1, c1) in zip(hops, hops[1:]):
                d = r1 - r0
                if d > best[0]:
                    best = (d, f"{n0[:14]}({c0})", f"{n1[:14]}({c1})")
            when = datetime.fromtimestamp(r.get("timestamp", 0), timezone.utc)
            rows.append(dict(time=when.strftime("%Y-%m-%d %H:%M"), probe=lbl, cat=cat, target=host,
                             target_ip=ip, reached=pr.destination_ip_responded,
                             dest_rtt=(round(pr.last_median_rtt, 1) if pr.last_median_rtt else ""),
                             max_rtt=v["max_rtt"], tromboned=(v["status"] == "trombone"),
                             exit=(v["exit_name"] or v["exit_cc"]) if v["status"] == "trombone" else "",
                             max_hop_delta=round(best[0], 1), delta_link=f"{best[1]}->{best[2]}" if best[1] else ""))
            traces.append((cat, host, str(lbl), when, pr, v))

    if not rows:
        print("no results yet (measurements need a few minutes to produce a first round)."); return
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # baseline = median dest_rtt of the earliest round per (probe,target); flag 2-3x spikes
    series = collections.defaultdict(list)
    for x in rows:
        if x["dest_rtt"] != "":
            series[(x["probe"], x["target"])].append((x["time"], x["dest_rtt"]))
    base = {}
    for k, v in series.items():
        vals = [d for _, d in sorted(v)][:2]           # first two rounds as baseline
        base[k] = sum(vals) / len(vals) if vals else None
    for x in rows:
        b = base.get((x["probe"], x["target"]))
        x["baseline_rtt"] = round(b, 1) if b else ""
        x["spike_x"] = round(x["dest_rtt"] / b, 1) if (b and x["dest_rtt"] != "") else ""

    cols = ["time", "probe", "cat", "target", "target_ip", "reached", "dest_rtt", "baseline_rtt",
            "spike_x", "max_rtt", "max_hop_delta", "delta_link", "tromboned", "exit"]
    out_csv = os.path.join(OUT, f"outage_{ts}.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    # routes txt (standing rule) - one block per (probe,target) latest round
    latest = {}
    for cat, host, lbl, when, pr, v in traces:
        latest[(lbl, host)] = (cat, host, lbl, when, pr, v)
    lines = [f"Exp 06 - submarine-outage traceroutes (SMW5), {len(latest)} latest per (probe,target)",
             "'<<< LEAVES PK' = exit hop. delta = RTT jump vs previous hop (the delaying link).", ""]
    for cat, host, lbl, when, pr, v in sorted(latest.values(), key=lambda x: (x[0], x[1], x[2])):
        lines.append("=" * 84)
        lines.append(f" [{cat}] {host} -> {meta['target_ip'][host]}   ({meta['target_host'].get(host,'')})")
        lines.append(f" SOURCE  {lbl}    {when:%Y-%m-%d %H:%M} UTC")
        lines.append(f" VERDICT {v['status'].upper()}  reached={pr.destination_ip_responded}  "
                     f"destRTT={round(pr.last_median_rtt,1) if pr.last_median_rtt else '-'}ms  "
                     f"maxRTT={v['max_rtt']}ms  exit={v['exit_name'] or v['exit_cc'] or '-'}")
        lines.append("-" * 84)
        lines.append("  hop   rtt(ms)   d-prev   ip                asn      operator (cc)")
        prev = None
        for hop in pr.hops:
            hip = next((p.origin for p in hop.packets if p.origin), None)
            rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
            if not hip:
                lines.append(f"  {hop.index:>3}      *      (no response)"); continue
            a, name, ccc = cs.hop_geo(hip)
            d = (rtt - prev) if (rtt is not None and prev is not None) else None
            if rtt is not None:
                prev = rtt
            foreign = (ccc not in ("PK", "") and not cs.pk.PRIVATE(hip) and a not in cs.ARTIFACT_ASN
                       and rtt is not None and cs.FOREIGN_RTT_FLOOR <= rtt <= cs.QUEUE_CEIL)
            lines.append(f"  {hop.index:>3}   {('%.1f'%rtt) if rtt is not None else '':>7}   "
                         f"{('%+.1f'%d) if d is not None else '':>6}   {hip:<16} {('AS'+a) if a else '-':<8} "
                         f"{name[:26]}{(' ('+ccc+')') if ccc else ''}{'   <<< LEAVES PK' if foreign else ''}")
        lines.append("")
    out_txt = os.path.join(OUT, f"routes_outage_{ts}.txt")
    open(out_txt, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # quick summary: spikes by category
    sp = collections.defaultdict(list)
    for x in rows:
        if x["spike_x"] != "":
            sp[x["cat"]].append(x["spike_x"])
    print(f"rows: {len(rows)}  rounds: {len({x['time'] for x in rows})}  targets: {len(meta['trace'])}")
    for cat in ("CDN", "Abroad", "Pakistan"):
        v = sp.get(cat, [])
        if v:
            print(f"  {cat:8} median spike x{sorted(v)[len(v)//2]:.1f}  max x{max(v):.1f}  (>=2x: {sum(1 for z in v if z>=2)})")
    print(f"wrote {out_csv}\nwrote {out_txt}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "schedule"
    {"schedule": schedule, "fetch": fetch, "stop": stop}.get(cmd, schedule)()
