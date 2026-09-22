#!/usr/bin/env python3
"""
RIPE Atlas: do the CDN sites answer ping and traceroute, and where do they land?

Sends a ping, an ICMP traceroute and a TCP/443 traceroute to every site in
Selection_of_CDN_sites.csv (24 sites: Fastly, Akamai, Cloudflare, Hyperscaler)
from two Pakistani probes in different cities. This is a feasibility check,
not a study run. It answers three things:
    - are ping and ICMP traceroute blocked, at the target or on the way
    - does a TCP/443 traceroute get through where ICMP does not
    - which city does each probe hand off to the CDN in (the landing)

Targets are resolved ON the probe (resolve_on_probe), so each city gets the
answer its own local resolver would give. The IP that was actually hit is
read back from the results (dst_addr), so ping and traceroute from the same
probe can differ if the CDN rotates answers.

Requirements: pip install requests dnspython python-dotenv

Usage (run from repo root):
    python site_collection/runs/cdn_probe_check.py
    python site_collection/runs/cdn_probe_check.py --fetch <measurements_TS.json>

The second form re-analyses an earlier run from its saved measurement IDs and
spends no credits. Use it if the first run is interrupted while waiting.

Before running:
    1. Set RIPE_API_KEY in .env
    2. Probe status is checked for you (Connected, in PK, more than
       MIN_SEPARATION_KM apart). The run aborts if any of that fails.

Results saved to:
    site_collection/runs/results/cdn_probe_check/
"""

import argparse
import csv
import ipaddress
import json
import math
import os
import sys
import time
from collections import Counter
from datetime import datetime

import dns.resolver
import requests
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "measurement"))
import geo_utils   # handoff-hop location helper, shared with the other runs

load_dotenv(os.path.join(REPO_ROOT, ".env"))

# geo_utils only treats some ASNs as anycast (location = the handoff hop, not the
# server IP). Every target here is a CDN or hyperscaler front, so geolocating the
# server IP would be misleading. Extend the set for this run only.
geo_utils.ANYCAST_ASNS.update({
    "16625": "Akamai",
    "32934": "Meta",
    "714":   "Apple",
    "8075":  "Microsoft",
})

API_KEY = os.environ.get("RIPE_API_KEY", "your-api-key-here")

RUN_NAME    = "cdn_probe_check"
SITES_FILE  = os.path.join(REPO_ROOT, "site_collection", "pipeline", "outputs",
                           "CDN", "Selection_of_CDN_sites.csv")
RESULTS_DIR = os.path.join(REPO_ROOT, "site_collection", "runs", "results", RUN_NAME)

# (probe_id, city as deployed, ISP). Both were Connected on 2026-09-17.
# Swap in from experiments/07_longitudinal_panel/analysis/probe_label_map.csv if needed,
# e.g. Karachi: 1016126 (PTCL), 1016143 (Cybernet). Not checked Connected.
# Avoid 62224 (Transworld) and 7764 (PTCL Lahore): both filter ICMP.
PROBES = [
    (60223, "Islamabad", "Nayatel"),
    ( 7613, "Lahore",    "Zcom"),
]

# Platform coordinates are used for this check. They can disagree with the
# deployment record for a few probes (see probe_label_map.csv notes).
MIN_SEPARATION_KM = 100

TCP_PORT = 443
METHODS  = ("ping", "icmp", "tcp")

# Conservative per-result credit figures. The traceroute number is the one the
# other scripts use. Treat the total as an upper-ish estimate.
CREDITS_PER_TRACE = 20
CREDITS_PER_PING  = 3

# How long to wait for the measurements to finish (seconds)
RESULT_TIMEOUT = 1200

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BASE = "https://atlas.ripe.net/api/v2"
HDR  = {
    "Authorization": f"Key {API_KEY}",
    "Content-Type":  "application/json",
}

# ─────────────────────────────────────────────────────
#  ASN LOOKUP (Team Cymru DNS)
# ─────────────────────────────────────────────────────

_asn_cache  = {}
_name_cache = {}

def asn_for_ip(ip):
    """Origin ASN for an IPv4 address as a string, '' if unknown."""
    if ip in _asn_cache:
        return _asn_cache[ip]
    asn = ""
    try:
        rev = ".".join(reversed(ip.split(".")))
        ans = dns.resolver.resolve(f"{rev}.origin.asn.cymru.com", "TXT", lifetime=5)
        for r in ans:
            p = [x.strip() for x in str(r).strip('"').split("|")]
            asn = p[0].split()[0]
            break
    except Exception:
        pass
    _asn_cache[ip] = asn
    return asn

def asn_name(asn):
    if not asn:
        return ""
    if asn in _name_cache:
        return _name_cache[asn]
    name = ""
    try:
        ans = dns.resolver.resolve(f"AS{asn}.asn.cymru.com", "TXT", lifetime=5)
        for r in ans:
            p = [x.strip() for x in str(r).strip('"').split("|")]
            name = p[4] if len(p) > 4 else p[-1]
            break
    except Exception:
        pass
    _name_cache[asn] = name
    return name

def is_private(ip):
    """True for RFC1918, CGNAT, loopback and link-local. Nothing routable."""
    try:
        return not ipaddress.ip_address(ip).is_global
    except ValueError:
        return False

# ─────────────────────────────────────────────────────
#  STEP 1: LOAD SITES, CHECK PROBES
# ─────────────────────────────────────────────────────

def load_sites():
    with open(SITES_FILE, newline="", encoding="utf-8") as f:
        return [
            {"domain": r["domain"], "group": r["group"], "ahrefs_rank": r["ahrefs_rank"]}
            for r in csv.DictReader(f)
        ]

def km_between(a, b):
    (lat1, lon1), (lat2, lon2) = a, b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))

def check_probes():
    """Confirm each probe is Connected, in PK, and that the two are in different
    cities. Returns probe dicts, or None if any check fails."""
    probes = []
    ok = True
    for pid, city, isp in PROBES:
        r = requests.get(f"{BASE}/probes/{pid}/", headers=HDR, timeout=15)
        r.raise_for_status()
        d = r.json()
        status = (d.get("status") or {}).get("name", "?")
        cc     = d.get("country_code", "?")
        coords = (d.get("geometry") or {}).get("coordinates")   # [lon, lat]
        lat, lon = (coords[1], coords[0]) if coords else (None, None)
        probes.append({
            "probe_id": pid, "city": city, "isp": isp,
            "asn": d.get("asn_v4"), "status": status, "country": cc,
            "lat": lat, "lon": lon,
        })
        flag = "" if (status == "Connected" and cc == "PK") else "   <-- PROBLEM"
        if flag:
            ok = False
        print(f"    Probe {pid:<8} {city:<10} {isp:<10} AS{d.get('asn_v4')!s:<7} "
              f"{status:<13} {cc}  lat/lon {lat},{lon}{flag}")

    a, b = probes[0], probes[1]
    if None in (a["lat"], b["lat"]):
        print("    (no platform coordinates for one probe, skipping the distance check)")
    else:
        km = km_between((a["lat"], a["lon"]), (b["lat"], b["lon"]))
        print(f"    Separation: {km:.0f} km")
        if km < MIN_SEPARATION_KM:
            print(f"    <-- PROBLEM: under {MIN_SEPARATION_KM} km, not two different cities")
            ok = False
    return probes if ok else None

# ─────────────────────────────────────────────────────
#  STEP 2: SCHEDULE MEASUREMENTS
# ─────────────────────────────────────────────────────

def create_site_measurements(site, probe_ids):
    """One POST per site, three definitions, both probes in each. Returns
    {'ping': id, 'icmp': id, 'tcp': id}."""
    host   = site["domain"]
    common = {"target": host, "af": 4, "resolve_on_probe": True}
    trace  = {**common, "type": "traceroute", "paris": 16, "first_hop": 1,
              "max_hops": 32, "size": 48, "dont_fragment": True}
    payload = {
        "definitions": [
            {**common, "type": "ping", "packets": 3,
             "description": f"cdn_check ping {host}"},
            {**trace, "protocol": "ICMP",
             "description": f"cdn_check icmp-trace {host}"},
            {**trace, "protocol": "TCP", "port": TCP_PORT,
             "description": f"cdn_check tcp{TCP_PORT}-trace {host}"},
        ],
        "probes": [{"type": "probes",
                    "value": ",".join(str(p) for p in probe_ids),
                    "requested": len(probe_ids)}],
        "is_oneoff": True,
    }
    r = requests.post(f"{BASE}/measurements/", headers=HDR, json=payload, timeout=20)
    r.raise_for_status()
    ids = r.json()["measurements"]
    if len(ids) != len(METHODS):
        raise ValueError(f"expected {len(METHODS)} measurement ids, got {ids}")
    return dict(zip(METHODS, ids))

def schedule():
    """Check probes, confirm the cost, create everything. Returns
    (manifest, manifest_path), or (None, None) if aborted."""
    if API_KEY in ("", "your-api-key-here"):
        print("  RIPE_API_KEY is not set (put it in .env). Aborting.")
        return None, None

    sites = load_sites()

    print("\n[1] Checking probes...")
    probes = check_probes()
    if not probes:
        print("  Probe check failed. Fix PROBES and rerun. Nothing was scheduled.")
        return None, None

    per_site = len(probes) * (2 * CREDITS_PER_TRACE + CREDITS_PER_PING)
    print(f"\n[2] {len(sites)} sites x {len(probes)} probes x "
          f"(ping + ICMP traceroute + TCP/{TCP_PORT} traceroute)")
    print(f"  {len(sites) * len(METHODS)} measurements, "
          f"estimated {len(sites) * per_site:,} credits")
    if input("\n  Proceed? (yes/no): ").strip().lower() != "yes":
        print("  Aborted.")
        return None, None

    manifest_path = os.path.join(RESULTS_DIR, f"measurements_{TIMESTAMP}.json")
    manifest = {"created": TIMESTAMP, "probes": probes, "measurements": []}

    print("\n[3] Scheduling...")
    for site in sites:
        ids = None
        for attempt in range(3):
            try:
                ids = create_site_measurements(site, [p["probe_id"] for p in probes])
                break
            except requests.HTTPError as e:
                print(f"  ERROR {site['domain']}: {e.response.status_code} {e.response.text[:200]}")
                break
            except (requests.RequestException, ValueError) as e:
                print(f"  retry {attempt + 1}/3 {site['domain']}: {type(e).__name__}")
                time.sleep(5)
        if ids:
            manifest["measurements"].append({"site": site, **ids})
            print(f"  {site['domain']:<22} {site['group']:<12} "
                  f"ping {ids['ping']}  icmp {ids['icmp']}  tcp {ids['tcp']}")
            # Save after every site so an interruption never loses paid-for IDs.
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
        time.sleep(1.0)   # gentle rate limiting

    print(f"\n  Scheduled {len(manifest['measurements'])}/{len(sites)} sites")
    print(f"  Manifest -> {manifest_path}")
    return manifest, manifest_path

# ─────────────────────────────────────────────────────
#  STEP 3: WAIT, FETCH
# ─────────────────────────────────────────────────────

def wait_for_all(msm_ids, timeout):
    """Poll until every measurement is terminal or the timeout hits."""
    pending  = set(msm_ids)
    failed   = {}
    deadline = time.time() + timeout
    print(f"  Polling {len(pending)} measurements", end="", flush=True)
    while pending and time.time() < deadline:
        for mid in list(pending):
            try:
                r = requests.get(f"{BASE}/measurements/{mid}/", headers=HDR, timeout=10)
                r.raise_for_status()
                st = r.json().get("status", {})
            except Exception:
                continue
            # 0-3 still running, 4 Stopped, 5 Forced, 6 No suitable probes, 7 Failed
            if st.get("id", 0) >= 4:
                pending.discard(mid)
                if st.get("name") != "Stopped":
                    failed[mid] = st.get("name")
        if pending:
            print(".", end="", flush=True)
            time.sleep(10)
    print(f"\n  {len(msm_ids) - len(pending) - len(failed)} stopped, "
          f"{len(failed)} failed, {len(pending)} timed out")
    for mid, name in failed.items():
        print(f"    msm {mid}: {name}")

def fetch_all(msm_ids):
    """Results for every measurement, including partial ones. Missing = []."""
    raw = {}
    for mid in msm_ids:
        try:
            r = requests.get(f"{BASE}/measurements/{mid}/results/", headers=HDR, timeout=30)
            raw[str(mid)] = r.json() if r.ok else []
        except Exception:
            raw[str(mid)] = []
    return raw

# ─────────────────────────────────────────────────────
#  STEP 4: PARSE
# ─────────────────────────────────────────────────────

def pick(results, probe_id):
    return next((r for r in results or [] if r.get("prb_id") == probe_id), None)

def parse_ping(rec):
    if rec is None:
        return {"got": False}
    sent, rcvd = rec.get("sent") or 0, rec.get("rcvd") or 0
    avg = rec.get("avg")
    return {
        "got": True,
        "err": rec.get("dnserr") or rec.get("error"),
        "dst": rec.get("dst_addr", ""),
        "ok": rcvd > 0,
        "sent": sent, "rcvd": rcvd,
        "avg": round(avg, 1) if rcvd and avg is not None and avg >= 0 else "",
    }

def parse_trace(rec, site, probe, method):
    """Returns (summary dict, hop rows)."""
    if rec is None:
        return {"got": False}, []
    dst = rec.get("dst_addr", "")
    rows, last_hop, dest_rtt = [], 0, ""
    for h in rec.get("result", []):
        num     = h.get("hop")
        replies = [x for x in h.get("result", []) if "from" in x]
        row = {
            "site": site["domain"], "group": site["group"],
            "probe_id": probe["probe_id"], "probe_city": probe["city"],
            "method": method, "hop": num,
            "hop_ip": "*", "rtt_ms": "", "hop_asn": "", "hop_asn_name": "",
            "is_private": False, "is_timeout": True,
        }
        if replies:
            ip   = replies[0]["from"]
            rtts = [x["rtt"] for x in replies if x["from"] == ip and "rtt" in x]
            priv = is_private(ip)
            asn  = "" if priv else asn_for_ip(ip)
            row.update({
                "hop_ip": ip,
                "rtt_ms": round(min(rtts), 1) if rtts else "",
                "hop_asn": asn,
                "hop_asn_name": "RFC1918/CGNAT" if priv else asn_name(asn),
                "is_private": priv, "is_timeout": False,
            })
            last_hop = num or last_hop
            if ip == dst:
                dest_rtt = row["rtt_ms"]
        rows.append(row)
    reached = bool(rec.get("destination_ip_responded"))
    return {
        "got": True,
        "err": rec.get("dnserr") or rec.get("error"),
        "dst": dst, "ok": reached, "reached": reached,
        "last_hop": last_hop, "dest_rtt": dest_rtt,
    }, rows

def verdict(ping, icmp, tcp):
    ms = (ping, icmp, tcp)
    if not any(m.get("got") for m in ms):
        return "no result from probe (offline, or timed out)"
    err = next((m["err"] for m in ms if m.get("err")), None)
    if err:
        return f"probe error: {err}"
    p, i, t = (bool(m.get("ok")) for m in ms)
    if p and i and t:
        return "all reachable"
    if t and not (p or i):
        return f"ICMP blocked, TCP/{TCP_PORT} works"
    if (p or i) and not t:
        return f"ICMP works, TCP/{TCP_PORT} does not complete"
    if not (p or i or t):
        last = max(icmp.get("last_hop", 0), tcp.get("last_hop", 0))
        where = "early, likely the probe's own network" if last <= 3 else "at or near the target"
        return f"nothing reaches the target, paths stop at hop {last} ({where})"
    yn = lambda b: "yes" if b else "no"
    return f"mixed: ping {yn(p)}, ICMP traceroute {yn(i)}, TCP {yn(t)}"

def format_route(site, probe, method, summ, rows):
    label = "ICMP" if method == "icmp" else f"TCP/{TCP_PORT}"
    head = (f"== {site['domain']} ({site['group']}, ahrefs #{site['ahrefs_rank']}) | "
            f"{probe['city']} probe {probe['probe_id']} ({probe['isp']}) | "
            f"{label} traceroute -> {summ.get('dst') or '?'} | "
            f"reached: {'yes' if summ.get('reached') else 'no'}")
    lines = [head]
    for r in rows:
        if r["is_timeout"]:
            lines.append(f"  {r['hop']:>2}  *")
        else:
            asn = f"AS{r['hop_asn']}" if r["hop_asn"] else "AS?"
            lines.append(f"  {r['hop']:>2}  {r['hop_ip']:<16} {asn:<9} {r['rtt_ms']!s:>6} ms  {r['hop_asn_name']}")
    return "\n".join(lines)

# ─────────────────────────────────────────────────────
#  STEP 5: ANALYSE, SAVE, REPORT
# ─────────────────────────────────────────────────────

SUMMARY_FIELDS = [
    "site", "group", "ahrefs_rank", "probe_id", "probe_city", "probe_isp",
    "dst_ip", "dst_asn", "dst_asn_name",
    "ping_rcvd", "ping_avg_ms",
    "icmp_reached", "icmp_last_hop", "icmp_dest_rtt_ms",
    "tcp_reached", "tcp_last_hop", "tcp_dest_rtt_ms",
    "landing", "landing_via", "verdict",
]

HOP_FIELDS = [
    "site", "group", "probe_id", "probe_city", "method", "hop", "hop_ip",
    "rtt_ms", "hop_asn", "hop_asn_name", "is_private", "is_timeout",
]

def analyse(manifest, raw):
    probes = manifest["probes"]
    summaries, hop_rows, routes = [], [], []
    print(f"\n[5] Analysing {len(manifest['measurements'])} sites "
          f"(ASN and landing lookups, this takes a minute)...")
    for entry in manifest["measurements"]:
        site = entry["site"]
        for p in probes:
            recs = {m: pick(raw.get(str(entry[m])), p["probe_id"]) for m in METHODS}
            ping = parse_ping(recs["ping"])
            icmp, icmp_hops = parse_trace(recs["icmp"], site, p, "icmp")
            tcp,  tcp_hops  = parse_trace(recs["tcp"],  site, p, f"tcp{TCP_PORT}")
            hop_rows += icmp_hops + tcp_hops
            routes += [format_route(site, p, "icmp", icmp, icmp_hops),
                       format_route(site, p, "tcp",  tcp,  tcp_hops)]

            dst_ip   = next((m["dst"] for m in (ping, icmp, tcp) if m.get("dst")), "")
            dst_asn  = asn_for_ip(dst_ip) if dst_ip else ""
            # Landing comes from whichever traceroute got furthest.
            best = max(((icmp, icmp_hops), (tcp, tcp_hops)),
                       key=lambda t: (t[0].get("reached", False), t[0].get("last_hop", 0)))
            # serving_location would call the last router seen the "handoff" even when the
            # path died before the CDN, so only ask it when a hop is inside the target's ASN.
            if dst_asn and any(r["hop_asn"] == dst_asn for r in best[1]):
                landing, via = geo_utils.serving_location(best[1], dst_asn, dst_ip)
            else:
                landing, via = "", "path never entered the target's ASN"

            summaries.append({
                "site": site["domain"], "group": site["group"],
                "ahrefs_rank": site["ahrefs_rank"],
                "probe_id": p["probe_id"], "probe_city": p["city"], "probe_isp": p["isp"],
                "dst_ip": dst_ip, "dst_asn": dst_asn, "dst_asn_name": asn_name(dst_asn),
                "ping_rcvd": f"{ping['rcvd']}/{ping['sent']}" if ping.get("got") else "",
                "ping_avg_ms": ping.get("avg", ""),
                "icmp_reached": icmp.get("reached", ""), "icmp_last_hop": icmp.get("last_hop", ""),
                "icmp_dest_rtt_ms": icmp.get("dest_rtt", ""),
                "tcp_reached": tcp.get("reached", ""), "tcp_last_hop": tcp.get("last_hop", ""),
                "tcp_dest_rtt_ms": tcp.get("dest_rtt", ""),
                "landing": landing, "landing_via": via,
                "verdict": verdict(ping, icmp, tcp),
            })
    return summaries, hop_rows, routes

def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"  {path}")

def save(raw, summaries, hop_rows, routes):
    print("\n[6] Saving files...")
    write_csv(os.path.join(RESULTS_DIR, f"summary_{TIMESTAMP}.csv"), SUMMARY_FIELDS, summaries)
    write_csv(os.path.join(RESULTS_DIR, f"hops_{TIMESTAMP}.csv"), HOP_FIELDS, hop_rows)
    routes_path = os.path.join(RESULTS_DIR, f"routes_{TIMESTAMP}.txt")
    with open(routes_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(routes) + "\n")
    print(f"  {routes_path}")
    raw_path = os.path.join(RESULTS_DIR, f"raw_{TIMESTAMP}.json")
    with open(raw_path, "w") as f:
        json.dump(raw, f)
    print(f"  {raw_path}")

def report(summaries):
    print("\n" + "=" * 70)
    by_site = {}
    for s in summaries:
        by_site.setdefault(s["site"], []).append(s)
    for site, rows in by_site.items():
        r0 = rows[0]
        print(f"\n{site}  [{r0['group']}]")
        for s in rows:
            ping = f"ping {s['ping_rcvd'] or '-'}" + (f" avg {s['ping_avg_ms']} ms" if s["ping_avg_ms"] != "" else "")
            print(f"  {s['probe_city']:<10} {s['dst_ip'] or '-':<16} AS{s['dst_asn'] or '?':<6} "
                  f"{s['verdict']}")
            print(f"  {'':<10} {ping} | lands: {s['landing'] or 'not determined'}")
    print("\n" + "=" * 70)
    for city in dict.fromkeys(s["probe_city"] for s in summaries):
        # Drop the variable tail ("mixed: ...", "... paths stop at hop N") so like cases group.
        counts = Counter(s["verdict"].split(":")[0].split(", paths")[0]
                         for s in summaries if s["probe_city"] == city)
        print(f"\n  {city}")
        for v, n in counts.most_common():
            print(f"    {n:>3}  {v}")

# ─────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--fetch", metavar="MANIFEST",
                    help="skip scheduling, re-analyse from a saved measurements_*.json")
    args = ap.parse_args()

    print("=" * 70)
    print("  RIPE Atlas: CDN ping / traceroute check from two Pakistani cities")
    print("=" * 70)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    if args.fetch:
        with open(args.fetch) as f:
            manifest = json.load(f)
        print(f"  Re-analysing {args.fetch}")
    else:
        manifest, manifest_path = schedule()
        if not manifest or not manifest["measurements"]:
            return

    all_ids = [entry[m] for entry in manifest["measurements"] for m in METHODS]

    if not args.fetch:
        print(f"\n[4] Waiting for {len(all_ids)} measurements...")
        try:
            wait_for_all(all_ids, RESULT_TIMEOUT)
        except KeyboardInterrupt:
            print(f"\n  Interrupted. Resume later with:\n"
                  f"    python site_collection/runs/cdn_probe_check.py --fetch {manifest_path}")
            return

    print(f"\n  Fetching results for {len(all_ids)} measurements...")
    raw = fetch_all(all_ids)

    summaries, hop_rows, routes = analyse(manifest, raw)
    save(raw, summaries, hop_rows, routes)
    report(summaries)


if __name__ == "__main__":
    main()
