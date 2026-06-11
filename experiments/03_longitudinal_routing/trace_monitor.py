#!/usr/bin/env python3
"""
Experiment 03 - Longitudinal Routing Monitor
============================================
From SEVERAL probes (one per PK ISP), traceroute the SAME destinations every 15
minutes for several days, and record whether the PATH and the RTT change over time
- per (site, probe), so you can compare ISPs.

Where Exp 01 is a one-off snapshot, this adds the time axis. It uses a RIPE Atlas
*periodic* measurement (one per target) so RIPE's own infrastructure fires every
15 min on schedule and the results persist server-side - fetch them whenever.

Methodology rationale (cadence, Paris traceroute, single-probe choice, metrics):
see `notes.md` in this folder. In short:
  - ICMP Paris traceroute (paris=16) so an observed path change is a REAL routing
    change, not a load-balancer artifact.
  - 15-min spacing (paper 2 used ~10 min): fine enough for path changes + the
    diurnal RTT curve, coarse enough to avoid noise.
  - around-the-clock for >=48-72h to capture the full day/night cycle.

Reuses Exp 01's helpers (ASN lookup, RDAP fallback, serving location) WITHOUT
modifying them - read-only import, same as Exp 1.1 / 1.2.

Run from the repo root:
    python experiments/03_longitudinal_routing/trace_monitor.py schedule
    python experiments/03_longitudinal_routing/trace_monitor.py fetch
    python experiments/03_longitudinal_routing/trace_monitor.py stop

Requires: RIPE_API_KEY in the environment / .env.
"""

import os
import sys
import csv
import json
import time
import subprocess
import statistics
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

# Reuse config + helpers from the main Exp 01 script (read-only).
sys.path.insert(0, os.path.join("scripts", "measurement"))
from pk_multi_probe import (                       # noqa: E402
    BASE, HDR, resolve, asn_for_ip, asn_name, registry_lookup, PRIVATE,
)
from geo_utils import serving_location             # noqa: E402

if "your-api-key-here" in HDR.get("Authorization", ""):
    sys.exit("RIPE_API_KEY not found. Put it in a .env file at the repo root.")

# ── CONFIG - edit before scheduling ───────────────────
RUN_NAME      = "run_20260611_24h"
INTERVAL_SEC  = 900          # 15 minutes between traceroutes (see notes.md for why 15)
DURATION_HOURS = 24          # full day -> ~96 rounds/site/probe, covers the diurnal cycle

# Optional ping companion (paper 2's design): 1 ping/min alongside the traceroutes
# for finer RTT / jitter / packet-loss than 15-min traceroutes can give.
# NOTE: with many probes this multiplies credit cost - watch the estimate schedule prints.
PING_COMPANION    = True
PING_INTERVAL_SEC = 60       # one ping per minute
PING_PACKETS      = 3        # packets per ping -> per-minute loss + jitter

# After the run window closes, watch() auto-commits the results folder and pushes.
# Needs working git auth on this machine (SSH deploy key, or a cached HTTPS token).
AUTO_PUSH = True

# Probes: (probe_id, asn, label). The PK RIPE Atlas probes for this run.
# ONE measurement per target runs from ALL of these at once (RIPE multi-probe), so
# each result carries its prb_id and every output is per (site, probe) for ISP comparison.
PROBES = [
    (60223,   23674,  "Nayatel"),
    (62224,   38193,  "Transworld"),
    (7613,    152605, "Z COM Networks"),
    (1016036, 9541,   "Cybernet"),
    (1015679, 136174, "LocalInternetProj01"),
]

# 5 targets: 1 PK-hosted news + 2 banks hosted abroad + 2 more PK-hosted.
TARGETS = [
    {"hostname": "dunyanews.tv",  "label": "Dunya News", "category": "news"},        # PK (Multinet)
    {"hostname": "hbl.com",       "label": "HBL Bank",   "category": "banking"},     # abroad (Incapsula, US)
    {"hostname": "mcb.com.pk",    "label": "MCB Bank",   "category": "banking"},     # abroad (Sucuri)
    {"hostname": "ptcl.com.pk",   "label": "PTCL",       "category": "telecom"},     # PK (PTCL)
    {"hostname": "pseb.org.pk",   "label": "PSEB",       "category": "government"},   # PK (Multinet)
]
# ──────────────────────────────────────────────────────

RESULTS_DIR = os.path.join("experiments", "03_longitudinal_routing", "results", RUN_NAME)
STATE_FILE  = os.path.join(RESULTS_DIR, "measurements.json")

GROUPED_FIELDS = [
    "target_hostname", "target_label", "target_category",
    "probe_id", "probe_asn", "probe_city",
    "trace_time", "hop", "hop_ip", "rtt_ms",
    "hop_asn", "hop_prefix", "hop_country", "hop_asn_name",
    "is_private", "is_timeout",
    "target_ip", "target_asn", "target_asn_name", "target_country",
    "destination_responded", "measurement_id",
]
SUMMARY_FIELDS = [
    "trace_time", "target_hostname", "target_label", "target_category",
    "probe_id", "probe_asn", "probe_city",
    "target_ip", "target_asn", "target_asn_name", "target_country",
    "dest_rtt_ms", "total_hops", "timeout_hops",
    "asns_in_path", "countries_in_path",
    "dest_location", "location_via", "destination_responded",
    "measurement_id",
]
PING_FIELDS = [
    "ping_time", "target_hostname", "target_label",
    "probe_id", "probe_asn", "probe_city",
    "sent", "rcvd", "loss_pct", "rtt_min", "rtt_avg", "rtt_max", "measurement_id",
]


# ─────────────────────────────────────────────────────
#  SCHEDULE
# ─────────────────────────────────────────────────────

def _probes_block(probe_ids):
    """RIPE multi-probe selector: run one measurement from ALL these probes."""
    return [{"type": "probes",
             "value": ",".join(str(p) for p in probe_ids),
             "requested": len(probe_ids)}]


def _post_measurement(payload, tries=4):
    """POST a measurement, retrying transient network errors so a flaky link can't
    orphan a measurement mid-schedule. A real API error (HTTP 4xx/5xx) is raised
    immediately - retrying it would just create duplicates."""
    last = None
    for i in range(tries):
        try:
            r = requests.post(f"{BASE}/measurements/", headers=HDR, json=payload, timeout=20)
            r.raise_for_status()
            return r.json()["measurements"][0]
        except requests.HTTPError:
            raise
        except Exception as e:                          # ConnectTimeout etc. -> retry
            last = e
            if i < tries - 1:
                time.sleep(3)
    raise last


def create_periodic(probe_ids, target_ip, description, start, stop):
    """One PERIODIC ICMP Paris traceroute from ALL probe_ids (same shape as Exp 01's
    one-off, but is_oneoff=False + interval, so RIPE fires it every INTERVAL_SEC)."""
    payload = {
        "definitions": [{
            "target":           target_ip,
            "description":      description,
            "type":             "traceroute",
            "protocol":         "ICMP",
            "af":               4,
            "paris":            16,          # hold flow tuple => real path changes only
            "first_hop":        1,
            "max_hops":         32,
            "size":             48,
            "dont_fragment":    True,
            "resolve_on_probe": False,
            "interval":         INTERVAL_SEC,
        }],
        "probes":      _probes_block(probe_ids),
        "is_oneoff":   False,
        "start_time":  start,
        "stop_time":   stop,
    }
    return _post_measurement(payload)


def create_ping(probe_ids, target_ip, description, start, stop):
    """One PERIODIC ping (1/min) from ALL probe_ids - the RTT/jitter/loss companion."""
    payload = {
        "definitions": [{
            "target":           target_ip,
            "description":      description,
            "type":             "ping",
            "af":               4,
            "packets":          PING_PACKETS,
            "size":             48,
            "interval":         PING_INTERVAL_SEC,
            "resolve_on_probe": False,
        }],
        "probes":      _probes_block(probe_ids),
        "is_oneoff":   False,
        "start_time":  start,
        "stop_time":   stop,
    }
    return _post_measurement(payload)


def schedule():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    probe_ids   = [p[0] for p in PROBES]
    probes_meta = {str(pid): {"asn": asn, "city": label} for (pid, asn, label) in PROBES}
    nprb  = len(probe_ids)
    start = int(time.time()) + 60                       # +1 min lead
    stop  = start + DURATION_HOURS * 3600
    rounds = DURATION_HOURS * 3600 // INTERVAL_SEC

    print("Experiment 03 - longitudinal routing monitor")
    print(f"  {nprb} probes ({', '.join(p[2] for p in PROBES)}) -> {len(TARGETS)} targets")
    print(f"  every {INTERVAL_SEC//60} min for {DURATION_HOURS}h "
          f"(~{rounds} rounds/site/probe)")
    ping_rounds = DURATION_HOURS * 3600 // PING_INTERVAL_SEC if PING_COMPANION else 0
    est = len(TARGETS) * rounds * nprb * 20 + len(TARGETS) * ping_rounds * nprb * PING_PACKETS
    print(f"  ping companion: {'ON (1/min)' if PING_COMPANION else 'off'}   "
          f"auto-push: {'ON' if AUTO_PUSH else 'off'}")
    print(f"  est. credits: ~{est:,}  (make sure your RIPE balance covers this)\n")

    # attended run -> confirm the spend (skip with EXP03_YES=1 for automation)
    if sys.stdin.isatty() and os.environ.get("EXP03_YES") != "1":
        try:
            ans = input("  proceed and spend these credits? [y/N]: ").strip().lower()
        except EOFError:
            ans = "n"
        if ans not in ("y", "yes"):
            print("  aborted - nothing scheduled."); return

    state = {
        "run_name": RUN_NAME, "interval_sec": INTERVAL_SEC,
        "probe_ids": probe_ids, "probes": probes_meta,
        "start": start, "stop": stop,
        "start_iso": datetime.fromtimestamp(start, timezone.utc).isoformat(),
        "stop_iso":  datetime.fromtimestamp(stop, timezone.utc).isoformat(),
        "targets": [],
    }
    def _save():
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    for t in TARGETS:
        ip, err = resolve(t["hostname"])
        if err:
            print(f"  x {t['label']:<16} {t['hostname']} - DNS failed: {err}")
            continue
        try:
            mid = create_periodic(probe_ids, ip, f"{t['label']} (exp03)", start, stop)
        except requests.HTTPError as e:
            print(f"  x {t['label']:<16} HTTP {e.response.status_code}: {e.response.text[:120]}")
            continue
        except Exception as e:
            print(f"  x {t['label']:<16} trace POST failed: {e}")
            continue
        # trace exists on RIPE - record it NOW so a later ping failure can't orphan it
        entry = {**t, "ip": ip, "msm_id": mid, "ping_msm_id": None}
        state["targets"].append(entry)
        _save()
        if PING_COMPANION:
            try:
                entry["ping_msm_id"] = create_ping(
                    probe_ids, ip, f"{t['label']} ping (exp03)", start, stop)
                _save()
            except Exception as e:
                print(f"  ! {t['label']:<16} ping POST failed (trace {mid} kept): {e}")
        pinfo = f" + ping {entry['ping_msm_id']}" if entry["ping_msm_id"] else " (no ping)"
        print(f"  ok {t['label']:<16} {t['hostname']:<24} {ip:<16} trace {mid}{pinfo}")
        time.sleep(0.3)

    _save()
    print(f"\n  scheduled {len(state['targets'])} target(s) x {nprb} probes; state -> {STATE_FILE}")
    print(f"  window: {state['start_iso']}  ->  {state['stop_iso']}")
    print(f"  fetch any time with:  python {sys.argv[0]} fetch")


# ─────────────────────────────────────────────────────
#  FETCH + FLATTEN  (per-round, with the round's real timestamp)
# ─────────────────────────────────────────────────────

def _hop_rows_for_round(state, t, result):
    """One traceroute result (one round) -> (hop_rows, summary_row).

    Adapted from pk_multi_probe.flatten, but: uses the ROUND's epoch as the
    timestamp, stores the MIN reply RTT per hop (best-of-3, less jittery than
    Exp 01's first-reply), and derives 'destination_responded' from the path
    actually reaching dst_addr.
    """
    t_ip   = result.get("dst_addr") or t["ip"]
    t_asn, _t_prefix, t_cc = asn_for_ip(t_ip) if t_ip else (None, "", "")
    t_name = asn_name(t_asn) if t_asn else ""
    epoch  = result.get("timestamp")
    trace_time = (datetime.fromtimestamp(epoch, timezone.utc).isoformat()
                  if epoch else datetime.now(timezone.utc).isoformat())

    prb    = result.get("prb_id")                       # which probe produced this round
    pmeta  = state.get("probes", {}).get(str(prb), {})
    p_asn  = pmeta.get("asn", "")
    p_city = pmeta.get("city", str(prb) if prb is not None else "")

    hop_rows, all_asns, all_cc = [], [], []
    real_count = tmout_count = 0
    dest_rtt = None

    base = {
        "target_hostname": t["hostname"], "target_label": t["label"],
        "target_category": t["category"], "probe_id": prb,
        "probe_asn": p_asn, "probe_city": p_city,
        "trace_time": trace_time, "target_ip": t_ip, "target_asn": t_asn or "",
        "target_asn_name": t_name, "target_country": t_cc,
        "measurement_id": t["msm_id"],
    }

    for hop in result.get("result", []):
        hop_num = hop.get("hop")
        replies = hop.get("result", []) or []
        rtts    = [r["rtt"] for r in replies if isinstance(r, dict) and "rtt" in r]
        chosen  = next((r for r in replies if isinstance(r, dict) and "from" in r), None)

        if chosen is None or not rtts:
            tmout_count += 1
            hop_rows.append({**base, "hop": hop_num, "hop_ip": "*", "rtt_ms": "",
                             "hop_asn": "", "hop_prefix": "", "hop_country": "",
                             "hop_asn_name": "", "is_private": False,
                             "is_timeout": True, "destination_responded": False})
            continue

        real_count += 1
        ip  = chosen["from"]
        rtt = min(rtts)                     # best-of-3, less jitter
        if PRIVATE(ip):
            h_asn, h_prefix, h_cc, h_name, is_priv = "", "", "", "RFC1918", True
        else:
            h_asn, h_prefix, h_cc = asn_for_ip(ip)
            h_name, is_priv = (asn_name(h_asn) if h_asn else ""), False
            if not h_asn:                  # unannounced internal/IXP hop -> RDAP
                r_prefix, r_cc, r_name = registry_lookup(ip)
                h_prefix, h_cc, h_name = h_prefix or r_prefix, h_cc or r_cc, h_name or r_name

        if h_asn and h_asn not in all_asns:
            all_asns.append(h_asn)
        if h_cc and h_cc not in all_cc:
            all_cc.append(h_cc)
        if t_ip and ip == t_ip:
            dest_rtt = rtt if dest_rtt is None else min(dest_rtt, rtt)

        hop_rows.append({**base, "hop": hop_num, "hop_ip": ip, "rtt_ms": rtt,
                         "hop_asn": h_asn or "", "hop_prefix": h_prefix,
                         "hop_country": h_cc, "hop_asn_name": h_name,
                         "is_private": is_priv, "is_timeout": False,
                         "destination_responded": False})

    responded = dest_rtt is not None
    for r in hop_rows:
        r["destination_responded"] = responded

    dest_location, location_via = serving_location(hop_rows, t_asn or "", t_ip)
    summary = {
        "trace_time": trace_time, "target_hostname": t["hostname"],
        "target_label": t["label"], "target_category": t["category"],
        "probe_id": prb, "probe_asn": p_asn,
        "probe_city": p_city, "target_ip": t_ip,
        "target_asn": t_asn or "", "target_asn_name": t_name, "target_country": t_cc,
        "dest_rtt_ms": dest_rtt if dest_rtt is not None else "",
        "total_hops": real_count, "timeout_hops": tmout_count,
        "asns_in_path": " > ".join(all_asns), "countries_in_path": " > ".join(all_cc),
        "dest_location": dest_location, "location_via": location_via,
        "destination_responded": responded, "measurement_id": t["msm_id"],
    }
    return hop_rows, summary


def _load_state():
    if not os.path.exists(STATE_FILE):
        sys.exit(f"No state file at {STATE_FILE} - run 'schedule' first.")
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def _get_results(mid, tries=3):
    """GET a measurement's results with a few retries, so a transient network
    timeout doesn't silently drop a target from a watch/fetch cycle."""
    for i in range(tries):
        try:
            return requests.get(f"{BASE}/measurements/{mid}/results/",
                                 headers=HDR, timeout=30).json()
        except Exception:
            if i < tries - 1:
                time.sleep(2)
    return None


def _collect(state, verbose=True):
    """Pull every round collected so far from RIPE and flatten it. Returns
    (grouped_rows, summary_rows). Idempotent - safe to call repeatedly; each call
    returns the full dataset accumulated up to now."""
    all_grouped, all_summary = [], []
    for t in state["targets"]:
        raw = _get_results(t["msm_id"])
        if raw is None:
            print(f"  ! {t['label']:<16} trace fetch failed after retries - "
                  f"kept out of THIS snapshot (data is safe on RIPE; next cycle restores it)")
            continue
        rounds = raw if isinstance(raw, list) else []
        for result in rounds:
            hop_rows, summary = _hop_rows_for_round(state, t, result)
            all_grouped.extend(hop_rows)
            all_summary.append(summary)
        if verbose:
            print(f"  ok {t['label']:<16} {len(rounds)} round(s)")
    all_grouped.sort(key=lambda x: (x["target_hostname"], str(x["probe_id"]),
                                    x["trace_time"], x["hop"] or 0))
    all_summary.sort(key=lambda x: (x["target_hostname"], str(x["probe_id"]), x["trace_time"]))
    return all_grouped, all_summary


def _collect_pings(state):
    """Pull the 1/min ping companion. Returns (series_rows, stats) where stats is
    {(hostname, probe_id): {label, probe_city, probe_asn, sent, rcvd, rtts[]}} for the
    per-(site,probe) aggregate (loss%, rtt min/median/max, jitter=stdev)."""
    rows, stats = [], {}
    probes_meta = state.get("probes", {})
    for t in state["targets"]:
        pmid = t.get("ping_msm_id")
        if not pmid:
            continue
        raw = _get_results(pmid)
        if raw is None:
            print(f"  ! {t['label']:<16} ping fetch failed after retries - "
                  f"kept out of THIS snapshot (data is safe on RIPE)")
            continue
        for r in raw if isinstance(raw, list) else []:
            prb   = r.get("prb_id")
            pmeta = probes_meta.get(str(prb), {})
            pcity = pmeta.get("city", str(prb) if prb is not None else "")
            pasn  = pmeta.get("asn", "")
            st = stats.setdefault((t["hostname"], prb),
                                  {"label": t["label"], "probe_city": pcity,
                                   "probe_asn": pasn, "sent": 0, "rcvd": 0, "rtts": []})
            epoch = r.get("timestamp")
            ptime = (datetime.fromtimestamp(epoch, timezone.utc).isoformat()
                     if epoch else "")
            sent = r.get("sent", 0) or 0
            rcvd = r.get("rcvd", 0) or 0
            rtts = [x["rtt"] for x in r.get("result", []) if isinstance(x, dict) and "rtt" in x]
            st["sent"] += sent; st["rcvd"] += rcvd; st["rtts"] += rtts
            rows.append({
                "ping_time": ptime, "target_hostname": t["hostname"],
                "target_label": t["label"], "probe_id": prb,
                "probe_asn": pasn, "probe_city": pcity, "sent": sent, "rcvd": rcvd,
                "loss_pct": round(100 * (sent - rcvd) / sent, 1) if sent else "",
                "rtt_min": r.get("min") if r.get("min", -1) not in (-1, None) else "",
                "rtt_avg": r.get("avg") if r.get("avg", -1) not in (-1, None) else "",
                "rtt_max": r.get("max") if r.get("max", -1) not in (-1, None) else "",
                "measurement_id": pmid,
            })
    rows.sort(key=lambda x: (x["target_hostname"], str(x["probe_id"]), x["ping_time"]))
    return rows, stats


def _short_op(asn_name):
    """'ZCOMNETWORKS-AS-AP - Z COM NETWORKS, PK' -> 'Z COM NETWORKS'."""
    if not asn_name:
        return ""
    s = asn_name.split(" - ", 1)[1] if " - " in asn_name else asn_name
    head, _, tail = s.rpartition(", ")
    if head and len(tail.strip()) <= 3:      # strip trailing ', PK' / ', US'
        s = head
    return s.strip()


def write_routes(path, grouped):
    """Readable hop-by-hop route report: one block per (site, 15-min round), so
    you can read each traceroute and watch hops shift over time. The time-domain
    analogue of Exp 01's routes_*.txt."""
    groups = {}
    for r in grouped:
        groups.setdefault((r["target_hostname"], r["trace_time"], r["probe_id"]), []).append(r)
    lines = ["Readable traceroutes  -  one block per (site, 15-min round)",
             f"{len(groups)} traces", ""]
    for (host, ttime, pid) in sorted(groups):
        rows = sorted(groups[(host, ttime, pid)],
                      key=lambda x: int(x["hop"]) if str(x["hop"]).isdigit() else 0)
        f0 = rows[0]
        resp = str(f0.get("destination_responded", "")).lower() == "true"
        dest_op = f0["target_asn_name"] or (f"AS{f0['target_asn']}" if f0["target_asn"] else "?")
        lines.append("=" * 78)
        lines.append(f" {host}   -   {f0['target_label']}  ({f0['target_category']})")
        lines.append(f" TIME    {ttime}")
        lines.append(f" SOURCE  probe {pid} - AS{f0['probe_asn']} - {f0['probe_city']}")
        lines.append(f" DEST    {f0['target_ip']} - {dest_op} - {f0['target_country']} - "
                     f"{'reached' if resp else 'no reply from destination'}")
        lines.append("-" * 78)
        lines.append("  hop   rtt(ms)   ip                 asn       operator (country)")
        for r in rows:
            hop = str(r["hop"])
            if str(r.get("is_timeout", "")).lower() == "true" or r["hop_ip"] == "*":
                lines.append(f"  {hop:>3}      *     (no response)")
                continue
            try:
                rtt = f"{float(r['rtt_ms']):.1f}"
            except (ValueError, TypeError):
                rtt = "?"
            asn = f"AS{r['hop_asn']}" if r["hop_asn"] else "-"
            op  = _short_op(r["hop_asn_name"])
            cc  = f" ({r['hop_country']})" if r["hop_country"] else ""
            tag = "  <<< DESTINATION" if r["hop_ip"] == r["target_ip"] else ""
            lines.append(f"  {hop:>3}   {rtt:>7}   {r['hop_ip']:<18} {asn:<9} {op}{cc}{tag}")
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write(state, grouped, summary, ping_rows, ping_stats, tag):
    """Write the output files with a filename `tag` (a timestamp for a one-shot
    fetch, or 'live' for the continuously-overwritten watch dataset)."""
    grouped_path = os.path.join(RESULTS_DIR, f"trace_grouped_{tag}.csv")
    summary_path = os.path.join(RESULTS_DIR, f"trace_summary_{tag}.csv")
    changes_path = os.path.join(RESULTS_DIR, f"path_changes_{tag}.txt")
    routes_path  = os.path.join(RESULTS_DIR, f"routes_{tag}.txt")
    with open(grouped_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=GROUPED_FIELDS); w.writeheader(); w.writerows(grouped)
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS); w.writeheader(); w.writerows(summary)
    write_path_changes(changes_path, state, summary, ping_stats)
    write_routes(routes_path, grouped)
    paths = [grouped_path, summary_path, changes_path, routes_path]
    if ping_rows:
        ping_path = os.path.join(RESULTS_DIR, f"ping_series_{tag}.csv")
        with open(ping_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=PING_FIELDS); w.writeheader(); w.writerows(ping_rows)
        paths.append(ping_path)
    return paths


def fetch():
    """One-shot pull: grab all rounds so far and write timestamped files."""
    state = _load_state()
    print(f"Fetching results for {len(state['targets'])} target(s)...")
    grouped, summary = _collect(state)
    ping_rows, ping_stats = _collect_pings(state)
    tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = _write(state, grouped, summary, ping_rows, ping_stats, tag)
    print(f"\n  grouped CSV   -> {paths[0]}  ({len(grouped)} hop rows)")
    print(f"  summary CSV   -> {paths[1]}  ({len(summary)} trace rounds)")
    print(f"  path changes  -> {paths[2]}")
    print(f"  routes (read) -> {paths[3]}")
    if ping_rows:
        print(f"  ping series   -> {paths[4]}  ({len(ping_rows)} pings)")


def git_autopush(state):
    """After the run completes, commit just this run's results folder and push.
    Never raises - on any git/auth failure it reports and leaves the files in place
    (they are also safe on RIPE). Run from the repo root."""
    msg = (f"Exp03 results: {state['run_name']} "
           f"({len(state.get('probe_ids', []))} probes x {len(state['targets'])} sites)")
    try:
        subprocess.run(["git", "add", RESULTS_DIR], check=True,
                       capture_output=True, text=True)
        c = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True)
        if c.returncode != 0 and "nothing to commit" in (c.stdout + c.stderr):
            print("  auto-push: nothing new to commit"); return
        if c.returncode != 0:
            print(f"  auto-push: commit FAILED:\n   {(c.stdout + c.stderr).strip()[:300]}"); return
        p = subprocess.run(["git", "push"], capture_output=True, text=True)
        if p.returncode == 0:
            print("  auto-push: committed + pushed OK")
        else:
            print(f"  auto-push: commit OK but PUSH FAILED:\n   {p.stderr.strip()[:300]}")
            print("   results are saved locally + safe on RIPE; push manually once git auth is set up.")
    except Exception as e:
        print(f"  auto-push: FAILED ({e}); results saved locally")


def watch():
    """Auto-update the local data every INTERVAL_SEC: re-fetch on the interval and
    overwrite a single live dataset (trace_*_live.*) until the run window ends,
    then write a final timestamped snapshot (and, if AUTO_PUSH, commit + push it).
    Keep this running in a terminal (tmux/VNC) so it survives disconnects."""
    state = _load_state()
    stop  = state["stop"]
    every = state["interval_sec"]
    completed = False
    print(f"watch: refreshing every {every//60} min until "
          f"{state.get('stop_iso','?')}  (Ctrl-C to stop)\n")
    try:
        while True:
            grouped, summary = _collect(state, verbose=False)
            ping_rows, ping_stats = _collect_pings(state)
            _write(state, grouped, summary, ping_rows, ping_stats, "live")
            now = datetime.now(timezone.utc).strftime("%H:%M:%S")
            print(f"  [{now}Z] {len(summary)} trace rounds, {len(ping_rows)} pings "
                  f"-> *_live.* refreshed")
            if time.time() > stop + 120:          # window closed (+2 min grace)
                completed = True
                break
            time.sleep(every)
    except KeyboardInterrupt:
        print("\n  interrupted - writing final snapshot...")
    grouped, summary = _collect(state, verbose=False)
    ping_rows, ping_stats = _collect_pings(state)
    paths = _write(state, grouped, summary, ping_rows, ping_stats,
                   datetime.now().strftime("%Y%m%d_%H%M%S"))
    print("\n  final snapshot:")
    for p in paths:
        print(f"   {p}")
    if AUTO_PUSH and completed:
        print()
        git_autopush(state)
    elif AUTO_PUSH and not completed:
        print("\n  auto-push skipped (interrupted before the window closed); "
              "run a manual git add/commit/push if you want these saved.")


# ─────────────────────────────────────────────────────
#  READABLE LONGITUDINAL REPORT  (the time-domain routes_*.txt)
# ─────────────────────────────────────────────────────

def write_path_changes(path, state, summaries, ping_stats=None):
    """Per target: distinct AS-paths over time, transitions, and RTT stats.

    This is the longitudinal analogue of Exp 01's routes_*.txt - instead of one
    block per trace, it shows how the path/RTT for each target MOVED over the run.
    If a ping companion ran, its per-target loss/RTT/jitter is appended too.
    """
    ping_stats = ping_stats or {}
    bykey = {}
    for s in summaries:
        bykey.setdefault((s["target_hostname"], s["probe_id"]), []).append(s)

    probes = state.get("probes", {})
    plist = ", ".join(f"{m['city']}(AS{m['asn']})" for m in probes.values()) or "?"
    lines = [f"Longitudinal routing - {state['run_name']}",
             f"{len(state.get('probe_ids', []))} probes: {plist}"
             f"  every {state['interval_sec']//60} min   (blocks below are per site x probe)",
             f"window {state.get('start_iso','?')}  ->  {state.get('stop_iso','?')}", ""]

    for (host, prb) in sorted(bykey, key=lambda k: (k[0], str(k[1]))):
        rows = sorted(bykey[(host, prb)], key=lambda x: x["trace_time"])
        n = len(rows)
        answered = [r for r in rows if r["destination_responded"]]
        rtts = [float(r["dest_rtt_ms"]) for r in answered if r["dest_rtt_ms"] != ""]
        label = rows[0]["target_label"]

        lines.append("=" * 70)
        lines.append(f" {host}   -   {label}  ({rows[0]['target_category']})")
        lines.append(f"   probe {prb}  AS{rows[0]['probe_asn']}  {rows[0]['probe_city']}")
        lines.append(f"   rounds: {n}   reachable: {len(answered)}/{n} "
                     f"({100*len(answered)//n if n else 0}%)")
        if rtts:
            jit = statistics.pstdev(rtts) if len(rtts) > 1 else 0.0
            lines.append(f"   dest RTT (ms): min {min(rtts):.1f}  median "
                         f"{statistics.median(rtts):.1f}  max {max(rtts):.1f}  "
                         f"jitter(stdev) {jit:.1f}")

        # distinct AS-paths + the metro each round served from
        seen = {}
        for r in rows:
            key = r["asns_in_path"] or "(no path visible)"
            d = seen.setdefault(key, {"count": 0, "metros": set(), "first": r["trace_time"], "last": r["trace_time"]})
            d["count"] += 1
            d["last"] = r["trace_time"]
            if r["dest_location"]:
                d["metros"].add(r["dest_location"])
        lines.append(f"   distinct AS-paths: {len(seen)}")
        for key, d in sorted(seen.items(), key=lambda kv: -kv[1]["count"]):
            metros = "; ".join(sorted(d["metros"])) or "-"
            lines.append(f"     [{d['count']:>4}x]  {key}")
            lines.append(f"              served via: {metros}")

        # chronological transitions (only when the AS-path flips)
        transitions = []
        prev = None
        for r in rows:
            key = r["asns_in_path"] or "(no path visible)"
            if prev is not None and key != prev:
                transitions.append((r["trace_time"], prev, key))
            prev = key
        if transitions:
            lines.append(f"   path changes: {len(transitions)}")
            for tm, a, b in transitions:
                lines.append(f"     {tm}   {a}   ->   {b}")
        else:
            lines.append("   path changes: 0  (stable for the whole window)")

        ps = ping_stats.get((host, prb))
        if ps and ps["sent"]:
            loss = 100 * (ps["sent"] - ps["rcvd"]) / ps["sent"]
            pr = ps["rtts"]
            if pr:
                jit = statistics.pstdev(pr) if len(pr) > 1 else 0.0
                lines.append(
                    f"   ping 1/min: {ps['sent']} pkts, loss {loss:.1f}%  |  "
                    f"rtt min {min(pr):.1f}  median {statistics.median(pr):.1f}  "
                    f"max {max(pr):.1f}  jitter(stdev) {jit:.1f} ms")
            else:
                lines.append(f"   ping 1/min: {ps['sent']} pkts, loss {loss:.1f}% (no replies)")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ─────────────────────────────────────────────────────
#  STOP
# ─────────────────────────────────────────────────────

def stop():
    if not os.path.exists(STATE_FILE):
        sys.exit(f"No state file at {STATE_FILE}.")
    with open(STATE_FILE, encoding="utf-8") as f:
        state = json.load(f)
    for t in state["targets"]:
        for kind, mid in (("trace", t.get("msm_id")), ("ping", t.get("ping_msm_id"))):
            if not mid:
                continue
            try:
                r = requests.delete(f"{BASE}/measurements/{mid}/", headers=HDR, timeout=15)
                print(f"  stop {t['label']:<16} {kind:<5} msm {mid}  HTTP {r.status_code}")
            except Exception as e:
                print(f"  x {t['label']:<16} {kind} {e}")


# ─────────────────────────────────────────────────────
#  STATS  (data volume, storage, credits - estimate + actuals)
# ─────────────────────────────────────────────────────

def _human(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _dir_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


# rough per-row sizes of our output files, from the 2h baseline run
_BYTES = {"grouped_hop": 150, "summary_row": 200, "ping_row": 120, "routes_hop": 55}
_AVG_HOPS  = 16          # typical hops per traceroute (reach/decay)
_TR_PKTS   = 3           # RIPE traceroute packets per hop
_HDR_OVH   = 28         # IP+ICMP header bytes added to the 48B payload


def _estimate_storage(trace_rounds, pings):
    grouped = trace_rounds * _AVG_HOPS * _BYTES["grouped_hop"]
    summary = trace_rounds * _BYTES["summary_row"]
    routes  = trace_rounds * (_AVG_HOPS + 6) * _BYTES["routes_hop"]
    pingcsv = pings * _BYTES["ping_row"]
    return grouped + summary + routes + pingcsv


def stats():
    """Report data volume, storage footprint and credits for this run - both the
    pre-run estimate (from config) and on-disk actuals if results exist."""
    nprb, ntar = len(PROBES), len(TARGETS)
    rounds      = DURATION_HOURS * 3600 // INTERVAL_SEC
    ping_rounds = DURATION_HOURS * 3600 // PING_INTERVAL_SEC if PING_COMPANION else 0
    trace_total = ntar * rounds * nprb
    ping_total  = ntar * ping_rounds * nprb
    cadence = ("off" if not PING_COMPANION else
               "1/min" if PING_INTERVAL_SEC == 60 else f"1/{PING_INTERVAL_SEC//60}min")

    # probe wire traffic (sent + received), from measurement params
    pkt = 48 + _HDR_OVH
    tr_wire = trace_total * _AVG_HOPS * _TR_PKTS * pkt * 2
    pg_wire = ping_total * PING_PACKETS * pkt * 2
    wire    = tr_wire + pg_wire
    credits = trace_total * 20 + ping_total * PING_PACKETS

    print(f"Exp 03 stats - {RUN_NAME}")
    print(f"  {nprb} probes x {ntar} targets, traceroute every {INTERVAL_SEC//60} min, "
          f"ping {cadence}, {DURATION_HOURS}h")
    print(f"  measurements created: {ntar * (2 if PING_COMPANION else 1)} "
          f"({ntar} trace{f' + {ntar} ping' if PING_COMPANION else ''})")
    print(f"  expected results: {trace_total:,} trace rounds, {ping_total:,} pings\n")

    print(f"  probe wire traffic (sent+received, whole run, all probes):")
    print(f"    traceroute ~{_human(tr_wire)}   ping ~{_human(pg_wire)}   total ~{_human(wire)}")
    print(f"    => ~{_human(wire/nprb)} per probe over {DURATION_HOURS}h  "
          f"(assumes {_AVG_HOPS} hops, {_TR_PKTS} pkts/hop, {PING_PACKETS} ping pkts, "
          f"{pkt}B/pkt)\n")

    print(f"  RIPE credits: ~{credits:,}\n")

    if os.path.isdir(RESULTS_DIR) and _dir_size(RESULTS_DIR):
        size = _dir_size(RESULTS_DIR)
        print(f"  stored on disk now: {_human(size)}  ({RESULTS_DIR})")
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, encoding="utf-8") as f:
                st = json.load(f)
            span = st["stop"] - st["start"]
            frac = min(max((time.time() - st["start"]) / span, 0.001), 1.0) if span else 1.0
            if frac < 0.99:
                print(f"    ~{frac*100:.0f}% through the window "
                      f"-> projected full-run size ~{_human(size/frac)}")
        print(f"  note: fetching pulls the raw JSON from RIPE (~2-3x the CSV size) into memory,"
              f" but only the CSV/txt above are written to disk.")
    else:
        print(f"  stored on disk: none yet (run schedule -> fetch/watch first)")
        print(f"  estimated full-run storage: ~{_human(_estimate_storage(trace_total, ping_total))}"
              f"  (CSVs + routes/path_changes txt)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if   mode == "schedule": schedule()
    elif mode == "fetch":    fetch()
    elif mode == "watch":    watch()
    elif mode == "stats":    stats()
    elif mode == "stop":     stop()
    else:
        sys.exit("usage: trace_monitor.py [schedule|fetch|watch|stats|stop]")
