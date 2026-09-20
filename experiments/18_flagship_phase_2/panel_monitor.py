#!/usr/bin/env python3
"""
Exp 18 - flagship phase 2 (replication and extension of Exp 07).

Same design as Exp 07 (every connected Pakistani RIPE Atlas probe, a TCP/80 Paris traceroute every
60 min and a ping every 30 min, for 7 days, as server-side periodic measurements) on 150 sites:
the original 100 sites plus 50 new ones. Standalone, it imports nothing from other
experiments.

This collector stores RAW FACTS ONLY. There is no trombone / local / inconclusive label here.
Classify offline later from the raw dump (dump_raw.py).

How each site is looked up (column `resolve` in the targets file):
    probe  (default, used for every site) each probe looks the site up itself, so it traces to
           the server its own ISP's users are sent to. The IP each probe actually used is saved
           in the dst_ip column.
    fixed  optional: every probe traces to one IP, taken from the `validated_ip` column or looked
           up once with public resolvers (8.8.8.8 then 1.1.1.1), never the machine's own resolver.

A round where the lookup or the trace fails is kept as a row with the reason in the `error`
column. Every probe tries again at the next round (hourly), so nothing is dropped or guessed.

    python panel_monitor.py schedule     # place the standing orders (once per account)
    python panel_monitor.py watch        # background: collect every 30 min
    python panel_monitor.py fetch        # one-off collect
    python panel_monitor.py stop         # cancel early

Settings (environment variables):
    PANEL_ACCOUNT         which account pays: saqib, rayan or anan. Uses that account's key
                          from the RIPE_KEY_<NAME> line of .env
    PANEL_RIPE_KEY        alternative: the API key itself
    PANEL_INSTANCE        results sub-folder name (defaults to the account name)
    TARGETS_FILE          which site list to use (default: site_collection/targets_exp18_all150.csv)
    PANEL_TRACE_ONLY=1    only traceroutes
    PANEL_PING_ONLY=1     only pings
    PANEL_PARALLEL_CAP    the account's parallel-measurement cap (default 100)
    TRACEROUTE_EVERY_MIN, PING_EVERY_MIN, DURATION_DAYS, WATCH_EVERY_MIN

Probes 7764, 62224 and 1015210 filter ICMP, so their hop counts are unreliable. They are kept in
the data; exclude them at analysis time.
"""
import os, sys, csv, json, time, glob
from datetime import datetime, timezone, timedelta

import requests
import dns.resolver
from dotenv import load_dotenv
from ripe.atlas.cousteau import (Traceroute, Ping, AtlasSource, AtlasCreateRequest,
                                 AtlasStopRequest, AtlasResultsRequest)
from ripe.atlas.sagan import TracerouteResult, PingResult

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, "..", "..", ".env"))

INSTANCE = os.environ.get("PANEL_INSTANCE", "").strip() or os.environ.get("PANEL_ACCOUNT", "").strip().lower()
OUT = os.path.join(HERE, "results", INSTANCE) if INSTANCE else os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)
MJSON = os.path.join(OUT, "measurements.json")
TARGETS_CSV = os.environ.get(
    "TARGETS_FILE",
    os.path.join(HERE, "..", "..", "site_collection", "targets_exp18_all150.csv"))

# ============================ CONFIG ============================
TRACEROUTE_EVERY_MIN = int(os.environ.get("TRACEROUTE_EVERY_MIN", 60))
PING_EVERY_MIN       = int(os.environ.get("PING_EVERY_MIN", 30))
DURATION_DAYS        = float(os.environ.get("DURATION_DAYS", 7))
WATCH_EVERY_MIN      = int(os.environ.get("WATCH_EVERY_MIN", 30))
TRACE_ONLY           = os.environ.get("PANEL_TRACE_ONLY", "0") == "1"
PING_ONLY            = os.environ.get("PANEL_PING_ONLY", "0") == "1"
TRACE_PORT           = 80
PUBLIC_DNS           = ["8.8.8.8", "1.1.1.1"]
# ================================================================

ACCOUNT = os.environ.get("PANEL_ACCOUNT", "").strip().lower()
if ACCOUNT:   # e.g. PANEL_ACCOUNT=saqib uses the RIPE_KEY_SAQIB line of .env, with no fallback to another key
    KEY = (os.environ.get(f"RIPE_KEY_{ACCOUNT.upper()}") or "").strip() or None
    KEY_SOURCE = f".env RIPE_KEY_{ACCOUNT.upper()}"
else:
    KEY = os.environ.get("PANEL_RIPE_KEY") or os.environ.get("RIPE_API_KEY")
    KEY_SOURCE = "PANEL_RIPE_KEY" if os.environ.get("PANEL_RIPE_KEY") else ".env RIPE_API_KEY"
TRACE_INTERVAL = TRACEROUTE_EVERY_MIN * 60   # RIPE expects seconds
PING_INTERVAL  = PING_EVERY_MIN * 60
WATCH_EVERY    = WATCH_EVERY_MIN * 60
RIPE_PROBES    = "https://atlas.ripe.net/api/v2/probes/"
PK_ASN = {17557: "ptcl", 45595: "ptcl-bb", 38193: "transworld", 135407: "tes", 9541: "cybernet",
          23674: "nayatel", 136174: "nova", 150683: "fasttel", 151983: "orbit", 152605: "zcom",
          38264: "wateen", 9260: "multinet", 23888: "ntc", 45773: "pern"}


def pkt(dt):
    return dt + timedelta(hours=5)   # Pakistan Standard Time = UTC+5


def discover_probes():
    """All connected Pakistani probes, live. -> {id: 'isp.id'}"""
    probes, url = {}, RIPE_PROBES
    params = {"country_code": "PK", "status": 1, "fields": "id,asn_v4", "page_size": 100}
    while url:
        j = requests.get(url, params=params, timeout=30).json()
        params = None
        for p in j.get("results", []):
            a = p.get("asn_v4")
            probes[p["id"]] = f"{PK_ASN.get(a, 'AS' + str(a))}.{p['id']}"
        url = j.get("next")
    return probes


def public_lookup(host):
    """A-record answers from public resolvers only. Returns a list of IPs, one per answering resolver."""
    got = []
    for ns in PUBLIC_DNS:
        r = dns.resolver.Resolver(configure=False)
        r.nameservers = [ns]
        r.timeout = r.lifetime = 6
        for _ in range(2):
            try:
                got.append(r.resolve(host, "A")[0].to_text())
                break
            except Exception:
                pass
    return got


def load_targets():
    """Read the targets file -> [(class, host, ip, mode)].
    mode 'probe': ip is '' (each probe resolves the name itself).
    mode 'fixed': ip is the validated_ip column, or a one-off public-resolver lookup."""
    out = []
    if not os.path.exists(TARGETS_CSV):
        print(f"ERROR: {TARGETS_CSV} not found.")
        return out
    for r in csv.DictReader(open(TARGETS_CSV, encoding="utf-8")):
        cls, tgt = (r.get("class") or "").strip(), (r.get("target") or "").strip()
        if cls.startswith("#") or not tgt or tgt.startswith("#"):
            continue
        mode = (r.get("resolve") or "").strip().lower()
        if mode not in ("probe", "fixed"):
            mode = "probe"
        ip = ""
        if mode == "fixed":
            ip = (r.get("validated_ip") or "").strip()
            if not ip:
                if tgt.replace(".", "").isdigit():
                    ip = tgt
                else:
                    got = public_lookup(tgt)
                    if not got:
                        print(f"  skip {tgt} (public resolvers gave no answer)")
                        continue
                    ip = got[0]
                    if len({x.rsplit('.', 1)[0] for x in got}) > 1:
                        print(f"  CHECK {tgt}: resolvers disagree {got}, using {ip}")
        out.append((cls or "?", tgt, ip, mode))
    return out


def running_measurements():
    """How many measurements this account is running right now (for the preflight check)."""
    try:
        r = requests.get("https://atlas.ripe.net/api/v2/measurements/my/",
                         params={"status": 2, "page_size": 1},
                         headers={"Authorization": "Key " + KEY}, timeout=20)
        return r.json().get("count", 0) if r.ok else 0
    except Exception:
        return -1


def account_credits():
    try:
        r = requests.get("https://atlas.ripe.net/api/v2/credits/",
                         headers={"Authorization": "Key " + KEY}, timeout=20)
        return r.json().get("current_balance") if r.ok else None
    except Exception:
        return None


def schedule():
    if not KEY:
        print(f"no API key found from {KEY_SOURCE}: paste the key into .env, then run again."); return
    if os.path.exists(MJSON):
        print("measurements.json exists - stop/remove before re-scheduling."); return
    probes = discover_probes()
    targets = load_targets()
    if not probes or not targets:
        print("need probes and targets to schedule."); return

    ntypes = 1 if (TRACE_ONLY or PING_ONLY) else 2
    n_new = len(targets) * ntypes
    cap = int(os.environ.get("PANEL_PARALLEL_CAP", "100"))
    running = running_measurements()
    n_probe = sum(1 for t in targets if t[3] == "probe")
    bal = account_credits()
    print(f"API key from {KEY_SOURCE}; credits in this account: "
          f"{f'{bal:,}' if isinstance(bal, int) else 'unknown (key rejected?)'}; results go to {OUT}")
    print(f"plan: {len(targets)} targets ({n_probe} looked up by each probe, {len(targets) - n_probe} fixed IP) "
          f"x {ntypes} type(s) = {n_new} measurements to {len(probes)} probes; "
          f"currently {running} running; parallel cap = {cap}.")
    if running >= 0 and running + n_new > cap and os.environ.get("PANEL_FORCE") != "1":
        print(f"ABORT: {running} + {n_new} exceeds the {cap} parallel-measurement cap. "
              f"Use fewer sites or another account (PANEL_FORCE=1 overrides).")
        return

    if os.environ.get("PANEL_YES") != "1":
        if input("Type START to place these orders and begin the 7-day run: ").strip() != "START":
            print("cancelled, nothing scheduled."); return

    src = AtlasSource(type="probes", value=",".join(str(p) for p in probes), requested=len(probes))
    start = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=1)
    stop_t = start + timedelta(days=DURATION_DAYS)
    meta = {"created": start.isoformat() + "Z", "stop": stop_t.isoformat() + "Z",
            "trace_interval": TRACE_INTERVAL, "ping_interval": PING_INTERVAL, "trace_port": TRACE_PORT,
            "probes": {str(k): v for k, v in probes.items()},
            "trace": {}, "ping": {}, "ip": {}, "mode": {}, "class": {}}
    for cls, host, ip, mode in targets:
        meta["ip"][host] = ip
        meta["mode"][host] = mode
        meta["class"][host] = cls
        tgt = host if mode == "probe" else ip
        extra = {"resolve_on_probe": True} if mode == "probe" else {}
        tr = Traceroute(af=4, target=tgt, protocol="TCP", port=TRACE_PORT, paris=16, packets=3,
                        interval=TRACE_INTERVAL, description=f"exp18 trace {cls} {host}", **extra)
        pg = Ping(af=4, target=tgt, packets=3, interval=PING_INTERVAL,
                  description=f"exp18 ping {cls} {host}", **extra)
        specs = ([("ping", pg)] if PING_ONLY else
                 [("trace", tr)] if TRACE_ONLY else
                 [("trace", tr), ("ping", pg)])
        for kind, spec in specs:
            ok, resp = AtlasCreateRequest(key=KEY, measurements=[spec], sources=[src],
                                          is_oneoff=False, start_time=start, stop_time=stop_t).create()
            if ok:
                meta[kind][host] = resp["measurements"][0]
                print(f"  {kind:5} {cls:11} {mode:5} {host:28} -> msm {resp['measurements'][0]}")
            else:
                print(f"  FAIL {kind} {host}: {resp}")
    json.dump(meta, open(MJSON, "w"), indent=2)
    print(f"\nscheduled {len(meta['trace']) + len(meta['ping'])} periodic measurements until "
          f"{pkt(stop_t):%Y-%m-%d %H:%M} PKT. saved {MJSON}")


def stop():
    if not KEY:
        print("no API key: set PANEL_RIPE_KEY."); return
    meta = json.load(open(MJSON))
    for kind in ("trace", "ping"):
        for host, mid in meta[kind].items():
            try:
                AtlasStopRequest(msm_id=mid, key=KEY).create()
                print(f"  stopped {mid} ({host})")
            except Exception as e:
                print(f"  {mid}: {e}")


def trace_facts(pr, r):
    """Raw facts from one traceroute result. No verdict."""
    dst = r.get("dst_addr") or ""
    hop_count, last_ip, last_rtt, dest_rtt, rtts = 0, "", "", "", []
    for hop in pr.hops:
        got = [p for p in hop.packets if p.origin]
        if not got:
            continue
        rtt = min((p.rtt for p in got if p.rtt is not None), default=None)
        ip = got[0].origin
        if hop.index < 255:
            hop_count = hop.index
        last_ip = ip
        last_rtt = round(rtt, 1) if rtt is not None else ""
        if rtt is not None:
            rtts.append(rtt)
            if ip == dst:
                dest_rtt = round(rtt, 1)
    return dict(dst_ip=dst, hop_count=hop_count, dest_reached=bool(r.get("destination_ip_responded")),
                dest_rtt_ms=dest_rtt, last_hop_ip=last_ip, last_hop_rtt_ms=last_rtt,
                max_rtt_ms=round(max(rtts), 1) if rtts else "")


COLS = ["ts_utc", "ts_pkt", "kind", "probe_id", "probe", "target", "cls", "resolve", "dst_ip",
        "rtt_min", "loss", "hop_count", "dest_reached", "dest_rtt_ms", "last_hop_ip",
        "last_hop_rtt_ms", "max_rtt_ms", "error"]


def result_error(r, parsed=None):
    """Why a round failed, or ''. Checks the top-level error fields RIPE sets and the parsed result."""
    for k in ("error", "err", "dnserr"):
        v = r.get(k)
        if v:
            return str(v)[:120]
    if parsed is not None and getattr(parsed, "is_error", False):
        return (getattr(parsed, "error_message", "") or "error")[:120]
    return ""


def base_row(kind, r, host, meta):
    ts = r.get("timestamp", 0)
    prb = r.get("prb_id")
    d = {c: "" for c in COLS}
    d.update(ts_utc=datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
             ts_pkt=pkt(datetime.fromtimestamp(ts, timezone.utc)).strftime("%Y-%m-%d %H:%M:%S"),
             kind=kind, probe_id=prb, probe=meta["probes"].get(str(prb), prb), target=host,
             cls=meta["class"][host], resolve=meta.get("mode", {}).get(host, ""),
             dst_ip=r.get("dst_addr") or "", error=result_error(r))
    return d, ts, prb


def ping_row(r, host, meta):
    """One row per ping round. A failed or unreadable round is kept, with the reason in `error`."""
    d, _, _ = base_row("ping", r, host, meta)
    try:
        pg = PingResult.get(r)
    except Exception:
        d["error"] = d["error"] or "unparseable"
        return d
    d["error"] = d["error"] or result_error({}, pg)
    sent, rcvd = pg.packets_sent or 0, pg.packets_received or 0
    d.update(rtt_min=(round(pg.rtt_min, 1) if pg.rtt_min is not None else ""),
             loss=(round(1 - rcvd / sent, 3) if sent else ""))
    return d


def trace_row(r, host, meta):
    """One row per traceroute round -> (row, timestamp, probe_id, parsed result or None)."""
    d, ts, prb = base_row("trace", r, host, meta)
    try:
        pr = TracerouteResult.get(r)
    except Exception:
        d["error"] = d["error"] or "unparseable"
        return d, ts, prb, None
    d["error"] = d["error"] or result_error({}, pr)
    try:
        d.update(trace_facts(pr, r))
    except Exception:
        d["error"] = d["error"] or "no-hops"
    return d, ts, prb, pr


def fetch(stable=False):
    """Pull all results so far -> a panel CSV (raw facts) + routes txt.
    stable=True (used by watch): keep one current panel_<ts>.csv / routes_<ts>.txt.
    stable=False (manual one-off): never delete files, write panel_updated_<ts>.csv alongside."""
    meta = json.load(open(MJSON))
    P = meta["probes"]
    rows, latest_trace = [], {}

    for host, mid in meta["ping"].items():
        try:
            ok, res = AtlasResultsRequest(msm_id=mid).create()
        except Exception as e:
            print(f"  ping {host}: {e}"); continue
        if not ok:
            continue
        for r in res:
            rows.append(ping_row(r, host, meta))

    for host, mid in meta["trace"].items():
        try:
            ok, res = AtlasResultsRequest(msm_id=mid).create()
        except Exception as e:
            print(f"  trace {host}: {e}"); continue
        if not ok:
            continue
        for r in res:
            d, ts, prb, pr = trace_row(r, host, meta)
            rows.append(d)
            if pr is not None and not d["error"]:
                key = (str(P.get(str(prb), prb)), host)
                if key not in latest_trace or ts > latest_trace[key][0]:
                    latest_trace[key] = (ts, host, prb, pr, d["dst_ip"])

    if not rows:
        print("no results yet (first round lands about one interval after schedule)."); return
    rows.sort(key=lambda x: (x["target"], str(x["probe"]), x["ts_utc"]))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if stable:
        for old in glob.glob(os.path.join(OUT, "panel_*.csv")):
            os.remove(old)
        out_csv = os.path.join(OUT, f"panel_{stamp}.csv")
    else:
        out_csv = os.path.join(OUT, f"panel_updated_{stamp}.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)

    lines = [f"Exp 18 - latest traceroute per (probe, target)  [{len(latest_trace)} traces]",
             "TCP/80 Paris. Raw hops only, no verdict.", ""]
    for _, (t, host, prb, pr, dst) in sorted(latest_trace.items(), key=lambda kv: (kv[1][1], str(kv[0][0]))):
        when = pkt(datetime.fromtimestamp(t, timezone.utc))
        lines.append("=" * 84)
        lines.append(f" {host} -> {dst}   [{meta['class'][host]}, {meta.get('mode', {}).get(host, '')}]"
                     f"   probe {prb} - {P.get(str(prb), prb)}   {when:%Y-%m-%d %H:%M} PKT")
        lines.append("-" * 84)
        lines.append("  hop   rtt(ms)   ip")
        for hop in pr.hops:
            ipx = next((p.origin for p in hop.packets if p.origin), None)
            rtt = min([p.rtt for p in hop.packets if p.rtt is not None], default=None)
            if not ipx:
                lines.append(f"  {hop.index:>3}      *      (no response)")
                continue
            lines.append(f"  {hop.index:>3}   {('%.1f' % rtt) if rtt is not None else '':>7}   {ipx}")
        lines.append("")
    if stable:
        for old in glob.glob(os.path.join(OUT, "routes_*.txt")):
            os.remove(old)
        out_txt = os.path.join(OUT, f"routes_{stamp}.txt")
    else:
        out_txt = os.path.join(OUT, f"routes_updated_{stamp}.txt")
    open(out_txt, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    nping = sum(1 for x in rows if x["kind"] == "ping")
    nerr = sum(1 for x in rows if x["error"])
    print(f"[{datetime.now():%H:%M:%S}] rows: {len(rows)} (ping {nping}, trace {len(rows) - nping}, "
          f"failed rounds kept {nerr}) "
          f"-> {os.path.basename(out_csv)} + {os.path.basename(out_txt)}")


def watch():
    """Background loop: fetch every WATCH_EVERY seconds until the run window ends."""
    meta = json.load(open(MJSON))
    stop_at = datetime.fromisoformat(meta["stop"].rstrip("Z")).replace(tzinfo=timezone.utc)
    print(f"watch: fetching every {WATCH_EVERY // 60} min until {pkt(stop_at):%Y-%m-%d %H:%M} PKT. Ctrl-C to stop.")
    while True:
        try:
            fetch(stable=True)
        except Exception as e:
            print(f"  fetch error: {e}")
        if datetime.now(timezone.utc) >= stop_at + timedelta(hours=1):
            print("watch: run window ended; final fetch done.")
            break
        time.sleep(WATCH_EVERY)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    {"schedule": schedule, "watch": watch, "fetch": fetch, "stop": stop}.get(cmd, fetch)()
