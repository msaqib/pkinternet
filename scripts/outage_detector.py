"""
outage_detector.py
==================
Three-layer submarine cable / internet outage detection system for Pakistan.

Layer 1 (PRIMARY)  — RTT Threshold Detection
    Periodically pings international and domestic targets from each probe
    (Raspberry Pi). Flags when international RTT spikes 2-3 x baseline while
    domestic RTT stays flat.  Produces a 3-way classification:
        CABLE_CUT       → international spike, domestic stable
        LOCAL_OUTAGE    → both spike
        PROBE_FAILURE   → silence / no response

Layer 2 (CORROBORATION) — Disco-style TCP Keep-alive Disconnection Burst
    Each probe maintains a persistent TCP connection to a central server.
    Synchronized disconnections across multiple cities within a 2-minute
    window are a near-certain outage signal.

Layer 3 (ENRICHMENT) — IODA API + BGPStream BGP Visibility
    Pulls the three IODA signals (BGP, active-probing, IBR) for Pakistan
    and watches for withdrawals of Pakistani AS prefixes via pybgpstream.
    Used to corroborate and timestamp an event already flagged by Layer 1/2.

Integration:
    Each layer runs as an independent async task.  An OutageEvent is raised
    when Layer 1 fires.  Layers 2 and 3 then vote; a confirmed event is
    written to events.jsonl and (optionally) dispatched via webhook.

Usage (on every Raspberry Pi probe):
    python outage_detector.py --mode probe --probe-id KHI-1 \
        --server-host 192.168.1.100 --server-port 9000

Usage (on the central server in Lahore/Islamabad):
    python outage_detector.py --mode server --server-port 9000

Dependencies:
    pip install requests scipy numpy pybgpstream  (pybgpstream needs libBGPStream)
    Standard library: asyncio, socket, subprocess, statistics, json, logging
"""

from __future__ import annotations

import argparse
import asyncio
import collections
import datetime
import json
import logging
import math
import socket
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Deque, Dict, List, Optional, Tuple

import requests

# pybgpstream is optional — Layer 3 BGP monitor degrades gracefully without it
try:
    import pybgpstream  # type: ignore
    _BGPSTREAM_AVAILABLE = True
except ImportError:
    _BGPSTREAM_AVAILABLE = False

# numpy / scipy for robust statistics in Layer 1 (also optional — fallback to stdlib)
try:
    import numpy as np
    from scipy import stats as scipy_stats
    _SCIPY_AVAILABLE = True
except ImportError:
    _SCIPY_AVAILABLE = False

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("outage_detector")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# ── Pakistan-specific ASes (BGPStream filter) ──────────────────────────────
PAKISTAN_ASES = [
    "17557",   # PTCL (Pakistan Telecom)
    "45595",   # PTCL Wireless
    "38193",   # StormFiber / Cybernet
    "9541",    # Transworld Associates (TWA) — main submarine cable operator
    "24499",   # Wateen Telecom
    "56167",   # Zong / CMPak
    "45669",   # Telenor Pakistan
]

# ── RTT probe targets ──────────────────────────────────────────────────────
INTERNATIONAL_TARGETS = [
    "8.8.8.8",           # Google DNS (USA)
    "1.1.1.1",           # Cloudflare DNS (USA/Anycast)
    "208.67.222.222",    # OpenDNS (USA)
    "194.50.185.1",      # RIPE NCC (Netherlands) — good for Asia-routed traffic
]

DOMESTIC_TARGETS = [
    "103.210.90.1",      # PTCL NOC Islamabad (example — replace with real reachable IPs)
    "202.83.164.1",      # Karachi IXP upstream (PAIX)
    "182.176.0.1",       # PTCL DNS Lahore
]

# ── RTT detection parameters (from Fontugne et al. methodology) ────────────
RTT_BASELINE_WINDOW        = 60       # samples to build rolling baseline
RTT_SPIKE_MULTIPLIER       = 2.5      # fire if RTT > baseline_median × this
RTT_PROBE_INTERVAL_S       = 30       # seconds between ICMP probe rounds
RTT_MIN_PROBES_TO_FIRE     = 3        # minimum international targets that must spike
RTT_SILENCE_THRESHOLD_MS   = 9999     # treat as timeout / silence

# ── Disco parameters ──────────────────────────────────────────────────────
DISCO_SYNC_WINDOW_S        = 120      # seconds within which disconnects are "synchronised"
DISCO_MIN_PROBES_TO_FIRE   = 2        # minimum cities that must disconnect together
DISCO_KEEPALIVE_INTERVAL_S = 10       # TCP keep-alive heartbeat

# ── IODA API ──────────────────────────────────────────────────────────────
IODA_API_BASE  = "https://api.ioda.caida.org/v2"
IODA_COUNTRY   = "PK"
IODA_POLL_S    = 300       # check IODA every 5 minutes (their data lags ~5 min)
IODA_LOOKBACK_S = 600      # look back 10 minutes when polling

# ── Output ─────────────────────────────────────────────────────────────────
EVENTS_FILE = "events.jsonl"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class EventType(str, Enum):
    CABLE_CUT    = "CABLE_CUT"
    LOCAL_OUTAGE = "LOCAL_OUTAGE"
    PROBE_FAILURE = "PROBE_FAILURE"
    UNKNOWN      = "UNKNOWN"


@dataclass
class RTTSample:
    ts: float           # Unix timestamp
    target: str
    rtt_ms: float       # 9999 = timeout


@dataclass
class OutageEvent:
    ts: float
    event_type: EventType
    probe_id: str
    intl_rtt_median_ms: float
    dom_rtt_median_ms: float
    intl_baseline_ms: float
    dom_baseline_ms: float
    layer2_confirmed: bool = False
    layer3_bgp_confirmed: bool = False
    layer3_ioda_score: float = 0.0
    notes: str = ""


# ---------------------------------------------------------------------------
# ── LAYER 1: RTT Threshold Detection ─────────────────────────────────────
# ---------------------------------------------------------------------------

def _ping_icmp(host: str, count: int = 3, timeout: int = 5) -> float:
    """
    Send ICMP pings via the OS `ping` command.
    Returns median RTT in ms, or RTT_SILENCE_THRESHOLD_MS on failure.
    Works on Linux (Raspberry Pi) and macOS.
    """
    try:
        cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout * count + 5
        )
        # Parse "rtt min/avg/max/mdev = 1.234/2.345/3.456/0.567 ms" (Linux)
        for line in result.stdout.splitlines():
            if "rtt min" in line or "round-trip" in line:
                parts = line.split("=")[1].strip().split("/")
                avg_ms = float(parts[1])
                return avg_ms
        return RTT_SILENCE_THRESHOLD_MS
    except Exception:
        return RTT_SILENCE_THRESHOLD_MS


def _robust_median(samples: List[float]) -> float:
    """Median of non-timeout samples; fallback to RTT_SILENCE_THRESHOLD_MS."""
    valid = [s for s in samples if s < RTT_SILENCE_THRESHOLD_MS]
    if not valid:
        return RTT_SILENCE_THRESHOLD_MS
    return statistics.median(valid)


class RollingBaseline:
    """
    Maintains a rolling window of RTT samples and provides the baseline
    median used by Layer 1 to compute the spike multiplier.

    Implements the differential RTT concept from Fontugne et al. (2017):
    instead of a single end-to-end RTT, we maintain per-target baselines
    and compare the current median to the rolling historical median.
    """

    def __init__(self, window: int = RTT_BASELINE_WINDOW) -> None:
        self._window = window
        self._samples: Deque[float] = collections.deque(maxlen=window)

    def push(self, rtt_ms: float) -> None:
        if rtt_ms < RTT_SILENCE_THRESHOLD_MS:
            self._samples.append(rtt_ms)

    @property
    def baseline(self) -> Optional[float]:
        """Returns None if we don't have enough samples yet."""
        if len(self._samples) < max(10, self._window // 4):
            return None
        return statistics.median(self._samples)

    @property
    def ready(self) -> bool:
        return self.baseline is not None

    def is_spike(self, current_ms: float, multiplier: float = RTT_SPIKE_MULTIPLIER) -> bool:
        b = self.baseline
        if b is None or b == 0:
            return False
        return current_ms >= b * multiplier


class RTTDetector:
    """
    Layer 1 primary detector.

    Algorithm:
        Every RTT_PROBE_INTERVAL_S seconds:
          1. Ping all INTERNATIONAL_TARGETS and compute current median RTT.
          2. Ping all DOMESTIC_TARGETS and compute current median RTT.
          3. Compare both to their rolling baselines.
          4. Classify:
               CABLE_CUT    → intl spike, domestic stable
               LOCAL_OUTAGE → both spike
               PROBE_FAILURE → all silence (no ICMP responses from any target)
          5. Require RTT_MIN_PROBES_TO_FIRE individual international targets
             to spike (not just the median) to avoid single-host false positives.

    Exactly matches the "two-target design" described in the recommendation
    section of Asad Ayub's analysis document.
    """

    def __init__(self, probe_id: str) -> None:
        self.probe_id = probe_id
        self._intl_baselines: Dict[str, RollingBaseline] = {
            t: RollingBaseline() for t in INTERNATIONAL_TARGETS
        }
        self._dom_baselines: Dict[str, RollingBaseline] = {
            t: RollingBaseline() for t in DOMESTIC_TARGETS
        }
        self._event_callbacks: List = []

    def add_event_callback(self, cb) -> None:
        self._event_callbacks.append(cb)

    async def run(self) -> None:
        log.info("[L1] RTT detector started on probe %s", self.probe_id)
        while True:
            try:
                await self._probe_round()
            except Exception as exc:
                log.error("[L1] Probe round error: %s", exc)
            await asyncio.sleep(RTT_PROBE_INTERVAL_S)

    async def _probe_round(self) -> None:
        ts = time.time()

        # Probe all targets concurrently using a thread pool (ping is blocking)
        loop = asyncio.get_event_loop()

        intl_results: Dict[str, float] = {}
        for target in INTERNATIONAL_TARGETS:
            rtt = await loop.run_in_executor(None, _ping_icmp, target)
            intl_results[target] = rtt
            self._intl_baselines[target].push(rtt)
            log.debug("[L1] INTL %s → %.1f ms", target, rtt)

        dom_results: Dict[str, float] = {}
        for target in DOMESTIC_TARGETS:
            rtt = await loop.run_in_executor(None, _ping_icmp, target)
            dom_results[target] = rtt
            self._dom_baselines[target].push(rtt)
            log.debug("[L1] DOM  %s → %.1f ms", target, rtt)

        # Only classify if we have baselines
        intl_ready = all(b.ready for b in self._intl_baselines.values())
        dom_ready  = all(b.ready for b in self._dom_baselines.values())
        if not (intl_ready and dom_ready):
            log.debug("[L1] Building baselines (%d/%d intl samples)",
                      min(len(b._samples) for b in self._intl_baselines.values()),
                      RTT_BASELINE_WINDOW)
            return

        intl_median = _robust_median(list(intl_results.values()))
        dom_median  = _robust_median(list(dom_results.values()))

        intl_baseline = statistics.median(
            [b.baseline for b in self._intl_baselines.values() if b.baseline]
        )
        dom_baseline = statistics.median(
            [b.baseline for b in self._dom_baselines.values() if b.baseline]
        )

        # Count how many individual international targets are spiking
        intl_spike_count = sum(
            1 for t, rtt in intl_results.items()
            if self._intl_baselines[t].is_spike(rtt)
        )
        dom_spike_count = sum(
            1 for t, rtt in dom_results.items()
            if self._dom_baselines[t].is_spike(rtt)
        )

        # All-silence check
        all_intl_silent = all(
            rtt >= RTT_SILENCE_THRESHOLD_MS for rtt in intl_results.values()
        )
        all_dom_silent = all(
            rtt >= RTT_SILENCE_THRESHOLD_MS for rtt in dom_results.values()
        )

        # ── Classification logic ───────────────────────────────────────────
        event_type = EventType.UNKNOWN

        if all_intl_silent and all_dom_silent:
            event_type = EventType.PROBE_FAILURE  # probe itself is offline
        elif intl_spike_count >= RTT_MIN_PROBES_TO_FIRE and dom_spike_count < 2:
            event_type = EventType.CABLE_CUT      # international only → cable
        elif intl_spike_count >= RTT_MIN_PROBES_TO_FIRE and dom_spike_count >= 2:
            event_type = EventType.LOCAL_OUTAGE   # both → local exchange/IXP failure

        if event_type not in (EventType.UNKNOWN, EventType.PROBE_FAILURE):
            evt = OutageEvent(
                ts=ts,
                event_type=event_type,
                probe_id=self.probe_id,
                intl_rtt_median_ms=intl_median,
                dom_rtt_median_ms=dom_median,
                intl_baseline_ms=intl_baseline,
                dom_baseline_ms=dom_baseline,
            )
            log.warning(
                "[L1] ⚠  EVENT: %s | intl=%.0f ms (baseline %.0f) | "
                "dom=%.0f ms (baseline %.0f)",
                event_type.value,
                intl_median, intl_baseline,
                dom_median, dom_baseline,
            )
            for cb in self._event_callbacks:
                asyncio.create_task(cb(evt))


# ---------------------------------------------------------------------------
# ── LAYER 2: Disco-style TCP Keep-alive Disconnection Monitor ─────────────
# ---------------------------------------------------------------------------

class DiscoProbeClient:
    """
    Runs on each Raspberry Pi probe.
    Maintains a persistent TCP connection to the central server
    and sends periodic heartbeats.  Reconnects on drop.

    Mirrors Disco (Shah et al. 2017): RIPE Atlas probes maintain SSH
    keep-alive sessions; we use raw TCP with a JSON heartbeat line.
    """

    def __init__(self, probe_id: str, server_host: str, server_port: int) -> None:
        self.probe_id    = probe_id
        self.server_host = server_host
        self.server_port = server_port

    async def run(self) -> None:
        log.info("[L2-probe] Keep-alive client to %s:%d", self.server_host, self.server_port)
        while True:
            try:
                reader, writer = await asyncio.open_connection(
                    self.server_host, self.server_port
                )
                log.info("[L2-probe] Connected.")
                while True:
                    hb = json.dumps({
                        "type": "heartbeat",
                        "probe_id": self.probe_id,
                        "ts": time.time(),
                    }) + "\n"
                    writer.write(hb.encode())
                    await writer.drain()
                    await asyncio.sleep(DISCO_KEEPALIVE_INTERVAL_S)
            except (ConnectionRefusedError, OSError, asyncio.IncompleteReadError) as e:
                log.warning("[L2-probe] Connection lost (%s), retrying in 5s...", e)
                await asyncio.sleep(5)


class DiscoServer:
    """
    Runs on the central server.
    Tracks which probes are connected and detects synchronised disconnections.

    When >= DISCO_MIN_PROBES_TO_FIRE probes disconnect within
    DISCO_SYNC_WINDOW_S seconds, a CABLE_CUT event is raised.

    This implements Disco's core insight: a burst of simultaneous disconnections
    across geographically distributed probes is a near-certain outage signal,
    unlike a single disconnection which might be a probe issue.
    """

    def __init__(self, port: int) -> None:
        self.port = port
        self._connected: Dict[str, float] = {}     # probe_id → last_seen ts
        self._disconnect_log: Deque[Tuple[str, float]] = collections.deque()
        self._event_callbacks: List = []

    def add_event_callback(self, cb) -> None:
        self._event_callbacks.append(cb)

    async def run(self) -> None:
        server = await asyncio.start_server(
            self._handle_probe, "0.0.0.0", self.port
        )
        log.info("[L2-server] Listening on port %d", self.port)
        async with server:
            await server.serve_forever()

    async def _handle_probe(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        probe_id: Optional[str] = None
        peer = writer.get_extra_info("peername")
        try:
            while True:
                line = await asyncio.wait_for(
                    reader.readline(), timeout=DISCO_KEEPALIVE_INTERVAL_S * 3
                )
                if not line:
                    break
                msg = json.loads(line.decode().strip())
                if msg.get("type") == "heartbeat":
                    probe_id = msg["probe_id"]
                    self._connected[probe_id] = msg["ts"]
        except (asyncio.TimeoutError, json.JSONDecodeError, ConnectionResetError):
            pass
        finally:
            if probe_id:
                disconnect_ts = time.time()
                log.info("[L2-server] Probe %s disconnected (peer=%s)", probe_id, peer)
                self._connected.pop(probe_id, None)
                self._disconnect_log.append((probe_id, disconnect_ts))
                await self._check_sync_disconnects(disconnect_ts)

    async def _check_sync_disconnects(self, now: float) -> None:
        """Check if multiple probes disconnected within the synchronization window."""
        cutoff = now - DISCO_SYNC_WINDOW_S
        recent = [(pid, ts) for pid, ts in self._disconnect_log if ts >= cutoff]

        # Count distinct probes disconnected in window
        distinct_probes = {pid for pid, _ in recent}
        if len(distinct_probes) >= DISCO_MIN_PROBES_TO_FIRE:
            log.warning(
                "[L2-server] ⚠  SYNC DISCONNECT: %d probes in %.0fs window → %s",
                len(distinct_probes), DISCO_SYNC_WINDOW_S, distinct_probes
            )
            evt = OutageEvent(
                ts=now,
                event_type=EventType.CABLE_CUT,
                probe_id="MULTI:" + ",".join(sorted(distinct_probes)),
                intl_rtt_median_ms=0,
                dom_rtt_median_ms=0,
                intl_baseline_ms=0,
                dom_baseline_ms=0,
                layer2_confirmed=True,
                notes=f"Disco: {len(distinct_probes)} probes disconnected within "
                      f"{DISCO_SYNC_WINDOW_S}s"
            )
            for cb in self._event_callbacks:
                asyncio.create_task(cb(evt))


# ---------------------------------------------------------------------------
# ── LAYER 3A: IODA API Corroboration ─────────────────────────────────────
# ---------------------------------------------------------------------------

class IODAMonitor:
    """
    Polls the IODA REST API (api.ioda.caida.org/v2) for Pakistan.
    Checks all three signals:
        bgp          — BGP visibility (visible /24s)
        ping-slash24 — Active probing (Trinocular method, up /24s)
        ucsd-nt      — Internet Background Radiation (unique source IPs)

    A significant drop in ping-slash24 is the strongest cable-cut signal.
    BGP remaining stable while ping-slash24 drops reproduces the exact
    Mediterranean 2008 pattern described in the document.

    API spec: https://github.com/CAIDA/ioda-api/wiki/API-Specification
    """

    def __init__(self) -> None:
        self._event_callbacks: List = []
        self._last_signals: Dict[str, List[float]] = {}

    def add_event_callback(self, cb) -> None:
        self._event_callbacks.append(cb)

    async def run(self) -> None:
        log.info("[L3-IODA] IODA monitor started for country=%s", IODA_COUNTRY)
        while True:
            try:
                await self._poll()
            except Exception as exc:
                log.error("[L3-IODA] Poll error: %s", exc)
            await asyncio.sleep(IODA_POLL_S)

    async def _poll(self) -> None:
        now   = int(time.time())
        until = now
        frm   = now - IODA_LOOKBACK_S

        loop = asyncio.get_event_loop()
        signals = await loop.run_in_executor(
            None, self._fetch_signals, frm, until
        )
        if not signals:
            return

        for ds_data in signals:
            datasource = ds_data.get("datasource", "unknown")
            values     = ds_data.get("values", [])
            if not values:
                continue

            self._last_signals[datasource] = values

            # Simple drop detection: last value < 60% of window mean
            window_mean = statistics.mean(
                [v for v in values if v is not None and v > 0] or [1]
            )
            last_val = values[-1] if values[-1] is not None else 0
            drop_pct = 1.0 - (last_val / window_mean) if window_mean else 0

            log.info(
                "[L3-IODA] %s: last=%.0f  mean=%.0f  drop=%.0f%%",
                datasource, last_val, window_mean, drop_pct * 100
            )

            if drop_pct >= 0.40:   # 40% drop below window mean
                log.warning(
                    "[L3-IODA] ⚠  Signal DROP: %s  %.0f%% below baseline",
                    datasource, drop_pct * 100
                )

    def _fetch_signals(self, frm: int, until: int) -> List[dict]:
        """Synchronous IODA API call — runs in thread executor."""
        url = (
            f"{IODA_API_BASE}/signals/country/{IODA_COUNTRY}"
            f"?from={frm}&until={until}"
        )
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception as exc:
            log.warning("[L3-IODA] API request failed: %s", exc)
            return []

    def fetch_alerts(self, lookback_s: int = 3600) -> List[dict]:
        """
        One-shot: fetch IODA alerts for Pakistan.
        Call this when Layer 1 fires to check if IODA concurs.
        Returns list of alert dicts from the IODA API.

        Example usage:
            ioda = IODAMonitor()
            alerts = ioda.fetch_alerts(lookback_s=1800)
            for a in alerts:
                print(a['datasource'], a['level'], a['value'], a['historyValue'])
        """
        now  = int(time.time())
        frm  = now - lookback_s
        url  = (
            f"{IODA_API_BASE}/outages/alerts/country/{IODA_COUNTRY}"
            f"?from={frm}&until={now}"
        )
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception as exc:
            log.warning("[L3-IODA] Alerts fetch failed: %s", exc)
            return []

    def get_ioda_score(self, lookback_s: int = 1800) -> float:
        """
        Returns a composite IODA score for Pakistan in [0, 1].
        0 = normal, 1 = complete outage.
        Weights: ping-slash24 (0.6) > bgp (0.3) > ucsd-nt (0.1).
        """
        now  = int(time.time())
        frm  = now - lookback_s
        url  = (
            f"{IODA_API_BASE}/outages/summary/country/{IODA_COUNTRY}"
            f"?from={frm}&until={now}"
        )
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            for entry in data:
                if entry.get("entityCode") == IODA_COUNTRY:
                    scores = entry.get("scores", {})
                    overall = scores.get("overall", 0)
                    # Normalise: IODA scores are unbounded; we cap at 10000
                    return min(1.0, overall / 10000.0)
        except Exception:
            pass
        return 0.0


# ---------------------------------------------------------------------------
# ── LAYER 3B: BGPStream Prefix Withdrawal Monitor ────────────────────────
# ---------------------------------------------------------------------------

class BGPWithdrawalMonitor:
    """
    Uses pybgpstream (CAIDA's live BGP stream) to watch for prefix
    WITHDRAWALS from Pakistani ASes in near-real-time.

    Connects to the RIPE RIS live stream and Route Views stream.
    Filters for elements where the origin AS is in PAKISTAN_ASES.

    A burst of withdrawals affecting >20% of Pakistan's routed prefixes
    within a 5-minute window is a BGP-level outage signal.

    Note: BGP alone is insufficient (routes can stay up while traffic is
    blackholed — 2008 Mediterranean case). This is therefore Layer 3
    enrichment only, not a primary trigger.

    Requires: libBGPStream + pybgpstream installed
    See: bgpstream.caida.org/docs/install/pybgpstream
    """

    # Approximate number of /24-equivalent prefixes Pakistan advertises
    PAKISTAN_TOTAL_PREFIXES_ESTIMATE = 1800

    def __init__(self) -> None:
        self._withdrawal_window: Deque[Tuple[str, str, float]] = collections.deque()
        self._event_callbacks: List = []

    def add_event_callback(self, cb) -> None:
        self._event_callbacks.append(cb)

    async def run(self) -> None:
        if not _BGPSTREAM_AVAILABLE:
            log.warning(
                "[L3-BGP] pybgpstream not installed. "
                "BGP monitoring disabled. Install with: pip install pybgpstream"
            )
            return

        log.info("[L3-BGP] BGP withdrawal monitor started (live stream)")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._stream_loop)

    def _stream_loop(self) -> None:
        """
        Blocking BGPStream loop — runs in a thread executor.
        Subscribes to the RIPE RIS live stream and Route Views stream.
        Filters for withdrawals by Pakistani ASes.

        BGPStream API: bgpstream.caida.org/docs/tutorials/pybgpstream
        """
        stream = pybgpstream.BGPStream(
            project="ris-live",              # RIPE RIS live feed
            record_type="updates",
            filter=" or ".join(
                f"aspath _{asn}_" for asn in PAKISTAN_ASES
            ),
        )
        # Also add Route Views live stream
        stream2 = pybgpstream.BGPStream(
            project="routeviews-stream",
            record_type="updates",
            filter=" or ".join(
                f"aspath _{asn}_" for asn in PAKISTAN_ASES
            ),
        )

        for stream_inst in [stream, stream2]:
            for elem in stream_inst:
                if elem.type == "W":    # Withdrawal
                    prefix   = elem.fields.get("prefix", "?")
                    as_path  = elem.fields.get("as-path", "")
                    ts       = float(elem.time)
                    log.info(
                        "[L3-BGP] WITHDRAWAL: %s  AS-path: %s",
                        prefix, as_path
                    )
                    self._withdrawal_window.append((prefix, as_path, ts))
                    self._check_withdrawal_burst(ts)

    def _check_withdrawal_burst(self, now: float) -> None:
        """Flag if >20% of Pakistani prefixes have been withdrawn in 5 minutes."""
        WINDOW_S = 300
        cutoff = now - WINDOW_S
        recent = [(pfx, asp, ts) for pfx, asp, ts in self._withdrawal_window
                  if ts >= cutoff]
        distinct_prefixes = {pfx for pfx, _, _ in recent}
        pct = len(distinct_prefixes) / self.PAKISTAN_TOTAL_PREFIXES_ESTIMATE
        log.info(
            "[L3-BGP] %.0f unique prefixes withdrawn in last %.0fs (%.1f%%)",
            len(distinct_prefixes), WINDOW_S, pct * 100
        )
        if pct >= 0.20:
            log.warning(
                "[L3-BGP] ⚠  BGP WITHDRAWAL BURST: %.1f%% of Pakistan prefixes", pct * 100
            )
            evt = OutageEvent(
                ts=now,
                event_type=EventType.CABLE_CUT,
                probe_id="BGP-MONITOR",
                intl_rtt_median_ms=0,
                dom_rtt_median_ms=0,
                intl_baseline_ms=0,
                dom_baseline_ms=0,
                layer3_bgp_confirmed=True,
                notes=(
                    f"BGPStream: {len(distinct_prefixes)} Pakistani prefixes "
                    f"withdrawn in {WINDOW_S}s ({pct*100:.1f}%)"
                )
            )
            for cb in self._event_callbacks:
                # BGP loop is in a thread — schedule on event loop
                try:
                    loop = asyncio.get_event_loop()
                    loop.call_soon_threadsafe(
                        lambda: asyncio.create_task(cb(evt))
                    )
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# ── Event Router: fuses all three layers ──────────────────────────────────
# ---------------------------------------------------------------------------

class OutageRouter:
    """
    Receives OutageEvents from all three layers and:
     1. Deduplicates events within a 5-minute window (avoid alert storms).
     2. Cross-correlates Layer 1 events with Layer 2 (Disco) and Layer 3
        (IODA / BGP) confirmation.
     3. Writes confirmed events to events.jsonl.
     4. Optionally sends a webhook notification.

    The three-layer logic:
        Layer 1 fires  → CANDIDATE event
        + Layer 2 fires within 2 min → HIGH_CONFIDENCE
        + Layer 3 (IODA score > 0.3 OR BGP withdrawal burst) → CONFIRMED
        Any single layer alone → still logged, but lower confidence
    """

    DEDUP_WINDOW_S = 300  # 5 minutes

    def __init__(
        self,
        ioda: IODAMonitor,
        webhook_url: Optional[str] = None,
    ) -> None:
        self._ioda = ioda
        self._webhook_url = webhook_url
        self._recent_events: Deque[OutageEvent] = collections.deque()

    async def on_event(self, evt: OutageEvent) -> None:
        # Deduplicate
        now = time.time()
        if any(
            abs(e.ts - evt.ts) < self.DEDUP_WINDOW_S
            and e.event_type == evt.event_type
            for e in self._recent_events
        ):
            log.debug("[router] Deduplicating event %s", evt.event_type)
            return

        self._recent_events.append(evt)

        # Enrich with IODA check (synchronous, but fast since it's a cached call)
        ioda_score = self._ioda.get_ioda_score(lookback_s=600)
        evt.layer3_ioda_score = ioda_score
        if ioda_score >= 0.3:
            log.info("[router] IODA corroborates (score=%.2f)", ioda_score)

        # Determine confidence
        confidence = self._compute_confidence(evt)

        log.warning(
            "[router] ★ OUTAGE EVENT | type=%s | probe=%s | confidence=%s | "
            "IODA_score=%.2f | L2=%s | L3_bgp=%s",
            evt.event_type.value,
            evt.probe_id,
            confidence,
            ioda_score,
            evt.layer2_confirmed,
            evt.layer3_bgp_confirmed,
        )

        # Persist
        self._write_event(evt, confidence)

        # Notify
        if self._webhook_url:
            await self._send_webhook(evt, confidence)

    def _compute_confidence(self, evt: OutageEvent) -> str:
        score = 0
        if evt.event_type in (EventType.CABLE_CUT, EventType.LOCAL_OUTAGE):
            score += 1   # Layer 1 fired
        if evt.layer2_confirmed:
            score += 1   # Layer 2 fired
        if evt.layer3_bgp_confirmed or evt.layer3_ioda_score >= 0.3:
            score += 1   # Layer 3 corroborates
        return {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "CONFIRMED"}.get(score, "LOW")

    def _write_event(self, evt: OutageEvent, confidence: str) -> None:
        record = asdict(evt)
        record["confidence"] = confidence
        record["ts_human"] = datetime.datetime.utcfromtimestamp(evt.ts).isoformat() + "Z"
        record["event_type"] = evt.event_type.value
        with open(EVENTS_FILE, "a") as f:
            f.write(json.dumps(record) + "\n")
        log.info("[router] Event written to %s", EVENTS_FILE)

    async def _send_webhook(self, evt: OutageEvent, confidence: str) -> None:
        payload = {
            "event_type": evt.event_type.value,
            "confidence": confidence,
            "probe_id": evt.probe_id,
            "ts_utc": datetime.datetime.utcfromtimestamp(evt.ts).isoformat() + "Z",
            "intl_rtt_ms": evt.intl_rtt_median_ms,
            "dom_rtt_ms": evt.dom_rtt_median_ms,
            "ioda_score": evt.layer3_ioda_score,
        }
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: requests.post(self._webhook_url, json=payload, timeout=10)
            )
            log.info("[router] Webhook sent.")
        except Exception as exc:
            log.warning("[router] Webhook failed: %s", exc)


# ---------------------------------------------------------------------------
# ── Entry points ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

async def run_probe(
    probe_id: str,
    server_host: str,
    server_port: int,
    webhook_url: Optional[str] = None,
) -> None:
    """
    Run on each Raspberry Pi probe.
    Starts Layer 1 (RTT) and the Layer 2 keep-alive client.
    The probe sends Layer 2 keep-alives to the central server independently.
    Layer 1 events are emitted locally and (if webhook set) POSTed upstream.
    """
    ioda    = IODAMonitor()
    router  = OutageRouter(ioda=ioda, webhook_url=webhook_url)
    rtt     = RTTDetector(probe_id=probe_id)
    disco   = DiscoProbeClient(probe_id, server_host, server_port)

    rtt.add_event_callback(router.on_event)

    await asyncio.gather(
        rtt.run(),
        disco.run(),
        ioda.run(),        # Layer 3 IODA polling (enrichment)
    )


async def run_server(
    server_port: int,
    webhook_url: Optional[str] = None,
) -> None:
    """
    Run on the central server (Lahore/Islamabad).
    Hosts the Layer 2 Disco server and Layer 3 BGP monitor.
    """
    ioda   = IODAMonitor()
    bgp    = BGPWithdrawalMonitor()
    disco  = DiscoServer(port=server_port)
    router = OutageRouter(ioda=ioda, webhook_url=webhook_url)

    disco.add_event_callback(router.on_event)
    bgp.add_event_callback(router.on_event)

    await asyncio.gather(
        disco.run(),
        bgp.run(),
        ioda.run(),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pakistan ISP outage detector — three-layer RTT + Disco + IODA/BGP"
    )
    parser.add_argument(
        "--mode", choices=["probe", "server", "demo"], default="probe",
        help="probe: run on Raspberry Pi | server: run on central server | "
             "demo: run a single Layer 1 probe round and exit"
    )
    parser.add_argument("--probe-id",    default="PKT-PROBE-1")
    parser.add_argument("--server-host", default="127.0.0.1")
    parser.add_argument("--server-port", type=int, default=9000)
    parser.add_argument("--webhook-url", default=None,
                        help="Optional URL to POST OutageEvent JSON to")
    args = parser.parse_args()

    if args.mode == "probe":
        asyncio.run(run_probe(
            probe_id=args.probe_id,
            server_host=args.server_host,
            server_port=args.server_port,
            webhook_url=args.webhook_url,
        ))
    elif args.mode == "server":
        asyncio.run(run_server(
            server_port=args.server_port,
            webhook_url=args.webhook_url,
        ))
    elif args.mode == "demo":
        # Quick smoke-test: do one RTT probe round and print results
        async def _demo():
            probe = RTTDetector("DEMO-PROBE")
            log.info("=== DEMO MODE: probing targets ===")
            for t in INTERNATIONAL_TARGETS + DOMESTIC_TARGETS:
                rtt = _ping_icmp(t)
                log.info("  %-22s → %s ms", t,
                         f"{rtt:.1f}" if rtt < RTT_SILENCE_THRESHOLD_MS else "TIMEOUT")
            ioda = IODAMonitor()
            score = ioda.get_ioda_score(lookback_s=3600)
            log.info("IODA Pakistan score (last 1h): %.3f", score)
            alerts = ioda.fetch_alerts(lookback_s=3600)
            log.info("IODA alerts: %d found", len(alerts))
            for a in alerts[:5]:
                log.info("  [%s] %s level=%s value=%.0f history=%.0f",
                         a.get("datasource", "?"),
                         a.get("entity", {}).get("name", "?"),
                         a.get("level", "?"),
                         a.get("value", 0),
                         a.get("historyValue", 0))
        asyncio.run(_demo())


if __name__ == "__main__":
    main()