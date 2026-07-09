#!/usr/bin/env python3
"""
Exp 07 - PKIX-underuse longitudinal panel monitor.

All connected Pakistani probes (discovered live) -> targets from targets.csv, via
server-side RIPE *periodic* measurements: TCP/80 Paris traceroute every 60 min + ping
every 30 min, for 7 days. Runs on an external server; collection is server-side so the
watch loop can restart freely. LOCAL ONLY - this tool never touches git.

    python panel_monitor.py schedule     # discover probes, read targets.csv, register measurements (7-day window)
    nohup python panel_monitor.py watch & # background: fetch every 30 min -> panel CSV + routes txt
    python panel_monitor.py fetch         # one-off pull
    python panel_monitor.py stop          # stop measurements early

Config: the CONFIG block at the top (frequencies in minutes, duration in days). Env vars
RIPE_API_KEY, DURATION_DAYS, TRACEROUTE_EVERY_MIN, PING_EVERY_MIN, WATCH_EVERY_MIN,
PANEL_TRACE_ONLY override it.
"""
import os, sys, csv, json, time, socket, glob
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results"); os.makedirs(OUT, exist_ok=True)
MJSON = os.path.join(OUT, "measurements.json")
TARGETS_CSV = os.path.join(HERE, "targets.csv")

sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "measurement"))
import pk_multi_probe as pk
sys.path.insert(0, os.path.join(HERE, "..", "04.1_small_isp_tromboning"))
import census_sweep as cs
import requests
from ripe.atlas.cousteau import (Traceroute, Ping, AtlasSource, AtlasCreateRequest,
                                 AtlasStopRequest, AtlasResultsRequest)
from ripe.atlas.sagan import TracerouteResult, PingResult

# ============================ CONFIG — edit these ============================
TRACEROUTE_EVERY_MIN = 60      # run one traceroute per target every N minutes
PING_EVERY_MIN       = 30      # run one ping per target every N minutes
DURATION_DAYS        = 7       # how many days the whole run lasts
WATCH_EVERY_MIN      = 30      # how often the `watch` loop pulls new results
TRACE_ONLY           = False   # True = skip pings (halves the measurement count; fits RIPE caps)
# (env vars TRACEROUTE_EVERY_MIN / PING_EVERY_MIN / DURATION_DAYS / WATCH_EVERY_MIN /
#  PANEL_TRACE_ONLY override the values above if set, e.g. for the server.)
# ============================================================================
TRACEROUTE_EVERY_MIN = int(os.environ.get("TRACEROUTE_EVERY_MIN", TRACEROUTE_EVERY_MIN))
PING_EVERY_MIN       = int(os.environ.get("PING_EVERY_MIN", PING_EVERY_MIN))
DURATION_DAYS        = float(os.environ.get("DURATION_DAYS", DURATION_DAYS))
WATCH_EVERY_MIN      = int(os.environ.get("WATCH_EVERY_MIN", WATCH_EVERY_MIN))
TRACE_ONLY           = (os.environ.get("PANEL_TRACE_ONLY", "1" if TRACE_ONLY else "0") == "1")
TRACE_INTERVAL = TRACEROUTE_EVERY_MIN * 60     # seconds (RIPE expects seconds)
PING_INTERVAL  = PING_EVERY_MIN * 60
WATCH_EVERY    = WATCH_EVERY_MIN * 60
RIPE_PROBES    = "https://atlas.ripe.net/api/v2/probes/"
HOP_EXCLUDE    = {7764, 62224, 1015210}  # ICMP-filtered / Docker-opaque: hop counts unreliable
PK_ASN = {17557: "ptcl", 45595: "ptcl-bb", 38193: "transworld", 135407: "tes", 9541: "cybernet",
          23674: "nayatel", 136174: "nova", 150683: "fasttel", 151983: "orbit", 152605: "zcom",
          38264: "wateen", 9260: "multinet", 23888: "ntc", 45773: "pern"}


def pkt(dt): return dt + timedelta(hours=5)   # Pakistan Standard Time = UTC+5


def discover_probes():
    """All connected Pakistani probes, live. -> {id: 'isp.id'}"""
    probes, url = {}, RIPE_PROBES
    params = {"country_code": "PK", "status": 1, "fields": "id,asn_v4", "page_size": 100}
    while url:
        j = requests.get(url, params=params, timeout=30).json(); params = None
        for p in j.get("results", []):
            a = p.get("asn_v4")
            probes[p["id"]] = f"{PK_ASN.get(a, 'AS'+str(a))}.{p['id']}"
        url = j.get("next")
    return probes


def load_targets():
    """Read targets.csv (class,target); resolve hostnames -> (class, host, ip)."""
    out = []
    if not os.path.exists(TARGETS_CSV):
        print(f"ERROR: {TARGETS_CSV} not found."); return out
    for r in csv.DictReader(open(TARGETS_CSV, encoding="utf-8")):
        cls, tgt = (r.get("class") or "").strip(), (r.get("target") or "").strip()
        if cls.startswith("#") or not tgt or tgt.startswith("#"):
            continue
        try:
            ip = tgt if tgt.replace(".", "").isdigit() else socket.gethostbyname(tgt)
        except Exception:
            print(f"  skip {tgt} (no DNS)"); continue
        out.append((cls or "?", tgt, ip))
    return out


def running_measurements():
    """Current count of the account's ongoing measurements (for the preflight check)."""
    try:
        r = requests.get("https://atlas.ripe.net/api/v2/measurements/my/",
                         params={"status": 2, "page_size": 1},
                         headers={"Authorization": "Key " + pk.API_KEY}, timeout=20)
        return r.json().get("count", 0) if r.ok else 0
    except Exception:
        return -1


def schedule():
    if os.path.exists(MJSON):
        print("measurements.json exists - stop/remove before re-scheduling."); return
    probes = discover_probes()
    targets = load_targets()
    if not probes or not targets:
        print("need probes and targets to schedule."); return

    # --- preflight: don't half-create a run that busts the parallel-measurement cap ---
    ntypes = 1 if TRACE_ONLY else 2
    n_new = len(targets) * ntypes
    cap = int(os.environ.get("PANEL_PARALLEL_CAP", "100"))
    running = running_measurements()
    print(f"plan: {len(targets)} targets x {ntypes} type(s) = {n_new} measurements to {len(probes)} "
          f"probes; currently {running} running; parallel cap = {cap}.")
    if running >= 0 and running + n_new > cap and os.environ.get("PANEL_FORCE") != "1":
        print(f"ABORT: {running} + {n_new} exceeds the {cap} parallel-measurement cap. Options:\n"
              f"  - wait for the RIPE limit increase, then set PANEL_PARALLEL_CAP={running + n_new} and re-run;\n"
              f"  - set TRACE_ONLY=True in CONFIG (halves to {len(targets)} measurements);\n"
              f"  - PANEL_FORCE=1 to proceed anyway (excess measurements will be rejected by RIPE).")
        return

    src = AtlasSource(type="probes", value=",".join(str(p) for p in probes), requested=len(probes))
    start = datetime.utcnow() + timedelta(minutes=1)
    stop = start + timedelta(days=DURATION_DAYS)
    meta = {"created": start.isoformat() + "Z", "stop": stop.isoformat() + "Z",
            "trace_interval": TRACE_INTERVAL, "ping_interval": PING_INTERVAL,
            "probes": {str(k): v for k, v in probes.items()},
            "trace": {}, "ping": {}, "ip": {}, "class": {}}
    print(f"scheduling {len(targets)} targets x (trace+ping) to {len(probes)} probes, "
          f"{DURATION_DAYS:g}-day window...")
    for cls, host, ip in targets:
        meta["ip"][host] = ip; meta["class"][host] = cls
        tr = Traceroute(af=4, target=ip, protocol="TCP", port=80, paris=16, packets=3,
                        interval=TRACE_INTERVAL, description=f"exp07 trace {cls} {host}")
        pg = Ping(af=4, target=ip, packets=3, interval=PING_INTERVAL,
                  description=f"exp07 ping {cls} {host}")
        specs = [("trace", tr)] + ([] if TRACE_ONLY else [("ping", pg)])
        for kind, spec in specs:
            ok, resp = AtlasCreateRequest(key=pk.API_KEY, measurements=[spec], sources=[src],
                                          is_oneoff=False, start_time=start, stop_time=stop).create()
            if ok:
                meta[kind][host] = resp["measurements"][0]
                print(f"  {kind:5} {cls:9} {host:28} -> msm {resp['measurements'][0]}")
            else:
                print(f"  FAIL {kind} {host}: {resp}")
    json.dump(meta, open(MJSON, "w"), indent=2)
    print(f"\nscheduled {len(meta['trace'])+len(meta['ping'])} periodic measurements until "
          f"{pkt(stop):%Y-%m-%d %H:%M} PKT. saved {MJSON}")


def stop():
    meta = json.load(open(MJSON))
    for kind in ("trace", "ping"):
        for host, mid in meta[kind].items():
            try:
                AtlasStopRequest(msm_id=mid, key=pk.API_KEY).create(); print(f"  stopped {mid} ({host})")
            except Exception as e:
                print(f"  {mid}: {e}")


def _hopcount(pr):
    last = 0
    for hop in pr.hops:
        if any(p.origin for p in hop.packets):
            last = hop.index
    return last


def fetch():
    """Pull all results so far -> panel_<ts>.csv (rewritten) + routes_<ts>.txt."""
    meta = json.load(open(MJSON))
    P = meta["probes"]
    rows, latest_trace = [], {}   # panel rows; latest trace per (probe,host) for routes txt
    for host, mid in meta["ping"].items():
        cls = meta["class"][host]
        try:
            ok, res = AtlasResultsRequest(msm_id=mid).create()
        except Exception as e:
            print(f"  ping {host}: {e}"); continue
        if not ok: continue
        for r in res:
            try: pg = PingResult.get(r)
            except Exception: continue
            ts = r.get("timestamp", 0); sent = pg.packets_sent or 0; rcvd = pg.packets_received or 0
            rows.append(dict(ts_utc=datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                             ts_pkt=pkt(datetime.fromtimestamp(ts, timezone.utc)).strftime("%Y-%m-%d %H:%M:%S"),
                             kind="ping", probe_id=r.get("prb_id"), probe=P.get(str(r.get("prb_id")), r.get("prb_id")),
                             target=host, cls=cls, rtt_min=(round(pg.rtt_min, 1) if pg.rtt_min is not None else ""),
                             loss=(round(1 - rcvd / sent, 3) if sent else ""), hop_count="", tromboned="",
                             exit_cc="", transit=""))
    for host, mid in meta["trace"].items():
        cls = meta["class"][host]
        try:
            ok, res = AtlasResultsRequest(msm_id=mid).create()
        except Exception as e:
            print(f"  trace {host}: {e}"); continue
        if not ok: continue
        for r in res:
            try:
                pr = TracerouteResult.get(r); v = cs.classify(r, "0")
            except Exception:
                continue
            ts = r.get("timestamp", 0); prb = r.get("prb_id")
            rows.append(dict(ts_utc=datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                             ts_pkt=pkt(datetime.fromtimestamp(ts, timezone.utc)).strftime("%Y-%m-%d %H:%M:%S"),
                             kind="trace", probe_id=prb, probe=P.get(str(prb), prb), target=host, cls=cls,
                             rtt_min="", loss="", hop_count=(_hopcount(pr) if prb not in HOP_EXCLUDE else ""),
                             tromboned=(v["status"] == "trombone"), exit_cc=v["exit_cc"], transit=v["transit"]))
            key = (str(P.get(str(prb), prb)), host)
            if key not in latest_trace or ts > latest_trace[key][0]:
                latest_trace[key] = (ts, cls, host, prb, pr, v)

    if not rows:
        print("no results yet (first round lands ~an interval after schedule)."); return
    rows.sort(key=lambda x: (x["target"], str(x["probe"]), x["ts_utc"]))
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    cols = ["ts_utc", "ts_pkt", "kind", "probe_id", "probe", "target", "cls", "rtt_min", "loss",
            "hop_count", "tromboned", "exit_cc", "transit"]
    # rewrite a single current panel file (keep it stable across watch cycles)
    for old in glob.glob(os.path.join(OUT, "panel_*.csv")):
        os.remove(old)
    out_csv = os.path.join(OUT, f"panel_{ts}.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    # routes txt (standing rule): latest trace per (probe, target)
    lines = [f"Exp 07 - latest traceroute per (probe, target)  [{len(latest_trace)} traces]",
             "TCP/80 Paris. '<<< high RTT' = hop >=40ms (likely off-PK). VERDICT from RTT-physics.", ""]
    for _, (t, cls, host, prb, pr, v) in sorted(latest_trace.items(), key=lambda kv: (kv[1][1], kv[1][2], str(kv[0][0]))):
        when = pkt(datetime.fromtimestamp(t, timezone.utc))
        lines.append("=" * 84)
        lines.append(f" [{cls}] {host} -> {meta['ip'][host]}    probe {prb} - {P.get(str(prb), prb)}   {when:%Y-%m-%d %H:%M} PKT")
        lines.append(f" VERDICT {v['status'].upper()}  exit={v['exit_cc'] or '-'}  transit={v['transit']}  maxRTT={v['max_rtt']}ms")
        lines.append("-" * 84)
        lines.append("  hop   rtt(ms)   ip")
        for hop in pr.hops:
            ipx = next((p.origin for p in hop.packets if p.origin), None)
            rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
            if not ipx:
                lines.append(f"  {hop.index:>3}      *      (no response)"); continue
            mark = ("   <<< high RTT" if (rtt is not None and not cs.pk.PRIVATE(ipx)
                    and cs.FOREIGN_RTT_FLOOR <= rtt <= cs.QUEUE_CEIL) else "")
            lines.append(f"  {hop.index:>3}   {('%.1f'%rtt) if rtt is not None else '':>7}   {ipx:<16}{mark}")
        lines.append("")
    for old in glob.glob(os.path.join(OUT, "routes_*.txt")):
        os.remove(old)
    out_txt = os.path.join(OUT, f"routes_{ts}.txt")
    open(out_txt, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    nping = sum(1 for x in rows if x["kind"] == "ping"); ntr = len(rows) - nping
    rounds = len({x["ts_utc"][:13] for x in rows})
    print(f"[{datetime.now():%H:%M:%S}] rows: {len(rows)} (ping {nping}, trace {ntr}), ~{rounds} hourly buckets "
          f"-> {os.path.basename(out_csv)} + {os.path.basename(out_txt)}")


def watch():
    """Background loop: fetch every WATCH_EVERY seconds until the run window ends. No git."""
    meta = json.load(open(MJSON))
    stop_at = datetime.fromisoformat(meta["stop"].rstrip("Z")).replace(tzinfo=timezone.utc)
    print(f"watch: fetching every {WATCH_EVERY//60} min until {pkt(stop_at):%Y-%m-%d %H:%M} PKT. Ctrl-C to stop.")
    while True:
        try:
            fetch()
        except Exception as e:
            print(f"  fetch error: {e}")
        if datetime.now(timezone.utc) >= stop_at + timedelta(hours=1):
            print("watch: run window ended; final fetch done."); break
        time.sleep(WATCH_EVERY)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    {"schedule": schedule, "watch": watch, "fetch": fetch, "stop": stop}.get(cmd, fetch)()
