#!/usr/bin/env python3
"""
Experiment 1.2 - CDN / cache presence in Pakistan
=================================================
Which big content providers (Netflix, Google, Meta, Akamai, Cloudflare, ...)
actually serve from a cache INSIDE Pakistan, and through which ISP?

For each target we run a PING from each Pakistani probe with resolve_on_probe=True,
so every probe resolves the name via its own ISP and pings the IP it got. That one
measurement gives both:
  - the IP each ISP was handed (look up its ASN + country), and
  - the RTT to it (the strongest signal: single-digit ms == a local cache).

Verdict per (target, probe): PK-local (<15 ms) / regional (<50 ms) / abroad,
plus the resolved IP's network and country.

Run from the repo root:
    python experiments/01.2_cdn_presence/cdn_check.py

Requires RIPE_API_KEY in the environment / .env.
"""

import os
import sys
import csv
import time
from datetime import datetime, timezone
from collections import defaultdict

import requests
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join("scripts", "measurement"))
from pk_multi_probe import (                       # noqa: E402
    BASE, HDR, PROBES, load_targets, asn_for_ip, asn_name,
)

if "your-api-key-here" in HDR.get("Authorization", ""):
    sys.exit("RIPE_API_KEY not found. Put it in a .env file at the repo root.")

# ── CONFIG ────────────────────────────────────────────
RUN_NAME       = "run_20260606_cdn1"
TARGETS_FILE   = "data/pk_cdn_targets.csv"
RESULT_TIMEOUT = 600
OFFLINE_PROBES = {1015679, 1015210}   # TPCPL/Nova, PTCL - offline; skip (empty when back)

PN = {136174: "TPCPL", 17557: "PTCL", 38193: "Transworld", 23674: "Nayatel", 152605: "Z-Com"}
OUTDIR = os.path.join("experiments", "01.2_cdn_presence", "results", RUN_NAME)
FIELDS = ["hostname", "provider", "category", "probe", "resolved_ip", "ip_asn",
          "ip_operator", "ip_country", "rtt_ms", "verdict", "timestamp"]


def create_ping(hostname, probe_ids):
    payload = {
        "definitions": [{
            "type": "ping", "af": 4, "target": hostname,
            "resolve_on_probe": True, "packets": 3,
            "description": f"ping {hostname}",
        }],
        "probes": [{"type": "probes",
                    "value": ",".join(str(p) for p in probe_ids),
                    "requested": len(probe_ids)}],
        "is_oneoff": True,
    }
    r = requests.post(f"{BASE}/measurements/", headers=HDR, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()["measurements"][0]


def wait_for_all(ids, timeout=RESULT_TIMEOUT):
    pending, done = set(ids), set()
    deadline = time.time() + timeout
    print("  polling", end="", flush=True)
    while pending and time.time() < deadline:
        for mid in list(pending):
            try:
                s = requests.get(f"{BASE}/measurements/{mid}/", headers=HDR,
                                 timeout=10).json().get("status", {})
                if s.get("id", 0) >= 4:
                    pending.discard(mid)
                    if s.get("name") == "Stopped":
                        done.add(mid)
            except Exception:
                pass
        if pending:
            print(".", end="", flush=True)
            time.sleep(5)
    print(f" done ({len(done)} ok)")
    return done


def verdict(rtt):
    if rtt is None or rtt < 0:
        return "no reply"
    if rtt < 15:
        return "PK-local"
    if rtt < 50:
        return "regional"
    return "abroad"


def main():
    probe_ids = [p[0] for p in PROBES if p[0] not in OFFLINE_PROBES]
    targets = load_targets(TARGETS_FILE, 0, None)   # hostname, provider(label), category
    print(f"Experiment 1.2 - CDN presence in Pakistan")
    print(f"  {len(targets)} services x {len(probe_ids)} probes\n")
    os.makedirs(OUTDIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    scheduled = {}
    for t in targets:
        try:
            scheduled[create_ping(t["hostname"], probe_ids)] = t
            time.sleep(0.3)
        except requests.HTTPError as e:
            print(f"  ERROR {t['hostname']}: {e.response.status_code}")
    done = wait_for_all(list(scheduled))

    rows = []
    for mid, t in scheduled.items():
        if mid not in done:
            continue
        try:
            raw = requests.get(f"{BASE}/measurements/{mid}/results/",
                               headers=HDR, timeout=15).json()
        except Exception:
            continue
        for r in raw:
            ip = r.get("dst_addr") or ""
            rtt = r.get("min")
            asn = cc = name = ""
            if ip:
                asn, _, cc = asn_for_ip(ip)
                name = asn_name(asn) if asn else ""
            rows.append({
                "hostname": t["hostname"], "provider": t["label"],
                "category": t["category"], "probe": PN.get(r.get("prb_id"), r.get("prb_id")),
                "resolved_ip": ip, "ip_asn": asn or "", "ip_operator": (name or "").split(" - ")[0],
                "ip_country": cc, "rtt_ms": rtt if rtt is not None else "",
                "verdict": verdict(rtt), "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    csv_path = os.path.join(OUTDIR, f"cdn_{ts}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)

    # readable txt
    bysite = defaultdict(list)
    for r in rows:
        bysite[(r["hostname"], r["provider"], r["category"])].append(r)
    lines = [f"CDN / cache presence in Pakistan  -  {RUN_NAME}",
             "Per service: where each PK ISP reaches it. PK-local (<15 ms) = cache inside Pakistan.",
             ""]
    local_by_provider = defaultdict(set)
    for (host, prov, cat), rs in sorted(bysite.items()):
        lines.append("=" * 64)
        lines.append(f" {host}   ({prov} / {cat})")
        n_local = 0
        for r in sorted(rs, key=lambda x: str(x["probe"])):
            rttx = f"{float(r['rtt_ms']):.0f} ms" if r["rtt_ms"] != "" else "  -  "
            who = f"{r['ip_operator'][:24]} ({r['ip_country']})" if r['ip_operator'] else ""
            lines.append(f"   {str(r['probe']):<11} {r['resolved_ip']:<16} {rttx:>7}  "
                         f"{r['verdict']:<9} {who}")
            if r["verdict"] == "PK-local":
                n_local += 1
                local_by_provider[prov].add(r["probe"])
        tag = (f"=> PK-local cache (seen by {n_local}/{len(rs)} ISPs)"
               if n_local else "=> no local cache detected (served regional/abroad)")
        lines.append("   " + tag)
        lines.append("")
    txt_path = os.path.join(OUTDIR, f"cdn_{ts}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  saved {len(rows)} rows -> {csv_path}")
    print(f"  readable           -> {txt_path}")
    print("\n  Providers with a PK-local cache (by ISPs that saw it):")
    for prov, isps in sorted(local_by_provider.items(), key=lambda x: -len(x[1])):
        print(f"    {prov:<14} {sorted(isps)}")
    if not local_by_provider:
        print("    (none detected - all served regional/abroad)")


if __name__ == "__main__":
    main()
