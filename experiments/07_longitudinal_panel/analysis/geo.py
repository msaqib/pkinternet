#!/usr/bin/env python3
"""
Exp 07 — geolocation & distance toolkit. One script, three subcommands (see METHODOLOGY.md):

  python geo.py distances            # probe -> website great-circle distances     -> distances.csv
  python geo.py locate [targets...]  # compare 5 geolocation methods on a few sites (default sample)
  python geo.py relocate             # physics arbiter: geo-IP vs latency, per site -> relocate.csv
  python geo.py hops                  # annotate EVERY unique hop IP in the raw archive -> hop_annotations.csv

Read-only lookups only: RIPE Atlas probe API (public, no key, 0 credits) + ip-api geo-IP (cached).
Never touches the running measurements.
"""
import os, sys, json, math, time, csv, socket
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RESULTS = os.path.join(EXP, "results")
PROBE_CACHE = os.path.join(HERE, ".cache_probe_geo.json")
IP_CACHE = os.path.join(HERE, ".cache_ip_geo.json")

# ---- constants (METHODOLOGY §Constants) ----
EARTH_R = 6371.0                 # km, mean Earth radius
V_FIBER = 204.218                # km/ms, speed of light in fibre (c/1.468)
V_VAC = 299.792                  # km/ms, speed of light in vacuum
T_LOCAL = 20.0                   # ms, multilateration localize-vs-far threshold
EPS = 0.5                        # ms, weighting guard

# ---- vantage corrections (METHODOLOGY §0) ----
LABEL_FIX = {1015491: "zcom"}            # RIPE asn_v4 = AS152605 (Z-Com); measurements.json mislabels "AS13335"
EXCLUDE_FROM_DISTANCE = {1016036}        # placeholder coordinate (30.0,70.0); 22 ms access floor -> cannot re-locate


# ================================ shared helpers ================================
def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(a))


def rough_city(lat, lon):
    for n, la, lo in [("Lahore", 31.52, 74.35), ("Karachi", 24.86, 67.01),
                      ("Islamabad", 33.66, 73.04), ("Faisalabad", 31.4, 73.1)]:
        if haversine_km(lat, lon, la, lo) < 70:
            return n
    return f"{lat:.2f},{lon:.2f}"


def _load(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}


def _save(p, o):
    json.dump(o, open(p, "w", encoding="utf-8"), indent=0, sort_keys=True)


_pcache, _icache = _load(PROBE_CACHE), _load(IP_CACHE)


def probe_latlon(pid):                    # RIPE Atlas probe API (public, cached)
    k = str(pid)
    if k in _pcache:
        return _pcache[k]
    out = {"lat": None, "lon": None, "cc": ""}
    try:
        r = requests.get(f"https://atlas.ripe.net/api/v2/probes/{pid}/", timeout=20)
        if r.ok:
            d = r.json()
            g = (d.get("geometry") or {}).get("coordinates")
            if g and g[0] is not None:
                out = {"lat": g[1], "lon": g[0], "cc": d.get("country_code") or ""}
        time.sleep(0.25)
    except Exception as e:
        print(f"  ! probe {pid}: {e}")
    _pcache[k] = out; _save(PROBE_CACHE, _pcache)
    return out


def ip_latlon(ip):                        # ip-api geo-IP (cached)
    if not ip:
        return {"lat": None, "lon": None, "city": "", "cc": ""}
    if ip in _icache:
        return _icache[ip]
    out = {"lat": None, "lon": None, "city": "", "cc": ""}
    try:
        d = requests.get(f"http://ip-api.com/json/{ip}",
                         params={"fields": "status,lat,lon,city,countryCode"}, timeout=10).json()
        if d.get("status") == "success":
            out = {"lat": d.get("lat"), "lon": d.get("lon"),
                   "city": d.get("city") or "", "cc": d.get("countryCode") or ""}
        time.sleep(1.4)
    except Exception as e:
        print(f"  ! ip {ip}: {e}")
    _icache[ip] = out; _save(IP_CACHE, _icache)
    return out


def load_measurements():                  # probes {id:label}, ip {host:ip}, class {host:cls}
    probes, ipmap, clsmap = {}, {}, {}
    for inst in ("a", "b"):
        p = os.path.join(RESULTS, inst, "measurements.json")
        if os.path.exists(p):
            m = json.load(open(p, encoding="utf-8"))
            probes.update({int(k): v for k, v in (m.get("probes") or {}).items()})
            ipmap.update(m.get("ip") or {}); clsmap.update(m.get("class") or {})
    return probes, ipmap, clsmap


def isp_of(pid, label):
    return LABEL_FIX.get(pid) or (label.split(".")[0] if "." in label else label)


EXCLUDE_PROBES = {7764, 1015491}   # 7764: 90% loss; 1015491: mislabelled Z-Com duplicate of 7613.
                                   # Aligns geo.py with the notebook/paper's 14-probe roster.


def load_panel_rtt():                     # {target: {probe_id: min_rtt_ms}}  (min-of-N ping)
    import pandas as pd
    panel = max(f for f in os.listdir(os.path.join(RESULTS, "b")) if f.startswith("panel_"))
    df = pd.read_csv(os.path.join(RESULTS, "b", panel))
    df = df[df["kind"] == "ping"].dropna(subset=["rtt_min"])
    df = df[~df["probe_id"].isin(EXCLUDE_PROBES)]
    rtt = {}
    for (t, pid), v in df.groupby(["target", "probe_id"])["rtt_min"].min().items():
        rtt.setdefault(t, {})[int(pid)] = float(v)
    return rtt


# ================================ subcommand: distances ================================
def cmd_distances():
    probes, ipmap, clsmap = load_measurements()
    print(f"probes: {len(probes)}   websites: {len(ipmap)}")
    ploc = {pid: probe_latlon(pid) for pid in probes}
    tloc = {host: ip_latlon(ip) for host, ip in ipmap.items()}

    rows, missing = [], []
    for host, ip in ipmap.items():
        cls = clsmap.get(host, "?")
        t = tloc[host]
        method = "cdn_dstip" if cls.upper() == "CDN" else "server_ip"
        if t["lat"] is None:
            missing.append(host); continue
        for pid, lab in probes.items():
            if pid in EXCLUDE_FROM_DISTANCE:
                continue
            p = ploc[pid]
            if p["lat"] is None:
                continue
            d = haversine_km(p["lat"], p["lon"], t["lat"], t["lon"])
            rows.append(dict(probe_id=pid, probe_isp=isp_of(pid, lab),
                             probe_lat=round(p["lat"], 4), probe_lon=round(p["lon"], 4),
                             target=host, cls=cls, ip=ip,
                             target_lat=round(t["lat"], 4), target_lon=round(t["lon"], 4),
                             target_city=t["city"], target_cc=t["cc"], geo_method=method,
                             distance_km=round(d, 1)))
    cols = ["probe_id", "probe_isp", "probe_lat", "probe_lon", "target", "cls", "ip",
            "target_lat", "target_lon", "target_city", "target_cc", "geo_method", "distance_km"]
    with open(os.path.join(HERE, "distances.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"wrote distances.csv  -  {len(rows)} (probe x website) rows"
          + (f"; {len(missing)} sites unlocated" if missing else ""))


# ================================ subcommand: locate ================================
DEFAULT_LOCATE = ["zcomnetworks.com.pk", "phf.gop.pk", "paknavy.gov.pk", "588wingames.pk"]


def _reverse_dns(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "n/a (no PTR)"


def _ipmap(ip):
    try:
        j = requests.get(f"https://ipmap-api.ripe.net/v1/locate/{ip}/best", timeout=15).json()
        def find(o):
            if isinstance(o, dict):
                if "latitude" in o and "longitude" in o:
                    return o
                for v in o.values():
                    f = find(v)
                    if f: return f
            elif isinstance(o, list):
                for v in o:
                    f = find(v)
                    if f: return f
            return None
        loc = find(j)
        return f"{loc.get('cityName') or loc.get('city') or ''} ({loc['latitude']:.3f},{loc['longitude']:.3f})" if loc else "n/a"
    except Exception:
        return "n/a"


def _colo(host):
    try:
        for line in requests.get(f"https://{host}/cdn-cgi/trace", timeout=10).text.splitlines():
            if line.startswith("colo="):
                return line.split("=", 1)[1] + "  (Cloudflare PoP)"
        return "n/a (not Cloudflare)"
    except Exception:
        return "n/a (no HTTP/colo)"


def _latency_estimate(target, pcoord, rtt):
    pts = [(pid, pcoord.get(str(pid), {}), rtt[target][pid]) for pid in rtt.get(target, {})]
    pts = [(pid, c["lat"], c["lon"], t) for pid, c, t in pts if c.get("lat") is not None]
    if not pts:
        return "n/a (no RTT)", None
    pid, plat, plon, best = min(pts, key=lambda x: x[3])
    radius = best / 2 * V_FIBER
    if best <= T_LOCAL:
        w = [(1.0 / (t + EPS) ** 2, la, lo) for _, la, lo, t in pts]
        W = sum(x[0] for x in w)
        elat, elon = sum(x[0] * x[1] for x in w) / W, sum(x[0] * x[2] for x in w) / W
        return (f"LOCAL: within {radius:,.0f} km of {rough_city(plat, plon)} (nearest {best:.1f} ms) "
                f"-> est ({elat:.3f},{elon:.3f}) {rough_city(elat, elon)}"), (elat, elon)
    return f"FAR: nearest probe {best:.0f} ms ({rough_city(plat, plon)}) -> not local, can't pinpoint", None


def cmd_locate(targets):
    _, ipmap, clsmap = load_measurements()
    rtt = load_panel_rtt()
    for t in (targets or DEFAULT_LOCATE):
        ip = ipmap.get(t, "")
        g = ip_latlon(ip) if ip else {}
        geoip = f"{g.get('city')},{g.get('cc')} ({g['lat']:.3f},{g['lon']:.3f})" if g.get("lat") else "n/a"
        lat_str, lat_pt = _latency_estimate(t, _pcache, rtt)
        print("=" * 76)
        print(f"{t}   [{clsmap.get(t,'?')}]   IP {ip or 'unresolved'}")
        print(f"  1. geo-IP         : {geoip}")
        print(f"  2. reverse DNS    : {_reverse_dns(ip) if ip else 'n/a'}")
        print(f"  3. RIPE IPmap     : {_ipmap(ip) if ip else 'n/a'}")
        print(f"  4. Cloudflare colo: {_colo(t)}")
        print(f"  5. latency (ours) : {lat_str}")
        if g.get("lat") and lat_pt:
            print(f"     -> geo-IP vs latency disagree by {haversine_km(g['lat'],g['lon'],lat_pt[0],lat_pt[1]):,.0f} km")
    print("=" * 76)


# ================================ subcommand: relocate ================================
def cmd_relocate():
    import pandas as pd
    probes, ipmap, clsmap = load_measurements()
    rtt = load_panel_rtt()
    pcoord = {int(k): v for k, v in _pcache.items() if v.get("lat") is not None}
    rows = []
    for host, ip in ipmap.items():
        g = ip_latlon(ip)
        if g.get("lat") is None or host not in rtt:
            continue
        worst_gap, nearest = None, None
        for pid, obs in rtt[host].items():
            p = pcoord.get(pid)
            if not p:
                continue
            vac_floor = 2 * haversine_km(p["lat"], p["lon"], g["lat"], g["lon"]) / V_VAC
            gap = obs - vac_floor
            worst_gap = gap if worst_gap is None else min(worst_gap, gap)
            if nearest is None or obs < nearest[1]:
                nearest = (pid, obs, p["lat"], p["lon"])
        impossible = worst_gap < 0
        pid_n, best, plat, plon = nearest
        radius = best / 2 * V_FIBER
        if best <= T_LOCAL:
            verdict = f"LOCAL (~{radius:.0f} km of {rough_city(plat, plon)})"
        else:
            verdict = f"FAR (nearest {best:.0f} ms)"
        rows.append(dict(target=host, cls=clsmap.get(host, "?"), geoip_city=f"{g.get('city')},{g.get('cc')}",
                         min_rtt_ms=round(best, 1), worst_impossible_gap_ms=round(worst_gap, 1),
                         geoip_impossible=impossible, latency_verdict=verdict,
                         ruling="geo-IP WRONG -> latency" if impossible else "consistent"))
    with open(os.path.join(HERE, "relocate.csv"), "w", newline="", encoding="utf-8") as f:
        cols = ["target", "cls", "geoip_city", "min_rtt_ms", "worst_impossible_gap_ms",
                "geoip_impossible", "latency_verdict", "ruling"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    d = pd.DataFrame(rows)
    print(f"sites analysed: {len(d)}")
    print(f"geo-IP PROVEN WRONG by physics: {int(d.geoip_impossible.sum())}/{len(d)}")
    print(d[d.geoip_impossible].groupby("cls").size().to_string())


# ================================ subcommand: ratio ================================
def cmd_ratio():
    """Corrected latency ratio (METHODOLOGY §2-3, §3b): uses targets_corrected.csv (auto-runs
    `correct` if missing), computes distances inline from the corrected coordinates, writes
    ratio_corrected.csv, and regenerates the official deliverable figures (linear axes):
    figures/ratio_cdf_all3.png (with the CDN ratio from cdn.csv) and figures/ratio_box.png."""
    import pandas as pd, numpy as np
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

    tc = os.path.join(HERE, "targets_corrected.csv")
    if not os.path.exists(tc):
        cmd_correct()
    corr = pd.read_csv(tc).set_index("target")
    probes, ipmap, clsmap = load_measurements()
    rtt = load_panel_rtt()
    pcoord = {int(k): v for k, v in _pcache.items() if v.get("lat") is not None}

    rows = []
    for host, per in rtt.items():
        if host not in corr.index:
            continue
        s = corr.loc[host]
        if s.cls_corrected == "CDN" or pd.isna(s.lat):
            continue
        for pid, m in per.items():
            if pid not in pcoord or pid in EXCLUDE_FROM_DISTANCE:
                continue
            p = pcoord[pid]
            d = haversine_km(p["lat"], p["lon"], s.lat, s.lon)
            theo = 2 * d / V_FIBER
            rows.append(dict(probe_id=pid, probe_isp=isp_of(pid, probes.get(pid, str(pid))),
                             target=host, cls=s.cls_corrected, distance_km=round(d, 1),
                             theoretical_ms=round(theo, 3), measured_ms=m,
                             ratio=round(m / theo, 2) if theo > 0 else None,
                             intercity=d >= 30))
    n = pd.DataFrame(rows)
    n.to_csv(os.path.join(HERE, "ratio_corrected.csv"), index=False)
    ic = n[n.intercity]
    print(f"wrote ratio_corrected.csv ({len(n)} pairs; {len(ic)} inter-city in the ratio)")
    print(ic.groupby("cls")["ratio"].agg(["count", "median"]).round(2).to_string())
    same = n[~n.intercity]
    print(f"same-city pairs (reported in ms, no ratio): {len(same)}, median {same.measured_ms.median():.1f} ms")

    # official figures (linear axes) -- needs cdn.csv for the CDN curve
    cdnp = os.path.join(HERE, "cdn.csv")
    cdn = pd.read_csv(cdnp) if os.path.exists(cdnp) else None
    FIG = os.path.join(HERE, "figures"); os.makedirs(FIG, exist_ok=True)
    INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
    BLUE, GREEN, AMBER = "#2a78d6", "#1baf7a", "#eda100"
    plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                         "axes.edgecolor": "#c3c2b7", "text.color": INK, "axes.labelcolor": INK,
                         "xtick.color": INK2, "ytick.color": INK2, "font.family": "sans-serif",
                         "font.size": 11, "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True})
    series = [("Pakistan", ic[ic.cls == "Pakistan"].ratio, BLUE),
              ("Abroad", ic[ic.cls == "Abroad"].ratio, GREEN)]
    if cdn is not None and "ratio_vs_best" in cdn.columns:
        series.append(("CDN", cdn.ratio_vs_best, AMBER))
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    for name, vals, c in series:
        v = np.sort(vals.dropna().values); y = np.arange(1, len(v) + 1) / len(v)
        ax.plot(v, y, color=c, lw=2.2, label=f"{name} (median {np.median(v):.1f}×)")
    ax.axvline(1, color=MUTED, lw=1.2, ls="--")
    ax.text(1.3, 0.97,
            "1× = theoretical minimum\n(PK/Abroad: straight fibre; CDN: best ISP's real path)",
            fontsize=8, color=INK2, va="top")
    ax.axhline(0.5, color=MUTED, lw=0.8, ls=":")
    ax.set_xlim(0, 40); ax.set_ylim(0, 1.02)
    ax.set_xticks([0, 1, 2, 3, 5, 10, 15, 20, 25, 30, 35, 40])
    ax.set_xlabel("latency ratio (measured ÷ theoretical minimum)")
    ax.set_ylabel("fraction of connections")
    ax.set_title("Latency ratio by site type (CDF)")
    ax.legend(frameon=False, fontsize=9.5, loc="lower right")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "ratio_cdf_all3.png"), dpi=155); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    data = [s[1].dropna().values for s in series]
    bp = ax.boxplot(data, tick_labels=[s[0] for s in series], patch_artist=True, showfliers=False,
                    medianprops=dict(color=INK, lw=1.7), whiskerprops=dict(color=INK2),
                    capprops=dict(color=INK2))
    for p, col in zip(bp["boxes"], [s[2] for s in series]):
        p.set_facecolor(col); p.set_alpha(0.8); p.set_edgecolor(INK2)
    ax.axhline(1, color=MUTED, lw=1.1, ls="--")
    ax.set_ylim(0, 60); ax.set_ylabel("latency ratio (measured ÷ theoretical minimum)")
    ax.set_title("Latency ratio by site type")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "ratio_box.png"), dpi=160); plt.close(fig)
    print("regenerated figures/ratio_cdf_all3.png + figures/ratio_box.png")


# ================================ subcommand: cdn ================================
def cmd_cdn():
    """Per-probe CDN treatment: a CDN has no single location (each ISP reaches a different PoP), so
    we don't compute a distance — we classify each (probe, CDN-site) as local / regional / distant by
    RTT, then score each ISP by how often it reaches CDNs locally. Answers RQ1 (better ISP = better
    service?) without needing a location. Thresholds follow Exp 1.2: local <15 ms, regional <50 ms."""
    import pandas as pd, numpy as np
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    LOCAL, REGIONAL = 15.0, 50.0

    probes, ipmap, clsmap = load_measurements()
    rtt = load_panel_rtt()
    rows = []
    for site, cls in clsmap.items():
        if cls != "CDN":
            continue
        for pid, r in rtt.get(site, {}).items():
            pop = "local" if r < LOCAL else ("regional" if r < REGIONAL else "distant")
            rows.append(dict(isp=isp_of(pid, probes.get(pid, str(pid))), probe_id=pid,
                             site=site, min_rtt_ms=round(r, 1), pop_class=pop))
    d = pd.DataFrame(rows)
    # Instructor's CDN ratio: the theoretical minimum for a site = the BEST RTT any PK probe
    # achieves to it (an attainable real path — any ISP could peer with that ISP and match it).
    # ratio_vs_best = what each ISP loses by not peering. 1.0 = at the frontier.
    d["ratio_vs_best"] = (d["min_rtt_ms"] / d.groupby("site")["min_rtt_ms"].transform("min")).round(2)
    d.to_csv(os.path.join(HERE, "cdn.csv"), index=False)
    print("per-ISP median ratio_vs_best (peering inefficiency):")
    print(d.groupby("isp")["ratio_vs_best"].median().sort_values().round(1).to_string())

    # per-ISP CDN-locality score
    def pct(s, k):
        return round((s == k).mean() * 100, 1)
    summ = d.groupby("isp").apply(lambda g: pd.Series({
        "n_pairs": len(g), "median_rtt": round(g["min_rtt_ms"].median(), 1),
        "pct_local": pct(g["pop_class"], "local"), "pct_regional": pct(g["pop_class"], "regional"),
        "pct_distant": pct(g["pop_class"], "distant")}), include_groups=False).reset_index()
    summ = summ.sort_values("pct_local", ascending=False)
    print(f"wrote cdn.csv - {len(d)} (probe x CDN-site) pairs")
    print("\nper-ISP CDN access (how often a CDN is reached LOCALLY):")
    print(summ.to_string(index=False))

    # figure: grouped bars per ISP (local / regional / distant side by side, all from a shared
    # zero baseline), ISPs on the x-axis, left-to-right in the same best-to-worst peering order
    # as the printed ranking above. Switched from a 100%-stacked bar after review: stacking makes
    # the bottom segment (local) easy to compare across ISPs but hides the middle segment
    # (regional), since its baseline shifts with every bar's local share — grouped bars give
    # every segment its own shared zero baseline, so regional-vs-regional is now a fair read too.
    GREEN, AMBER, RED = "#1baf7a", "#eda100", "#e34948"
    INK2, GRID, SURF = "#52514e", "#e1e0d9", "#fcfcfb"
    plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                         "axes.edgecolor": "#c3c2b7", "font.family": "sans-serif", "font.size": 10,
                         "xtick.color": INK2, "ytick.color": INK2})
    fig, ax = plt.subplots(figsize=(max(7.5, 1.05 * len(summ)), 5.6))
    labs = list(summ.isp)
    loc, reg, dis = summ.pct_local.to_numpy(), summ.pct_regional.to_numpy(), summ.pct_distant.to_numpy()
    x = np.arange(len(labs))
    w = 0.27
    bars_loc = ax.bar(x - w, loc, w, color=GREEN, label="local (<15 ms)")
    bars_reg = ax.bar(x,     reg, w, color=AMBER, label="regional (15–50 ms)")
    bars_dis = ax.bar(x + w, dis, w, color=RED,   label="distant (>50 ms)")
    for bars in (bars_loc, bars_reg, bars_dis):
        for b in bars:
            h = b.get_height()
            if h >= 1:
                ax.text(b.get_x() + b.get_width() / 2, h + 1.5, f"{h:.0f}%",
                        ha="center", va="bottom", fontsize=7, color=INK2)
    for i, m in enumerate(summ.median_rtt):
        ax.text(i, 108, f"median {m:.0f} ms", ha="center", va="bottom", fontsize=7.8,
                color=INK2, style="italic")
    ax.set_ylim(0, 118); ax.set_ylabel("share of that ISP's CDN connections (%)")
    ax.set_xticks(x, labs)
    ax.set_title("CDN access by ISP — how much content is served locally vs far", pad=12)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    ax.legend(frameon=False, ncol=3, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "figures", "cdn_by_isp.png"), dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("\nwrote figures/cdn_by_isp.png (grouped-bar version)")

    # table: per-site BEST case across all ISPs -- "sometimes near/regional (best case)" vs
    # "always far" (no ISP, however well-peered, reaches this site under 50 ms).
    best = d.loc[d.groupby("site")["min_rtt_ms"].idxmin(), ["site", "min_rtt_ms", "pop_class"]]
    best = best.rename(columns={"min_rtt_ms": "best_rtt_ms", "pop_class": "best_case"})
    n_sites = len(best)
    order = ["distant", "regional", "local"]
    label = {"distant": "always far (no ISP reaches it <50 ms)",
              "regional": "sometimes regional (best case 15-50 ms)",
              "local": "sometimes near (best case <15 ms)"}
    counts = best["best_case"].value_counts().reindex(order).fillna(0).astype(int)
    print(f"\nCDN sites by best-case reachability (closest any of the {summ.isp.nunique()} ISPs "
          f"gets, out of {n_sites} CDN sites):")
    for k in order:
        names = best.loc[best.best_case == k, "site"].tolist()
        example = ", ".join(names[:5]) + (f", +{len(names)-5} more" if len(names) > 5 else "")
        print(f"  {label[k]:42s} {counts[k]:3d} / {n_sites} ({100*counts[k]/n_sites:4.1f}%)  e.g. {example}")
    best["best_case"] = pd.Categorical(best["best_case"], categories=order, ordered=True)
    best.sort_values(["best_case", "best_rtt_ms"]).to_csv(
        os.path.join(HERE, "cdn_site_bestcase.csv"), index=False)
    print("wrote cdn_site_bestcase.csv")

    # figure: single 100%-stacked bar over all 39 CDN sites, by best-case reachability.
    # Companion to cdn_by_isp.png (per-ISP), this one is per-SITE: does *any* ISP peer well
    # enough to reach it locally, regardless of which ISP the citizen happens to be on.
    fig, ax = plt.subplots(figsize=(7.5, 1.9))
    pct = {k: 100 * counts[k] / n_sites for k in order}
    left = 0
    for k, color, lab in [("distant", RED, "always far"),
                           ("regional", AMBER, "sometimes regional (best case)"),
                           ("local", GREEN, "sometimes near (best case)")]:
        ax.barh(["all CDN sites"], pct[k], left=left, color=color,
                label=f"{lab} — {counts[k]} ({pct[k]:.0f}%)")
        if pct[k] > 3:
            ax.text(left + pct[k] / 2, 0, f"{pct[k]:.0f}%", ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")
        left += pct[k]
    ax.set_xlim(0, 100); ax.set_xlabel("share of the 39 CDN-hosted sites (%)")
    ax.set_yticks([]); ax.set_title("Is a local path available at all? (best PoP across all ISPs, per site)", pad=10, fontsize=11)
    ax.legend(frameon=False, fontsize=8, loc="upper center", ncol=1, bbox_to_anchor=(1.32, 1.05))
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "figures", "cdn_site_bestcase.png"), dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("wrote figures/cdn_site_bestcase.png")


# ================================ subcommand: correct ================================
def cmd_correct():
    """Fix the locations/classes that physics proved wrong (simple rules):
      - unicast site, geo-IP impossible, latency says LOCAL  -> replace coords with the
        multilateration estimate (it IS local; geo-IP had the wrong city)
      - class 'Pakistan' but latency says FAR                -> class_corrected = 'Abroad'
        (geo-IP location kept: physics is consistent with it; the LABEL was wrong)
      - CDN sites: unchanged here (no single location; per-ISP treatment, cmd_cdn)
    Writes targets_corrected.csv, then rebuilds distances/ratio on the corrected data."""
    import pandas as pd
    probes, ipmap, clsmap = load_measurements()
    rtt = load_panel_rtt()
    pcoord = {int(k): v for k, v in _pcache.items() if v.get("lat") is not None}

    rows = []
    for host, ip in ipmap.items():
        cls = clsmap.get(host, "?")
        g = ip_latlon(ip)
        rec = dict(target=host, cls_design=cls, cls_corrected=cls, ip=ip,
                   lat=g.get("lat"), lon=g.get("lon"), loc_source="geoip", note="")
        if cls != "CDN" and g.get("lat") is not None and host in rtt:
            # physics check + latency verdict (same rules as relocate)
            worst = None; nearest = None
            for pid, obs in rtt[host].items():
                p = pcoord.get(pid)
                if not p:
                    continue
                floor = 2 * haversine_km(p["lat"], p["lon"], g["lat"], g["lon"]) / V_VAC
                worst = min(worst, obs - floor) if worst is not None else obs - floor
                if nearest is None or obs < nearest[1]:
                    nearest = (pid, obs)
            impossible = worst is not None and worst < 0
            best = nearest[1] if nearest else None
            if impossible and best is not None and best <= T_LOCAL:
                # genuinely local, geo-IP city wrong -> multilateration estimate
                _, est = _latency_estimate(host, _pcache, rtt)
                if est:
                    rec.update(lat=round(est[0], 4), lon=round(est[1], 4),
                               loc_source="multilateration", note="geo-IP city impossible; relocated")
            elif cls == "Pakistan" and best is not None and best > T_LOCAL:
                rec.update(cls_corrected="Abroad", note=f"labelled PK but FAR (nearest {best:.0f} ms)")
        rows.append(rec)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(HERE, "targets_corrected.csv"), index=False)
    ch = df[(df.loc_source != "geoip") | (df.cls_design != df.cls_corrected)]
    print(f"wrote targets_corrected.csv ({len(df)} sites; {len(ch)} corrected):")
    print(ch[["target", "cls_design", "cls_corrected", "loc_source", "note"]].to_string(index=False))


# ================================ subcommand: annotate ================================
ASN_CACHE = os.path.join(HERE, ".cache_hop_asn.json")


def _is_private(ip):
    o = ip.split(".")
    if len(o) != 4:
        return True
    a, b = int(o[0]), int(o[1])
    return (a == 10 or (a == 172 and 16 <= b <= 31) or (a == 192 and b == 168)
            or (a == 100 and 64 <= b <= 127) or a == 127 or (a == 169 and b == 254))


_acache = _load(ASN_CACHE)


def hop_info(ip):
    """ASN + holder + geo-IP cc for a hop IP, via RIPEstat (no key). Cached, offline-safe."""
    if ip in _acache:
        return _acache[ip]
    out = {"asn": "", "holder": "", "cc": ""}
    net_error = False  # a network failure must NOT poison the cache with a blank (re-run repairs)
    try:
        j = requests.get("https://stat.ripe.net/data/network-info/data.json",
                         params={"resource": ip}, timeout=15).json()
        asns = j.get("data", {}).get("asns") or []
        if asns:
            out["asn"] = str(asns[0])
            k = requests.get("https://stat.ripe.net/data/as-overview/data.json",
                             params={"resource": "AS" + out["asn"]}, timeout=15).json()
            out["holder"] = (k.get("data", {}).get("holder") or "")[:32]
        time.sleep(0.15)
    except Exception:
        net_error = True
    if not out["asn"]:
        # unannounced in BGP (e.g. Transworld backbone, Equinix egress) -> RDAP registry name
        try:
            j = requests.get(f"https://rdap.org/ip/{ip}", timeout=15,
                             headers={"Accept": "application/rdap+json"}).json()
            out["holder"] = ("[registry] " + (j.get("name") or "?"))[:32]
            out["cc"] = out["cc"] or (j.get("country") or "")
            time.sleep(0.15)
        except Exception:
            net_error = True
    g = _icache.get(ip) or {}
    out["cc"] = g.get("cc", "")
    # cache a genuine answer, or a definitive "no data" (both requests returned) — but never a
    # blank produced by a dropped connection, so a later re-run retries only the network gaps.
    if not (net_error and not out["asn"] and not out["holder"]):
        _acache[ip] = out; _save(ASN_CACHE, _acache)
    return out


def cmd_hops(args):
    """Full-coverage hop annotation: extract EVERY unique hop IP across all traces in the raw
    archive (not just the latest-snapshot routes.txt) and resolve each to ASN | operator | cc.
    Complete IP->owner table so no router on any path variation is unlabelled. Reuses hop_info's
    per-IP cache, so it is resumable and cheap after a partial run.
        python geo.py hops [raw_a_*.json.gz]   (default: newest results/a/raw_a_*.json.gz)"""
    import glob as _g, gzip
    src = args[0] if args else max(_g.glob(os.path.join(RESULTS, "a", "raw_a_*.json.gz")))
    raw = json.load(gzip.open(src, "rt", encoding="utf-8"))
    ips = set()
    for mid, results in raw.items():
        if mid == "_meta":
            continue
        for r in results:
            for hop in r.get("result", []):
                for pkt in hop.get("result", []):
                    frm = pkt.get("from")
                    if frm and not _is_private(frm):
                        ips.add(frm)
    ips = sorted(ips)
    print(f"{os.path.basename(src)}: {len(ips):,} unique public hop IPs to annotate")
    rows, done = [], 0
    for ip in ips:
        h = hop_info(ip)
        rows.append({"ip": ip, "asn": h["asn"], "holder": h["holder"], "cc": h["cc"]})
        done += 1
        if done % 100 == 0:
            print(f"  {done}/{len(ips)} ...")
    miss = sum(1 for r in rows if not r["asn"] and not r["holder"])
    with open(os.path.join(HERE, "hop_annotations.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ip", "asn", "holder", "cc"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote hop_annotations.csv ({len(rows):,} IPs; {miss} still unresolved"
          f"{' - re-run to retry network gaps' if miss else ''})")


def cmd_annotate(args):
    """Offline route annotator: re-render a routes_*.txt with per-hop ASN | operator | geo-cc.
    Run ONCE on frozen data (post-run) - no live lookups during collection, no drift (cached).
        python geo.py annotate [routes.txt] [max_blocks]
    Defaults: newest results/a/routes_*.txt, all blocks. Geo-cc is registration data and is NOT
    trusted for the verdict (RTT-physics decides); it is a label. Output: <input>_annotated.txt"""
    import glob as _g, re
    src = args[0] if args else max(_g.glob(os.path.join(RESULTS, "a", "routes_*.txt")))
    maxb = int(args[1]) if len(args) > 1 else 10 ** 9
    lines = open(src, encoding="utf-8").read().splitlines()
    out, nb = [], 0
    hop_re = re.compile(r"^(\s+\d+\s+(?:[\d.]+|\*)\s+)(\d+\.\d+\.\d+\.\d+)(\s*)(.*)$")
    for ln in lines:
        if ln.startswith("=" * 10):
            nb += 1
            if nb > maxb:
                break
        m = hop_re.match(ln)
        if m:
            ip = m.group(2)
            if _is_private(ip):
                ann = "private"
            else:
                h = hop_info(ip)
                ann = f"AS{h['asn'] or '?'} {h['holder'] or '?'}" + (f" [{h['cc']}]" if h["cc"] else "")
            ln = f"{m.group(1)}{ip:<16} {ann:<42}{m.group(4)}"
        out.append(ln)
    dst = src.replace(".txt", "_annotated.txt")
    open(dst, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"wrote {os.path.basename(dst)}  ({min(nb, maxb)} trace blocks annotated)")


# ================================ dispatch ================================
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "distances"
    if cmd == "distances":
        cmd_distances()
    elif cmd == "locate":
        cmd_locate(sys.argv[2:])
    elif cmd == "relocate":
        cmd_relocate()
    elif cmd == "ratio":
        cmd_ratio()
    elif cmd == "cdn":
        cmd_cdn()
    elif cmd == "correct":
        cmd_correct()
    elif cmd == "hops":
        cmd_hops(sys.argv[2:])
    elif cmd == "annotate":
        cmd_annotate(sys.argv[2:])
    else:
        print(__doc__)
