#!/usr/bin/env python3
"""
RIPE Atlas one-off run: TCP/443 traceroutes to the 100 PK-hosted sites,
from every connected Pakistani probe.

One measurement per site with all live probes attached. Measurements go out in
waves (RIPE allows about 100 concurrent, so the default wave is 50). Raw RIPE
JSON is saved per measurement before any enrichment, so a crash in the
enrichment step never costs credits. Enrichment (Team Cymru ASN, RDAP) runs
with parallel lookups and a shared cache.

Reuses the lookup, flatten and field definitions from verify_pk_hits.py so the
output matches the earlier Exp 17 runs (grouped CSV, summary CSV, routes txt).

Usage (from anywhere):
    python site_collection/pipeline/outputs/PK/pk100_all_probes.py --pilot 2 --yes
    python site_collection/pipeline/outputs/PK/pk100_all_probes.py --yes

Re-running with the same --run-name resumes from manifest.json and raw/ in the
run folder, so nothing already paid for is scheduled twice.

Results: experiments/17_tranco_pk_cdn_discovery/results/{run-name}/
"""

import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "scripts" / "measurement"))
import verify_pk_hits as v   # noqa: E402  (lookups, flatten, field lists)

TARGETS_FILE = Path(__file__).resolve().parent / "pk_targets_100.csv"
PORT = 443
CREDITS_PER_TRACE = 60        # 10 x 3 packets, doubled for a one-off
WAVE_TIMEOUT = 1800           # seconds to wait for one wave to stop
MAX_WORKERS_DNS = 20
MAX_WORKERS_RDAP = 8


# ─────────────────────────────────────────────────────
#  Inputs
# ─────────────────────────────────────────────────────

def load_targets(pilot=None):
    with open(TARGETS_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    targets = [{
        "hostname":    r["domain"],
        "label":       r["domain"],
        "category":    "pk100-all-probes",
        "resolved_ip": r["ip"],
        "rank":        r["tranco_rank"],
    } for r in rows]
    return targets[:pilot] if pilot else targets


def connected_pk_probes():
    url = (f"{v.BASE}/probes/?country_code=PK&status=1&page_size=100"
           "&fields=id,asn_v4,address_v4,geometry")
    out = []
    while url:
        d = requests.get(url, headers=v.HDR, timeout=30).json()
        for p in d["results"]:
            if not p.get("address_v4"):
                continue
            lon, lat = (p.get("geometry") or {}).get("coordinates", [None, None])
            out.append({"probe_id": p["id"], "asn_v4": p["asn_v4"],
                        "city": "Pakistan", "description": "",
                        "lat": lat, "lon": lon})
        url = d.get("next")
    return sorted(out, key=lambda p: p["probe_id"])


# ─────────────────────────────────────────────────────
#  Scheduling
# ─────────────────────────────────────────────────────

def create_measurement(target, probe_ids):
    payload = {
        "definitions": [{
            "target":           target["resolved_ip"],
            "description":      f"pk100 {target['label']} all PK probes",
            "type":             "traceroute",
            "protocol":         "TCP",
            "port":             PORT,
            "af":               4,
            "paris":            16,
            "first_hop":        1,
            "max_hops":         32,
            "size":             48,
            "dont_fragment":    True,
            "resolve_on_probe": False,
        }],
        "probes": [{"type": "probes",
                    "value": ",".join(map(str, probe_ids)),
                    "requested": len(probe_ids)}],
        "is_oneoff": True,
    }
    for attempt in range(5):
        try:
            r = requests.post(f"{v.BASE}/measurements/", headers=v.HDR,
                              json=payload, timeout=30)
            if r.status_code in (400, 429) and attempt < 4:
                print(f"    {target['label']}: {r.status_code} {r.text[:160]}  "
                      f"(backing off 60 s, try {attempt + 1}/5)")
                time.sleep(60)
                continue
            r.raise_for_status()
            return r.json()["measurements"][0]
        except requests.RequestException as e:
            if attempt == 4:
                print(f"    {target['label']}: giving up ({type(e).__name__})")
                return None
            time.sleep(5)
    return None


def status_of(mid):
    try:
        r = requests.get(f"{v.BASE}/measurements/{mid}/", headers=v.HDR, timeout=15)
        r.raise_for_status()
        s = r.json().get("status", {})
        return s.get("id", 0), s.get("name", "")
    except Exception:
        return 0, "unknown"


def wait_for(mids, timeout=WAVE_TIMEOUT):
    pending, terminal = set(mids), {}
    deadline = time.time() + timeout
    with ThreadPoolExecutor(10) as ex:
        while pending and time.time() < deadline:
            for mid, (sid, sname) in zip(list(pending), ex.map(status_of, list(pending))):
                if sid >= 4:
                    terminal[mid] = sname
                    pending.discard(mid)
            if pending:
                print(f"    {len(mids) - len(pending)}/{len(mids)} stopped", flush=True)
                time.sleep(15)
    return terminal, pending


def save_raw(mid, raw_dir):
    path = raw_dir / f"{mid}.json"
    if path.exists():
        return
    r = requests.get(f"{v.BASE}/measurements/{mid}/results/", headers=v.HDR, timeout=60)
    r.raise_for_status()
    path.write_text(json.dumps(r.json()), encoding="utf-8")


# ─────────────────────────────────────────────────────
#  Enrichment (parallel lookups, then reuse flatten)
# ─────────────────────────────────────────────────────

def prewarm_lookups(raws, dest_ips):
    ips = set(dest_ips)
    for raw in raws:
        for res in raw:
            for hop in res.get("result", []):
                for rep in hop.get("result", []):
                    ip = rep.get("from")
                    if ip and not v.PRIVATE(ip):
                        ips.add(ip)
    print(f"  {len(ips)} unique public IPs to look up")

    with ThreadPoolExecutor(MAX_WORKERS_DNS) as ex:
        list(ex.map(v.asn_for_ip, ips))
    # Under 20 parallel DNS queries some time out and get cached as unresolved.
    # Clear those and retry gently so a timeout is not read as "no ASN".
    retry = [ip for ip in ips if not v._asn_cache.get(ip, (None,))[0]]
    for ip in retry:
        v._asn_cache.pop(ip, None)
    with ThreadPoolExecutor(5) as ex:
        list(ex.map(v.asn_for_ip, retry))

    asns = {v._asn_cache[ip][0] for ip in ips if v._asn_cache.get(ip, (None,))[0]}
    with ThreadPoolExecutor(MAX_WORKERS_DNS) as ex:
        list(ex.map(v.asn_name, asns))

    unresolved = [ip for ip in ips if not v._asn_cache.get(ip, (None,))[0]]
    with ThreadPoolExecutor(MAX_WORKERS_RDAP) as ex:
        list(ex.map(v.registry_lookup, unresolved))
    print(f"  {len(asns)} ASNs, {len(unresolved)} IPs fell back to RDAP")


# ─────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-name", default=None)
    ap.add_argument("--pilot", type=int, default=None, help="only the first N sites")
    ap.add_argument("--wave", type=int, default=50, help="measurements per wave")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = ap.parse_args()

    run_name = args.run_name or ("pk100_all_probes_pilot" if args.pilot else "pk100_all_probes")
    run_dir = ROOT / "experiments" / "17_tranco_pk_cdn_discovery" / "results" / run_name
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "manifest.json"
    stamp = time.strftime("%Y%m%d_%H%M%S")

    print("=" * 60)
    print(f"  PK100 TCP/{PORT} from all connected PK probes   run: {run_name}")
    print("=" * 60)

    targets = load_targets(args.pilot)
    probes = connected_pk_probes()
    by_id = {p["probe_id"]: p for p in probes}
    print(f"  {len(targets)} sites, {len(probes)} connected PK probes with public IPv4")
    print("  probes:", ", ".join(f"{p['probe_id']}(AS{p['asn_v4']})" for p in probes))

    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    todo = [t for t in targets if t["hostname"] not in {m["hostname"] for m in manifest.values()}]

    cost = len(todo) * len(probes) * CREDITS_PER_TRACE
    bal = requests.get(f"{v.BASE}/credits/", headers=v.HDR, timeout=15).json().get("current_balance", 0)
    print(f"  to schedule: {len(todo)} sites -> up to {len(todo) * len(probes)} traces, "
          f"~{cost:,} credits (balance {bal:,})")
    if todo and bal < cost * 3:
        sys.exit("  balance is under 3x the estimate, stopping")
    if todo and not args.yes and input("  Proceed? (yes/no): ").strip().lower() != "yes":
        sys.exit("  aborted")

    t0 = time.time()
    probe_ids = [p["probe_id"] for p in probes]

    # waves: schedule, wait, download raw
    waves = [todo[i:i + args.wave] for i in range(0, len(todo), args.wave)]
    if not todo:   # resume path: finish any scheduled-but-not-downloaded ones
        waves = [[]]
    for wi, wave in enumerate(waves, 1):
        print(f"\n[wave {wi}/{len(waves)}] scheduling {len(wave)} measurements "
              f"({time.time() - t0:.0f}s elapsed)")
        for t in wave:
            mid = create_measurement(t, probe_ids)
            if mid:
                manifest[str(mid)] = {**t, "probe_ids": probe_ids}
                manifest_path.write_text(json.dumps(manifest, indent=1))
            time.sleep(1.0)
        wave_mids = [int(m) for m, meta in manifest.items()
                     if not (raw_dir / f"{m}.json").exists()]
        terminal, pending = wait_for(wave_mids)
        bad = {m: s for m, s in terminal.items() if s != "Stopped"}
        if bad:
            print(f"    non-Stopped: {bad}")
        if pending:
            print(f"    timed out waiting on {sorted(pending)}")
        with ThreadPoolExecutor(10) as ex:
            list(ex.map(lambda m: save_raw(m, raw_dir),
                        [m for m, s in terminal.items() if s == "Stopped"]))
        print(f"    raw saved for {len(list(raw_dir.glob('*.json')))} measurements "
              f"({time.time() - t0:.0f}s elapsed)")
    t_meas = time.time() - t0

    # enrichment
    print(f"\n[enrich] loading raw results ({t_meas:.0f}s elapsed)")
    raws = {m: json.loads((raw_dir / f"{m}.json").read_text())
            for m in manifest if (raw_dir / f"{m}.json").exists()}
    prewarm_lookups(raws.values(), {meta["resolved_ip"] for meta in manifest.values()})

    all_grouped, all_summaries = [], []
    coverage = {}
    for m, raw in raws.items():
        meta = manifest[m]
        by_probe = {}
        for res in raw:
            by_probe.setdefault(res.get("prb_id"), []).append(res)
        coverage[meta["hostname"]] = {"requested": len(meta["probe_ids"]), "returned": len(by_probe)}
        for pid, results in by_probe.items():
            probe = by_id.get(pid) or {"probe_id": pid, "asn_v4": "", "city": "Pakistan",
                                       "lat": None, "lon": None}
            _hops, sum_row, grouped = v.flatten(int(m), probe, meta, results)
            all_grouped.extend(grouped)
            if sum_row:
                all_summaries.append(sum_row)

    all_grouped.sort(key=lambda x: (x["target_hostname"], x["probe_id"], x["hop"] or 0))
    grouped_file = run_dir / f"pk_grouped_{stamp}.csv"
    summary_file = run_dir / f"pk_summary_{stamp}.csv"
    with open(grouped_file, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=v.GROUPED_FIELDS)
        w.writeheader()
        w.writerows(all_grouped)
    with open(summary_file, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=v.SUMMARY_FIELDS)
        w.writeheader()
        w.writerows(all_summaries)
    (run_dir / "coverage.json").write_text(json.dumps(coverage, indent=1))
    try:
        from format_routes import format_file
        print(f"  readable routes -> {format_file(str(grouped_file))}")
    except Exception as e:
        print(f"  (routes txt skipped: {e})")

    reached = sum(1 for r in all_summaries if str(r["destination_responded"]) == "True")
    short = {h: c for h, c in coverage.items() if c["returned"] < c["requested"]}
    print("\n" + "=" * 60)
    print(f"  measurements with raw results : {len(raws)} of {len(manifest)}")
    print(f"  traces in summary CSV          : {len(all_summaries)}")
    print(f"  destination reached (TCP/{PORT})  : {reached}")
    print(f"  sites where some probes returned nothing: {len(short)}")
    print(f"  measuring: {t_meas:.0f}s   total: {time.time() - t0:.0f}s")
    print(f"  results in {run_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
