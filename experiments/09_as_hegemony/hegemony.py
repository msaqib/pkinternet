#!/usr/bin/env python3
"""
Exp 09 - AS Hegemony via IIJ's Internet Health Report (IHR) public API. See notes.md.

  python hegemony.py deps [asn ...]   # per-origin dependency table (default: probe ISPs + operators)
  python hegemony.py rollup           # every PK origin AS -> results/pk_hegemony_rollup.csv

Free public API, no key. Per-AS results cached in .cache_hegemony.json (resumable).
Hegemony = trimmed mean fraction of BGP AS-paths toward the origin that traverse a transit AS
(Fontugne et al.); 1.0 = total dependency. IPv4 (af=4). Paths, not traffic volume.
"""
import os, sys, json, time, csv
from datetime import datetime, timedelta, timezone
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)
CACHE = os.path.join(HERE, ".cache_hegemony.json")
IHR = "https://ihr.iijlab.net/ihr/api/hegemony/"
PTCL, TWA = 17557, 38193

# our probe ISPs (Exp 07 roster) + the two operators
PROBE_ISPS = {
    23674: "Nayatel", 152605: "Z-Com", 9541: "Cybernet", 136174: "Nova/TPCPL",
    135407: "TES (Transworld Home)", 150683: "Fasttel", 151983: "Orbit",
    23888: "NTC", 17557: "PTCL", 38193: "Transworld",
}


def _load(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}


_cache = _load(CACHE)


def as_name(asn):
    key = f"name:{asn}"
    if key in _cache:
        return _cache[key]
    nm = ""
    try:
        j = requests.get("https://stat.ripe.net/data/as-overview/data.json",
                         params={"resource": f"AS{asn}"}, timeout=15).json()
        nm = (j.get("data", {}).get("holder") or "")[:40]
        time.sleep(0.1)
    except Exception:
        pass
    _cache[key] = nm
    json.dump(_cache, open(CACHE, "w", encoding="utf-8"))
    return nm


def local_hegemony(origin):
    """Latest-bin dependency list for one origin AS: [(transit_asn, hegemony), ...] desc.
    Also caches the transit AS names the API returns inline."""
    key = f"deps:{origin}"
    if key in _cache:
        return _cache[key]
    now = datetime.now(timezone.utc)
    params = {"originasn": origin, "af": 4,
              "timebin__gte": (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S"),
              "timebin__lte": now.strftime("%Y-%m-%dT%H:%M:%S")}
    rows, url = [], IHR
    try:
        while url:
            r = requests.get(url, params=params, timeout=60); params = None
            j = r.json()
            rows += j.get("results", [])
            url = j.get("next")
            time.sleep(0.2)
    except Exception as e:
        print(f"  ! AS{origin}: {e}")
    deps = {}
    if rows:
        latest = max(r["timebin"] for r in rows)
        for r in rows:
            if r["timebin"] == latest and int(r["asn"]) != int(origin):
                deps[int(r["asn"])] = round(float(r["hege"]), 4)
                if r.get("asn_name"):
                    _cache[f"name:{r['asn']}"] = r["asn_name"][:40]
    out = sorted(deps.items(), key=lambda kv: -kv[1])
    _cache[key] = out
    json.dump(_cache, open(CACHE, "w", encoding="utf-8"))
    return out


def pk_asns():
    j = requests.get("https://stat.ripe.net/data/country-resource-list/data.json",
                     params={"resource": "PK"}, timeout=30).json()
    out = []
    for item in j["data"]["resources"]["asn"]:
        if "-" in str(item):
            a, b = str(item).split("-"); out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(item))
    return out


def cmd_deps(asns):
    asns = [int(a) for a in asns] or list(PROBE_ISPS)
    rows = []
    for o in asns:
        deps = local_hegemony(o)
        label = PROBE_ISPS.get(o) or as_name(o)
        print(f"\nAS{o}  {label}")
        if not deps:
            print("   (no hegemony data - AS may not be announcing prefixes)"); continue
        for asn, h in deps[:6]:
            tag = " <-- PTCL" if asn == PTCL else (" <-- Transworld" if asn == TWA else "")
            print(f"   depends on AS{asn:<7} hege={h:5.2f}  {as_name(asn)}{tag}")
            rows.append(dict(origin=o, origin_name=label, transit=asn,
                             transit_name=as_name(asn), hegemony=h))
    with open(os.path.join(RES, "probe_isp_deps.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["origin", "origin_name", "transit", "transit_name", "hegemony"])
        w.writeheader(); w.writerows(rows)
    print(f"\nwrote results/probe_isp_deps.csv ({len(rows)} rows)")


def cmd_rollup():
    asns = pk_asns()
    print(f"PK origin ASes: {len(asns)}")
    rows = []
    for i, o in enumerate(asns, 1):
        deps = local_hegemony(o)
        d = dict(deps)
        top = deps[0] if deps else (None, None)
        rows.append(dict(origin=o, hege_ptcl=d.get(PTCL, 0.0), hege_twa=d.get(TWA, 0.0),
                         top_dep=top[0], top_hege=top[1],
                         n_deps=len(deps)))
        if i % 25 == 0:
            print(f"  {i}/{len(asns)} ...")
    with open(os.path.join(RES, "pk_hegemony_rollup.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["origin", "hege_ptcl", "hege_twa", "top_dep", "top_hege", "n_deps"])
        w.writeheader(); w.writerows(rows)

    live = [r for r in rows if r["n_deps"] > 0]          # ASes with BGP visibility
    def frac(th):
        n = sum(1 for r in live if r["hege_ptcl"] >= th or r["hege_twa"] >= th)
        return n, round(100 * n / len(live), 1)
    n50, p50 = frac(0.5); n10, p10 = frac(0.1)
    import statistics as st
    med_p = st.median([r["hege_ptcl"] for r in live])
    med_t = st.median([r["hege_twa"] for r in live])
    print(f"\n=== RQ1 summary ({len(live)} PK ASes visible in BGP, of {len(asns)} registered) ===")
    print(f"  PTCL or TWA hegemony >= 0.5 (majority of paths): {n50}/{len(live)} = {p50}%")
    print(f"  PTCL or TWA hegemony >= 0.1 (material dependency): {n10}/{len(live)} = {p10}%")
    print(f"  median hegemony across PK origins: PTCL {med_p:.2f}, TWA {med_t:.2f}")
    print("wrote results/pk_hegemony_rollup.csv")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "deps"
    if cmd == "deps":
        cmd_deps(sys.argv[2:])
    elif cmd == "rollup":
        cmd_rollup()
    else:
        print(__doc__)
