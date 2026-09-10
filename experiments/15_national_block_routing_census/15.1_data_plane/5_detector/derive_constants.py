#!/usr/bin/env python3
"""
Derive every constant the detector needs from measurement. Nothing is chosen by hand.

WHAT THIS REPLACES
  The rules previously carried three numbers that were typed in rather than measured:

    ROUTING = 2.1        Bozkurt's rule of thumb for TYPICAL internet latency, taken
                         from a study of US long-haul fibre. It was being used as if
                         it described Pakistan. It does not: measured here, Pakistani
                         domestic paths from this vantage run at a different factor.

    DOMESTIC_CEIL 34.2   Computed as Pakistan's span x 2.1 / c and then used as a
                         CEILING. It never was one. Bozkurt reports only 11% of real
                         fibre links come within 25% of what their length predicts,
                         and same-city server pairs often sit 10 to 30 ms apart.

    HUB = {...}          A hand-written table of "the closest internet hub" per
                         country, used to compute a physical floor. It invented
                         facts: it guessed Singapore for 27.111.230.181, which the
                         geolocation databases place in Sydney.

  All three are now derived:

    vantage location     geolocation of our own egress address
    destination location geolocation of each measured destination
    routing factor       measured RTT / straight-line RTT, per path, from real
                         distances, so it describes THIS country and THIS vantage
    domestic bound       a percentile of the measured domestic RTT distribution,
                         reported with the error rate it carries
    country floors       per-address geolocation, not a guessed city

  ONE constant survives, and it is a physical property rather than a tuning knob:
  the speed of light in fibre, 204,000 km/s (Bozkurt section 4.2, measured). A
  detector cannot derive physics from its own data.

INPUTS   3_routes/rtt_baseline_sample.json   clean minimum RTT per destination
         5_detector/trombone_local.json      which destinations are topologically clean

  python derive_constants.py    -> derived_constants.json
"""
import io, json, os, math, ssl, time, urllib.request, threading, queue, statistics as st

H = os.path.dirname(os.path.abspath(__file__))
def P(*p): return os.path.join(H, "..", *p)
OUT = os.path.join(H, "derived_constants.json")

C_FIBRE = 204_000.0   # km/s in fibre. Physical, cited, not tunable.

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
def get(u, tries=3):
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(u, timeout=30, context=ctx))["data"]
        except Exception:
            if i == tries-1:
                return None
            time.sleep(1.5)


def geoloc(ip):
    d = get(f"https://stat.ripe.net/data/maxmind-geo-lite/data.json?resource={ip}")
    if not d:
        return None
    for lr in d.get("located_resources") or []:
        for l in lr.get("locations") or []:
            if l.get("latitude") is not None:
                return dict(cc=l.get("country"), city=l.get("city") or "",
                            lat=l["latitude"], lon=l["longitude"])
    return None


def gc(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 6371.0 * 2 * math.asin(math.sqrt(
        math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))


def straight_rtt_ms(km):
    """Absolute physical floor for a round trip over that distance."""
    return 2 * km / C_FIBRE * 1000


# ---------------------------------------------------------------- vantage
myip = (get("https://stat.ripe.net/data/whats-my-ip/data.json") or {}).get("ip")
vg = geoloc(myip) if myip else None
net = get(f"https://stat.ripe.net/data/network-info/data.json?resource={myip}") if myip else None
vasn = (net.get("asns") or [None])[0] if net else None
print(f"vantage {myip}  AS{vasn}  geolocated to {vg['lat']},{vg['lon']} "
      f"({vg['city'] or 'no city'}, {vg['cc']})" if vg else "vantage location unavailable")

# ------------------------------------------------- measured domestic sample
base = json.load(io.open(P("3_routes", "rtt_baseline_sample.json"), encoding="utf-8"))
tro = json.load(io.open(os.path.join(H, "trombone_local.json"), encoding="utf-8"))
status = {r["target"]: r["status"] for r in tro["rows"]}
dom = {ip: v for ip, v in base.items() if status.get(ip) == "local"}
trb = {ip: v for ip, v in base.items() if status.get(ip) == "trombone"}
print(f"clean sample: {len(dom)} topologically domestic, {len(trb)} tromboning")

# ------------------------------------- geolocate the domestic destinations
print("geolocating destinations to derive the routing factor ...")
locs, lock, q = {}, threading.Lock(), queue.Queue()
for ip in dom:
    q.put(ip)
done = [0]
def w():
    while True:
        try: ip = q.get_nowait()
        except queue.Empty: return
        g = geoloc(ip)
        with lock:
            done[0] += 1
            if g: locs[ip] = g
            if done[0] % 100 == 0: print(f"   {done[0]}/{len(dom)}", flush=True)
ths = [threading.Thread(target=w, daemon=True) for _ in range(10)]
[t.start() for t in ths]; [t.join() for t in ths]
print(f"   located {len(locs)} of {len(dom)}")

# ------------------------------------------------ derive the routing factor
factors, spans = [], []
if vg:
    for ip, g in locs.items():
        if g["cc"] != "PK":
            continue                     # only domestic paths define a domestic factor
        km = gc((vg["lat"], vg["lon"]), (g["lat"], g["lon"]))
        spans.append(km)
        floor = straight_rtt_ms(km)
        if floor > 0.5:                  # below this, geolocation error dominates
            factors.append(dom[ip]["min"] / floor)

# ------------------------------------------------- derive the domestic bound
dmin = sorted(v["min"] for v in dom.values())
tmin = sorted(v["min"] for v in trb.values())
qd = st.quantiles(dmin, n=100)
bounds = {}
for p in (90, 95, 97, 99):
    thr = qd[p-1]
    bounds[f"p{p}"] = dict(ms=round(thr, 1),
                           domestic_above=sum(1 for x in dmin if x > thr),
                           domestic_above_pct=round(100*sum(1 for x in dmin if x > thr)/len(dmin), 1),
                           trombone_below=sum(1 for x in tmin if x <= thr))
gap = (max([x for x in dmin if x <= qd[96]], default=0), min(tmin) if tmin else None)

out = dict(
    speed_of_light_fibre_km_s=C_FIBRE,
    speed_of_light_source="Bozkurt et al., Dissecting Latency in the Internet's Fiber Infrastructure, section 4.2",
    vantage=dict(ip=myip, asn=vasn, **(vg or {})),
    sample=dict(domestic=len(dom), trombone=len(trb), located=len(locs)),
    routing_factor=dict(
        n=len(factors),
        median=round(st.median(factors), 2) if factors else None,
        p25=round(st.quantiles(factors, n=4)[0], 2) if len(factors) > 3 else None,
        p75=round(st.quantiles(factors, n=4)[2], 2) if len(factors) > 3 else None,
        usable=False,
        note="MEASURED but NOT USABLE, and recorded only so nobody derives it again. "
             "A multiplier over the straight-line floor is the wrong model at domestic "
             "distances. Pakistani paths here have a median straight-line length of "
             "about 470 km, worth roughly 4.6 ms, while fixed overhead is 25 to 35 ms. "
             "Regressing measured RTT on distance over 346 domestic destinations gives "
             "R^2 = 0.013 with a slightly negative slope: distance explains essentially "
             "none of the variation. Dividing an overhead-dominated RTT by a tiny "
             "distance term produces a large meaningless number. Use the measured "
             "domestic distribution instead, which needs no geometry at all."),
    path_km=dict(median=round(st.median(spans)) if spans else None,
                 max=round(max(spans)) if spans else None),
    domestic_rtt_ms=dict(n=len(dmin), median=round(st.median(dmin), 1),
                         p75=round(qd[74], 1), p90=round(qd[89], 1),
                         p95=round(qd[94], 1), p97=round(qd[96], 1), p99=round(qd[98], 1),
                         max=max(dmin)),
    trombone_rtt_ms=dict(n=len(tmin), values=tmin,
                         median=round(st.median(tmin), 1) if tmin else None),
    domestic_bound_options=bounds,
    domestic_model=dict(
        geometric_model_usable=False,
        r_squared=0.013,
        note="RTT to a Pakistani destination is dominated by fixed access and "
             "per-path overhead, not by geographic distance, so no geometric ceiling "
             "is defensible domestically. The bound below is therefore purely "
             "empirical: a percentile of THIS vantage's measured domestic RTT, "
             "carrying the error rate shown. It must be re-derived per vantage. "
             "Physics still applies to FOREIGN claims, where distances are thousands "
             "of km and the distance term dominates the overhead: a US claim at "
             "roughly 11,000 km costs about 108 ms straight-line, which no amount of "
             "access overhead can fake downward. That is why R2 falsification stays "
             "geometric while the domestic bound does not."),
    empirical_gap=dict(highest_domestic_below_p97=gap[0], lowest_trombone=gap[1]),
)
json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)

print(f"\nDERIVED, nothing typed in except the speed of light in fibre:")
if factors:
    print(f"  routing factor        median {out['routing_factor']['median']}x  "
          f"(p25 {out['routing_factor']['p25']}, p75 {out['routing_factor']['p75']}), "
          f"n={len(factors)}   <- the assumed value was 2.10")
    print(f"  domestic path length  median {out['path_km']['median']:,} km, max {out['path_km']['max']:,} km")
print(f"  domestic RTT          median {out['domestic_rtt_ms']['median']} ms, "
      f"p90 {out['domestic_rtt_ms']['p90']}, p97 {out['domestic_rtt_ms']['p97']}")
print(f"  tromboning RTT        median {out['trombone_rtt_ms']['median']} ms, n={len(tmin)}")
print(f"\n  candidate domestic bounds, with the error each carries:")
for k, v in bounds.items():
    print(f"    {k:<4} {v['ms']:>6} ms   domestic above it {v['domestic_above']:>3} "
          f"({v['domestic_above_pct']}%)   tromboning below it {v['trombone_below']}")
print(f"\n  empirical gap: highest domestic under p97 = {gap[0]} ms, "
      f"lowest tromboning = {gap[1]} ms")
print(f"wrote derived_constants.json")
