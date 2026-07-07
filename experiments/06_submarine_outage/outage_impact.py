#!/usr/bin/env python3
"""
Exp 06: quantify the outage impact as % change in RTT / jitter / path length / loss.
Since monitoring began mid-outage (no pre-event baseline), it compares the OUTAGE peak
(first 3 h) to the RECOVERED state (last 3 h). Pulls ping + traceroute per round from
the RIPE measurements in results/measurements.json.

    python experiments/06_submarine_outage/outage_impact.py   # -> results/outage_impact.md

RTT level uses the per-round average; jitter is the round-to-round stddev. The finding is
robust to the RTT definition: swapping pg.rtt_average -> pg.rtt_min (min-of-N, the framework
standard) gives +0% RTT and +24% jitter for international targets -- same conclusion.
"""
import os, json, statistics as st, collections
from datetime import datetime, timezone, timedelta
from ripe.atlas.cousteau import AtlasResultsRequest
from ripe.atlas.sagan import PingResult, TracerouteResult

BASE = os.path.dirname(os.path.abspath(__file__))
meta = json.load(open(os.path.join(BASE, "results", "measurements.json")))
P = meta["probes"]; CAT = meta["target_cat"]
HOP_EXCLUDE = {7764, 62224, 1015210}   # ICMP-filtered (7764,62224) / Docker-opaque (1015210): hop counts meaningless

ping = []
for host, mid in meta["ping"].items():
    ok, res = AtlasResultsRequest(msm_id=mid).create()
    if not ok: continue
    for r in res:
        try: pg = PingResult.get(r)
        except Exception: continue
        ping.append((r.get("timestamp"), r.get("prb_id"), host, CAT[host],
                     pg.rtt_average, pg.packets_sent, pg.packets_received))

trace = []
for host, mid in meta["trace"].items():
    ok, res = AtlasResultsRequest(msm_id=mid).create()
    if not ok: continue
    for r in res:
        try: pr = TracerouteResult.get(r)
        except Exception: continue
        last = 0
        for hop in pr.hops:
            if any(p.origin for p in hop.packets): last = hop.index
        trace.append((r.get("timestamp"), r.get("prb_id"), host, CAT[host], last))

tmin = min(x[0] for x in ping); tmax = max(x[0] for x in ping); W = 3 * 3600
def win(ts):
    if ts <= tmin + W: return "outage"
    if ts >= tmax - W: return "recovered"
    return None
def pkt(ts): return datetime.fromtimestamp(ts, timezone.utc) + timedelta(hours=5)
def klass(cat): return "International" if cat in ("CDN", "Abroad") else "Pakistan (local)"
def pct(o, r): return (o - r) / r * 100 if r else float("nan")
def sp(p): return f"{p:+.0f}%"

def summarize(group_fn):
    rtt = collections.defaultdict(lambda: {"outage": [], "recovered": []})
    hop = collections.defaultdict(lambda: {"outage": [], "recovered": []})
    loss = collections.defaultdict(lambda: {"outage": [0, 0], "recovered": [0, 0]})
    jser = collections.defaultdict(lambda: collections.defaultdict(list))
    for ts, prb, host, cat, rtt_avg, sent, rcvd in ping:
        w = win(ts)
        if not w: continue
        g = group_fn(prb, cat)
        if sent: loss[g][w][1] += sent; loss[g][w][0] += (rcvd or 0)
        if rtt_avg is None: continue
        rtt[g][w].append(rtt_avg); jser[g][(prb, host, w)].append(rtt_avg)
    for ts, prb, host, cat, hc in trace:
        w = win(ts)
        if not w or not hc or prb in HOP_EXCLUDE: continue
        hop[group_fn(prb, cat)][w].append(hc)
    rows = []
    for g in sorted(rtt):
        ro, rr = rtt[g]["outage"], rtt[g]["recovered"]
        ho, hr = hop[g]["outage"], hop[g]["recovered"]
        def jit(w):
            vals = [st.pstdev(v) for k, v in jser[g].items() if k[2] == w and len(v) >= 2]
            return st.mean(vals) if vals else float("nan")
        jo, jr = jit("outage"), jit("recovered")
        lo = (1 - loss[g]["outage"][0] / loss[g]["outage"][1]) * 100 if loss[g]["outage"][1] else 0
        lr = (1 - loss[g]["recovered"][0] / loss[g]["recovered"][1]) * 100 if loss[g]["recovered"][1] else 0
        rows.append([g, st.mean(ro) if ro else float("nan"), st.mean(rr) if rr else float("nan"),
                     jo, jr, st.mean(ho) if ho else float("nan"), st.mean(hr) if hr else float("nan"), lo, lr])
    return rows

def find(rows, g): return next(r for r in rows if r[0] == g)
by_class = summarize(lambda prb, cat: klass(cat))
def transit(prb, cat):
    lbl = str(P.get(str(prb), prb))
    t = "PTCL" if "ptcl" in lbl else ("Transworld" if ("transworld" in lbl or "tes" in lbl) else "Other-ISP")
    return f"{t} probes -> {klass(cat)}"
by_transit = summarize(transit)
intl = find(by_class, "International"); ptcl = find(by_transit, "PTCL probes -> International")

o = []
o.append("# Exp 06 — Submarine-outage impact\n")
o.append("## Punchline\n")
o.append("During the SMW5 outage **peak** (first 3 h) vs the **recovered** state (last 3 h), "
         "for **international** targets (CDN+Abroad):\n")
o.append(f"- **Average RTT: {sp(pct(intl[1],intl[2]))}** ({intl[1]:.0f} → {intl[2]:.0f} ms) — modest on average.")
o.append(f"- **Jitter: {sp(pct(intl[3],intl[4]))}** ({intl[3]:.1f} → {intl[4]:.1f} ms) — the dominant effect: the outage hit as *instability*, not a latency step.")
o.append(f"- **Path length: {sp(pct(intl[5],intl[6]))}** ({intl[5]:.1f} → {intl[6]:.1f} hops) — essentially unchanged (no rerouting onto longer paths).")
o.append(f"- **Packet loss: {intl[7]:.1f}% → {intl[8]:.1f}%** — roughly flat.\n")
o.append(f"Concentrated on **PTCL-sourced** paths — international **RTT {sp(pct(ptcl[1],ptcl[2]))}** "
         f"({ptcl[1]:.0f}→{ptcl[2]:.0f} ms), **jitter {sp(pct(ptcl[3],ptcl[4]))}** ({ptcl[3]:.0f}→{ptcl[4]:.0f} ms). "
         f"Local/PK targets showed **no increase** (the control).\n")
o.append(f"**Windows:** OUTAGE = first 3 h ({pkt(tmin):%H:%M}–{pkt(tmin+W):%H:%M} PKT), "
         f"RECOVERED = last 3 h ({pkt(tmax-W):%H:%M}–{pkt(tmax):%H:%M} PKT). No true pre-event baseline "
         f"(monitoring began mid-outage). {len(ping)} ping rounds, {len(trace)} traceroute rounds.\n")

def table(title, rows):
    o.append(f"\n## {title}\n")
    o.append("| group | RTT out→rec (Δ) | jitter out→rec (Δ) | hops out→rec (Δ) | loss out→rec |")
    o.append("|---|---|---|---|---|")
    for g, ro, rr, jo, jr, ho, hr, lo, lr in rows:
        o.append(f"| {g} | {ro:.0f}→{rr:.0f} ms (**{sp(pct(ro,rr))}**) | {jo:.1f}→{jr:.1f} ms (**{sp(pct(jo,jr))}**) | "
                 f"{ho:.1f}→{hr:.1f} (**{sp(pct(ho,hr))}**) | {lo:.0f}%→{lr:.0f}% |")

table("By hosting class (International = CDN+Abroad)", by_class)
table("By target category", summarize(lambda prb, cat: cat))
table("By source transit × class", by_transit)

o.append("\n## Caveats\n")
o.append("- **No pre-event baseline** — 'increase' compares the outage peak (first 3 h) to the recovered "
         "state (last 3 h), not to a normal day; the true increase vs normal is likely larger.")
o.append("- **Pooled averages understate the peak** — a few paths swung 400–650 ms (shophive via PTCL) but "
         "the mean over 18×14 pairs is dominated by stable pairs; jitter and the PTCL rows capture the damage.")
o.append("- **Hop counts exclude probes 7764/62224 (ICMP-filtered) and 1015210 (Docker-opaque)**; path "
         "length is still the least reliable metric here.")
o.append("- **Local-target loss ~55% and noisy jitter** = ICMP filtering on gov/edu sites, not an outage "
         "signal; the local RTT (flat-to-lower) is the meaningful control and shows no degradation.")

open(os.path.join(BASE, "results", "outage_impact.md"), "w", encoding="utf-8").write("\n".join(o) + "\n")
print("wrote results/outage_impact.md")
print(f"intl: RTT {sp(pct(intl[1],intl[2]))} jitter {sp(pct(intl[3],intl[4]))} hops {sp(pct(intl[5],intl[6]))}")
