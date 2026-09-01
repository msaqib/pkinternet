#!/usr/bin/env python3
"""
Exp 12 -- probe mesh panel: the 7-day longitudinal version of Exp 11.

Every connected PK probe pings every OTHER connected PK probe hourly, and
traceroutes every other probe twice a day, continuously for a week. Uses the
same target workaround as Exp 11 (a probe's own public address_v4, since RIPE
Atlas has no first-class "probe -> probe" measurement type) but schedules it as
server-side *periodic* measurements (Exp 07's mechanism) instead of one-off pairs.

Measurement-count trick (see notes.md "Why not N*(N-1)"): a single RIPE
measurement already fans one target out to many source probes. So instead of one
periodic measurement per DIRECTED PAIR (2*N*(N-1) -- would blow the 100-parallel
cap), this creates one periodic ping + one periodic traceroute PER DESTINATION
PROBE, with sources = every other connected probe. That still captures every
directed pair (each result carries its own prb_id) but needs only 2*N measurement
objects (34 for the current 17-probe roster).

    python mesh_panel_monitor.py list        # who's online right now -- free, run first
    python mesh_panel_monitor.py schedule    # create the 2*N periodic measurements (7-day window)
    nohup python mesh_panel_monitor.py watch &   # background: pull new results hourly -> panel CSV
    python mesh_panel_monitor.py check       # run once a day: health report (no credits spent)
    python mesh_panel_monitor.py fetch       # one-off pull, same as watch's cycle but on demand
    python mesh_panel_monitor.py stop        # stop early

Config: the CONFIG block below (env vars MESH_PING_EVERY_MIN, MESH_TRACE_EVERY_MIN,
MESH_DURATION_DAYS, MESH_WATCH_EVERY_MIN, MESH_PARALLEL_CAP, MESH_FORCE override it).
LOCAL ONLY -- this tool never touches git.
"""
import os, sys, csv, json, time, glob
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)
MJSON = os.path.join(OUT, "measurements.json")
ROSTER_JSON = os.path.join(OUT, "roster.json")

sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "measurement"))
import pk_multi_probe as pk
sys.path.insert(0, os.path.join(HERE, "..", "11_probe_mesh"))
import mesh_sweep as ms   # classify_trace() -- the RTT-physics trace classifier only

import requests
from ripe.atlas.cousteau import (Traceroute, Ping, AtlasSource, AtlasCreateRequest,
                                 AtlasStopRequest, AtlasResultsRequest)
from ripe.atlas.sagan import TracerouteResult, PingResult

# ============================ CONFIG — edit these ============================
PING_EVERY_MIN  = 60     # ping every OTHER probe once per hour, each direction
TRACE_EVERY_MIN = 720    # traceroute every OTHER probe twice a day (every 12h), each direction
DURATION_DAYS   = 7      # how many days the whole run lasts
WATCH_EVERY_MIN = 60     # how often the `watch` loop pulls new results
# Env overrides: MESH_PING_EVERY_MIN, MESH_TRACE_EVERY_MIN, MESH_DURATION_DAYS,
# MESH_WATCH_EVERY_MIN, MESH_PARALLEL_CAP, MESH_FORCE, PANEL_RIPE_KEY.
# ===============================================================================
PING_EVERY_MIN  = int(os.environ.get("MESH_PING_EVERY_MIN", PING_EVERY_MIN))
TRACE_EVERY_MIN = int(os.environ.get("MESH_TRACE_EVERY_MIN", TRACE_EVERY_MIN))
DURATION_DAYS   = float(os.environ.get("MESH_DURATION_DAYS", DURATION_DAYS))
WATCH_EVERY_MIN = int(os.environ.get("MESH_WATCH_EVERY_MIN", WATCH_EVERY_MIN))
PING_INTERVAL   = PING_EVERY_MIN * 60      # seconds (RIPE expects seconds)
TRACE_INTERVAL  = TRACE_EVERY_MIN * 60
WATCH_EVERY     = WATCH_EVERY_MIN * 60
PARALLEL_CAP    = int(os.environ.get("MESH_PARALLEL_CAP", "100"))
KEY = os.environ.get("PANEL_RIPE_KEY") or pk.API_KEY
RIPE_PROBES_API = "https://atlas.ripe.net/api/v2/probes/"
# Same ASN->name map as Exp 07's panel_monitor.py, used only to make labels readable.
PK_ASN = {17557: "ptcl", 45595: "ptcl-bb", 38193: "transworld", 135407: "tes", 9541: "cybernet",
          23674: "nayatel", 136174: "nova", 150683: "fasttel", 151983: "orbit", 152605: "zcom",
          38264: "wateen", 9260: "multinet", 23888: "ntc", 45773: "pern",
          147302: "falcon", 154578: "leapdigital"}
# Known ICMP-filtered probes (Exp 11 finding) -- traceroute/ping to/from these go thin
# regardless of which discovery method found them.
ICMP_FILTERED = {62224, 7764}
HOP_EXCLUDE = set(ICMP_FILTERED)   # hop counts unreliable for these probes


def pkt(dt): return dt + timedelta(hours=5)   # Pakistan Standard Time = UTC+5


def label(pid):
    return ROSTER_LABELS.get(pid, str(pid))


def discover_probes():
    """All Connected probes with country_code=PK, live -- Exp 07's exact discovery
    method (RIPE API, no key needed, no roster/hardcoded list). Note: this is a
    self-reported RIPE field, so it can include probes outside our project (e.g.
    other operators' probes in Pakistan) and can miss a project probe whose
    country_code is stale -- see notes.md "Which live source". Returns
    {id: {"label": "<isp>.<id>", "ip": address_v4 or None, "asn": asn_v4}}.
    A probe with no public IPv4 can still SOURCE measurements but can't be a
    TARGET (RIPE Atlas has no probe->probe measurement type -- Exp 11 notes)."""
    probes, url = {}, RIPE_PROBES_API
    params = {"country_code": "PK", "status": 1, "fields": "id,asn_v4,address_v4", "page_size": 100}
    while url:
        j = requests.get(url, params=params, timeout=30).json(); params = None
        for p in j.get("results", []):
            a = p.get("asn_v4")
            probes[p["id"]] = {"label": f"{PK_ASN.get(a, 'AS' + str(a))}.{p['id']}",
                               "ip": p.get("address_v4"), "asn": a}
        url = j.get("next")
    return probes


ROSTER_LABELS = {}   # filled by list_probes()/schedule() so label() works everywhere


def list_probes(quiet=False):
    """Live country_code=PK roster (no key needed, no credits). Run this FIRST,
    always, and again right before `schedule` -- the connected set moves fast."""
    global ROSTER_LABELS
    active = discover_probes()
    ROSTER_LABELS.update({pid: info["label"] for pid, info in active.items()})
    no_ip = [pid for pid, info in active.items() if not info["ip"]]
    if not quiet:
        print(f"{len(active)} probes currently Connected with country_code=PK:")
        for pid, info in sorted(active.items()):
            icmp = "  [ICMP-filtered]" if pid in ICMP_FILTERED else ""
            ip = info["ip"] or "(no public IPv4 -- can source, can't be a target)"
            print(f"  {pid:>8}  {info['label']:<16} AS{info['asn']:<8} {ip}{icmp}")
        n, nt = len(active), len(active) - len(no_ip)
        print(f"\nplanned periodic measurements: {nt} ping (hourly) + {nt} traceroute "
              f"(every {TRACE_EVERY_MIN // 60}h) = {2 * nt} -- vs the {PARALLEL_CAP} parallel cap "
              f"({nt} of {n} probes have a usable target IP).")
    return active


def running_measurements():
    """Current count of the account's ongoing measurements (for the preflight check)."""
    try:
        r = requests.get("https://atlas.ripe.net/api/v2/measurements/my/",
                         params={"status": 2, "page_size": 1},
                         headers={"Authorization": "Key " + KEY}, timeout=20)
        return r.json().get("count", 0) if r.ok else 0
    except Exception:
        return -1


def schedule():
    if os.path.exists(MJSON):
        print("measurements.json exists - stop/remove before re-scheduling."); return
    active = list_probes()
    if len(active) < 3:
        print("need >=3 connected probes (>=1 other source + >=1 target)."); return

    ids = sorted(active)                                          # every connected probe -- can all SOURCE
    targets = sorted(p for p in ids if active[p]["ip"])            # only these can be a TARGET (need a public IP)
    if len(targets) < 1 or len(ids) < 2:
        print("need >=1 target with a public IPv4 and >=2 total connected probes."); return

    n_new = 2 * len(targets)
    cap = PARALLEL_CAP
    running = running_measurements()
    print(f"\nplan: {len(targets)} destinations (of {len(ids)} connected probes) x 2 kinds = "
          f"{n_new} periodic measurements; currently {running} running; parallel cap = {cap}.")
    if running >= 0 and running + n_new > cap and os.environ.get("MESH_FORCE") != "1":
        print(f"ABORT: {running} + {n_new} would exceed the {cap} parallel-measurement cap.\n"
              f"  set MESH_PARALLEL_CAP higher if it's wrong, or MESH_FORCE=1 to proceed anyway.")
        return

    start = datetime.utcnow() + timedelta(minutes=1)
    stop = start + timedelta(days=DURATION_DAYS)
    meta = {"created": start.isoformat() + "Z", "stop": stop.isoformat() + "Z",
            "ping_interval": PING_INTERVAL, "trace_interval": TRACE_INTERVAL,
            "probes": {str(pid): {"label": label(pid), "ip": info["ip"], "asn": info["asn"]}
                       for pid, info in active.items()},
            "ping": {}, "trace": {}}
    print(f"\nscheduling {len(targets)} destinations x (ping+trace), sources = all OTHER connected "
          f"probes ({len(ids)} total, incl. any with no public IPv4), {DURATION_DAYS:g}-day window...")
    for dst in targets:
        others = [p for p in ids if p != dst]
        src = AtlasSource(type="probes", value=",".join(map(str, others)), requested=len(others))
        dst_ip = active[dst]["ip"]
        pg = Ping(af=4, target=dst_ip, packets=3, interval=PING_INTERVAL,
                  description=f"exp12 mesh ping to {label(dst)}")
        tr = Traceroute(af=4, target=dst_ip, protocol="TCP", port=80, paris=16, packets=3,
                        interval=TRACE_INTERVAL, description=f"exp12 mesh trace to {label(dst)}")
        for kind, spec in (("ping", pg), ("trace", tr)):
            ok, resp = AtlasCreateRequest(key=KEY, measurements=[spec], sources=[src],
                                          is_oneoff=False, start_time=start, stop_time=stop).create()
            if ok:
                meta[kind][str(dst)] = resp["measurements"][0]
                print(f"  {kind:5} -> {label(dst):<16} (from {len(others)} sources) "
                      f"-> msm {resp['measurements'][0]}")
            else:
                print(f"  FAIL {kind} -> {label(dst)}: {resp}")
    json.dump(meta, open(MJSON, "w"), indent=2)
    json.dump({"checked_at": datetime.now(timezone.utc).isoformat(), "probes": meta["probes"]},
               open(ROSTER_JSON, "w"), indent=2)
    print(f"\nscheduled {len(meta['ping']) + len(meta['trace'])} periodic measurements until "
          f"{pkt(stop):%Y-%m-%d %H:%M} PKT. saved {MJSON}")


def stop():
    meta = json.load(open(MJSON))
    global ROSTER_LABELS
    ROSTER_LABELS.update({int(pid): info["label"] for pid, info in meta["probes"].items()})
    for kind in ("ping", "trace"):
        for dst, mid in meta[kind].items():
            try:
                AtlasStopRequest(msm_id=mid, key=KEY).create()
                print(f"  stopped {mid} ({kind} -> {label(int(dst))})")
            except Exception as e:
                print(f"  {mid}: {e}")


def _hopcount(pr):
    last = 0
    for hop in pr.hops:
        if any(p.origin for p in hop.packets):
            last = hop.index
    return last


def fetch(stable=False):
    """Pull all results so far -> a panel CSV + routes txt. stable=True (used by
    watch()) overwrites one current panel_<ts>.csv/routes_<ts>.txt each cycle;
    stable=False (manual `fetch`) writes panel_updated_<ts>.csv alongside what's there."""
    meta = json.load(open(MJSON))
    P = meta["probes"]
    def plabel(pid): return P.get(str(pid), {}).get("label", pid)
    rows, latest_trace = [], {}

    for dst, mid in meta["ping"].items():
        try:
            ok, res = AtlasResultsRequest(msm_id=mid).create()
        except Exception as e:
            print(f"  ping -> {plabel(int(dst))}: {e}"); continue
        if not ok: continue
        for r in res:
            try: pg = PingResult.get(r)
            except Exception: continue
            ts = r.get("timestamp", 0); sent = pg.packets_sent or 0; rcvd = pg.packets_received or 0
            src = r.get("prb_id")
            rows.append(dict(
                ts_utc=datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                ts_pkt=pkt(datetime.fromtimestamp(ts, timezone.utc)).strftime("%Y-%m-%d %H:%M:%S"),
                kind="ping", src_probe_id=src, src=plabel(src),
                dst_probe_id=int(dst), dst=P[dst]["label"],
                rtt_min=(round(pg.rtt_min, 1) if pg.rtt_min is not None else ""),
                loss=(round(1 - rcvd / sent, 3) if sent else ""), hop_count="",
                tromboned="", status="", exit_cc="", transit="", trace_rtt_ms=""))

    for dst, mid in meta["trace"].items():
        try:
            ok, res = AtlasResultsRequest(msm_id=mid).create()
        except Exception as e:
            print(f"  trace -> {plabel(int(dst))}: {e}"); continue
        if not ok: continue
        for r in res:
            try:
                pr = TracerouteResult.get(r); v, _ = ms.classify_trace(pr)
            except Exception:
                continue
            ts = r.get("timestamp", 0); src = r.get("prb_id")
            rows.append(dict(
                ts_utc=datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                ts_pkt=pkt(datetime.fromtimestamp(ts, timezone.utc)).strftime("%Y-%m-%d %H:%M:%S"),
                kind="trace", src_probe_id=src, src=plabel(src),
                dst_probe_id=int(dst), dst=P[dst]["label"],
                rtt_min="", loss="",
                hop_count=(_hopcount(pr) if src not in HOP_EXCLUDE and int(dst) not in HOP_EXCLUDE else ""),
                tromboned=(v["status"] in ("trombone_hop", "trombone_rtt")),
                status=v["status"], exit_cc=v["exit_country"], transit=v["transit_name"],
                trace_rtt_ms=v["max_rtt_ms"]))
            key = (str(src), dst)
            if key not in latest_trace or ts > latest_trace[key][0]:
                latest_trace[key] = (ts, src, dst, pr, v)

    if not rows:
        print("no results yet (first round lands ~an interval after schedule)."); return
    rows.sort(key=lambda x: (x["dst"], str(x["src"]), x["ts_utc"]))
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    cols = ["ts_utc", "ts_pkt", "kind", "src_probe_id", "src", "dst_probe_id", "dst",
            "rtt_min", "loss", "hop_count", "tromboned", "status", "exit_cc", "transit", "trace_rtt_ms"]
    if stable:
        for old in glob.glob(os.path.join(OUT, "panel_*.csv")): os.remove(old)
        out_csv = os.path.join(OUT, f"panel_{ts}.csv")
    else:
        out_csv = os.path.join(OUT, f"panel_updated_{ts}.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    lines = [f"Exp 12 - latest traceroute per directed pair  [{len(latest_trace)} pairs]",
             "TCP/80 Paris. VERDICT from the same RTT-physics detector as Exp 04/07/11.", ""]
    for _, (t, src, dst, pr, v) in sorted(latest_trace.items(),
                                          key=lambda kv: (kv[1][2], str(kv[1][1]))):
        when = pkt(datetime.fromtimestamp(t, timezone.utc))
        lines.append("=" * 84)
        lines.append(f" {plabel(src)} -> {P[dst]['label']}   {when:%Y-%m-%d %H:%M} PKT")
        lines.append(f" VERDICT {v['status'].upper()}  exit={v['exit_country'] or '-'}  "
                     f"transit={v['transit_name']}  maxRTT={v['max_rtt_ms']}ms")
        lines.append("-" * 84)
        lines.append("  hop   rtt(ms)   ip")
        for hop in pr.hops:
            ipx = next((p.origin for p in hop.packets if p.origin), None)
            rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
            if not ipx:
                lines.append(f"  {hop.index:>3}      *      (no response)"); continue
            lines.append(f"  {hop.index:>3}   {('%.1f' % rtt) if rtt is not None else '':>7}   {ipx:<16}")
        lines.append("")
    if stable:
        for old in glob.glob(os.path.join(OUT, "routes_*.txt")): os.remove(old)
        out_txt = os.path.join(OUT, f"routes_{ts}.txt")
    else:
        out_txt = os.path.join(OUT, f"routes_updated_{ts}.txt")
    open(out_txt, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    nping = sum(1 for x in rows if x["kind"] == "ping"); ntr = len(rows) - nping
    print(f"[{datetime.now():%H:%M:%S}] rows: {len(rows)} (ping {nping}, trace {ntr}) "
          f"-> {os.path.basename(out_csv)} + {os.path.basename(out_txt)}")


def watch():
    """Background loop: fetch every WATCH_EVERY seconds until the run window ends. No git."""
    meta = json.load(open(MJSON))
    stop_at = datetime.fromisoformat(meta["stop"].rstrip("Z")).replace(tzinfo=timezone.utc)
    print(f"watch: fetching every {WATCH_EVERY // 60} min until {pkt(stop_at):%Y-%m-%d %H:%M} PKT. Ctrl-C to stop.")
    while True:
        try:
            fetch(stable=True)
        except Exception as e:
            print(f"  fetch error: {e}")
        if datetime.now(timezone.utc) >= stop_at + timedelta(hours=1):
            print("watch: run window ended; final fetch done."); break
        time.sleep(WATCH_EVERY)


def check():
    """Daily health report -- run this once a day. No credits spent (reads only).
    Prints a report and writes results/health_<date>.md."""
    meta = json.load(open(MJSON))
    global ROSTER_LABELS
    ROSTER_LABELS.update({int(pid): info["label"] for pid, info in meta["probes"].items()})
    now = datetime.now(timezone.utc)
    start = datetime.fromisoformat(meta["created"].rstrip("Z")).replace(tzinfo=timezone.utc)
    stop_at = datetime.fromisoformat(meta["stop"].rstrip("Z")).replace(tzinfo=timezone.utc)
    elapsed_h = max(0.0, (min(now, stop_at) - start).total_seconds() / 3600)
    n_sources = len(meta["probes"]) - 1
    lines = [f"# Exp 12 mesh panel — health check {pkt(now):%Y-%m-%d %H:%M} PKT", ""]

    # 1. Roster drift
    active_now = discover_probes()
    scheduled = {int(pid) for pid in meta["probes"]}
    dropped = scheduled - set(active_now)
    lines.append("## Roster")
    lines.append(f"- scheduled with {len(scheduled)} probes; {len(set(active_now) & scheduled)} still Connected now.")
    if dropped:
        lines.append("- ⚠ DROPPED since schedule (no longer Connected — will silently "
                     "stop contributing/receiving results): "
                     + ", ".join(label(p) for p in sorted(dropped)))
    else:
        lines.append("- ✅ no probes have dropped off since schedule.")

    # 2. Per-measurement liveness + 3. loss outliers (single pass over each measurement's results)
    lines.append("\n## Measurement liveness")
    problems = []
    pair_loss = {}   # (kind, src, dst) -> [loss values] for the outlier pass (ping only)
    for kind, interval_s in (("ping", meta["ping_interval"]), ("trace", meta["trace_interval"])):
        expected_rounds = max(1, int(elapsed_h * 3600 / interval_s))
        expected_n = expected_rounds * n_sources
        for dst, mid in meta[kind].items():
            try:
                status = requests.get(f"https://atlas.ripe.net/api/v2/measurements/{mid}/",
                                      timeout=20).json().get("status", {}).get("name", "?")
            except Exception as e:
                status = f"ERR({e})"
            try:
                ok, res = AtlasResultsRequest(msm_id=mid, start=start).create()
            except Exception:
                ok, res = False, None
            res = res or []
            n = len(res)
            last_ts = max((r.get("timestamp", 0) for r in res), default=0)
            stale_h = (now.timestamp() - last_ts) / 3600 if last_ts else None
            pct = (n / expected_n * 100) if expected_n else 0
            dst_label = label(int(dst))
            flag = ""
            if status not in ("Ongoing", "Stopped"):
                flag = f"⚠ status={status}"
            elif stale_h is not None and stale_h > 2 * interval_s / 3600:
                flag = f"⚠ stale ({stale_h:.1f}h since last result)"
            elif n_sources and pct < 70:
                flag = f"⚠ only {pct:.0f}% of expected results so far"
            if flag:
                problems.append(f"  {kind:5} -> {dst_label:<16} {flag}  (status={status}, {n}/{expected_n} results)")
            if kind == "ping":
                for r in res:
                    try:
                        pg = PingResult.get(r)
                    except Exception:
                        continue
                    sent = pg.packets_sent or 0
                    if not sent:
                        continue
                    loss = 1 - (pg.packets_received or 0) / sent
                    pair_loss.setdefault((r.get("prb_id"), int(dst)), []).append(loss)
    if problems:
        lines.append(f"⚠ {len(problems)} measurement(s) need attention:")
        lines.extend(problems)
    else:
        lines.append("✅ all measurements Ongoing, fresh, and at/near expected volume.")

    lines.append("\n## Loss outliers (ping, vs. fleet average)")
    if pair_loss:
        avg_by_pair = {k: sum(v) / len(v) for k, v in pair_loss.items()}
        fleet_avg = sum(avg_by_pair.values()) / len(avg_by_pair)
        outliers = sorted(((k, v) for k, v in avg_by_pair.items() if v >= max(0.1, fleet_avg + 0.2)),
                          key=lambda kv: -kv[1])
        if outliers:
            lines.append(f"fleet-average loss {fleet_avg:.1%}; {len(outliers)} pair(s) well above it:")
            for (src, dst), loss in outliers[:20]:
                lines.append(f"  {label(src):<16} -> {label(dst):<16} loss={loss:.1%}")
        else:
            lines.append(f"✅ no pair stands out (fleet-average loss {fleet_avg:.1%}).")
    else:
        lines.append("(no ping results yet)")

    # 4. Quota
    running = running_measurements()
    lines.append(f"\n## Quota\n- currently {running} running measurements on this account "
                f"(cap {PARALLEL_CAP}).")

    n_issues = len(problems) + (len(outliers) if pair_loss and outliers else 0) + len(dropped)
    lines.insert(1, f"**Verdict: {'✅ all clear' if n_issues == 0 else f'⚠ {n_issues} item(s) need attention'}**\n")

    report = "\n".join(lines)
    print(report)
    outp = os.path.join(OUT, f"health_{now:%Y%m%d}.md")
    open(outp, "w", encoding="utf-8").write(report + "\n")
    print(f"\n[saved {outp}]")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    {"list": list_probes, "schedule": schedule, "watch": watch, "fetch": fetch,
     "check": check, "stop": stop}.get(cmd, list_probes)()
