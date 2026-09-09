#!/usr/bin/env python3
"""Generate slides.html and slides.pptx for the block-routing census.

Single source of truth for the deck. Edit SLIDES, re-run, both outputs update.
    python make_slides.py
"""
import html
import os
import sys

OUT = os.path.dirname(os.path.abspath(__file__))

# Each slide: (eyebrow, title, blocks)
# block kinds: ("p", text) | ("ul", [items]) | ("table", [headers], [[row]]) | ("flow", [steps])
SVG_TROMBONE = """
<svg viewBox="0 0 760 285" role="img" aria-label="A packet from a Lahore vantage to a Lahore block: seven addresses stay inside Pakistan at 3.3 ms, one exits via Omantel in Oman at 113.8 ms and returns." style="max-width:100%;height:auto">
  <defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
  <marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="#b4531f"/></marker></defs>
  <rect x="30" y="150" width="700" height="115" rx="8" fill="none" stroke="currentColor" stroke-dasharray="5 5" opacity=".35"/>
  <text x="44" y="255" font-size="11" fill="currentColor" opacity=".55" letter-spacing="1.5">PAKISTAN</text>
  <rect x="60" y="178" width="185" height="50" rx="5" fill="none" stroke="currentColor"/>
  <text x="152" y="199" font-size="12.5" text-anchor="middle" fill="currentColor">Vantage — Nova</text>
  <text x="152" y="216" font-size="11.5" text-anchor="middle" fill="currentColor" opacity=".7">Lahore</text>
  <rect x="515" y="178" width="185" height="50" rx="5" fill="none" stroke="currentColor"/>
  <text x="607" y="199" font-size="12.5" text-anchor="middle" fill="currentColor">122.129.94.0/24</text>
  <text x="607" y="216" font-size="11.5" text-anchor="middle" fill="currentColor" opacity=".7">Brain Telecom, Lahore</text>
  <line x1="250" y1="203" x2="508" y2="203" stroke="currentColor" stroke-width="1.6" marker-end="url(#ar)"/>
  <text x="379" y="195" font-size="11.5" text-anchor="middle" fill="currentColor">7 addresses · local · 3.3 ms</text>
  <rect x="300" y="30" width="160" height="46" rx="5" fill="none" stroke="#b4531f" stroke-width="1.5"/>
  <text x="380" y="49" font-size="12.5" text-anchor="middle" fill="#b4531f">Omantel</text>
  <text x="380" y="65" font-size="11.5" text-anchor="middle" fill="#b4531f" opacity=".85">Oman</text>
  <path d="M152,176 C152,110 220,53 296,53" fill="none" stroke="#b4531f" stroke-width="1.6" marker-end="url(#arw)"/>
  <path d="M464,53 C540,53 607,110 607,176" fill="none" stroke="#b4531f" stroke-width="1.6" marker-end="url(#arw)"/>
  <text x="185" y="105" font-size="11.5" fill="#b4531f">.199 leaves</text>
  <text x="530" y="105" font-size="11.5" fill="#b4531f">113.8 ms</text>
</svg>"""

SVG_FUNNEL = """
<svg viewBox="0 0 740 300" role="img" aria-label="Funnel from 77 FLL licensees to 48 announcing ISPs, yielding 747 announced blocks." style="max-width:100%;height:auto">
  <defs><marker id="fa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
  <rect x="20" y="18" width="520" height="34" rx="4" fill="currentColor" opacity=".13"/>
  <text x="32" y="40" font-size="12.5" fill="currentColor">77 &nbsp;FLL licensees</text>
  <text x="556" y="40" font-size="11" fill="currentColor" opacity=".6">PTA licence roster</text>
  <rect x="20" y="66" width="479" height="34" rx="4" fill="currentColor" opacity=".18"/>
  <text x="32" y="88" font-size="12.5" fill="currentColor">71 &nbsp;have an ASN on record</text>
  <text x="556" y="88" font-size="11" fill="#b4531f">− 6 no ASN</text>
  <rect x="20" y="114" width="446" height="34" rx="4" fill="currentColor" opacity=".23"/>
  <text x="32" y="136" font-size="12.5" fill="currentColor">66 &nbsp;distinct ASNs</text>
  <text x="556" y="136" font-size="11" fill="#b4531f">− 5 share an ASN</text>
  <rect x="20" y="162" width="324" height="34" rx="4" fill="currentColor" opacity=".3"/>
  <text x="32" y="184" font-size="12.5" fill="currentColor">48 &nbsp;announce prefixes</text>
  <text x="556" y="184" font-size="11" fill="#b4531f">− 18 announce nothing</text>
  <line x1="182" y1="202" x2="182" y2="228" stroke="currentColor" stroke-width="1.5" marker-end="url(#fa)"/>
  <rect x="20" y="234" width="520" height="48" rx="5" fill="none" stroke="currentColor" stroke-width="1.6"/>
  <text x="32" y="255" font-size="13" fill="currentColor">747 announced blocks</text>
  <text x="32" y="273" font-size="11.5" fill="currentColor" opacity=".7">206,592 addresses · 725 are /24, 22 are larger</text>
  <text x="556" y="262" font-size="11" fill="currentColor" opacity=".6">the census universe</text>
</svg>"""

SVG_K = """
<svg viewBox="0 0 740 175" role="img" aria-label="A /24 block of 256 addresses with eight evenly spaced probe targets marked." style="max-width:100%;height:auto">
  <text x="20" y="26" font-size="12.5" fill="currentColor">One block — 203.128.7.0/24 — is 256 addresses</text>
  <rect x="20" y="42" width="700" height="30" rx="3" fill="currentColor" opacity=".12"/>
  <text x="20" y="92" font-size="11" fill="currentColor" opacity=".6">.0</text>
  <text x="706" y="92" font-size="11" fill="currentColor" opacity=".6">.255</text>
  <circle cx="97" cy="57" r="6" fill="#2f5fa8"/><circle cx="174" cy="57" r="6" fill="#2f5fa8"/>
  <circle cx="253" cy="57" r="6" fill="#2f5fa8"/><circle cx="330" cy="57" r="6" fill="#2f5fa8"/>
  <circle cx="410" cy="57" r="6" fill="#2f5fa8"/><circle cx="487" cy="57" r="6" fill="#2f5fa8"/>
  <circle cx="566" cy="57" r="6" fill="#2f5fa8"/><circle cx="643" cy="57" r="6" fill="#2f5fa8"/>
  <text x="97" y="118" font-size="10.5" text-anchor="middle" fill="currentColor" opacity=".75">.28</text>
  <text x="174" y="118" font-size="10.5" text-anchor="middle" fill="currentColor" opacity=".75">.56</text>
  <text x="253" y="118" font-size="10.5" text-anchor="middle" fill="currentColor" opacity=".75">.85</text>
  <text x="330" y="118" font-size="10.5" text-anchor="middle" fill="currentColor" opacity=".75">.113</text>
  <text x="410" y="118" font-size="10.5" text-anchor="middle" fill="currentColor" opacity=".75">.142</text>
  <text x="487" y="118" font-size="10.5" text-anchor="middle" fill="currentColor" opacity=".75">.170</text>
  <text x="566" y="118" font-size="10.5" text-anchor="middle" fill="currentColor" opacity=".75">.199</text>
  <text x="643" y="118" font-size="10.5" text-anchor="middle" fill="currentColor" opacity=".75">.227</text>
  <text x="20" y="152" font-size="12.5" fill="#2f5fa8">K = 8 — we traceroute these eight, and none of the other 248</text>
</svg>"""

SVG_SPLIT = """
<svg viewBox="0 0 740 250" role="img" aria-label="Two real blocks: in one, all eight probed addresses trombone via CHINANET; in the other, seven are local and one exits via Omantel." style="max-width:100%;height:auto">
  <text x="20" y="24" font-size="12.5" fill="currentColor">203.128.7.0/24 &nbsp;from PTCL Karachi</text>
  <circle cx="60" cy="56" r="9" fill="#b4531f"/><circle cx="140" cy="56" r="9" fill="#b4531f"/>
  <circle cx="220" cy="56" r="9" fill="#b4531f"/><circle cx="300" cy="56" r="9" fill="#b4531f"/>
  <circle cx="380" cy="56" r="9" fill="#b4531f"/><circle cx="460" cy="56" r="9" fill="#b4531f"/>
  <circle cx="540" cy="56" r="9" fill="#b4531f"/><circle cx="620" cy="56" r="9" fill="#b4531f"/>
  <text x="20" y="92" font-size="12" fill="#b4531f">All 8 exit via CHINANET at ~42 ms — the block is unambiguous</text>
  <line x1="20" y1="112" x2="720" y2="112" stroke="currentColor" opacity=".2"/>
  <text x="20" y="146" font-size="12.5" fill="currentColor">122.129.94.0/24 &nbsp;from Nova Lahore</text>
  <circle cx="60" cy="178" r="9" fill="#22705f"/><circle cx="140" cy="178" r="9" fill="#22705f"/>
  <circle cx="220" cy="178" r="9" fill="#22705f"/><circle cx="300" cy="178" r="9" fill="#22705f"/>
  <circle cx="380" cy="178" r="9" fill="#22705f"/><circle cx="460" cy="178" r="9" fill="#22705f"/>
  <circle cx="540" cy="178" r="9" fill="#b4531f"/><circle cx="620" cy="178" r="9" fill="#22705f"/>
  <text x="540" y="206" font-size="10.5" text-anchor="middle" fill="#b4531f">.199</text>
  <text x="20" y="238" font-size="12" fill="currentColor">Seven local at 3–20 ms · <tspan fill="#b4531f">one exits via Omantel at 113.8 ms</tspan> — the block is split</text>
</svg>"""

SVG_PHASES = """
<svg viewBox="0 0 760 210" role="img" aria-label="Six phases: freeze vantages, pilot, three census rounds, detect, aggregate, write up — each with its exit criterion." style="max-width:100%;height:auto">
  <defs><marker id="pa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
  <g font-size="11.5" fill="currentColor">
  <rect x="8" y="40" width="108" height="52" rx="5" fill="none" stroke="currentColor"/>
  <text x="62" y="62" text-anchor="middle" font-size="10.5" opacity=".6">PHASE 1</text>
  <text x="62" y="80" text-anchor="middle">Freeze vantages</text>
  <rect x="138" y="40" width="108" height="52" rx="5" fill="none" stroke="currentColor"/>
  <text x="192" y="62" text-anchor="middle" font-size="10.5" opacity=".6">PHASE 2</text>
  <text x="192" y="80" text-anchor="middle">Pilot</text>
  <rect x="268" y="40" width="108" height="52" rx="5" fill="none" stroke="#2f5fa8" stroke-width="1.8"/>
  <text x="322" y="62" text-anchor="middle" font-size="10.5" fill="#2f5fa8">PHASE 3</text>
  <text x="322" y="80" text-anchor="middle" fill="#2f5fa8">Census × 3</text>
  <rect x="398" y="40" width="108" height="52" rx="5" fill="none" stroke="currentColor"/>
  <text x="452" y="62" text-anchor="middle" font-size="10.5" opacity=".6">PHASE 4</text>
  <text x="452" y="80" text-anchor="middle">Detect</text>
  <rect x="528" y="40" width="108" height="52" rx="5" fill="none" stroke="currentColor"/>
  <text x="582" y="62" text-anchor="middle" font-size="10.5" opacity=".6">PHASE 5</text>
  <text x="582" y="80" text-anchor="middle">Aggregate</text>
  <rect x="658" y="40" width="94" height="52" rx="5" fill="none" stroke="currentColor"/>
  <text x="705" y="62" text-anchor="middle" font-size="10.5" opacity=".6">PHASE 6</text>
  <text x="705" y="80" text-anchor="middle">Write up</text>
  <line x1="118" y1="66" x2="134" y2="66" stroke="currentColor" marker-end="url(#pa)"/>
  <line x1="248" y1="66" x2="264" y2="66" stroke="currentColor" marker-end="url(#pa)"/>
  <line x1="378" y1="66" x2="394" y2="66" stroke="currentColor" marker-end="url(#pa)"/>
  <line x1="508" y1="66" x2="524" y2="66" stroke="currentColor" marker-end="url(#pa)"/>
  <line x1="638" y1="66" x2="654" y2="66" stroke="currentColor" marker-end="url(#pa)"/>
  </g>
  <g font-size="10" fill="currentColor" opacity=".65">
  <text x="62" y="115" text-anchor="middle">7 probes, path</text><text x="62" y="128" text-anchor="middle">visibility confirmed</text>
  <text x="192" y="115" text-anchor="middle">split rate measured</text><text x="192" y="128" text-anchor="middle">on this population</text>
  <text x="322" y="115" text-anchor="middle">3 complete rounds,</text><text x="322" y="128" text-anchor="middle">equal per vantage</text>
  <text x="452" y="115" text-anchor="middle">verdict per</text><text x="452" y="128" text-anchor="middle">address</text>
  <text x="582" y="115" text-anchor="middle">per-ISP ranges,</text><text x="582" y="128" text-anchor="middle">vantage × dest matrix</text>
  <text x="705" y="115" text-anchor="middle">findings</text><text x="705" y="128" text-anchor="middle">document</text>
  </g>
  <text x="8" y="175" font-size="11" fill="currentColor" opacity=".8">Exit criteria — a phase is not done until its line above is true.</text>
  <text x="8" y="194" font-size="11" fill="#2f5fa8">Phase 3 is the only one that repeats. Equal coverage per vantage is what makes it quotable.</text>
</svg>"""



# --- the vantage x destination matrix, from run_20260627_192918 -------------
# columns, in the order drawn
MCOLS = ["PTCL Khi", "Cybernet Hrp", "Cybernet Khi", "Orbit Fsd",
         "Nova Lhe", "Zcom Lhe", "Nayatel Isb"]
# rows: (destination ISP, [(rate%, n) or None per column])
MROWS = [
    ("Connect Communications",  [(0,39),(52,116),(7,608),(3,515),(2,829),(3,859),(3,377)]),
    ("Optix Pakistan",          [(9,162),(39,36),(12,348),(7,312),(6,592),(2,626),(2,457)]),
    ("Brain Telecommunication", [(4,336),(10,121),(6,264),(6,291),(4,346),(6,387),(7,298)]),
    ("Broadband Vision",        [(14,224),(100,4),(18,157),(32,44),(24,352),(22,418),(3,493)]),
    ("CMPak LDI",               [(9,293),None,None,(4,24),(5,444),(3,485),(4,341)]),
    ("Pace Telecom",            [(80,90),(47,90),(41,99),(9,99),(12,106),(9,109),(6,115)]),
    ("Multinet Pakistan",       [None,None,(2,112),(3,145),(7,183),(4,184),(15,60)]),
    ("Cube XS Weatherly",       [(0,8),(100,54),(0,93),(0,82),(2,96),(1,95),(5,172)]),
]
MIN_N = 40   # below this a cell is too thin to read as a rate

# Brain Telecom, per vantage: (vantage, detours, probes)
BRAIN = [("PTCL Karachi", 13, 336), ("Cybernet Haripur", 12, 121),
         ("Nayatel Islamabad", 22, 298), ("Cybernet Karachi", 16, 264),
         ("Z-Com Lahore", 23, 387), ("Orbit Faisalabad", 17, 291),
         ("Nova Lahore", 13, 346)]


def svg_brain():
    """Horizontal bars: one destination ISP seen from seven vantage points."""
    W, LX, BX, BW = 740, 148, 158, 500
    rowh, top = 32, 46
    H = top + rowh * len(BRAIN) + 30
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Brain Telecommunication\'s '
         f'detour rate from seven vantage points, after the squatted-address correction: '
         f'between 3.8 and 9.9 percent everywhere, with no outlier." style="max-width:100%;height:auto">']
    p.append(f'<text x="0" y="18" font-size="12.5" fill="currentColor">Brain Telecommunication — '
             f'the same 49 blocks, reached from seven different networks</text>')
    for i, (name, t, n) in enumerate(BRAIN):
        y = top + i * rowh
        hot = t / n > 0.5
        col = "#b4531f" if hot else "#22705f"
        p.append(f'<text x="{LX}" y="{y+13}" font-size="11.5" text-anchor="end" '
                 f'fill="currentColor">{name}</text>')
        p.append(f'<rect x="{BX}" y="{y+2}" width="{BW}" height="15" rx="2" '
                 f'fill="currentColor" opacity=".07"/>')
        w = max(1.5, BW * t / n)
        p.append(f'<rect x="{BX}" y="{y+2}" width="{w:.1f}" height="15" rx="2" fill="{col}"/>')
        p.append(f'<text x="{BX+w+8:.1f}" y="{y+14}" font-size="11" fill="{col}">'
                 f'{100*t/n:.1f}%  ({t} of {n})</text>')
    p.append(f'<text x="0" y="{H-8}" font-size="11.5" fill="currentColor" opacity=".7">'
             f'Corrected for the squatted address: 5.7% overall, and no vantage stands out.</text>')
    p.append('</svg>')
    return "".join(p)


def svg_matrix():
    """Heatmap: destination ISP (rows) x vantage point (columns)."""
    LX, CW, CH, TOP = 168, 78, 30, 62
    W, H = LX + CW * len(MCOLS) + 8, TOP + CH * len(MROWS) + 46
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Heatmap of detour rate by '
         f'destination ISP and vantage point. Rates vary strongly across both axes; several '
         f'cells are missing or too thinly sampled." style="max-width:100%;height:auto">']
    for j, c in enumerate(MCOLS):
        x = LX + j * CW + CW / 2
        p.append(f'<text x="{x:.0f}" y="{TOP-12}" font-size="10" text-anchor="middle" '
                 f'fill="currentColor" opacity=".65">{c}</text>')
    for i, (name, cells) in enumerate(MROWS):
        y = TOP + i * CH
        p.append(f'<text x="{LX-10}" y="{y+19}" font-size="11" text-anchor="end" '
                 f'fill="currentColor">{name}</text>')
        for j, cell in enumerate(cells):
            x = LX + j * CW
            if cell is None:
                p.append(f'<rect x="{x+1}" y="{y+1}" width="{CW-3}" height="{CH-3}" rx="2" '
                         f'fill="none" stroke="currentColor" stroke-opacity=".18"/>')
                p.append(f'<text x="{x+CW/2:.0f}" y="{y+20}" font-size="11" '
                         f'text-anchor="middle" fill="currentColor" opacity=".3">—</text>')
                continue
            rate, n = cell
            if n < MIN_N:
                p.append(f'<rect x="{x+1}" y="{y+1}" width="{CW-3}" height="{CH-3}" rx="2" '
                         f'fill="none" stroke="currentColor" stroke-opacity=".3" '
                         f'stroke-dasharray="3 3"/>')
                p.append(f'<text x="{x+CW/2:.0f}" y="{y+20}" font-size="9.5" '
                         f'text-anchor="middle" fill="currentColor" opacity=".45">n={n}</text>')
                continue
            op = 0.08 + 0.84 * (rate / 100) ** 0.65
            fg = "#ffffff" if rate >= 55 else "currentColor"
            p.append(f'<rect x="{x+1}" y="{y+1}" width="{CW-3}" height="{CH-3}" rx="2" '
                     f'fill="#b4531f" fill-opacity="{op:.2f}"/>')
            p.append(f'<text x="{x+CW/2:.0f}" y="{y+20}" font-size="11.5" '
                     f'text-anchor="middle" fill="{fg}">{rate}%</text>')
    yb = TOP + CH * len(MROWS) + 20
    p.append(f'<rect x="{LX}" y="{yb-9}" width="13" height="11" rx="2" fill="#b4531f" fill-opacity=".15"/>')
    p.append(f'<rect x="{LX+17}" y="{yb-9}" width="13" height="11" rx="2" fill="#b4531f" fill-opacity=".5"/>')
    p.append(f'<rect x="{LX+34}" y="{yb-9}" width="13" height="11" rx="2" fill="#b4531f" fill-opacity=".92"/>')
    p.append(f'<text x="{LX+55}" y="{yb}" font-size="10.5" fill="currentColor" opacity=".7">'
             f'low → high detour rate</text>')
    p.append(f'<text x="{LX+205}" y="{yb}" font-size="10.5" fill="currentColor" opacity=".7">'
             f'dashed = fewer than {MIN_N} probes · — = never measured</text>')
    p.append('</svg>')
    return "".join(p)



def svg_sizes():
    """Flat K vs constant density, on the three block sizes that actually occur."""
    W, H = 740, 292
    PANEL = [(18, "Flat K = 8 per block", [8, 8, 8]),
             (400, "8 per /24-equivalent", [8, 16, 32])]
    BW, ROWS = 322, [("/24", "256 addr", 76), ("/23", "512 addr", 146), ("/22", "1,024 addr", 216)]
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Comparison of flat K equals 8 versus '
         f'constant density sampling across /24, /23 and /22 blocks: a flat K thins out as the '
         f'block grows, constant density keeps the spacing even." style="max-width:100%;height:auto">']
    for px, title, counts in PANEL:
        good = counts[0] != counts[2]
        col = "#22705f" if good else "#b4531f"
        p.append(f'<text x="{px}" y="22" font-size="12.5" fill="{col}">{title}</text>')
        for (lab, addr, y), n in zip(ROWS, counts):
            p.append(f'<text x="{px}" y="{y-9}" font-size="10.5" fill="currentColor" '
                     f'opacity=".65">{lab} · {addr}</text>')
            p.append(f'<rect x="{px}" y="{y}" width="{BW}" height="26" rx="3" '
                     f'fill="currentColor" opacity=".09"/>')
            for i in range(1, n + 1):
                cx = px + BW * i / (n + 1)
                p.append(f'<circle cx="{cx:.1f}" cy="{y+13}" r="3.1" fill="{col}"/>')
            p.append(f'<text x="{px+BW+8}" y="{y+17}" font-size="10.5" fill="{col}">{n}</text>')
    p.append('<line x1="371" y1="34" x2="371" y2="252" stroke="currentColor" opacity=".18"/>')
    p.append('<text x="18" y="272" font-size="11.5" fill="#b4531f">Coverage thins 4× by /22 — '
             'and 32× on the single /19</text>')
    p.append('<text x="400" y="272" font-size="11.5" fill="#22705f">Spacing stays constant at '
             'every size · costs 8% more probes</text>')
    p.append('</svg>')
    return "".join(p)



def svg_bgp():
    """Provenance chain for the announced-prefix data."""
    W, H = 740, 210
    boxes = [(8, 158, "Pakistani ISPs", "announce prefixes in BGP"),
             (186, 158, "RIPE NCC RIS", "global route collectors"),
             (364, 158, "RIPEstat API", "announced-prefixes"),
             (542, 190, "blocks_all.csv", "747 blocks · 48 ASNs")]
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Announced prefixes come from ISPs '
         f'BGP announcements, seen by RIPE NCC RIS route collectors, served by the RIPEstat '
         f'announced-prefixes API, and written to blocks_all.csv." '
         f'style="max-width:100%;height:auto">']
    p.append('<defs><marker id="ba" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
             'markerHeight="7" orient="auto-start-reverse">'
             '<path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>')
    for i, (x, w, t1, t2) in enumerate(boxes):
        last = i == len(boxes) - 1
        st = "#2f5fa8" if last else "currentColor"
        p.append(f'<rect x="{x}" y="46" width="{w}" height="54" rx="5" fill="none" '
                 f'stroke="{st}" stroke-width="{1.8 if last else 1}"/>')
        p.append(f'<text x="{x+w/2:.0f}" y="70" font-size="12.5" text-anchor="middle" '
                 f'fill="{st}">{t1}</text>')
        p.append(f'<text x="{x+w/2:.0f}" y="88" font-size="11" text-anchor="middle" '
                 f'fill="{st}" opacity=".75">{t2}</text>')
        if not last:
            x2 = x + w
            p.append(f'<line x1="{x2+3}" y1="73" x2="{boxes[i+1][0]-4}" y2="73" '
                     f'stroke="currentColor" marker-end="url(#ba)"/>')
    p.append('<text x="8" y="26" font-size="11" fill="currentColor" opacity=".6">'
             'No API key, no credits — a public BGP view, queried once per ASN</text>')
    p.append('<text x="186" y="130" font-size="11" fill="#b4531f">'
             '↑ the limit lives here: RIS sees a prefix only if one of its peers is told about it</text>')
    p.append('<text x="186" y="152" font-size="11" fill="currentColor" opacity=".7">'
             'A prefix announced only to domestic peers may never reach a collector —</text>')
    p.append('<text x="186" y="170" font-size="11" fill="currentColor" opacity=".7">'
             'and that is exactly the kind this study cares about.</text>')
    p.append('</svg>')
    return "".join(p)


SVG_BRAIN = svg_brain()
SVG_BGP = svg_bgp()
SVG_SIZES = svg_sizes()
SVG_MATRIX = svg_matrix()


# --- real traces, transcribed from results/run_20260627_192918/routes_*.txt ----
# row = (hop, rtt, ip, "operator (cc)", flag)   flag: "" | "out" | "back" | "art" | "jump"
# Same target address, two vantage points. Both traces gapless and reached=True.
T_SAME_PTCL = (
    "from PTCL Karachi  ·  probe 1016126",
    "<b>TROMBONE</b> · exit CHINANET (CN) · maxRTT <b>43.7 ms</b> · reached=True · no missing hops",
    [("1","1.1","192.168.10.1","RFC1918",""),
     ("2","25.6","39.39.0.1","AS17557 PKTELECOM (PK)",""),
     ("3","25.9","10.253.5.94","RFC1918",""),
     ("4","26.0","10.253.4.40","RFC1918",""),
     ("5","41.6","10.253.4.17","RFC1918",""),
     ("6","40.9","10.253.8.19","RFC1918",""),
     ("7","41.1","182.45.51.22","AS4134 CHINANET (CN)","out"),
     ("8","43.3","10.181.224.166","RFC1918",""),
     ("9","43.7","203.128.7.75","AS17911 Brain Telecom (PK)","back"),
     ("10","43.6","203.128.7.75","AS17911 Brain Telecom (PK)","back")])

T_SAME_NOVA = (
    "from Nova Lahore  ·  probe 1015679",
    "<b>LOCAL</b> · never leaves PK · maxRTT <b>3.5 ms</b> · reached=True · no missing hops",
    [("1","0.5","192.168.100.1","RFC1918",""),
     ("2","1.4","70.70.71.137","AS6327 SHAW (CA)","art"),
     ("3","2.4","110.93.212.161","AS38193 Transworld (PK)",""),
     ("4","2.3","110.93.252.139","Transworld (PK)",""),
     ("5","2.5","110.93.255.94","Transworld (PK)",""),
     ("6","2.8","117.20.30.20","AS38193 Transworld (PK)",""),
     ("7","3.5","10.180.170.154","RFC1918",""),
     ("8","2.9","203.128.7.75","AS17911 Brain Telecom (PK)","back"),
     ("9","2.9","203.128.7.75","AS17911 Brain Telecom (PK)","back"),
     ("","","","","")])

T_CHINANET = (
    "Brain Telecommunication (AS17911)  →  122.129.64.113   ·   block 122.129.64.0/24",
    "from probe 1016126 · ptcl.khi &nbsp;|&nbsp; TROMBONE · reached=True · "
    "exit CHINANET (CN) · transit PTCL · maxRTT 43.8 ms · evidence=foreign_hop",
    [("1","1.1","192.168.10.1","RFC1918",""),
     ("2","25.4","39.39.0.1","PKTELECOM (PK)",""),
     ("3","26.0","10.253.5.98","RFC1918",""),
     ("4","*","(no response)","",""),
     ("5","42.1","10.253.4.37","RFC1918",""),
     ("6","42.7","10.253.8.39","RFC1918",""),
     ("7","42.3","182.45.51.22","CHINANET-BACKBONE (CN)","out"),
     ("8","43.0","10.181.224.166","RFC1918",""),
     ("9","43.8","203.128.7.254","BRAINPK — Brain Telecom (PK)","back"),
     ("10","*","(no response)","",""),
     ("255","*","(no response)","","")])

T_SPLIT_OUT = (
    "→ 122.129.94.<b>199</b>",
    "TROMBONE · exit OMANTEL (AE) · maxRTT 113.8 ms",
    [("1","0.8","192.168.100.1","RFC1918",""),
     ("2","14.3","70.70.71.137","SHAW (CA)","art"),
     ("3","16.7","110.93.212.161","TWA (PK)",""),
     ("4","14.8","110.93.197.153","TWA (PK)",""),
     ("5","15.8","172.16.48.2","RFC1918",""),
     ("6","20.0","172.16.253.2","RFC1918",""),
     ("7","*","(no response)","",""),
     ("8","103.6","213.202.6.198","OMANTEL (AE)","out"),
     ("9","100.7","134.0.220.242","OMANTEL (AE)","out"),
     ("10","99.0","103.231.152.16","BBIX (HK)","out"),
     ("11","113.7","119.110.116.166","MC-IX (ID)","out"),
     ("12","113.8","119.110.117.87","MC-IX (ID)","out"),
     ("13","113.3","119.110.117.87","MC-IX (ID)","out")])

T_SPLIT_LOCAL = (
    "→ 122.129.94.<b>170</b>",
    "LOCAL · maxRTT 15.1 ms",
    [("1","0.3","192.168.100.1","RFC1918",""),
     ("2","15.1","70.70.71.137","SHAW (CA)","art"),
     ("3","9.2","110.93.212.161","TWA (PK)",""),
     ("4","7.6","110.93.197.153","TWA (PK)",""),
     ("5","7.7","172.16.48.2","RFC1918",""),
     ("6","8.4","172.16.253.2","RFC1918",""),
     ("7","*","(no response)","",""),
     ("8","*","(no response)","",""),
     ("9","*","(no response)","",""),
     ("10","*","(no response)","",""),
     ("11","*","(no response)","",""),
     ("255","*","(no response)","",""),
     ("","","","","")])

T_BACKSTOP = (
    "Bliss Communication (AS141361)  →  119.157.80.113   ·   block 119.157.80.0/24",
    "from probe 1015679 · nova.lhe &nbsp;|&nbsp; TROMBONE · <b>exit = ? — no foreign hop ever "
    "replied</b> · maxRTT 97.1 ms · evidence=rtt(jump=66, max=97)",
    [("1","0.4","192.168.100.1","RFC1918",""),
     ("2","6.9","70.70.71.137","SHAW (CA)","art"),
     ("3","7.9","110.93.212.161","TWA (PK)",""),
     ("4","30.3","110.93.254.66","TWA (PK)",""),
     ("5","27.7","110.93.252.246","TWA (PK)",""),
     ("6","*","(no response)","",""),
     ("7","93.6","10.253.4.25","RFC1918","jump"),
     ("8","96.8","10.253.4.75","RFC1918",""),
     ("9","97.1","119.158.67.74","PKTELECOM (PK)",""),
     ("10","96.2","10.99.24.14","RFC1918",""),
     ("11","96.2","59.103.47.13","HG TELECOM (PK)",""),
     ("12","96.6","103.157.154.58","BCNL — Bliss (PK)","back")])

SLIDES = [
    ("", "National Block-Routing Census", [
        ("p", "Does traffic sent to a Pakistani small ISP actually stay in Pakistan?"),
        ("ul", ["Standalone exploratory run",
                "48 small ISPs &middot; 747 announced blocks &middot; 7 vantage points",
                "Rayan Atif &middot; September 2026"]),
    ]),

    ("The question", "What we mean by a detour", [
        ("svg", SVG_TROMBONE,
         "A real case from the June run. Both ends are in Lahore. Seven of the eight probed "
         "addresses stay inside Pakistan; the eighth leaves the country and comes back."),
        ("p", "That excursion is the thing we are counting — across every block of every small "
              "ISP, from several different starting points."),
    ]),

    ("Read this first", "Probes are vantage points, not targets", [
        ("table", ["", "Destinations — what we census", "Vantage points — where we measure FROM"], [
            ["Who", "48 small/local ISPs (PTA FLL licensees)",
             "7 Atlas probes, mostly at large ISPs"],
            ["Role", "The thing being measured", "The place the traceroute starts"],
            ["Chosen for", "Completeness — every block", "Transit diversity — one per upstream"],
        ]),
        ("p", "<b>PTCL, Nayatel, Cybernet, Nova and Z-Com are vantage points. They are never "
              "destinations.</b> The targets are always the 747 blocks of the 48 small ISPs."),
        ("p", "Why several vantage points? Because a detour depends on the <em>sender's</em> "
              "transit — the same block can be local from one network and foreign from another."),
    ]),

    ("Selection &middot; 1 of 2", "How we get to 747 blocks", [
        ("svg", SVG_FUNNEL,
         "Every number is derived from a file in the repo, not estimated."),
        ("ul", ["Roster from <span class='mono'>pk_isp_fll_list.csv</span>; prefixes from RIPEstat; "
                "blocks written to <span class='mono'>blocks_all.csv</span>",
                "The 18 that announce nothing are excluded from probing — and kept as a finding",
                "Top 5 ISPs hold 432 of 747 blocks (58%), so per-ISP rates lead, not block averages"]),
    ]),

    ("Selection &middot; provenance", "Where the BGP data comes from", [
        ("svg", SVG_BGP,
         "One HTTP call per ASN, run once on 2026-06-27 by "
         "<span class='mono'>enumerate_small_isps.py</span>."),
        ("table", ["", ""], [
            ["Endpoint", "stat.ripe.net/data/announced-prefixes/data.json?resource=AS&lt;n&gt;"],
            ["Underlying data", "RIPE NCC Routing Information Service (RIS) route collectors"],
            ["Cost", "free — no API key, no measurement credits"],
            ["Filter", "IPv4 only; IPv6 announcements are dropped"],
            ["Snapshot", "2026-06-27 — re-enumerate before the census runs"],
        ]),
        ("ul", ["<b>“Announced” means visible to RIS</b>, not announced in some absolute sense. "
                "A prefix propagated only to domestic peers may never reach a collector",
                "That caveat cuts toward this study specifically — locally-scoped prefixes are "
                "the ones a domestic-interconnection study would most want to see",
                "<b>Worth a cross-check against RouteViews</b> in Phase 1: if the two agree on 747, "
                "the universe is solid; if RouteViews sees more, we were under-counting"]),
    ]),

    ("Selection &middot; 2 of 2", "How we get to 7 vantage points", [
        ("table", ["Stage", "Count", "How that number was obtained"], [
            ["PK probes known to the project", "16", "Exp 4.1 roster + Exp 07 panel map"],
            ["connected", "12", "Atlas probe API status, checked 2026-09-01"],
            ["path-visible under TCP/80", "10", "drops 7764, 62224 — recorded ICMP-filtered"],
            ["deduplicated by transit", "7", "one probe per distinct upstream AS"],
        ]),
        ("ul", ["Selection rule: one vantage per distinct transit",
                "Plus two deliberate duplicates — a second Transworld and a second Cybernet — to "
                "<em>test</em> that behaviour clusters by transit rather than assume it",
                "Since June: two probes died, one came back. The roster needed re-checking"]),
    ]),

    ("Method", "The sampling rule", [
        ("ul", ["<b>The unit is the BGP prefix, not the address.</b> Every address in an announced "
                "block shares one route — so the block is what we census",
                "<b>Every block is kept.</b> None ranked, pruned or sampled away — a census claim "
                "needs completeness. Reduction happens inside blocks, never across them",
                "<b>We probe K addresses inside each block</b> — the next three slides are what K is",
                "<b>Density comes free</b> — how many of the K replied, from the same pass"]),
        ("p", "Prefix-as-unit and density come from <b>TASS</b> (Klick et al., IMC 2016). We invert "
              "their rule: TASS drops low-density prefixes; a census must keep every one."),
    ]),

    ("K &middot; 1 of 3", "K is how many addresses we probe per block", [
        ("svg", SVG_K,
         "A /24 holds 256 addresses. Probing all of them, for 747 blocks from 7 vantage points, "
         "would be 1.3 million traceroutes."),
        ("p", "So we probe <b>K</b> evenly spaced addresses instead and let the BGP route do the "
              "generalising: every address in the block shares one route, so a handful should "
              "tell us how the whole block is reached."),
        ("p", "<b>“Should” is the word doing the work.</b> The next slide tests it."),
    ]),

    ("K &middot; 2 of 3", "Two real blocks, same eight positions", [
        ("svg", SVG_SPLIT,
         "Left-to-right, each dot is one probed address. Red left the country; green stayed."),
        ("ul", ["<b>Top:</b> the assumption holds. All 8 agree, so any 2 of them would have given "
                "the same answer — K could safely be small",
                "<b>Bottom:</b> the assumption breaks. One address in the block routes abroad while "
                "its neighbours do not. Pick the wrong 2 and you record this block as clean"]),
    ]),

    ("K &middot; 3 of 3", "How often does the assumption break?", [
        ("p", "Measured on the June run — 1,758 block-and-vantage pairs that got the full K=8:"),
        ("table", ["Outcome", "Share", "Meaning"], [
            ["All probed addresses agree", "79.4%", "the block has one route — small K is safe"],
            ["Addresses disagree", "20.0%", "the block is genuinely split"],
            ["No usable answer", "0.6%", "all eight silent or inconclusive"],
        ]),
        ("ul", ["<b>One block in five is split.</b> “The route to a block” is not always a "
                "well-defined thing — which is itself a finding, and one nobody has published",
                "On the blocks that <em>are</em> unambiguous, a random K=2 reproduces the K=8 "
                "verdict <b>98.6%</b> of the time",
                "<b>So K=2 gets the verdict right and the picture wrong.</b> It cannot see that a "
                "block is split, because with two samples there is nothing to compare",
                "<b>Decision: keep K=8.</b> A 20% split rate is too high to sample away. Reduce "
                "vantages or rounds if the run needs shrinking — never K"]),
    ]),

    ("Method", "The 22 blocks that are not /24", [
        ("svg", SVG_SIZES,
         "Each dot is one probed address. Left: a fixed K spreads thinner as the block grows. "
         "Right: the sample count scales with the block, so density is the same everywhere."),
        ("p", "<b>The rule is one target per 32 addresses — at every block size.</b> That is what "
              "K=8 already means for a /24; the larger prefixes just keep the same density."),
        ("table", ["Prefix", "Addresses", "K", "Density"], [
            ["/24", "256", "8", "1 per 32"],
            ["/23", "512", "16", "1 per 32"],
            ["/22", "1,024", "32", "1 per 32"],
            ["/19", "8,192", "256", "1 per 32"],
        ]),
        ("table", ["Size", "Blocks", "Held by", "Targets at 8 per /24-equivalent"], [
            ["/23", "17", "CMPak LDI (12), Worldcall (2), Wise, New Millennium", "16 each → 272"],
            ["/22", "4", "Gemnet (2), Connect, Multinet", "32 each → 128"],
            ["/19", "1", "Connect Communications — 151.123.224.0/19", "256 — as many as 32 blocks"],
        ]),
        ("ul", ["Positions come from a formula, not a table: "
                "<span class='mono'>target_i = network + int(i × size / (K+1))</span>. For a /24 at "
                "K=8 that gives <span class='mono'>.28 .56 .85 .113 .142 .170 .199 .227</span> — "
                "exactly what the June run used, and it never lands on the network or broadcast "
                "address at any size",
                "<b>Why not a flat K?</b> Eight probes into a /19 is a 32× thinner sample at "
                "precisely the size most likely to be internally split",
                "<b>Cost of doing it properly: +8%</b> — 5,976 targets becomes 6,456, because only "
                "22 blocks are affected",
                "<b>Aggregates count /24-equivalents, not blocks.</b> 747 prefixes are <b>807 "
                "/24-equivalents</b> — otherwise Connect's /19 weighs the same as somebody's lone /24"]),
    ]),

    ("Classification &middot; 1 of 2", "What counts as a detour", [
        ("p", "What we call tromboning is what the measurement literature calls a <b>routing "
              "detour</b> — a path between two endpoints in one country that leaves and returns."),
        ("ul", ["<b>Edmundson et al., 2016</b> — <em>Characterizing and Avoiding Routing Detours "
                "Through Surveillance States.</em> Establishes the detour as a systematic property "
                "of interdomain routing, and how to identify it from traceroute paths",
                "<b>Gupta et al., PAM 2014</b> — <em>Peering at the Internet's Frontier: ISP "
                "Interconnectivity in Africa.</em> The direct regional antecedent: African traffic "
                "detouring via Europe because local interconnection was missing",
                "This census asks that same question of Pakistan"]),
    ]),

    ("Classification &middot; 2 of 2", "How we decide it left the country", [
        ("p", "Geolocation is used — but never on its own. Every foreign-hop claim is gated by RTT."),
        ("table", ["Rule", "Value", "Why"], [
            ["Foreign hop must also be slow", "≥ 40 ms",
             "Router geolocation databases disagree (Gharaibeh, IMC 2017), so a country code alone "
             "is not evidence. RTT bounds how far a hop can be (Gueye et al., 2006)"],
            ["Inter-hop jump", "≥ 60 ms", "PK→Singapore measures ~60–90 ms — no domestic leg does that"],
            ["Any hop RTT", "≥ 70 ms", "Clear of the domestic ceiling; PK→Europe is ~100–130 ms"],
            ["Stays local", "< 45 ms", "Domestic ceiling plus queueing headroom"],
            ["Known artifact", "AS6327", "Shaw CPE hop on the Nova probe — physically in PK at ~1.5 ms"],
        ]),
        ("ul", ["Thresholds are ours, calibrated to observed Pakistani RTTs. The <em>principles</em> "
                "are from the literature above",
                "<b>The RTT backstop matters:</b> 1,140 of the corrected run's 1,562 detours rest on "
                "it alone, where no foreign hop ever replied"]),
    ]),

    ("Evidence", "The same address, from two networks", [
        ("traces", [T_SAME_PTCL, T_SAME_NOVA]),
        ("p", "Target <span class='mono'>122.129.69.113</span> — one Brain Telecom address in "
              "Lahore. Both traces are <b>complete: every hop answered, and both reached the "
              "target.</b> Only the starting network differs."),
        ("ul", ["<b>Both end at the same router</b>, <span class='mono'>203.128.7.75</span>. "
                "Same destination, same final hop, two different paths to it",
                "Hop 7 of the PTCL trace, <span class='mono'>182.45.51.22</span>, is registered to "
                "<b>CHINANET Shandong</b>. The detector scored the trace as a detour to China",
                "<b>It is not in China.</b> Hop 6 is PTCL internal at 40.9 ms, hop 7 reads 41.1 ms, "
                "hop 8 is back inside PTCL at 43.3 ms. <b>A 0.2 ms step cannot cross to China</b>",
                "Z-Com sees the same address at <b>2.2 ms</b>. It is PTCL equipment in Pakistan "
                "using Chinese address space, and this one address produced <b>327 false "
                "detours</b>"]),
    ]),

    ("Evidence", "A split block — one address diverging", [
        ("traces", [T_SPLIT_OUT, T_SPLIT_LOCAL]),
        ("p", "Block <span class='mono'>122.129.94.0/24</span>, both from Nova Lahore. "
              "<b>Hops 1–6 are identical routers at identical addresses.</b> They diverge at hop 7."),
        ("ul", ["<b>.199</b> goes Oman → Hong Kong → Indonesia. Foreign hops are named and "
                "answering, so the detour is directly observed, not inferred",
                "<b>.170</b> stays domestic for six hops then goes silent — a dead address, which "
                "is normal for 89% of targets. Read it as “no evidence it left”, not as a "
                "confirmed complete path",
                "<b>Honest caveat:</b> gapless split pairs are rarer. Most are caught by the RTT "
                "rule rather than a visible foreign hop, and some of those are a spike on a "
                "repeated final hop — which can be last-hop rate limiting rather than a detour. "
                "Phase 2 must separate the two before any split rate is published"]),
    ]),

    ("Evidence", "When the foreign hop never replies", [
        ("trace", T_BACKSTOP),
        ("ul", ["<b>Every named hop here says PK.</b> No foreign country code appears anywhere "
                "in the trace",
                "But hop 6→7 jumps <b>27.7 → 93.6 ms</b>, and it stays near 96 ms for six more "
                "hops before landing back at Bliss. No domestic path in Pakistan costs 96 ms",
                "The packet went abroad through routers that did not answer. <b>The RTT rule "
                "catches it; the country codes never would</b>. This class is 1,140 of the "
                "1,562 corrected detours",
                "<b>Hop 2 is the mirror case:</b> AS6327 Shaw geolocates to Canada at 6.9 ms. "
                "Physically impossible — it is the probe's own CPE. The detector excludes it by "
                "name, which is why a country code alone is never enough"]),
    ]),

    ("Baseline", "What the first run found", [
        ("p", "Exp 4.1 ran a full pass on 2026-06-27 — 18,260 probes, 7 vantage points, "
              "696 of 747 blocks. Figures carry both detector corrections, which remove 440 false verdicts between them; see the correction slide."),
        ("table", ["Verdict", "Count", "Share"], [
            ["Local", "15,742", "86.2%"],
            ["Detour, caught by RTT backstop", "1,140", "6.2%"],
            ["Detour, foreign hop seen", "422", "2.3%"],
            ["Inconclusive", "956", "5.2%"],
            ["Detours, combined", "1,562", "8.6%"],
        ]),
        ("p", "Only 2,007 of 18,260 targets answered — 11%. Small-ISP blocks are mostly empty, "
              "exactly as the method assumes."),
    ]),

    ("Baseline", "Two detector corrections, 440 false detours", [
        ("p", "Two addresses are registered abroad but sit inside Pakistani networks, and the "
              "detector reads both as hops abroad. <span class='mono'>182.45.51.22</span> is "
              "CHINANET space inside PTCL, seen by Z-Com at a <b>2.4 ms median over 29 samples</b>. "
              "<span class='mono'>149.40.227.134</span> is Cogent space on Transworld, seen by "
              "Z-Com at <b>1.1 ms over 361</b> and Nova at <b>2.5 ms over 307</b>."),
        ("table", ["Measure", "Uncorrected", "Corrected"], [
            ["Census detour rate", "11.0%", "8.6%"],
            ["Detours with a foreign hop resolved", "811 (4.4%)", "422 (2.3%)"],
            ["PTCL Karachi, all destinations", "38.4%", "15.1%"],
            ["PTCL Karachi to Brain Telecom", "97.6%", "3.9%"],
        ]),
        ("p", "<b>A second correction: routers that are slow to answer, not far away.</b> A router "
              "that replies to its own probe twice, slowly the second time, produces the same RTT "
              "jump as a detour. Real case, Nova to Brain Telecom: hop 8 is "
              "<span class='mono'>203.128.7.75</span> at 3.0 ms and hop 9 is the <b>same address</b> "
              "at 211.7 ms. Nothing moved. That signature accounts for <b>71</b> more verdicts."),
        ("ul", ["<b>The hard-evidence tier lost 48% of its verdicts</b>, 811 down to 422",
                "Voiding a foreign hop does not make a trace local. It falls through to the RTT "
                "rule, and some traces still qualify there",
                "<b>The rule must use a median, not a minimum.</b> One anomalous packet otherwise "
                "clears a real foreign address: C-root sits at a 143 ms median with a single 3.4 ms "
                "sample, an Equinix Singapore address at 95.5 ms with one at 3.5 ms",
                "<b>Use:</b> an address is domestic if some vantage has 3 or more observations of it "
                "with a <b>median under 10 ms</b>. No new measurement needed",
                "Recomputed from <span class='mono'>census_*.csv</span> and "
                "<span class='mono'>raw_*.json</span>. The rebuilt RTT figures match the frozen "
                "census on <b>18,260 of 18,260</b> rows"]),
    ]),

    ("Reading the result", "One number, hiding two different things", [
        ("p", "The corrected June run comes out at <b>8.6% of probes detouring</b>. That single figure is an "
              "average over two axes that behave completely differently:"),
        ("ul", ["<b>Who you send to</b> — the destination ISP whose block is being probed. "
                "Ranges 0.6% to 64.5% across the 48 ISPs",
                "<b>Where you send from</b> — the vantage point the traceroute starts at. "
                "Ranges 4.0% to 46.3% across the 7 probes"]),
        ("p", "Two spreads of roughly the same size means the detour is <em>not</em> simply a "
              "property of the badly-connected ISP. The next three slides work through what it "
              "actually is."),
    ]),

    ("Reading the result", "The same ISP, asked from seven places", [
        ("svg", SVG_BRAIN,
         "Brain Telecommunication has 49 announced blocks. Every bar is those same blocks, and "
         "only the starting network changes. Shown corrected."),
        ("ul", ["Uncorrected, PTCL Karachi read <b>97.6%</b> against Nova's 3.8%, and it was this "
                "deck's sharpest example",
                "<b>315 of those 328 verdicts came from one squatted address.</b> Corrected, "
                "PTCL sits at <b>3.9%</b> and Brain is flat across all seven vantages",
                "The lesson survives the example: a per-vantage split of this size can be real, or "
                "it can be one bad address. <b>Only checking the hop tells you which</b>"]),
    ]),

    ("Reading the result", "Why the per-ISP average misleads", [
        ("p", "<b>Pace Telecom</b> reads <b>27.4%</b> overall (194 of 708). That average is built "
              "from vantages ranging from <b>80.0%</b> to <b>6.1%</b>, and it survives the "
              "squatted-address correction intact."),
        ("ul", ["<b>PTCL Karachi 80.0%</b> (72 of 90) against <b>Nayatel Islamabad 6.1%</b> "
                "(7 of 115), on the same 17 blocks",
                "<b>No network experiences 27.4%.</b> It is the mean of a broken path and six "
                "better ones, and it describes nobody",
                "This is why the deliverable is a <b>matrix</b>, not a league table of ISPs",
                "<b>Caveat, stated on the slide:</b> 59 of PTCL's 72 verdicts here rest on the RTT "
                "backstop with no foreign hop resolved. The spread is real; the mechanism is not "
                "yet pinned down"]),
        ("p", "It also shows why balanced coverage matters so much. If PTCL happened to contribute "
              "more probes than the others, Brain's average would climb — without anything in the "
              "network having changed."),
    ]),

    ("Reading the result", "The matrix — rows and columns both matter", [
        ("svg", SVG_MATRIX,
         "Detour rate by destination ISP (rows) and vantage point (columns). Read across a row to "
         "see how one ISP is reached from everywhere; read down a column to see how one network "
         "reaches everyone."),
        ("ul", ["<b>Rows are not flat</b> — so it is not purely the destination's fault",
                "<b>Columns are not flat</b> — so it is not purely the sender's fault",
                "<b>Hot cells are specific pairs</b> — PTCL→Brain, PTCL→Pace, Cybernet Haripur→"
                "Connect. That points at bilateral interconnection, not one bad operator"]),
    ]),

    ("Reading the result", "Which of the three worlds are we in?", [
        ("table", ["If the matrix looked like…", "Then the cause is…", "And the fix is…"], [
            ["Rows uniform, columns vary",
             "the destination ISP's own transit", "that ISP buys better transit"],
            ["Columns uniform, rows vary",
             "the sending network's transit", "that provider fixes its routing"],
            ["Neither — specific pairs are hot",
             "missing interconnection between the two", "peering, or a working IXP"],
        ]),
        ("ul", ["The June data looks like the <b>third</b> — but it cannot settle the question, "
                "because 8 of its 56 cells are empty or too thin to read",
                "<b>That is the whole reason for a balanced re-run.</b> Fill every cell with equal "
                "weight and the matrix answers it outright",
                "This is also where the census meets the IXP question: hot pairs are precisely what "
                "an exchange point would collapse"]),
    ]),

    ("Why again", "The first run cannot be quoted", [
        ("p", "Coverage was badly unbalanced across vantage points — an 8× range in probe counts."),
        ("table", ["Vantage point", "Probes in the run"], [
            ["Z-Com Lahore", "4,609"], ["Nova Lahore", "4,264"],
            ["Nayatel Islamabad", "3,204"], ["Cybernet Karachi", "2,084"],
            ["Orbit Faisalabad", "2,012"], ["PTCL Karachi", "1,525"],
            ["Cybernet Haripur", "562"],
        ]),
        ("ul", ["Cybernet Haripur's 46.3% rests on 562 probes; Z-Com's on 4,609",
                "Each vantage saw a different, non-random subset — the rates are not comparable",
                "Only 594 of 696 blocks got the full K=8, so the split rate is measured on a subset",
                "<b>Equal coverage per vantage is the point of re-running.</b>"]),
    ]),

    ("Sizing", "What the run comes to", [
        ("p", "Measured in traceroutes: <b>targets × vantage points</b>. Sampling at 8 per "
              "/24-equivalent puts <b>6,456 targets</b> across the 747 blocks."),
        ("table", ["Stage", "Design", "Traceroutes"], [
            ["Pilot, once", "K=8, 150 stratified blocks, 6 vantages", "7,200"],
            ["Census round × 3", "6,456 targets, 6 vantages", "38,736 each"],
            ["Total", "", "123,408"],
        ]),
        ("ul", ["Holding K at 8 is what the 20% split rate buys — and it is not negotiable "
                "without giving up split detection entirely",
                "If the run must shrink, drop a <em>vantage</em> or a <em>round</em>. Both lose "
                "something you can name; cutting K loses something you cannot see",
                "Paced under the 100-concurrent cap with randomised inter-launch delay — the "
                "same good-citizen discipline TASS argues for"]),
    ]),

    ("Plan", "Six phases", [
        ("svg", SVG_PHASES,
         "Each phase has an exit criterion; nothing proceeds until the line beneath it is true."),
        ("p", "Phase 2 re-measures the split rate on this exact population before the full census "
              "commits to it — the 20% figure comes from a subset of the June run, and deserves "
              "confirming on a clean, balanced sample."),
    ]),

    ("Payoff", "What we might find", [
        ("ul", ["A per-ISP detour rate and its real spread — quotable, because balanced",
                "Whether the <b>vantage</b> or the <b>destination</b> dominates. If it is the pair, "
                "the fix is bilateral peering; if the destination, that ISP's transit contract",
                "Who the detour transits through — PTCL or Transworld, per ISP",
                "Which foreign exchange it surfaces at — Equinix Singapore, DE-CIX, Omantel",
                "<b>How often a single block splits across two routes</b> — the June data says one "
                "in five, and nobody has published that for anywhere",
                "How sparse small-ISP address space really is",
                "Whether any trace touches PKIX or PIE — the panel found 0 of 222,944",
                "Announced-but-dark blocks, and the 18 licensed ISPs announcing nothing"]),
    ]),

    ("Honesty", "Limits we state up front", [
        ("ul", ["Density is an <b>active-address</b> proxy, not traffic — Atlas cannot see bytes. "
                "Report “% of active address space”, never “% of traffic”",
                "A single round is a snapshot — rates are quoted as a range across rounds",
                "<b>Geolocation is used, but never alone.</b> The residual risk is a hop that is "
                "both mis-geolocated and genuinely slow",
                "Transit clustering is an assumption, only partly tested",
                "The FLL roster includes a few large and LDI members — flagged, not dropped",
                "Block sizes are not uniform — 22 of 747 are larger than /24, so the eight "
                "positions are computed per prefix length",
                "<b>The RTT rule can fire on last-hop rate limiting</b> — a router answering slowly "
                "looks like distance. Traces whose only evidence is a spike on a repeated "
                "final hop need separating from real detours",
                "Every run ships a readable routes file next to the CSV. No verdict without the "
                "paths to check it against"]),
    ]),
]

# ---------------------------------------------------------------- HTML

CSS = """
:root{
  --bg:#eef0f3; --surface:#ffffff; --ink:#171c23; --body:#39424e;
  --muted:#6b7784; --rule:#dde2e8; --accent:#2f5fa8; --accent-soft:#e8eef7;
  --bad:#b4531f; --good:#22705f; --shadow:0 1px 2px rgba(23,28,35,.06),0 8px 24px rgba(23,28,35,.07);
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#14181d; --surface:#1c2128; --ink:#eef1f5; --body:#c2cad3;
    --muted:#8b96a3; --rule:#2c333b; --accent:#7ea6e0; --accent-soft:#22303f;
    --bad:#e08a54; --good:#5fb9a2; --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.28);
  }
}
:root[data-theme="dark"]{
  --bg:#14181d; --surface:#1c2128; --ink:#eef1f5; --body:#c2cad3;
  --muted:#8b96a3; --rule:#2c333b; --accent:#7ea6e0; --accent-soft:#22303f;
  --bad:#e08a54; --good:#5fb9a2; --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.28);
}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--body);
  font-family:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;
  margin:0;-webkit-font-smoothing:antialiased}
.deck{scroll-snap-type:y proximity;overflow-y:auto;height:100vh;scroll-behavior:smooth}
.slide{scroll-snap-align:center;min-height:100vh;height:auto;display:flex;
  align-items:center;justify-content:center;padding:40px 24px}
.card{background:var(--surface);border:1px solid var(--rule);border-radius:6px;
  box-shadow:var(--shadow);width:min(1060px,100%);
  min-height:min(596px,56.25vw);height:auto;overflow:visible;
  padding:48px 56px;display:flex;flex-direction:column;gap:18px}
.eyebrow{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;
  letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0}
h1,h2{font-family:"IBM Plex Serif",Georgia,serif;color:var(--ink);
  text-wrap:balance;margin:0;font-weight:600;letter-spacing:-.01em}
h1{font-size:clamp(30px,4.2vw,50px);line-height:1.08}
h2{font-size:clamp(22px,2.9vw,34px);line-height:1.15}
p{margin:0;font-size:16px;line-height:1.62;max-width:68ch}
ul{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:9px}
li{font-size:15.5px;line-height:1.52;max-width:74ch}
li::marker{color:var(--accent)}
b{color:var(--ink);font-weight:600}
em{font-style:italic;color:var(--ink)}
.bad{color:var(--bad);font-weight:600}
.good{color:var(--good);font-weight:600}
.muted{color:var(--muted);font-weight:600}
.tw{overflow-x:auto}
table{border-collapse:collapse;font-size:14.5px;width:100%;
  font-variant-numeric:tabular-nums}
th{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10.5px;
  letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
  text-align:left;padding:0 16px 8px 0;border-bottom:1px solid var(--rule);font-weight:500}
td{padding:8px 16px 8px 0;border-bottom:1px solid var(--rule);vertical-align:top}
tr:last-child td{border-bottom:none}
tbody tr:last-child td{color:var(--ink);font-weight:600}
.flow{display:flex;flex-direction:column;gap:0;margin:0;padding:0;list-style:none}
.flow li{display:flex;align-items:flex-start;gap:14px;padding:9px 0;font-size:15px}
.flow li::before{content:"";flex:0 0 9px;height:9px;margin-top:6px;border-radius:50%;
  background:var(--accent-soft);border:2px solid var(--accent)}
.flow li:not(:last-child){border-left:0}
.flow li+li{border-top:1px dashed var(--rule)}
.num{position:absolute;bottom:18px;right:26px;
  font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;color:var(--muted)}
.cardwrap{position:relative;width:min(1060px,100%)}
.title .card{justify-content:center;gap:26px}
.hint{position:fixed;bottom:14px;left:18px;font-family:"IBM Plex Mono",monospace;
  font-size:10.5px;color:var(--muted);opacity:.7}
figure{margin:0;display:flex;flex-direction:column;gap:9px}
figure svg{display:block;width:100%;height:auto;color:var(--ink)}
figcaption{font-size:12.5px;color:var(--muted);line-height:1.5;max-width:78ch}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:.93em}
.trace{border:1px solid var(--rule);border-radius:5px;overflow:hidden;background:var(--bg)}
.thead{font-size:12px;padding:7px 11px;background:var(--accent-soft);color:var(--ink);
  font-weight:600}
.tmeta{font-size:11px;padding:6px 11px;color:var(--muted);border-bottom:1px solid var(--rule);
  line-height:1.45}
table.hops{border-collapse:collapse;width:100%;font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:10.5px;font-variant-numeric:tabular-nums}
.hops td{padding:1.5px 9px;border:none;white-space:nowrap}
.hops td.rtt{text-align:right;width:1%}
.hops td.hop{text-align:right;width:1%;color:var(--muted)}
.hops tr.out{background:color-mix(in srgb,var(--bad) 16%,transparent);color:var(--bad)}
.hops tr.back{background:color-mix(in srgb,var(--good) 16%,transparent);color:var(--good)}
.hops tr.jump{background:color-mix(in srgb,var(--bad) 9%,transparent)}
.hops tr.art td{color:var(--muted);font-style:italic}
.tag{float:right;font-size:10px;letter-spacing:.04em}
.traces{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media (max-width:720px){.traces{grid-template-columns:1fr}}
@media print{
  .deck{height:auto;overflow:visible}
  .slide{min-height:auto;page-break-after:always;padding:0}
  .card{box-shadow:none;min-height:0}
  .hint{display:none}
}
@media (max-width:720px){
  .card{min-height:0;padding:32px 26px}
  .slide{padding:18px 12px;min-height:auto}
}
"""

JS = """
const slides=[...document.querySelectorAll('.slide')];
let i=0;
function go(n){i=Math.max(0,Math.min(slides.length-1,n));
  slides[i].scrollIntoView({behavior:'smooth'});}
addEventListener('keydown',e=>{
  if(['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)){e.preventDefault();go(i+1);}
  if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();go(i-1);}
  if(e.key==='Home'){e.preventDefault();go(0);}
  if(e.key==='End'){e.preventDefault();go(slides.length-1);}
});
const obs=new IntersectionObserver(es=>es.forEach(en=>{
  if(en.isIntersecting)i=slides.indexOf(en.target);}),{threshold:.5});
slides.forEach(s=>obs.observe(s));
"""



def render_trace(t):
    head, meta, rows = t
    out = [f"<div class='trace'><div class='thead'>{head}</div>"
           f"<div class='tmeta'>{meta}</div><table class='hops'>"]
    TAG = {"out": "LEAVES PK", "back": "BACK IN PK", "art": "known artifact",
           "jump": "RTT jump"}
    for hop, rtt, ip, op, flag in rows:
        if hop == "":
            out.append("<tr><td colspan='4'>&nbsp;</td></tr>")
            continue
        cls = f" class='{flag}'" if flag else ""
        tag = f"<span class='tag'>{TAG[flag]}</span>" if flag in TAG else ""
        out.append(f"<tr{cls}><td class='hop'>{hop}</td><td class='rtt'>{rtt}</td>"
                   f"<td>{ip}</td><td>{op}{tag}</td></tr>")
    out.append("</table></div>")
    return "".join(out)


def render_blocks(blocks):
    out = []
    for b in blocks:
        if b[0] == "p":
            out.append(f"<p>{b[1]}</p>")
        elif b[0] == "ul":
            items = "".join(f"<li>{x}</li>" for x in b[1])
            out.append(f"<ul>{items}</ul>")
        elif b[0] == "flow":
            items = "".join(f"<li>{x}</li>" for x in b[1])
            out.append(f"<ul class='flow'>{items}</ul>")
        elif b[0] == "svg":
            out.append(f"<figure>{b[1]}<figcaption>{b[2]}</figcaption></figure>")
        elif b[0] == "trace":
            out.append(render_trace(b[1]))
        elif b[0] == "traces":
            out.append("<div class='traces'>" +
                       "".join(render_trace(t) for t in b[1]) + "</div>")
        elif b[0] == "table":
            hs = "".join(f"<th>{h}</th>" for h in b[1])
            rs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in b[2])
            out.append(f"<div class='tw'><table><thead><tr>{hs}</tr></thead>"
                        f"<tbody>{rs}</tbody></table></div>")
    return "\n".join(out)


def build_html():
    parts = []
    for n, (eyebrow, title, blocks) in enumerate(SLIDES):
        tag = "h1" if n == 0 else "h2"
        cls = "slide title" if n == 0 else "slide"
        eb = f"<p class='eyebrow'>{eyebrow}</p>" if eyebrow else ""
        parts.append(
            f"<section class='{cls}'><div class='cardwrap'><div class='card'>"
            f"{eb}<{tag}>{title}</{tag}>{render_blocks(blocks)}</div>"
            f"<div class='num'>{n+1} / {len(SLIDES)}</div></div></section>")
    return (
        "<title>Block-Routing Census</title>\n"
        "<link rel='preconnect' href='https://fonts.googleapis.com'>\n"
        "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>\n"
        "<link rel='stylesheet' href='https://fonts.googleapis.com/css2?"
        "family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&"
        "family=IBM+Plex+Serif:wght@600&display=swap'>\n"
        f"<style>{CSS}</style>\n"
        f"<div class='deck'>{''.join(parts)}</div>\n"
        "<div class='hint'>← → to navigate</div>\n"
        f"<script>{JS}</script>\n")


# ---------------------------------------------------------------- PPTX

def strip(t):
    """Flatten inline HTML to plain text for PowerPoint."""
    for a, b in [("<b>", ""), ("</b>", ""), ("<em>", ""), ("</em>", ""),
                 ("&mdash;", "—"), ("&rarr;", "→"), ("&middot;", "·"),
                 ("&times;", "×"),
                 ("<span class='bad'>", ""), ("<span class='good'>", ""),
                 ("<span class='muted'>", ""), ("</span>", "")]:
        t = t.replace(a, b)
    return html.unescape(t)


def build_pptx():
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor

    INK, BODY, ACCENT, MUTED = (RGBColor(0x17, 0x1C, 0x23), RGBColor(0x39, 0x42, 0x4E),
                                RGBColor(0x2F, 0x5F, 0xA8), RGBColor(0x6B, 0x77, 0x84))
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    for n, (eyebrow, title, blocks) in enumerate(SLIDES):
        s = prs.slides.add_slide(blank)
        top = Inches(0.6)

        if eyebrow:
            tb = s.shapes.add_textbox(Inches(0.75), top, Inches(11.8), Inches(0.3))
            r = tb.text_frame.paragraphs[0].add_run()
            r.text = eyebrow.upper()
            r.font.size, r.font.name, r.font.color.rgb = Pt(11), "IBM Plex Mono", ACCENT
            top = Inches(1.0)

        tb = s.shapes.add_textbox(Inches(0.75), top, Inches(11.8), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        r = tf.paragraphs[0].add_run()
        r.text = title
        r.font.size = Pt(34 if n else 40)
        r.font.bold, r.font.name, r.font.color.rgb = True, "IBM Plex Serif", INK

        body = s.shapes.add_textbox(Inches(0.75), top + Inches(1.15),
                                    Inches(11.8), Inches(5.2))
        tf = body.text_frame
        tf.word_wrap = True
        first = True

        def para():
            nonlocal first
            if first:
                first = False
                return tf.paragraphs[0]
            return tf.add_paragraph()

        for b in blocks:
            if b[0] == "p":
                p = para()
                p.space_after = Pt(10)
                r = p.add_run()
                r.text = strip(b[1])
                r.font.size, r.font.name, r.font.color.rgb = Pt(15), "IBM Plex Sans", BODY
            elif b[0] in ("ul", "flow"):
                for it in b[1]:
                    p = para()
                    p.space_after = Pt(7)
                    r = p.add_run()
                    r.text = ("→  " if b[0] == "flow" else "•  ") + strip(it)
                    r.font.size, r.font.name, r.font.color.rgb = Pt(14), "IBM Plex Sans", BODY
            elif b[0] in ("trace", "traces"):
                p = para(); p.space_after = Pt(10)
                r = p.add_run(); r.text = "[ traceroute listing — see slides.html ]"
                r.font.size, r.font.name, r.font.color.rgb = Pt(13), "IBM Plex Sans", MUTED
                r.font.italic = True
            elif b[0] == "svg":
                p = para(); p.space_after = Pt(10)
                r = p.add_run(); r.text = "[ diagram — see slides.html ]  " + strip(b[2])
                r.font.size, r.font.name, r.font.color.rgb = Pt(13), "IBM Plex Sans", MUTED
                r.font.italic = True
            elif b[0] == "table":
                hdr = [h for h in b[1] if h]
                if hdr:
                    p = para()
                    p.space_after = Pt(4)
                    r = p.add_run()
                    r.text = "   ".join(hdr)
                    r.font.size, r.font.name = Pt(11), "IBM Plex Mono"
                    r.font.color.rgb, r.font.bold = MUTED, True
                for row in b[2]:
                    p = para()
                    p.space_after = Pt(4)
                    r = p.add_run()
                    r.text = "   ·   ".join(strip(c) for c in row if c)
                    r.font.size, r.font.name, r.font.color.rgb = Pt(13), "IBM Plex Sans", BODY

        tb = s.shapes.add_textbox(Inches(12.4), Inches(6.95), Inches(0.7), Inches(0.3))
        r = tb.text_frame.paragraphs[0].add_run()
        r.text = f"{n+1} / {len(SLIDES)}"
        r.font.size, r.font.name, r.font.color.rgb = Pt(10), "IBM Plex Mono", MUTED

    return prs


if __name__ == "__main__":
    hp = os.path.join(OUT, "slides.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(build_html())
    print("wrote", hp)

    if "--html" in sys.argv:
        print("(--html: leaving slides.pptx untouched)")
        raise SystemExit(0)

    prs = build_pptx()
    pp = os.path.join(OUT, "slides.pptx")
    try:
        prs.save(pp)
        print("wrote", pp, f"({len(SLIDES)} slides)")
    except PermissionError:
        alt = os.path.join(OUT, "slides_new.pptx")
        prs.save(alt)
        print(f"!! {pp} is open in another program — could not overwrite.")
        print(f"   wrote {alt} instead ({len(SLIDES)} slides).")
        print("   Close PowerPoint, delete slides.pptx, rename slides_new.pptx over it.")
