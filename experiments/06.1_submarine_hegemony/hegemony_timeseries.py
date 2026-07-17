#!/usr/bin/env python3
"""
Exp 6.1 - AS-hegemony time series across the SMW5 fault window (see notes.md).

Pulls daily hegemony curves from IIJ IHR for:
  (a) our probe ISPs' dependency on PTCL/TWA          (did downstreams re-route?)
  (b) PTCL's and TWA's own upstream mix               (did the operators' transit shift?)

Window 2026-06-15 .. 2026-07-10 brackets the fault (2026-07-02). API requires BOTH timebin bounds.
Cached per-origin (.cache_ts.json) - resumable, re-runs free.

    python hegemony_timeseries.py
"""
import os, json, time, csv
from collections import defaultdict
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)
CACHE = os.path.join(HERE, ".cache_ts.json")
IHR = "https://ihr.iijlab.net/ihr/api/hegemony/"
PTCL, TWA = 17557, 38193
T0, T1 = "2026-06-15T00:00:00", "2026-07-10T23:59:59"
FAULT = "2026-07-02"
MIN_HEGE = 0.02

ORIGINS = {
    23674: "Nayatel", 152605: "Z-Com", 9541: "Cybernet", 136174: "Nova",
    135407: "TES", 150683: "Fasttel", 151983: "Orbit", 23888: "NTC",
    17557: "PTCL", 38193: "Transworld",
}


def _load(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}


_cache = _load(CACHE)


def _chunks(t0, t1, days=6):
    """[(gte, lte), ...] covering t0..t1 in <7-day slices (API rejects larger ranges)."""
    from datetime import datetime, timedelta
    a = datetime.fromisoformat(t0); end = datetime.fromisoformat(t1)
    out = []
    while a < end:
        b = min(a + timedelta(days=days), end)
        out.append((a.strftime("%Y-%m-%dT%H:%M:%S"), b.strftime("%Y-%m-%dT%H:%M:%S")))
        a = b
    return out


def fetch_series(origin):
    """All (timebin, transit_asn, hege, transit_name) rows for one origin over the window.
    The API caps each query at <7 days, so the window is fetched in 6-day chunks."""
    key = str(origin)
    if key in _cache:
        return _cache[key]
    rows, ok = [], True
    for gte, lte in _chunks(T0, T1):
        url = IHR
        params = {"originasn": origin, "af": 4, "timebin__gte": gte, "timebin__lte": lte}
        try:
            while url:
                r = requests.get(url, params=params, timeout=60); params = None
                if r.status_code != 200:
                    print(f"  ! AS{origin} {gte[:10]}: HTTP {r.status_code} {r.text[:80]}")
                    ok = False; break
                j = r.json()
                for x in j.get("results", []):
                    if int(x["asn"]) != int(origin) and float(x["hege"]) >= MIN_HEGE:
                        rows.append([x["timebin"], int(x["asn"]),
                                     round(float(x["hege"]), 4), (x.get("asn_name") or "")[:36]])
                url = j.get("next")
                time.sleep(0.25)
        except Exception as e:
            print(f"  ! AS{origin} {gte[:10]}: {e}"); ok = False
    if ok:                                     # never cache a failed/partial pull
        _cache[key] = rows
        json.dump(_cache, open(CACHE, "w", encoding="utf-8"))
    return rows


def main():
    # ---- pull + daily downsample ----
    daily = defaultdict(list)      # (date, origin, transit) -> [hege...]
    names = {}
    for o, label in ORIGINS.items():
        rows = fetch_series(o)
        print(f"AS{o:<7} {label:<11} {len(rows)} rows")
        for tb, asn, h, nm in rows:
            daily[(tb[:10], o, asn)].append(h)
            if nm:
                names[asn] = nm

    out = [dict(date=d, origin=o, origin_name=ORIGINS[o], transit=t,
                transit_name=names.get(t, ""), hegemony=round(sum(v) / len(v), 4))
           for (d, o, t), v in sorted(daily.items())]
    with open(os.path.join(RES, "hegemony_timeseries.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "origin", "origin_name", "transit",
                                          "transit_name", "hegemony"])
        w.writeheader(); w.writerows(out)
    print(f"wrote results/hegemony_timeseries.csv ({len(out)} daily points)")

    # ---- figure ----
    import pandas as pd
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    df = pd.DataFrame(out); df["date"] = pd.to_datetime(df["date"])
    INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
    plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                         "axes.edgecolor": "#c3c2b7", "text.color": INK, "axes.labelcolor": INK,
                         "xtick.color": INK2, "ytick.color": INK2, "font.family": "sans-serif",
                         "font.size": 10, "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True})
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.2, 8.2), sharex=True)

    # top: downstream ISPs' dependency on PTCL (solid) / TWA (dashed)
    CLR = {23674: "#1baf7a", 152605: "#2a78d6", 9541: "#4a3aa7", 136174: "#e87ba4",
           135407: "#eda100", 150683: "#eb6834", 151983: "#008300", 23888: "#898781"}
    for o, c in CLR.items():
        g = df[(df.origin == o) & (df.transit == PTCL)]
        if len(g):
            a1.plot(g.date, g.hegemony, color=c, lw=1.6, label=ORIGINS[o])
        g = df[(df.origin == o) & (df.transit == TWA)]
        if len(g):
            a1.plot(g.date, g.hegemony, color=c, lw=1.6, ls="--")
    a1.set_ylabel("hegemony over origin")
    a1.set_title("Probe ISPs' dependency on PTCL (solid) and Transworld (dashed)", fontsize=10.5)
    a1.legend(frameon=False, fontsize=7.5, ncol=4, loc="upper left")
    a1.set_ylim(0, 1.05)

    # bottom: the operators' own top upstreams
    for o, ls in [(TWA, "-"), (PTCL, ":")]:
        sub = df[df.origin == o]
        top = sub.groupby("transit").hegemony.mean().sort_values(ascending=False).head(5).index
        for t in top:
            g = sub[sub.transit == t]
            a2.plot(g.date, g.hegemony, ls=ls, lw=1.6,
                    label=f"{ORIGINS[o]} ← {names.get(t, t)}"[:44])
    a2.set_ylabel("hegemony over operator")
    a2.set_title("The operators' own upstream mix (TWA solid, PTCL dotted)", fontsize=10.5)
    a2.legend(frameon=False, fontsize=7, ncol=2, loc="upper left")

    for ax in (a1, a2):
        ax.axvline(pd.Timestamp(FAULT), color="#e34948", lw=1.4, ls="--")
    a1.text(pd.Timestamp(FAULT), 1.02, " SMW5 fault (2 Jul)", color="#e34948", fontsize=8.5)
    fig.suptitle("Did the SMW5 fault move Pakistan's logical dependencies? (daily AS hegemony)",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "fig_hegemony_smw5.png"), dpi=150)
    print("wrote results/fig_hegemony_smw5.png")


if __name__ == "__main__":
    main()
