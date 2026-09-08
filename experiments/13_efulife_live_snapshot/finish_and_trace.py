#!/usr/bin/env python3
"""
Exp 13 -- autonomous finish: complete the liveness check for the remaining
8 Cybernet-hosted companies (banks/fintech/utility found via Cybernet's
asn-neighbours list), pick the best responding address per company (fall
back to .1 if nothing responds, since even a non-responding target still
yields a useful traceroute per this experiment's established pattern), then
run the full traceroute round across every live PK probe.

Run from repo root:
    python experiments/13_efulife_live_snapshot/finish_and_trace.py
"""
import sys, os, csv, time, json, requests
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "measurement"))
sys.path.insert(0, os.path.join(HERE, "..", "12_probe_mesh_panel"))
import pk_multi_probe as pk
import mesh_panel_monitor as mpm
from format_routes import format_file

LOG = os.path.join(HERE, "finish_and_trace.log")

def log(msg):
    line = f"[{datetime.now().isoformat()}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

BLOCKS = {
    "Intermarket": "103.94.186", "Shirazi": "103.103.112", "MTPPL": "103.110.52",
    "K-Electric": "103.125.142", "Khadim Ali Shah Bukhari": "103.155.145",
    "HBL Bank": "103.111.84", "NayaPay": "103.210.224", "DataCheck": "103.141.43",
}
CANDIDATES = [1, 2, 5, 10, 50, 100, 150, 200, 254]

def create_ping(probe_id, target_ip, description):
    payload = {
        "definitions": [{"target": target_ip, "description": description, "type": "ping",
                          "af": 4, "packets": 1, "size": 48}],
        "probes": [{"type": "probes", "value": str(probe_id), "requested": 1}],
        "is_oneoff": True,
    }
    r = requests.post(f"{pk.BASE}/measurements/", headers=pk.HDR, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()["measurements"][0]

def main():
    log("=== finish_and_trace starting ===")
    probes_map = mpm.discover_probes()
    probe_id = next((pid for pid, info in probes_map.items() if "cybernet" in info["label"]),
                     sorted(probes_map.keys())[0])
    log(f"live probes: {len(probes_map)}, using {probe_id} for liveness pings")

    # Step 1: schedule any still-missing liveness pings (re-fetch existing ones first)
    r = requests.get(f"{pk.BASE}/measurements/my/", headers=pk.HDR,
                      params={"page_size": 200, "sort": "-id"}, timeout=15)
    existing = {m["description"]: m["id"] for m in r.json().get("results", [])
                if "livecheck" in (m.get("description") or "")}

    ping_ids = {}  # (company, ip) -> mid
    for name, block in BLOCKS.items():
        for i in CANDIDATES:
            ip = f"{block}.{i}"
            desc = f"livecheck {name} {ip}"
            if desc in existing:
                ping_ids[(name, ip)] = existing[desc]
            else:
                try:
                    mid = create_ping(probe_id, ip, desc)
                    ping_ids[(name, ip)] = mid
                    log(f"  scheduled ping {desc} -> {mid}")
                except Exception as e:
                    log(f"  ERROR scheduling {desc}: {e}")
                time.sleep(0.3)
    log(f"total liveness pings tracked: {len(ping_ids)}")

    # Step 2: wait for all pings to finish
    all_ping_mids = list(ping_ids.values())
    completed = pk.wait_for_all(all_ping_mids, timeout=900)
    log(f"pings completed: {len(completed)} of {len(all_ping_mids)}")

    # Step 3: fetch each ping result, find first responding IP per company
    best_ip = {}
    for name, block in BLOCKS.items():
        for i in CANDIDATES:
            ip = f"{block}.{i}"
            mid = ping_ids.get((name, ip))
            if not mid or mid not in completed:
                continue
            try:
                raw = pk.fetch_result(mid)
                if raw and raw[0].get("avg", -1) not in (-1, None):
                    best_ip[name] = ip
                    log(f"  LIVE: {name} -> {ip}")
                    break
            except Exception as e:
                log(f"  error fetching ping {mid}: {e}")
        if name not in best_ip:
            fallback = f"{block}.1"
            best_ip[name] = fallback
            log(f"  no response anywhere for {name}, falling back to {fallback}")

    log(f"final target list: {json.dumps(best_ip, indent=2)}")
    with open(os.path.join(HERE, "results", "chosen_targets.json"), "w") as f:
        json.dump(best_ip, f, indent=2)

    # Step 4: run the full traceroute round
    TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
    RESULTS_DIR = os.path.join(HERE, "results", f"other_customers_batch2_{TIMESTAMP}")
    os.makedirs(RESULTS_DIR, exist_ok=True)

    probes_map = mpm.discover_probes()  # refresh, roster moves
    log(f"re-discovered {len(probes_map)} live probes for traceroute round")

    targets = [{"hostname": f"{name.replace(' ', '')}.pk", "label": name,
                "category": "Cybernet customer (own ASN)", "resolved_ip": ip}
               for name, ip in best_ip.items()]

    scheduled = []
    for target in targets:
        for pid, info in sorted(probes_map.items()):
            probe = {"probe_id": pid, "asn_v4": info["asn"], "city": info["label"],
                      "lat": None, "lon": None}
            try:
                mid = pk.create_traceroute(pid, target["resolved_ip"], f"{pid}→{target['label']}")
                scheduled.append((mid, probe, target))
            except Exception as e:
                log(f"  ERROR traceroute probe {pid} -> {target['label']}: {e}")
            time.sleep(0.35)
        log(f"  scheduled all probes -> {target['label']}")

    log(f"waiting for {len(scheduled)} traceroute measurements...")
    completed_tr = pk.wait_for_all([mid for mid, _, _ in scheduled], timeout=900)
    log(f"traceroutes completed: {len(completed_tr)} of {len(scheduled)}")

    all_grouped, all_summaries = [], []
    for mid, probe, target in scheduled:
        if mid not in completed_tr:
            continue
        try:
            raw = pk.fetch_result(mid)
            hop_rows, sum_row, grouped_rows = pk.flatten(mid, probe, target, raw)
            all_grouped.extend(grouped_rows)
            if sum_row:
                all_summaries.append(sum_row)
        except Exception as e:
            log(f"  ERROR fetching traceroute {mid}: {e}")

    all_grouped.sort(key=lambda x: (x["target_label"], x["probe_id"], x["hop"] or 0))
    grouped_file = os.path.join(RESULTS_DIR, f"grouped_{TIMESTAMP}.csv")
    summary_file = os.path.join(RESULTS_DIR, f"summary_{TIMESTAMP}.csv")
    with open(grouped_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pk.GROUPED_FIELDS); w.writeheader(); w.writerows(all_grouped)
    with open(summary_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pk.SUMMARY_FIELDS); w.writeheader(); w.writerows(all_summaries)
    routes_path = format_file(grouped_file)

    log(f"Grouped CSV -> {grouped_file}")
    log(f"Summary CSV -> {summary_file}")
    log(f"Readable    -> {routes_path}")
    log(f"scheduled={len(scheduled)} completed={len(all_summaries)}")

    # Step 5: write a plain-English summary markdown
    md_path = os.path.join(HERE, "OTHER_COMPANIES_RESULTS.md")
    with open(md_path, "w") as f:
        f.write("# Other Cybernet-hosted companies -- live traceroute results\n\n")
        f.write("Run finished autonomously. Target IPs chosen via one-off pings from a live\n")
        f.write("Pakistani probe (not from an external location, which earlier testing showed\n")
        f.write("gives false negatives for these networks).\n\n")
        f.write("## Target IPs used\n\n| Company | IP used | How chosen |\n|---|---|---|\n")
        for name, ip in best_ip.items():
            source = "responded to a live ping from inside Pakistan" if ip != f"{BLOCKS[name]}.1" or any(
                (name, f"{BLOCKS[name]}.1") in ping_ids and ping_ids[(name, f"{BLOCKS[name]}.1")] in completed
                for _ in [0]) else "fallback, .1 (no candidate responded)"
            f.write(f"| {name} | {ip} | {source} |\n")

        f.write("\n## Results by company (sorted fastest to slowest per company)\n\n")
        for name in BLOCKS:
            rows = [r for r in all_summaries if r["target_label"] == name]
            f.write(f"### {name}\n\n")
            if not rows:
                f.write("_No completed traceroutes for this target._\n\n")
                continue
            f.write("| Probe | ISP | Reached | Hops | Max RTT | ASNs in path | Countries |\n|---|---|---|---|---|---|---|\n")
            for row in sorted(rows, key=lambda r: float(r["max_rtt_ms"]) if r["max_rtt_ms"] not in ("", None) else 1e18):
                reached = "yes" if str(row["destination_responded"]).lower() == "true" else "no"
                f.write(f"| {row['probe_id']} | {row['probe_city']} | {reached} | {row['total_hops']} | "
                        f"{row['max_rtt_ms']} | {row['asns_in_path']} | {row['countries_in_path']} |\n")
            f.write("\n")

    log(f"Summary written -> {md_path}")
    log("=== finish_and_trace DONE ===")

if __name__ == "__main__":
    main()
