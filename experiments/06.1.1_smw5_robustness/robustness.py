#!/usr/bin/env python3
"""
Exp 6.1.1 - robustness checks for the SMW5 control-plane findings (see notes.md).

  python robustness.py baseline     # W3a: operators' day-over-day churn, 15 May - 10 Jul
  python robustness.py population   # W4: all PK origins, majority-gate switches in the fault window

IHR API rules (learned in Exp 09/6.1): both timebin bounds required, range < 7 days, no `format`
param; never cache partial pulls; operator-level analysis always unfiltered.
"""
import os, sys, json, time, csv
from datetime import datetime, timedelta
from collections import defaultdict
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)
IHR = "https://ihr.iijlab.net/ihr/api/hegemony/"
PTCL, TWA = 17557, 38193
FAULT_DAYS = ("2026-07-01", "2026-07-02")
BASE_DAYS = ("2026-06-26", "2026-06-30")          # inclusive range for W4 baseline


def _load(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}


def _chunks(t0, t1, days=6):
    a = datetime.fromisoformat(t0); end = datetime.fromisoformat(t1)
    out = []
    while a < end:
        b = min(a + timedelta(days=days), end)
        out.append((a.strftime("%Y-%m-%dT%H:%M:%S"), b.strftime("%Y-%m-%dT%H:%M:%S")))
        a = b
    return out


def fetch(origin, gte, lte, asn=None):
    """One chunk, paged. Returns rows or None on any failure (never cache partial)."""
    rows, url = [], IHR
    params = {"originasn": origin, "af": 4, "timebin__gte": gte, "timebin__lte": lte}
    if asn:
        params["asn"] = asn
    try:
        while url:
            r = requests.get(url, params=params, timeout=60); params = None
            if r.status_code != 200:
                print(f"  ! AS{origin} {gte[:10]} HTTP {r.status_code}: {r.text[:80]}")
                return None
            j = r.json()
            rows += j.get("results", [])
            url = j.get("next")
            time.sleep(0.2)
    except Exception as e:
        print(f"  ! AS{origin} {gte[:10]}: {e}")
        return None
    return rows


# ============================ W3a: churn baseline ============================
def cmd_baseline():
    CACHE = os.path.join(HERE, ".cache_baseline.json")
    cache = _load(CACHE)
    T0, T1 = "2026-05-15T00:00:00", "2026-07-10T23:59:59"
    daily = defaultdict(lambda: defaultdict(list))   # origin -> (date, transit) -> [hege]
    for origin in (TWA, PTCL):
        for gte, lte in _chunks(T0, T1):
            key = f"{origin}:{gte[:10]}"
            if key in cache:
                rows = cache[key]
            else:
                rows = fetch(origin, gte, lte)
                if rows is None:
                    print(f"  skipping uncached failed chunk {key}"); continue
                rows = [[x["timebin"][:10], int(x["asn"]), float(x["hege"])]
                        for x in rows if int(x["asn"]) != origin]
                cache[key] = rows
                json.dump(cache, open(CACHE, "w", encoding="utf-8"))
            for d, asn, h in rows:
                daily[origin][(d, asn)].append(h)
        print(f"AS{origin}: {len(cache)} chunks cached")

    # daily mean per transit -> day-over-day churn
    out = []
    for origin in (TWA, PTCL):
        mean = defaultdict(dict)                     # date -> transit -> hege
        for (d, asn), v in daily[origin].items():
            mean[d][asn] = sum(v) / len(v)
        dates = sorted(mean)
        for i in range(1, len(dates)):
            d0, d1 = dates[i - 1], dates[i]
            allt = set(mean[d0]) | set(mean[d1])
            churn = 0.5 * sum(abs(mean[d1].get(t, 0) - mean[d0].get(t, 0)) for t in allt)
            out.append(dict(date=d1, origin=origin, churn=round(churn, 4)))
    with open(os.path.join(RES, "churn_baseline.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "origin", "churn"]); w.writeheader(); w.writerows(out)

    # anomaly statement
    import statistics as st
    for origin, label in ((TWA, "TWA"), (PTCL, "PTCL")):
        series = [(r["date"], r["churn"]) for r in out if r["origin"] == origin]
        vals = [c for _, c in series]
        mu, sd = st.mean(vals), st.pstdev(vals)
        ranked = sorted(series, key=lambda x: -x[1])
        print(f"\n=== {label}: day-over-day churn, {series[0][0]} .. {series[-1][0]} "
              f"({len(vals)} days, mean {mu:.3f}, sd {sd:.3f}) ===")
        for d, c in ranked[:5]:
            z = (c - mu) / sd if sd else 0
            mark = "  <== FAULT WINDOW" if d in ("2026-07-01", "2026-07-02", "2026-07-03") else ""
            print(f"  {d}  churn={c:.3f}  z={z:+.1f}{mark}")
    print("\nwrote results/churn_baseline.csv")


# ============================ W4: population scan ============================
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


def cmd_population():
    CACHE = os.path.join(HERE, ".cache_population.json")
    cache = _load(CACHE)
    T0, T1 = "2026-06-26T00:00:00", "2026-07-06T23:59:59"
    asns = pk_asns()
    print(f"PK origins: {len(asns)}")
    rows_out = []
    for i, origin in enumerate(asns, 1):
        key = str(origin)
        if key in cache:
            series = cache[key]
        else:
            series, ok = [], True
            for gte, lte in _chunks(T0, T1):
                for gate in (PTCL, TWA):
                    rows = fetch(origin, gte, lte, asn=gate)
                    if rows is None:
                        ok = False; break
                    series += [[x["timebin"][:10], int(x["asn"]), float(x["hege"])] for x in rows]
                if not ok:
                    break
            if not ok:
                continue
            cache[key] = series
            if i % 10 == 0:
                json.dump(cache, open(CACHE, "w", encoding="utf-8"))
        # daily means for the two gates
        agg = defaultdict(lambda: defaultdict(list))
        for d, asn, h in series:
            agg[asn][d].append(h)
        def daymean(asn, d0, d1):
            vals = [sum(v) / len(v) for d, v in agg[asn].items() if d0 <= d <= d1]
            return sum(vals) / len(vals) if vals else 0.0
        bp = daymean(PTCL, *BASE_DAYS); bt = daymean(TWA, *BASE_DAYS)
        fp = daymean(PTCL, FAULT_DAYS[0], FAULT_DAYS[-1]); ft = daymean(TWA, FAULT_DAYS[0], FAULT_DAYS[-1])
        if max(bp, bt) < 0.1:
            verdict = "neither"                      # foreign-parent / not gate-dependent
        else:
            base_gate = "PTCL" if bp >= bt else "TWA"
            fault_gate = "PTCL" if fp >= ft else "TWA"
            switched = base_gate != fault_gate and max(fp, ft) >= 0.1
            verdict = "switched" if switched else "held"
        shift = max(abs(fp - bp), abs(ft - bt))
        rows_out.append(dict(origin=origin, base_ptcl=round(bp, 3), base_twa=round(bt, 3),
                             fault_ptcl=round(fp, 3), fault_twa=round(ft, 3),
                             verdict=verdict, max_shift=round(shift, 3),
                             material=shift >= 0.2))
        if i % 25 == 0:
            print(f"  {i}/{len(asns)} ...")
    json.dump(cache, open(CACHE, "w", encoding="utf-8"))
    with open(os.path.join(RES, "population_scan.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["origin", "base_ptcl", "base_twa", "fault_ptcl",
                                          "fault_twa", "verdict", "max_shift", "material"])
        w.writeheader(); w.writerows(rows_out)

    dep = [r for r in rows_out if r["verdict"] != "neither"]
    sw = [r for r in dep if r["verdict"] == "switched"]
    mat = [r for r in dep if r["material"]]
    print(f"\n=== W4 summary ===")
    print(f"  origins with data: {len(rows_out)}; gate-dependent (>=0.1): {len(dep)}")
    print(f"  SWITCHED majority gate on fault days: {len(sw)}/{len(dep)}"
          f"  ({100 * len(sw) / max(len(dep), 1):.1f}%)")
    print(f"  material shift >=0.2 (Fasttel-like): {len(mat)}/{len(dep)}"
          f"  ({100 * len(mat) / max(len(dep), 1):.1f}%)")
    if sw:
        print("  switchers:", [r["origin"] for r in sw][:15])
    print("wrote results/population_scan.csv")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "baseline":
        cmd_baseline()
    elif cmd == "population":
        cmd_population()
    else:
        print(__doc__)
