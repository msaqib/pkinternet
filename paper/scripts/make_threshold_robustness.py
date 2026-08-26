#!/usr/bin/env python3
"""
Robustness of the 40 ms tromboning threshold, two panels in one float.

(a) The RTT distribution of every foreign-registered hop on a Pakistani-hosted trace.
    It is sharply bimodal with a near-empty valley, so the threshold's exact value
    inside that valley barely matters.

(b) How the domestic latency ceiling moves with the assumed fibre refractive index.
    The threshold survives every physically achievable value with a wide margin, which
    answers the objection that v_f was assumed rather than measured.

    python paper/make_threshold_robustness.py
"""
import gzip
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "experiments", "07_longitudinal_panel")
AN, RES = os.path.join(EXP, "analysis"), os.path.join(EXP, "results")
OUT = os.path.join(ROOT, "paper", "figures", "fig_threshold_robustness.pdf")

INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
BLUE, RED, AMBER = "#2a78d6", "#d1495b", "#eda100"
FLOOR, CEIL = 40.0, 500.0
ART = {"6327", "174"}
PRIV = ("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.3")
EXCL = {1015491, 7764}
SPAN = 1801.0            # Gwadar to Khunjerab, km
C = 299.792              # km/ms in vacuum

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "font.family": "sans-serif",
    "font.size": 9.5, "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
})


def foreign_rtts():
    lut = {}
    h = pd.read_csv(os.path.join(AN, "hop_annotations.csv"))
    for _, r in h.iterrows():
        lut[r.ip] = (str(int(r.asn)) if pd.notna(r.asn) else "",
                     r.cc if pd.notna(r.cc) else "")
    for ip, v in json.load(open(os.path.join(AN, "_cymru_bulk_result.json"),
                                encoding="utf-8")).items():
        if v.get("asn") and v["asn"] != "NA":
            lut[ip] = (v["asn"], v.get("country", ""))
    for ip, v in json.load(open(os.path.join(AN, "_rdap_result.json"),
                                encoding="utf-8")).items():
        if v.get("country"):
            lut[ip] = (lut.get(ip, ("", ""))[0], v["country"])

    cls = pd.read_csv(os.path.join(AN, "targets_corrected.csv")) \
        .set_index("target")["cls_corrected"]
    pk = set(cls[cls == "Pakistan"].index)
    meas = json.load(open(os.path.join(RES, "a", "measurements.json"), encoding="utf-8"))
    msm = {v: k for k, v in meas["trace"].items()}
    arch = json.load(gzip.open(os.path.join(RES, "a", "raw_a_20260718_201113.json.gz"),
                               "rt", encoding="utf-8"))
    out = []
    for mid, rds in arch.items():
        if not mid.isdigit() or msm.get(int(mid)) not in pk:
            continue
        for rd in rds:
            if rd.get("prb_id") in EXCL:
                continue
            for hh in rd.get("result", []):
                p = hh.get("result", [])
                ip = next((x.get("from") for x in p if x.get("from")), None)
                rr = [x["rtt"] for x in p if isinstance(x.get("rtt"), (int, float))]
                if not ip or not rr or ip.startswith(PRIV):
                    continue
                asn, cc = lut.get(ip, ("", ""))
                if cc and cc != "PK" and asn not in ART:
                    v = min(rr)
                    if v <= CEIL:
                        out.append(v)
    return np.array(out)


def main():
    print("loading raw archive...")
    v = foreign_rtts()
    valley = ((v >= 35) & (v < 70)).sum()

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.4, 3.0))

    # ---- (a) the distribution and its valley
    ax.hist(v, bins=np.arange(0, 210, 5), color=BLUE, alpha=0.85, zorder=3)
    ax.axvspan(35, 70, color=AMBER, alpha=0.22, lw=0, zorder=1)
    ax.axvline(FLOOR, color=RED, lw=1.6, zorder=4)
    ax.set_xlim(0, 205)
    ax.set_xlabel("hop RTT (ms)")
    ax.set_ylabel("foreign-registered hop observations")
    ax.text(FLOOR + 4, ax.get_ylim()[1] * 0.93, "40 ms\nthreshold",
            fontsize=8, color=RED, va="top", zorder=5)
    ax.text(130, ax.get_ylim()[1] * 0.70,
            "%d of %s\nobservations\n(%.1f%%)" % (valley, format(len(v), ","),
                                                  100 * valley / len(v)),
            fontsize=7.8, color=INK, ha="center", va="center", zorder=5,
            bbox=dict(boxstyle="round,pad=0.32", facecolor="white",
                      edgecolor=MUTED, linewidth=0.6, alpha=0.95))
    ax.set_title("(a) hop RTT distribution", fontsize=9, loc="left", pad=6)

    # ---- (b) sensitivity to the assumed refractive index
    n = np.linspace(1.35, 2.7, 400)
    ceiling = SPAN * 1.5 / (C / n / 2)          # 1.5x circuitousness, round trip
    bx.plot(n, ceiling, color=BLUE, lw=2.0, zorder=3)
    bx.axhline(FLOOR, color=RED, lw=1.6, zorder=4)
    bx.axvspan(1.44, 1.50, color=BLUE, alpha=0.18, lw=0, zorder=1)
    cross = 2.22
    bx.plot([cross], [FLOOR], marker="o", ms=5, color=RED, zorder=5)
    bx.set_xlim(1.35, 2.7)
    bx.set_ylim(0, 60)
    bx.set_xlabel("assumed fibre refractive index $n$, $v_f = c/n$")
    bx.set_ylabel("domestic latency ceiling (ms)")
    bx.text(1.47, 57, "real\nfibre", fontsize=7.8, color=BLUE, ha="center", va="top")
    bx.text(2.22, 44, "argument fails\nat $c/2.22$", fontsize=7.8, color=RED,
            ha="center", va="bottom")
    bx.text(1.36, 41.5, "40 ms threshold", fontsize=7.8, color=RED, va="bottom")
    bx.set_title("(b) sensitivity to assumed $v_f$", fontsize=9, loc="left", pad=6)

    fig.tight_layout()
    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("wrote %s" % os.path.relpath(OUT, ROOT))
    print("  %s foreign-hop observations, %d (%.2f%%) between 35 and 70 ms"
          % (format(len(v), ","), valley, 100 * valley / len(v)))


if __name__ == "__main__":
    main()
