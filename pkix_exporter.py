#!/usr/bin/env python3
"""
PKIX Monitoring Exporter v2 — Full History
===========================================
Feeds ALL rows from trace_summary and ping_series CSVs into
Prometheus with correct timestamps, enabling time-series graphs
in Grafana showing 48h+ of RTT, PoP location, path changes.

Run from pkinternet repo root:
    python3 pkix_exporter_v2.py
"""

import csv
import os
import time
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── CONFIG ────────────────────────────────────────────
RESULTS_DIR  = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "experiments", "03_longitudinal_routing", "results", "run_20260612_48h"
)
SUMMARY_FILE = os.path.join(RESULTS_DIR, "trace_summary_live.csv")
PING_FILE    = os.path.join(RESULTS_DIR, "ping_series_live.csv")
PORT         = 8000
RELOAD_SECS  = 60   # re-read CSVs every 60s to pick up new data
# ─────────────────────────────────────────────────────

# Global cache of metric lines — rebuilt every RELOAD_SECS
_metrics_cache = ""
_cache_lock    = threading.Lock()


def ts_to_ms(ts_str):
    """Convert ISO timestamp string to Unix milliseconds for Prometheus."""
    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


def safe_float(val):
    try:
        f = float(val)
        if f != f:  # NaN check
            return None
        return f
    except (ValueError, TypeError):
        return None


def build_metrics():
    """Read both CSVs and build full Prometheus exposition text."""
    lines = []
    lines.append("# PKIX Monitoring — Full 48h History")
    lines.append(f"# Generated at {datetime.utcnow().isoformat()}Z")
    lines.append("")

    # ── TRACE SUMMARY ─────────────────────────────────

    if not os.path.exists(SUMMARY_FILE):
        lines.append("# WARNING: trace_summary_live.csv not found")
        return "\n".join(lines)

    summary_rows = []
    with open(SUMMARY_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            summary_rows.append(row)

    print(f"  Loaded {len(summary_rows)} trace summary rows")

    # pkix_rtt_ms — RTT time series
    lines.append("# HELP pkix_rtt_ms Destination RTT in ms per probe per site")
    lines.append("# TYPE pkix_rtt_ms gauge")
    for row in summary_rows:
        rtt = safe_float(row.get("dest_rtt_ms", ""))
        if rtt is None:
            continue
        ts = ts_to_ms(row.get("trace_time", ""))
        if ts is None:
            continue
        probe    = row.get("probe_city", "unknown").replace('"', '')
        site     = row.get("target_label", "unknown").replace('"', '')
        hostname = row.get("target_hostname", "unknown")
        cat      = row.get("target_category", "unknown")
        loc      = (row.get("dest_location") or "unknown").replace('"', '')
        country  = row.get("target_country", "unknown")
        label = (f'{{probe="{probe}",site="{site}",'
                 f'hostname="{hostname}",category="{cat}",'
                 f'dest_location="{loc}",target_country="{country}"}}')
        lines.append(f"pkix_rtt_ms{label} {rtt:.2f} {ts}")

    # pkix_destination_up — reachability time series
    lines.append("")
    lines.append("# HELP pkix_destination_up 1 if destination responded, 0 if not")
    lines.append("# TYPE pkix_destination_up gauge")
    for row in summary_rows:
        ts = ts_to_ms(row.get("trace_time", ""))
        if ts is None:
            continue
        probe    = row.get("probe_city", "unknown").replace('"', '')
        site     = row.get("target_label", "unknown").replace('"', '')
        hostname = row.get("target_hostname", "unknown")
        responded = row.get("destination_responded", "False")
        val = 1 if str(responded).lower() == "true" else 0
        label = f'{{probe="{probe}",site="{site}",hostname="{hostname}"}}'
        lines.append(f"pkix_destination_up{label} {val} {ts}")

    # pkix_total_hops — hop count time series
    lines.append("")
    lines.append("# HELP pkix_total_hops Total hops to destination")
    lines.append("# TYPE pkix_total_hops gauge")
    for row in summary_rows:
        hops = safe_float(row.get("total_hops", ""))
        if hops is None:
            continue
        ts = ts_to_ms(row.get("trace_time", ""))
        if ts is None:
            continue
        probe    = row.get("probe_city", "unknown").replace('"', '')
        site     = row.get("target_label", "unknown").replace('"', '')
        hostname = row.get("target_hostname", "unknown")
        label = f'{{probe="{probe}",site="{site}",hostname="{hostname}"}}'
        lines.append(f"pkix_total_hops{label} {int(hops)} {ts}")

    # pkix_serving_pk — 1 if served from Pakistan, 0 if abroad
    lines.append("")
    lines.append("# HELP pkix_serving_pk 1 if destination served from Pakistan, 0 if abroad")
    lines.append("# TYPE pkix_serving_pk gauge")
    for row in summary_rows:
        ts = ts_to_ms(row.get("trace_time", ""))
        if ts is None:
            continue
        probe    = row.get("probe_city", "unknown").replace('"', '')
        site     = row.get("target_label", "unknown").replace('"', '')
        hostname = row.get("target_hostname", "unknown")
        loc      = row.get("dest_location") or ""
        val = 1 if ", PK" in loc else 0
        label = f'{{probe="{probe}",site="{site}",hostname="{hostname}"}}'
        lines.append(f"pkix_serving_pk{label} {val} {ts}")

    # ── PING SERIES ───────────────────────────────────

    if not os.path.exists(PING_FILE):
        lines.append("\n# WARNING: ping_series_live.csv not found")
        return "\n".join(lines)

    ping_rows = []
    with open(PING_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ping_rows.append(row)

    print(f"  Loaded {len(ping_rows)} ping rows")

    # pkix_ping_rtt_avg
    lines.append("")
    lines.append("# HELP pkix_ping_rtt_avg Average ping RTT in ms")
    lines.append("# TYPE pkix_ping_rtt_avg gauge")
    for row in ping_rows:
        rtt = safe_float(row.get("rtt_avg", ""))
        if rtt is None:
            continue
        ts = ts_to_ms(row.get("ping_time", ""))
        if ts is None:
            continue
        probe    = row.get("probe_city", "unknown").replace('"', '')
        site     = row.get("target_label", "unknown").replace('"', '')
        hostname = row.get("target_hostname", "unknown")
        label = f'{{probe="{probe}",site="{site}",hostname="{hostname}"}}'
        lines.append(f"pkix_ping_rtt_avg{label} {rtt:.2f} {ts}")

    # pkix_ping_loss_pct
    lines.append("")
    lines.append("# HELP pkix_ping_loss_pct Packet loss percentage")
    lines.append("# TYPE pkix_ping_loss_pct gauge")
    for row in ping_rows:
        loss = safe_float(row.get("loss_pct", ""))
        if loss is None:
            continue
        ts = ts_to_ms(row.get("ping_time", ""))
        if ts is None:
            continue
        probe    = row.get("probe_city", "unknown").replace('"', '')
        site     = row.get("target_label", "unknown").replace('"', '')
        hostname = row.get("target_hostname", "unknown")
        label = f'{{probe="{probe}",site="{site}",hostname="{hostname}"}}'
        lines.append(f"pkix_ping_loss_pct{label} {loss:.1f} {ts}")

    return "\n".join(lines)


def reload_loop():
    """Background thread: rebuild metrics cache every RELOAD_SECS."""
    global _metrics_cache
    while True:
        print(f"\n[{datetime.utcnow().strftime('%H:%M:%S')}] Rebuilding metrics cache...")
        try:
            output = build_metrics()
            with _cache_lock:
                _metrics_cache = output
            line_count = output.count('\n')
            print(f"  Done — {line_count:,} lines in cache")
        except Exception as e:
            print(f"  ERROR building metrics: {e}")
        time.sleep(RELOAD_SECS)


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            with _cache_lock:
                output = _metrics_cache
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(output.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress per-request logs


if __name__ == "__main__":
    print("PKIX Exporter v2 — Full History Mode")
    print(f"Reading from: {RESULTS_DIR}")
    print(f"Port: {PORT}")
    print(f"Cache reload: every {RELOAD_SECS}s\n")

    # build initial cache before starting server
    print("Building initial metrics cache...")
    try:
        initial = build_metrics()
        with _cache_lock:
            _metrics_cache = initial
        print(f"Initial cache ready — {initial.count(chr(10)):,} lines\n")
    except Exception as e:
        print(f"ERROR on initial build: {e}")

    # start background reload thread
    t = threading.Thread(target=reload_loop, daemon=True)
    t.start()

    # start HTTP server
    server = HTTPServer(("", PORT), MetricsHandler)
    print(f"Metrics at: http://localhost:{PORT}/metrics")
    print("Ready. Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")