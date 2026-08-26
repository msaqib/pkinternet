#!/usr/bin/env python3
"""
Experiment 11: Pakistani probe-to-probe mesh.

Measures the real inter-probe RTT between Pakistani RIPE Atlas probes, to replace
the speed-of-light assumption in the CDN latency-ratio floor
    min_q ( d(p,q) + r0(q,s) )
with a measured value, and to see whether domestic probe-to-probe paths leave
the country.

    python experiments/11_probe_mesh/mesh.py schedule   # create measurements
    python experiments/11_probe_mesh/mesh.py fetch      # pull results, write CSV + routes txt

Writes results/mesh_<ts>/: measurements.json, summary_<ts>.csv, routes_<ts>.txt
"""
import csv
import json
import math
import os
import sys
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("RIPE_API_KEY", "")
BASE = "https://atlas.ripe.net/api/v2"
HDR = {"Authorization": f"Key {API_KEY}", "Content-Type": "application/json"}

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

# Table 3 labels (tab:probes)
LABEL = {1016036: "A1", 1016143: "A2", 1016154: "A3", 1014872: "B1", 60223: "C1",
         65892: "C2", 1015679: "D1", 64535: "E1", 1016126: "F1", 1016393: "F2",
         64078: "G1", 64722: "G2", 62224: "H1", 7613: "I1", 7764: "F3"}
V_FIBER = 204.218  # km/ms, c/1.468, same constant as analysis/geo.py


def haversine_km(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    dphi, dl = math.radians(c - a), math.radians(d - b)
    x = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def live_probes():
    r = requests.get(f"{BASE}/probes/",
                     params={"id__in": ",".join(map(str, LABEL)), "page_size": 100},
                     timeout=30)
    r.raise_for_status()
    out = {}
    for p in r.json()["results"]:
        st = (p.get("status") or {}).get("name", "")
        if st == "Connected" and p.get("address_v4"):
            out[p["id"]] = {"ip": p["address_v4"], "lat": p["geometry"]["coordinates"][1],
                            "lon": p["geometry"]["coordinates"][0], "asn": p.get("asn_v4")}
    return out


def schedule():
    probes = live_probes()
    ids = sorted(probes)
    print(f"connected Pakistani probes: {len(ids)}  ({', '.join(LABEL[i] for i in ids)})")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = os.path.join(RESULTS, f"mesh_{ts}")
    os.makedirs(outdir, exist_ok=True)

    created = {"ping": {}, "trace": {}, "probes": {str(k): v for k, v in probes.items()},
               "labels": {str(k): LABEL[k] for k in ids}}
    for tgt in ids:
        srcs = [i for i in ids if i != tgt]
        defs = [
            {"target": probes[tgt]["ip"], "description": f"PK probe mesh ping {LABEL[tgt]}",
             "type": "ping", "af": 4, "packets": 3, "resolve_on_probe": False},
            {"target": probes[tgt]["ip"], "description": f"PK probe mesh trace {LABEL[tgt]}",
             "type": "traceroute", "af": 4, "protocol": "ICMP", "paris": 16,
             "first_hop": 1, "max_hops": 32, "resolve_on_probe": False},
        ]
        payload = {"definitions": defs,
                   "probes": [{"type": "probes", "value": ",".join(map(str, srcs)),
                               "requested": len(srcs)}],
                   "is_oneoff": True}
        r = requests.post(f"{BASE}/measurements/", headers=HDR, json=payload, timeout=30)
        if r.status_code >= 300:
            print(f"  {LABEL[tgt]}: FAILED {r.status_code} {r.text[:200]}")
            continue
        m = r.json()["measurements"]
        created["ping"][str(tgt)], created["trace"][str(tgt)] = m[0], m[1]
        print(f"  {LABEL[tgt]:<3} {probes[tgt]['ip']:<16} ping={m[0]} trace={m[1]} "
              f"({len(srcs)} sources)")
        time.sleep(1)

    with open(os.path.join(outdir, "measurements.json"), "w", encoding="utf-8") as f:
        json.dump(created, f, indent=2)
    print(f"\nwrote {os.path.relpath(outdir, HERE)}/measurements.json")
    print("wait a few minutes, then:  python experiments/11_probe_mesh/mesh.py fetch")


def latest_dir():
    ds = sorted(d for d in os.listdir(RESULTS) if d.startswith("mesh_"))
    return os.path.join(RESULTS, ds[-1])


def fetch():
    outdir = latest_dir()
    meta = json.load(open(os.path.join(outdir, "measurements.json"), encoding="utf-8"))
    probes = {int(k): v for k, v in meta["probes"].items()}
    ts = os.path.basename(outdir).replace("mesh_", "")

    rows, routes = [], []
    for tgt_s, mid in meta["ping"].items():
        tgt = int(tgt_s)
        r = requests.get(f"{BASE}/measurements/{mid}/results/", timeout=60)
        for res in (r.json() if r.status_code == 200 else []):
            src = res.get("prb_id")
            if src not in probes:
                continue
            rtts = [x["rtt"] for x in res.get("result", []) if isinstance(x.get("rtt"), (int, float))]
            if not rtts:
                continue
            km = haversine_km(probes[src]["lat"], probes[src]["lon"],
                              probes[tgt]["lat"], probes[tgt]["lon"])
            theo = 2 * km / V_FIBER
            rows.append({"src": LABEL[src], "dst": LABEL[tgt], "src_id": src, "dst_id": tgt,
                         "distance_km": round(km, 1), "theoretical_ms": round(theo, 3),
                         "measured_ms": round(min(rtts), 2),
                         "ratio": round(min(rtts) / theo, 2) if theo > 0.05 else ""})

    for tgt_s, mid in meta["trace"].items():
        tgt = int(tgt_s)
        r = requests.get(f"{BASE}/measurements/{mid}/results/", timeout=60)
        for res in (r.json() if r.status_code == 200 else []):
            src = res.get("prb_id")
            if src not in probes:
                continue
            routes.append(f"\n{'=' * 62}\n  {LABEL.get(src, src)} -> {LABEL[tgt]} "
                          f"({probes[tgt]['ip']})\n{'=' * 62}")
            for hop in res.get("result", []):
                pk = hop.get("result", [])
                ip = next((x.get("from") for x in pk if x.get("from")), None)
                rr = [x["rtt"] for x in pk if isinstance(x.get("rtt"), (int, float))]
                routes.append(f"  {hop.get('hop', '?'):>3}  {ip or '*':<17}"
                              f"{(f'{min(rr):.1f} ms' if rr else '-'):>10}")

    csv_path = os.path.join(outdir, f"summary_{ts}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["src", "dst", "src_id", "dst_id", "distance_km",
                                          "theoretical_ms", "measured_ms", "ratio"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda x: (x["src"], x["dst"])))
    txt_path = os.path.join(outdir, f"routes_{ts}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Probe mesh traceroutes, {ts}\n")
        f.write("\n".join(routes) + "\n")
    print(f"{len(rows)} probe pairs -> {os.path.relpath(csv_path, HERE)}")
    print(f"traceroutes            -> {os.path.relpath(txt_path, HERE)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "schedule"
    {"schedule": schedule, "fetch": fetch}[cmd]()
