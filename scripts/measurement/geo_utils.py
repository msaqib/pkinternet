#!/usr/bin/env python3
"""
Shared geolocation helpers
==========================
One place for "where does this destination actually sit", used by the live
measurement, the route formatter, and the summary augmenter so they all agree.

Two ideas:
  - geolocate(ip)         -> "City, Region, CC" via ip-api.com (cached on disk).
  - serving_location(...) -> per-measurement actual location:
        * anycast CDN destinations (Cloudflare, Akamai, ...): the location is
          vantage-dependent, so we geolocate the HANDOFF hop — the last real
          router before traffic enters the CDN's ASN, i.e. the metro where THIS
          probe hands off to the CDN. (RIPE Atlas probes can't run HTTP, so
          Cloudflare's authoritative `colo` is unavailable; the handoff is the
          best probe-side signal.)
        * unicast destinations (real single servers): geolocate the server IP;
          that location is stable regardless of vantage.

Results are cached in `.geo_cache.json` next to this file so regenerating
outputs is instant and consistent (ip-api free tier is ~45 req/min).
"""

import json
import os
import time

import requests

_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".geo_cache.json")

# Destination ASNs that are anycast CDNs -> serving location is per-probe.
ANYCAST_ASNS = {
    "13335": "Cloudflare",
    "20940": "Akamai",
    "19551": "Incapsula/Imperva",
    "30148": "Sucuri",
    "54113": "Fastly",
    "15169": "Google",
}

try:
    with open(_CACHE_PATH, encoding="utf-8") as _fh:
        _cache = json.load(_fh)
except Exception:
    _cache = {}


def _save_cache():
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as fh:
            json.dump(_cache, fh, indent=0, sort_keys=True)
    except Exception:
        pass


def geolocate(ip):
    """Return 'City, Region, CC' for an IP (cached). Empty/invalid -> ''. """
    if not ip or ip == "*":
        return ""
    if ip in _cache:
        return _cache[ip]
    loc = ""
    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,countryCode,regionName,city"},
            timeout=10,
        )
        d = r.json()
        if d.get("status") == "success":
            parts = [d.get("city") or "", d.get("regionName") or "", d.get("countryCode") or ""]
            loc = ", ".join(p for p in parts if p)
        time.sleep(1.4)   # ip-api free tier ~45 req/min
    except Exception:
        pass
    _cache[ip] = loc
    _save_cache()
    return loc


def _hops_sorted(hops):
    return sorted(hops, key=lambda r: int(r["hop"]) if str(r.get("hop", "")).isdigit() else 9999)


def _handoff_ip(hops, dest_asn):
    """Last real (non-timeout, non-private) router before the first dest_asn hop."""
    ordered = _hops_sorted(hops)
    first_cdn = next((i for i, h in enumerate(ordered) if h.get("hop_asn") == dest_asn), None)
    scan = ordered[:first_cdn] if first_cdn is not None else ordered
    for h in reversed(scan):
        if (str(h.get("is_timeout", "")).lower() != "true"
                and str(h.get("is_private", "")).lower() != "true"
                and h.get("hop_ip") not in ("", "*", None)):
            return h["hop_ip"]
    return ""


def serving_location(hops, dest_asn, dest_ip):
    """Return (location, via) for one measurement.

    `via` explains the source: 'handoff <ip>' for anycast, 'server IP' for
    unicast, or '' when it can't be determined (trace filtered before the CDN).
    """
    if dest_asn in ANYCAST_ASNS:
        ho = _handoff_ip(hops, dest_asn)
        if not ho:
            return ("", "")
        loc = geolocate(ho)
        return (loc, f"handoff {ho}") if loc else ("", f"handoff {ho}")
    loc = geolocate(dest_ip)
    return (loc, "server IP") if loc else ("", "server IP")
