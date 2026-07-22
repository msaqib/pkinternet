#!/usr/bin/env python3
"""
Probe Location Map — Pakistan
==============================
Generates a clean map of Pakistan showing RIPE Atlas probe locations
colored by ISP. For inclusion in the paper.

Run from repo root:
    python3 experiments/07_longitudinal_panel/analysis/probe_map.py

Requires: pip install folium
Output: experiments/07_longitudinal_panel/analysis/figures/probe_map.html
"""

import folium
import os

# ── PROBE DATA (slightly offset to avoid overlap) ─────────────────────────────

PROBES = [
    # Haripur
    {'isp': 'Cybernet',   'city': 'Haripur',     'lat': 33.990, 'lon': 72.908, 'n': 1},
    # Islamabad cluster — offset each probe
    {'isp': 'Fasttel',    'city': 'Islamabad',   'lat': 33.640, 'lon': 72.970, 'n': 1},
    {'isp': 'Nayatel',    'city': 'Islamabad',   'lat': 33.699, 'lon': 73.030, 'n': 2},
    # Rawalpindi
    {'isp': 'TES',        'city': 'Rawalpindi',  'lat': 33.521, 'lon': 73.100, 'n': 1},
    # Mianwali
    {'isp': 'PTCL',       'city': 'Mianwali',    'lat': 32.569, 'lon': 71.531, 'n': 1},
    # Faisalabad
    {'isp': 'Orbit',      'city': 'Faisalabad',  'lat': 31.399, 'lon': 73.118, 'n': 1},
    # Lahore cluster — offset each probe
    {'isp': 'Nova',       'city': 'Lahore',      'lat': 31.520, 'lon': 74.280, 'n': 1},
    {'isp': 'Transworld', 'city': 'Lahore',      'lat': 31.470, 'lon': 74.340, 'n': 1},
    {'isp': 'Zcom',       'city': 'Lahore',      'lat': 31.509, 'lon': 74.400, 'n': 1},
    # Karachi cluster — offset each probe
    {'isp': 'Cybernet',   'city': 'Karachi',     'lat': 24.900, 'lon': 66.960, 'n': 2},
    {'isp': 'PTCL',       'city': 'Karachi',     'lat': 24.858, 'lon': 67.010, 'n': 1},
    {'isp': 'TES',        'city': 'Karachi',     'lat': 24.820, 'lon': 67.060, 'n': 1},
]

ISP_COLORS = {
    'Cybernet':   '#e41a1c',
    'Fasttel':    '#ff7f00',
    'Nayatel':    '#984ea3',
    'Nova':       '#f781bf',
    'Orbit':      '#a65628',
    'PTCL':       '#377eb8',
    'TES':        '#4daf4a',
    'Transworld': '#666666',
    'Zcom':       '#b8860b',
}

# PKIX/PIE locations
IXPS = [
    {'name': 'PKIX Islamabad', 'lat': 33.673603, 'lon': 73.054592},
    {'name': 'PKIX Lahore',    'lat': 31.475643, 'lon': 74.342492},
    {'name': 'PIE Karachi',    'lat': 24.850,    'lon': 67.000},
]

def main():
    m = folium.Map(
        location=[30.5, 69.5],
        zoom_start=6,
        tiles='CartoDB positron',
    )

    # IXP markers as small cross
    for ixp in IXPS:
        folium.Marker(
            location=[ixp['lat'], ixp['lon']],
            tooltip=ixp['name'],
            popup=folium.Popup(ixp['name'], max_width=150),
            icon=folium.DivIcon(
                html=f'<div style="font-size:18px;color:#1a75ff;font-weight:bold;line-height:1;text-align:center;">✕</div>',
                icon_size=(18, 18),
                icon_anchor=(9, 9),
            )
        ).add_to(m)

        # IXP label
        folium.Marker(
            location=[ixp['lat'] - 0.18, ixp['lon'] + 0.15],
            icon=folium.DivIcon(
                html=f'<div style="font-size:9px;color:#1a75ff;white-space:nowrap">{ixp["name"]}</div>',
                icon_size=(120, 15),
                icon_anchor=(0, 0),
            )
        ).add_to(m)

    # probe markers
    for p in PROBES:
        color = ISP_COLORS.get(p['isp'], '#333333')
        label = f"{p['isp']} — {p['city']}"
        if p['n'] > 1:
            label += f" ({p['n']} probes)"

        folium.CircleMarker(
            location=[p['lat'], p['lon']],
            radius=6,
            color='white',
            weight=1.2,
            fill=True,
            fill_color=color,
            fill_opacity=0.95,
            tooltip=label,
            popup=folium.Popup(label, max_width=200),
        ).add_to(m)

    # city labels (one per city, not per probe)
    cities = {
        'Haripur':    (34.05,  72.908),
        'Islamabad':  (33.80,  73.030),
        'Rawalpindi': (33.55,  73.20),
        'Mianwali':   (32.65,  71.531),
        'Faisalabad': (31.30,  73.118),
        'Lahore':     (31.60,  74.340),
        'Karachi':    (24.76,  67.010),
    }
    for city, (lat, lon) in cities.items():
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:bold;color:#333;white-space:nowrap">{city}</div>',
                icon_size=(80, 15),
                icon_anchor=(0, 0),
            )
        ).add_to(m)

    # legend
    legend_html = '''
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
                background:white;padding:12px;border-radius:8px;
                border:1px solid #ccc;font-size:11px;line-height:1.8;">
        <b>Probes by ISP</b><br>
    '''
    for isp, color in ISP_COLORS.items():
        legend_html += f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{color};margin-right:5px;vertical-align:middle;"></span>{isp}<br>'
    legend_html += '<br><span style="color:#1a75ff;font-size:14px;">✕</span> IXP (PKIX / PIE)</div>'

    m.get_root().html.add_child(folium.Element(legend_html))

    out = 'experiments/07_longitudinal_panel/analysis/figures/probe_map.html'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    m.save(out)
    print(f"Saved to {out}")

if __name__ == '__main__':
    main()