#!/usr/bin/env python3
"""
Experiment 1.1 - DNS Resolution Study
=====================================
Does each Pakistani ISP get a DIFFERENT IP for the same website, and does the
answer change over time?

Experiment 01 resolved each hostname once, centrally, and sent that single IP to
all five probes - so it could not see GeoDNS sites that hand different IPs to
different ISPs. This experiment instead asks each probe to resolve the name via
its OWN ISP resolver, using cheap RIPE Atlas DNS measurements (not traceroutes),
and compares the answers across ISPs.

Structured like Experiment 01: 10 sites per batch, each batch in its own folder
with a CSV and a readable .txt. One invocation processes all 100 sites, batch by
batch (10 at a time stays under RIPE's 100-concurrent limit).

Run from the repo root:
    python experiments/01.1_dns_resolution/dns_check.py

Requires: RIPE_API_KEY in the environment / .env, and `pip install dnspython`.
"""

import os
import sys
import csv
import time
import base64
from datetime import datetime, timezone
from collections import defaultdict

import requests
import dns.message
import dns.rdatatype
from dotenv import load_dotenv

# Load RIPE_API_KEY from the .env at the repo root BEFORE importing the config
# (pk_multi_probe builds its auth header from the environment at import time).
load_dotenv()

# Reuse config + helpers from the main script WITHOUT importing changes into it
# (read-only: probe list, target loader, ASN lookups, API base/headers).
sys.path.insert(0, os.path.join("scripts", "measurement"))
from pk_multi_probe import (                       # noqa: E402
    BASE, HDR, PROBES, WEBSITES_FILE, load_targets, asn_for_ip, asn_name,
)

if "your-api-key-here" in HDR.get("Authorization", ""):
    sys.exit("RIPE_API_KEY not found. Put it in a .env file at the repo root.")

# ── CONFIG ────────────────────────────────────────────
RUN_BASE       = "run_20260606_dns"   # each batch becomes {RUN_BASE}_batch{N}
BATCH_SIZE     = 10                    # sites per batch (like Experiment 01)
RESULT_TIMEOUT = 600

# Probe IDs currently offline - skip them. A one-off RIPE measurement waits for
# every requested probe, so an offline probe adds ~3-4 min per measurement while
# returning nothing. Empty this set (re-include them) when they are back online.
OFFLINE_PROBES = {1015679, 1015210}   # TPCPL/Nova, PTCL

RESULTS_ROOT = os.path.join("experiments", "01.1_dns_resolution", "results")
FIELDS = ["hostname", "label", "category", "probe_id", "probe_asn",
          "resolved_ips", "first_ip_asn", "first_ip_asn_name", "timestamp"]
PN = {136174: "TPCPL", 17557: "PTCL", 38193: "Transworld",
      23674: "Nayatel", 152605: "Z-Com"}


def create_dns(hostname, probe_ids):
    """One DNS A-record measurement for `hostname` on all probes, each using its
    own ISP resolver (use_probe_resolver)."""
    payload = {
        "definitions": [{
            "type":               "dns",
            "af":                 4,
            "query_class":        "IN",
            "query_type":         "A",
            "query_argument":     hostname,
            "use_probe_resolver": True,
            "description":        f"DNS A {hostname}",
        }],
        "probes": [{
            "type":      "probes",
            "value":     ",".join(str(p) for p in probe_ids),
            "requested": len(probe_ids),
        }],
        "is_oneoff": True,
    }
    r = requests.post(f"{BASE}/measurements/", headers=HDR, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()["measurements"][0]


def wait_for_all(ids, timeout=RESULT_TIMEOUT):
    pending, done = set(ids), set()
    deadline = time.time() + timeout
    print("    polling", end="", flush=True)
    while pending and time.time() < deadline:
        for mid in list(pending):
            try:
                s = requests.get(f"{BASE}/measurements/{mid}/", headers=HDR,
                                 timeout=10).json().get("status", {})
                if s.get("id", 0) >= 4:           # terminal
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


def a_records(result):
    """Decode a probe's DNS answer (base64 abuf) into a sorted list of A-record IPs."""
    blocks = []
    res = result.get("result")
    if isinstance(res, dict):
        blocks.append(res)
    elif isinstance(res, list):
        blocks.extend(res)
    for rs in result.get("resultset", []) or []:
        if isinstance(rs.get("result"), dict):
            blocks.append(rs["result"])
    ips = set()
    for b in blocks:
        abuf = b.get("abuf") if isinstance(b, dict) else None
        if not abuf:
            continue
        try:
            msg = dns.message.from_wire(base64.b64decode(abuf))
            for rr in msg.answer:
                if rr.rdtype == dns.rdatatype.A:
                    for item in rr:
                        ips.add(item.address)
        except Exception:
            pass
    return sorted(ips)


def fetch_rows(scheduled, done, asn_by_probe):
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
            ips = a_records(r)
            asn = asn_for_ip(ips[0])[0] if ips else ""
            rows.append({
                "hostname": t["hostname"], "label": t["label"],
                "category": t["category"], "probe_id": r.get("prb_id"),
                "probe_asn": asn_by_probe.get(r.get("prb_id"), ""),
                "resolved_ips": ";".join(ips),
                "first_ip_asn": asn,
                "first_ip_asn_name": asn_name(asn) if asn else "",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    return rows


def write_txt(path, run_name, rows):
    """Readable per-batch report. Returns the list of sites whose ISPs disagree."""
    bysite = defaultdict(list)
    for r in rows:
        bysite[(r["hostname"], r["category"])].append(r)
    differ = []
    lines = [f"DNS resolution per ISP  -  {run_name}",
             "Each probe resolved the name via its own ISP resolver.",
             ""]
    for (host, cat), rs in sorted(bysite.items()):
        ipsets = {r["resolved_ips"] for r in rs if r["resolved_ips"]}
        diff = len(ipsets) > 1
        if diff:
            differ.append(host)
        lines.append("=" * 60)
        lines.append(f" {host}   ({cat})")
        for r in sorted(rs, key=lambda x: PN.get(x["probe_asn"], "")):
            asn = r["probe_asn"]
            who = f"{PN.get(asn, asn)} (AS{asn})"
            ips = r["resolved_ips"].replace(";", "; ") or "(no A record)"
            lines.append(f"   {who:<22} {ips}")
        lines.append("   => DIFFERENT IPs per ISP (GeoDNS)" if diff
                     else "   => same IP from all responding ISPs")
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return differ


def main():
    probe_ids    = [p[0] for p in PROBES if p[0] not in OFFLINE_PROBES]
    asn_by_probe = {p[0]: p[1] for p in PROBES}
    targets = load_targets(WEBSITES_FILE, 0, None)
    n_batches = (len(targets) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Experiment 1.1 - per-ISP DNS resolution")
    print(f"  {len(targets)} sites, {len(probe_ids)} probes, "
          f"{n_batches} batches of {BATCH_SIZE}\n")

    all_differ = []
    for bi in range(0, len(targets), BATCH_SIZE):
        num   = bi // BATCH_SIZE + 1
        batch = targets[bi:bi + BATCH_SIZE]
        run_name = f"{RUN_BASE}_batch{num}"
        outdir = os.path.join(RESULTS_ROOT, run_name)
        os.makedirs(outdir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(outdir, f"dns_{ts}.csv")
        txt_path = os.path.join(outdir, f"dns_{ts}.txt")

        print(f"== batch {num}: sites {bi + 1}-{bi + len(batch)}  ->  {run_name}")
        scheduled = {}
        for t in batch:
            try:
                scheduled[create_dns(t["hostname"], probe_ids)] = t
                time.sleep(0.3)
            except requests.HTTPError as e:
                print(f"    ERROR {t['hostname']}: {e.response.status_code}")
        done = wait_for_all(list(scheduled))
        rows = fetch_rows(scheduled, done, asn_by_probe)

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader(); w.writerows(rows)
        differ = write_txt(txt_path, run_name, rows)
        all_differ += differ
        print(f"    saved {len(rows)} rows  +  readable txt  "
              f"({len(differ)} site(s) differ per ISP)\n")

    print("==== all batches done ====")
    print(f"{len(all_differ)} site(s) returned DIFFERENT IPs per ISP "
          f"(GeoDNS, candidates for per-vantage re-trace):")
    for h in sorted(set(all_differ)):
        print(f"  {h}")


if __name__ == "__main__":
    main()
