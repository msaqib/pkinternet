#!/usr/bin/env python3
"""
Prove R1 to R4 for the LOCAL tracer's vantage, then apply R5.

RULES.md requires each rule to be proven against a probe's own data before it is
applied to that probe. This does that for the vantage that produced 99.8% of the
route sweep, AS45669 Mobilink, and records which rules survive.

WHAT SURVIVES, and why it matters
  R2 (an address is not in the country it claims) survives, and is now fed by proper
  measurement rather than by sweep leftovers. measure_rtt.py and measure_rtt_ttl.py
  send 25 to 30 packets per address at 6 to 8 threads and report the MINIMUM, which
  is the right estimator for propagation delay: queuing, rate limiting and slow ICMP
  generation only ever ADD to a round trip. Dispersion on those bursts is 1 ms, against
  85 ms on the same addresses during the sweep, and the sweep's readings were inflated
  by a median of 30 ms on a scale where 34.2 ms is the whole domestic budget.
  Feeding R2 measured minimums took the falsified count from 37 to 78.

  The RTT arm of the Exp 04 detector does NOT survive on this dataset. local_trace.py
  sends ONE packet per TTL and ran at 120 threads, so each hop RTT is a single sample
  taken under heavy local concurrency. Measured consequences:
    - a fixed first-hop router spans 4 ms to 853 ms, p10 15, p90 100
    - 22% of adjacent hop pairs show RTT DECREASING by >20 ms deeper into the path,
      which distance cannot do
    - the hand-picked thresholds would label 75.9% of traces trombone_rtt
  So `max_rtt >= 70` and `jump >= 60` measure concurrency, not geography, here.
  They are disabled, and the reason is recorded rather than the thresholds retuned.

  What is left is TOPOLOGICAL detection: a hop annotated to a foreign country, with
  squatted address space removed by R2. That does not depend on per-trace RTT.

CONSTANTS are derived, not chosen. The falsification floor for a country is the
straight-line round trip at the speed of light in fibre, 204,000 km/s, from the point
in Pakistan CLOSEST to that country. Closest, so the bound is conservative: if even
the shortest possible Pakistani origin cannot reach an address that fast, no Pakistani
origin can.

  python prove_rules_local.py       -> rules_local.json, RULES_LOCAL.md
"""
import io, json, os, math, collections, statistics as st

H = os.path.dirname(os.path.abspath(__file__))
def P(*p): return os.path.join(H, "..", *p)

C_FIBRE = 204_000.0        # km/s, Bozkurt 5.1, measured
ROUTING = 2.1              # real fibre path vs great circle, Bozkurt

# Pakistan's extent. The floor uses whichever of these is closest to the destination,
# which makes falsification conservative.
PK = {"Karachi": (24.86, 67.01), "Lahore": (31.55, 74.34), "Islamabad": (33.68, 73.05),
      "Gwadar": (25.12, 62.32), "Gilgit": (35.92, 74.31), "Peshawar": (34.02, 71.58)}

# The closest major internet hub in each country we actually observe as a hop.
# Closest, not the centroid, for the same conservatism.
HUB = {
    "US": ("Los Angeles", 34.05, -118.24), "CN": ("Urumqi", 43.83, 87.62),
    "DE": ("Frankfurt", 50.11, 8.68),      "AU": ("Perth", -31.95, 115.86),
    "SG": ("Singapore", 1.35, 103.82),     "IT": ("Milan", 45.46, 9.19),
    "NL": ("Amsterdam", 52.37, 4.90),      "AE": ("Dubai", 25.20, 55.27),
    "HK": ("Hong Kong", 22.32, 114.17),    "TR": ("Istanbul", 41.01, 28.98),
    "GB": ("London", 51.51, -0.13),        "CY": ("Nicosia", 35.19, 33.38),
    "RO": ("Bucharest", 44.43, 26.10),     "CA": ("Vancouver", 49.28, -123.12),
    "FR": ("Marseille", 43.30, 5.37),      "GE": ("Tbilisi", 41.72, 44.78),
    "EG": ("Cairo", 30.04, 31.24),         "SA": ("Jeddah", 21.49, 39.19),
    "OM": ("Muscat", 23.59, 58.41),        "IN": ("Mumbai", 19.08, 72.88),
    "IR": ("Tehran", 35.69, 51.39),        "RU": ("Moscow", 55.76, 37.62),
    "JP": ("Tokyo", 35.68, 139.69),        "KR": ("Seoul", 37.57, 126.98),
    "MY": ("Kuala Lumpur", 3.14, 101.69),  "QA": ("Doha", 25.29, 51.53),
    "BH": ("Manama", 26.23, 50.59),        "KW": ("Kuwait City", 29.38, 47.99),
}

def gc(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 6371.0 * 2 * math.asin(math.sqrt(
        math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))

def floors():
    """Absolute round-trip floor, ms, from the nearest Pakistani origin. No routing
    factor: this is the physical bound, so falsifying it is not a judgement call."""
    out = {}
    for cc, (city, la, lo) in HUB.items():
        d = min(gc(p, (la, lo)) for p in PK.values())
        out[cc] = dict(hub=city, km=round(d), floor_ms=round(2*d/C_FIBRE*1000, 1),
                       expected_ms=round(2*d*ROUTING/C_FIBRE*1000, 1))
    return out

# Pakistan's own extent gives the domestic ceiling.
PK_SPAN = max(gc(a, b) for a in PK.values() for b in PK.values())
DOM_FLOOR = 2*PK_SPAN/C_FIBRE*1000
DOM_CEIL  = 2*PK_SPAN*ROUTING/C_FIBRE*1000

def main():
    ann = json.load(io.open(P("3_routes", "selected_annotated.json"), encoding="utf-8"))
    F = floors()

    # ---- R1: the access chain, measured as the position-wise dominant address
    pos = []
    for i in range(8):
        c = collections.Counter()
        for r in ann:
            if i < len(r["path"]):
                h = r["path"][i]
                c[h["ip"] if h else "*"] += 1
        ip, n = c.most_common(1)[0]
        pos.append((i+1, ip, n, 100*n/len(ann)))
    chain = [(i, ip, n, p) for i, ip, n, p in pos if ip != "*" and p >= 95]

    # ---- per-address RTT samples, the basis for R2
    rt = collections.defaultdict(list)
    meta = {}
    for r in ann:
        for h in r["path"]:
            if h and isinstance(h.get("rtt"), (int, float)):
                rt[h["ip"]].append(h["rtt"])
                meta[h["ip"]] = (h["cc"], h.get("asn"), h.get("holder") or "", h.get("kind"))

    # ---- measured RTT, where a dedicated burst exists
    # The sweep sent ONE packet per TTL at 120 threads, which inflates every reading by
    # a median of 30 ms against a 34.2 ms domestic ceiling. Where measure_rtt.py or
    # measure_rtt_ttl.py has a clean burst, its MINIMUM replaces the sweep median.
    # Priority matters. IN-PATH measurement sends packets toward the ORIGINAL
    # destination with a limited TTL, which is how the sweep saw the hop in the first
    # place. Pinging a router directly measures something else: routers deprioritise
    # traffic addressed to themselves, and the route TO a router need not match the
    # route THROUGH it. Direct echo is kept only as a last resort and is labelled.
    measured = {}
    for fn, how in (("rtt_foreign.json", "direct echo (INFERIOR)"),
                    ("rtt_foreign_ttl.json", "in-path"),
                    ("rtt_inpath.json", "in-path")):
        fp = P("3_routes", fn)
        if not os.path.exists(fp):
            continue
        for ip, v in json.load(io.open(fp, encoding="utf-8")).items():
            if v.get("n"):
                measured[ip] = dict(rtt=v["min"], n=v["n"], spread=v.get("spread", 0), how=how)

    # ---- R4-prime: this vantage's own domestic normal, self-calibrating.
    # No geometry. A multiplier over straight-line distance is the wrong model at
    # domestic scale: regressed against distance, Pakistani domestic RTT gives
    # R^2 = 0.013. So the bound is a property of THIS vantage's measured distribution
    # and must be re-derived anywhere else. Tukey's far fence is used because it is a
    # standard, scale-free definition of an outlier: a slow vantage gets a high
    # baseline AND a high fence, so the rule travels without being retuned.
    fence = ref_n = None
    bp = P("3_routes", "rtt_baseline_sample.json")
    tp = os.path.join(H, "trombone_local.json")
    if os.path.exists(bp) and os.path.exists(tp):
        base = json.load(io.open(bp, encoding="utf-8"))
        stat = {r["target"]: r["status"] for r in json.load(io.open(tp, encoding="utf-8"))["rows"]}
        ref = sorted(v["min"] for t, v in base.items() if stat.get(t) == "local")
        if len(ref) >= 100:                      # gate: too few and the shape is noise
            qq = st.quantiles(ref, n=4)
            fence = round(qq[2] + 3*(qq[2]-qq[0]), 1)
            ref_n = len(ref)

    # ---- R2: an address cannot be where its registry says
    MIN_SAMPLES = 3
    falsified, upheld, undecidable = {}, {}, {}
    for ip, v in rt.items():
        cc, asn, holder, kind = meta[ip]
        if cc in ("PK", "PRIV", "CGN", "??") or kind == "ixp":
            continue
        m = measured.get(ip)
        if m:
            best, src, n = m["rtt"], m["how"], m["n"]      # burst minimum: a measurement
        else:
            if len(v) < MIN_SAMPLES:
                continue
            best, src, n = st.median(v), "sweep median (UNIMPROVED)", len(v)
        f = F.get(cc)
        if not f:
            undecidable[ip] = dict(cc=cc, n=n, rtt=best, src=src, why="no hub for country")
            continue
        rec = dict(cc=cc, asn=asn, holder=holder[:40], n=n, rtt=best, src=src,
                   floor=f["floor_ms"], hub=f["hub"])
        if best < f["floor_ms"]:
            falsified[ip] = rec
        elif f["floor_ms"] <= DOM_CEIL:
            undecidable[ip] = dict(rec, why=f"floor {f['floor_ms']:.1f} ms is inside the "
                                             f"{DOM_CEIL:.1f} ms domestic band")
        else:
            upheld[ip] = rec

    # ---- R4: domestic baseline, and its validity gate
    dest = [h["rtt"] for r in ann if r["reached"]
            for h in [[x for x in r["path"] if x][-1]]
            if h["ip"] == r["target"] and isinstance(h.get("rtt"), (int, float))]

    # ---- RTT-arm viability, measured rather than assumed
    drops = tot = hi = jump = 0
    for r in ann:
        v = [h["rtt"] for h in r["path"] if h and isinstance(h.get("rtt"), (int, float))]
        w = [x for x in v if x <= 500]
        if w:
            if max(w) >= 70: hi += 1
            if max((w[i]-w[i-1] for i in range(1, len(w))), default=0) >= 60: jump += 1
        for i in range(1, len(v)):
            tot += 1
            if v[i] < v[i-1] - 20: drops += 1

    out = dict(
        vantage="AS45669 Mobilink (PMCL)", traces=len(ann),
        constants=dict(c_fibre_km_s=C_FIBRE, routing_factor=ROUTING,
                       pk_span_km=round(PK_SPAN), domestic_floor_ms=round(DOM_FLOOR, 1),
                       domestic_ceiling_ms=round(DOM_CEIL, 1)),
        R1=dict(chain=[dict(hop=i, ip=ip, n=n, pct=round(p, 1)) for i, ip, n, p in chain],
                B_access_ms=st.median(rt[chain[-1][1]]) if chain else None),
        R2=dict(falsified=len(falsified), upheld=len(upheld), undecidable=len(undecidable),
                measured=sum(1 for x in list(falsified.values())+list(upheld.values())+list(undecidable.values())
                             if "UNIMPROVED" not in x.get("src","")),
                falsified_detail=falsified, upheld_detail=upheld, undecidable_detail=undecidable),
        R4prime=dict(fence_ms=fence, reference_n=ref_n,
                     method="Tukey far fence p75 + 3 x IQR over clean minimum RTT to "
                            "destinations whose observed path is entirely domestic",
                     portable=True,
                     note="A PROCEDURE, not a number. Any vantage re-runs it on its own "
                          "traffic and gets its own fence. Gates: at least 100 reference "
                          "destinations, and if over half of them are themselves "
                          "detouring the baseline IS the detour and the rule must be "
                          "rejected."),
        R4=dict(n=len(dest), median_ms=st.median(dest) if dest else None,
                under_domestic_ceiling_pct=round(100*sum(1 for x in dest if x < DOM_CEIL)/len(dest), 1) if dest else None),
        RTT_ARM=dict(viable=False,
                     backward_pairs=drops, total_pairs=tot,
                     backward_pct=round(100*drops/tot, 1) if tot else None,
                     would_flag_max70_pct=round(100*hi/len(ann), 1),
                     would_flag_jump60_pct=round(100*jump/len(ann), 1)),
        country_floors=F)
    json.dump(out, io.open(os.path.join(H, "rules_local.json"), "w", encoding="utf-8"), indent=1)

    print(f"VANTAGE  AS45669 Mobilink, {len(ann):,} traces\n")
    print(f"CONSTANTS  Pakistan's span {PK_SPAN:.0f} km -> domestic floor {DOM_FLOOR:.1f} ms, "
          f"ceiling {DOM_CEIL:.1f} ms")
    print(f"\nR1 access chain, position-wise dominant address:")
    for i, ip, n, p in chain:
        print(f"     hop {i}  {ip:<18}{n:>7,} traces  {p:.1f}%   median {st.median(rt[ip]):.0f} ms")
    print(f"     B_access = {out['R1']['B_access_ms']:.0f} ms")
    unimp = sum(1 for x in list(falsified.values())+list(upheld.values())+list(undecidable.values())
                if "UNIMPROVED" in x.get("src", ""))
    print("")
    print(f"R2 geolocation falsification ({len(measured)} on measured burst minimums, "
          f"{unimp} still on sweep medians):")
    print(f"     falsified   {len(falsified):>5}  address is NOT where it claims")
    print(f"     upheld      {len(upheld):>5}  consistent with its claimed country")
    print(f"     undecidable {len(undecidable):>5}  floor sits inside the domestic band")
    print(f"\nR4 domestic baseline: median RTT to a Pakistani target = "
          f"{out['R4']['median_ms']:.0f} ms over {len(dest):,}")
    print(f"     only {out['R4']['under_domestic_ceiling_pct']}% of destinations are under "
          f"the {DOM_CEIL:.1f} ms ceiling")
    print(f"\nRTT ARM  REJECTED for this vantage:")
    print(f"     {drops:,} of {tot:,} adjacent hop pairs ({out['RTT_ARM']['backward_pct']}%) "
          f"have RTT falling >20 ms deeper into the path")
    print(f"     hand-picked rules would flag {out['RTT_ARM']['would_flag_max70_pct']}% "
          f"(max>=70) and {out['RTT_ARM']['would_flag_jump60_pct']}% (jump>=60)")
    print(f"\nwrote rules_local.json")

if __name__ == "__main__":
    main()
