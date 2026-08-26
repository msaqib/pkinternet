#!/usr/bin/env python3
"""
Geographic Traceroute Map — Pakistani Internet Routing
=======================================================
Creates an interactive folium map showing traceroute paths
from Pakistani ISP probes to PK-hosted sites.

Tromboning paths (exiting Pakistan) shown in red.
Local paths shown in green.

Run from repo root:
    python3 experiments/07_longitudinal_panel/analysis/routing_map.py

Requires: pip install folium pandas
Requires: hop_geo.csv from annotate_hops.py
"""

import folium
import pandas as pd
import ipaddress
import json
import math
import re
import os
from folium.plugins import MarkerCluster
from collections import defaultdict

# ── CONFIG ────────────────────────────────────────────────────────────────────

ROUTES_FILE  = 'experiments/07_longitudinal_panel/results/a/routes_20260718_195946.txt'
HOP_GEO_FILE = 'experiments/07_longitudinal_panel/analysis/hop_geo.csv'
PANEL_FILE   = 'experiments/07_longitudinal_panel/results/a/panel_20260718_195946.csv'
OUT_HTML     = 'experiments/07_longitudinal_panel/analysis/figures/routing_map.html'

# ── PHYSICS ARBITER (same method as geo.py's cmd_relocate/cmd_correct) ────────
# ip-api.com geolocation is a database lookup, not ground truth — it repeatedly
# mislabels well-known infrastructure (Cloudflare "Toronto", Google "Mountain
# View", and — caught here — Equinix Singapore as "Sydney"). A hop's claimed
# location is physically impossible if the observed RTT is below the speed-of-
# light-in-vacuum round-trip floor for that distance; such hops are either
# corrected to an independently-verified real location (KNOWN_LOCATIONS, from
# this project's own RDAP-confirmed findings — see METHODOLOGY.md / findings/04,
# findings/10) or dropped from the plotted path rather than shown somewhere false.
V_VAC = 299.792  # km/ms, speed of light in vacuum
EARTH_R = 6371.0  # km, mean Earth radius

# Prefixes RIPEstat whois / PTR hostname independently confirms are NOT where
# ip-api.com claims (checked 2026-07 for this map) — override rather than drop,
# since we have real ground truth for these specific, already-documented blocks.
KNOWN_LOCATIONS = {
    '27.111.228.': (1.290, 103.850, 'Equinix Singapore'),
    '27.111.230.': (1.290, 103.850, 'Equinix Singapore'),
    '27.111.231.': (1.290, 103.850, 'Equinix Singapore'),
    # ip-api claims Sydney/New York; GSL Networks' own PTR hostnames say
    # otherwise — 206.148.27.1/.2 -> "mct-eqxmc1" (Equinix Muscat).
    '206.148.27.': (23.610, 58.590, 'Equinix Muscat (GSL, via PTR)'),
    # 206.148.22.141 -> "sg-eqxsg3-cr7" (Equinix Singapore), same GSL entity.
    '206.148.22.': (1.290, 103.850, 'Equinix Singapore (GSL, via PTR)'),
}


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(a))


PHYSICS_STATS = {'corrected_hits': 0, 'dropped_ips': set(), 'kept': 0}


def resolve_hop_location(ip, hop_rtt, probe_lat, probe_lon, hop_geo):
    """Return (lat, lon) for a hop, or None if its location can't be trusted.

    Known-wrong blocks are corrected to their real (RDAP-verified) location.
    Otherwise, ip-api's claimed location is kept only if it survives the
    physics check: RTT must be >= the vacuum-speed-of-light round-trip floor
    for that distance. A claimed location closer to physically impossible
    than that is dropped rather than plotted."""
    for prefix, (lat, lon, _label) in KNOWN_LOCATIONS.items():
        if ip.startswith(prefix):
            PHYSICS_STATS['corrected_hits'] += 1
            return lat, lon

    geo = hop_geo.get(ip)
    if not geo or geo['lat'] is None or geo['lon'] is None:
        return None

    if hop_rtt is not None:
        vac_floor = 2 * haversine_km(probe_lat, probe_lon, geo['lat'], geo['lon']) / V_VAC
        if hop_rtt < vac_floor:
            PHYSICS_STATS['dropped_ips'].add(ip)
            return None  # physically impossible from this vantage — don't plot it

    PHYSICS_STATS['kept'] += 1
    return geo['lat'], geo['lon']

# ── PROBE LOCATIONS ───────────────────────────────────────────────────────────

PROBES = {
    'cybernet.1016036': {'label': 'Cybernet (Haripur)',    'lat': 33.990, 'lon': 72.908, 'isp': 'Cybernet'},
    'cybernet.1016143': {'label': 'Cybernet (Karachi)',    'lat': 24.858, 'lon': 66.999, 'isp': 'Cybernet'},
    'cybernet.1016154': {'label': 'Cybernet (Karachi)',    'lat': 24.860, 'lon': 66.999, 'isp': 'Cybernet'},
    'fasttel.1014872':  {'label': 'Fasttel (Islamabad)',   'lat': 33.608, 'lon': 72.990, 'isp': 'Fasttel'},
    'nayatel.60223':    {'label': 'Nayatel (Islamabad)',   'lat': 33.699, 'lon': 72.989, 'isp': 'Nayatel'},
    'nayatel.65892':    {'label': 'Nayatel (Islamabad)',   'lat': 33.518, 'lon': 74.362, 'isp': 'Nayatel'},
    'nova.1015679':     {'label': 'Nova (Lahore)',         'lat': 31.462, 'lon': 74.430, 'isp': 'Nova'},
    'orbit.64535':      {'label': 'Orbit (Faisalabad)',    'lat': 31.399, 'lon': 73.118, 'isp': 'Orbit'},
    'ptcl.1016126':     {'label': 'PTCL (Karachi)',        'lat': 24.860, 'lon': 66.999, 'isp': 'PTCL'},
    'ptcl.1016393':     {'label': 'PTCL (Mianwali)',       'lat': 32.569, 'lon': 71.531, 'isp': 'PTCL'},
    'tes.64078':        {'label': 'TES (Rawalpindi)',      'lat': 33.521, 'lon': 74.361, 'isp': 'TES'},
    'tes.64722':        {'label': 'TES (Karachi)',         'lat': 24.799, 'lon': 67.079, 'isp': 'TES'},
    'transworld.62224': {'label': 'Transworld (Lahore)',   'lat': 31.470, 'lon': 74.409, 'isp': 'Transworld'},
    'zcom.7613':        {'label': 'Zcom (Lahore)',         'lat': 31.509, 'lon': 74.338, 'isp': 'Zcom'},
}

ISP_COLORS = {
    'Cybernet':   '#e41a1c',
    'Fasttel':    '#ff7f00',
    'Nayatel':    '#984ea3',
    'Nova':       '#f781bf',
    'Orbit':      '#a65628',
    'PTCL':       '#377eb8',
    'TES':        '#4daf4a',
    'Transworld': '#999999',
    'Zcom':       '#ffff33',
}

# ── IXP LOCATIONS ─────────────────────────────────────────────────────────────

IXPS = [
    # Pakistani IXPs
    {'name': 'PKIX Islamabad', 'lat': 33.673603, 'lon': 73.054592, 'type': 'pk'},
    {'name': 'PKIX Lahore',    'lat': 31.475643, 'lon': 74.342492, 'type': 'pk'},
    {'name': 'PIE Karachi',    'lat': 24.860,    'lon': 67.010,    'type': 'pk'},
    # International IXPs
    {'name': 'DE-CIX Frankfurt',      'lat': 50.110,  'lon': 8.680,   'type': 'intl'},
    {'name': 'Equinix Singapore',     'lat': 1.290,   'lon': 103.850, 'type': 'intl'},
    {'name': 'Equinix Muscat',        'lat': 23.610,  'lon': 58.590,  'type': 'intl'},
    {'name': 'Equinix Dubai',         'lat': 25.200,  'lon': 55.270,  'type': 'intl'},
    {'name': 'LINX London',           'lat': 51.510,  'lon': -0.130,  'type': 'intl'},
    {'name': 'DE-CIX New York',       'lat': 40.710,  'lon': -74.010, 'type': 'intl'},
    {'name': 'AMS-IX Amsterdam',      'lat': 52.370,  'lon': 4.900,   'type': 'intl'},
]

_PRIVATE_NETS = [ipaddress.ip_network(n) for n in (
    '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',  # RFC1918
    '100.64.0.0/10',                                    # CGNAT (RFC 6598)
    '127.0.0.0/8',                                       # loopback
)]


def is_private(ip):
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return any(addr in net for net in _PRIVATE_NETS)

def parse_routes(routes_file):
    """Parse routes txt into list of traceroute paths."""
    paths = []
    current = None

    with open(routes_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()

            # new traceroute section
            m = re.match(r'\s*\[(\w+)\]\s+(\S+)\s+->\s+(\S+)\s+probe\s+(\d+)\s+-\s+(\S+)', line)
            if m:
                if current:
                    paths.append(current)
                current = {
                    'cls':    m.group(1),
                    'target': m.group(2),
                    'probe':  m.group(5),
                    'hops':   [],
                    'verdict': 'unknown',
                    'exit_cc': '',
                }
                continue

            # verdict line
            if current and 'VERDICT' in line:
                line_upper = line.upper()
                if 'INCONCLUSIVE' in line_upper:
                    current['verdict'] = 'inconclusive'
                elif 'TROMBONE' in line_upper:
                    current['verdict'] = 'trombone'
                elif 'LOCAL' in line_upper:
                    current['verdict'] = 'local'
                m2 = re.search(r'exit=(\S+)', line)
                if m2 and m2.group(1) != '-':
                    current['exit_cc'] = m2.group(1)
                continue

            # hop line
            if current and re.match(r'\s+\d+\s+', line):
                parts = line.split()
                if len(parts) >= 3:
                    ip = parts[2] if not parts[2].startswith('(') else None
                    if ip and not is_private(ip):
                        try:
                            rtt = float(parts[1])
                        except ValueError:
                            rtt = None
                        current['hops'].append((ip, rtt))

    if current:
        paths.append(current)

    return paths

def build_map(paths, hop_geo, panel_df):
    """Build folium map."""
    # center on Pakistan
    m = folium.Map(
        location=[30.0, 69.0],
        zoom_start=4,
        tiles='CartoDB positron',
    )

    # ── IXP markers ──────────────────────────────────────────────────────────
    for ixp in IXPS:
        color = 'blue' if ixp['type'] == 'pk' else 'gray'
        icon  = 'exchange' if ixp['type'] == 'pk' else 'cloud'
        folium.Marker(
            location=[ixp['lat'], ixp['lon']],
            popup=folium.Popup(ixp['name'], max_width=200),
            tooltip=ixp['name'],
            icon=folium.Icon(color=color, icon='asterisk', prefix='fa'),
        ).add_to(m)

    # ── Probe markers ─────────────────────────────────────────────────────────
    probe_layer = folium.FeatureGroup(name='Probes')
    for probe_key, info in PROBES.items():
        folium.CircleMarker(
            location=[info['lat'], info['lon']],
            radius=8,
            color='black',
            fill=True,
            fill_color=ISP_COLORS.get(info['isp'], '#333333'),
            fill_opacity=0.9,
            popup=folium.Popup(info['label'], max_width=200),
            tooltip=info['label'],
        ).add_to(probe_layer)
    probe_layer.add_to(m)

    # ── Traceroute paths ──────────────────────────────────────────────────────
    local_layer    = folium.FeatureGroup(name='Local paths (green)')
    trombone_layer = folium.FeatureGroup(name='Tromboning paths (red)')

    # filter PK-hosted sites only
    pk_paths = [p for p in paths if p['cls'] == 'Pakistan']
    print(f"Total paths: {len(paths)}, PK-hosted: {len(pk_paths)}")

    for path in pk_paths:
        # get probe location
        probe_key = path['probe']
        # match probe key to PROBES dict
        probe_info = None
        for k, v in PROBES.items():
            if probe_key.endswith(k.split('.')[-1]):
                probe_info = v
                break
        if not probe_info:
            continue

        # build coordinate sequence
        coords = [[probe_info['lat'], probe_info['lon']]]

        for ip, hop_rtt in path['hops']:
            loc = resolve_hop_location(ip, hop_rtt, probe_info['lat'], probe_info['lon'], hop_geo)
            if loc:
                coords.append([loc[0], loc[1]])

        if len(coords) < 2:
            continue

        # skip paths whose verdict isn't a confirmed local/trombone call —
        # plotting them as green would misrepresent inconclusive routing as local
        if path['verdict'] not in ('local', 'trombone'):
            continue

        color   = '#e41a1c' if path['verdict'] == 'trombone' else '#4daf4a'
        weight  = 1.5
        opacity = 0.5
        layer   = trombone_layer if path['verdict'] == 'trombone' else local_layer

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=weight,
            opacity=opacity,
            tooltip=f"{path['probe']} → {path['target']} [{path['verdict']}]",
        ).add_to(layer)

    local_layer.add_to(m)
    trombone_layer.add_to(m)

    print(f"Physics arbiter: {PHYSICS_STATS['corrected_hits']} hop-occurrences corrected "
          f"to a verified location, {len(PHYSICS_STATS['dropped_ips'])} unique IPs dropped "
          f"(claimed location physically impossible for their recorded RTT), "
          f"{PHYSICS_STATS['kept']} hop-occurrences kept as-is")

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: white; padding: 15px; border-radius: 8px;
                border: 1px solid #ccc; font-size: 13px;">
        <b>Pakistani Internet Routing</b><br>
        <span style="color:#4daf4a">━━</span> Local path (stays in PK)<br>
        <span style="color:#e41a1c">━━</span> Tromboning path (exits PK)<br>
        <br>
        <span style="color:blue">★</span> Pakistani IXP (PKIX/PIE)<br>
        <span style="color:gray">★</span> International IXP<br>
        <br>
        <b>Probes by ISP:</b><br>
    """
    for isp, color in ISP_COLORS.items():
        legend_html += f'<span style="color:{color}">●</span> {isp}<br>'
    legend_html += "</div>"

    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl().add_to(m)

    return m

def main():
    print("Loading data...")

    # load hop geolocation
    if not os.path.exists(HOP_GEO_FILE):
        print(f"ERROR: {HOP_GEO_FILE} not found — run annotate_hops.py first")
        return

    hop_df  = pd.read_csv(HOP_GEO_FILE)
    hop_geo = {}
    for _, row in hop_df.iterrows():
        hop_geo[row['ip']] = {
            'lat': row['lat'] if pd.notna(row['lat']) else None,
            'lon': row['lon'] if pd.notna(row['lon']) else None,
            'city': row['city'] if pd.notna(row['city']) else '',
            'cc':   row['country_code'] if pd.notna(row['country_code']) else '',
        }
    print(f"Loaded {len(hop_geo)} geolocated IPs")

    # load panel for context
    panel_df = pd.read_csv(PANEL_FILE)
    print(f"Loaded {len(panel_df)} panel rows")

    # parse routes
    print("Parsing routes...")
    paths = parse_routes(ROUTES_FILE)
    print(f"Parsed {len(paths)} traceroute paths")

    # build map
    print("Building map...")
    m = build_map(paths, hop_geo, panel_df)

    # save
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    m.save(OUT_HTML)
    print(f"Saved to {OUT_HTML}")
    print("Open in browser to view.")

if __name__ == '__main__':
    main()