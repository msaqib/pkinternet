#!/usr/bin/env python3
"""
Ablation of the tromboning rule: what each of the two substantive clauses is worth.

All variants share the same preconditions (hop replied, has an RTT, is not a private
address) and the same denominator: 75,600 traceroute rounds to Pakistani-hosted sites
from 14 probes. Only the artifact list and the 40 ms floor are varied.

    python experiments/07_longitudinal_panel/analysis/rule_ablation.py
"""
import collections
import gzip
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RES = os.path.join(EXP, "results")

FLOOR, CEIL = 40.0, 500.0
ARTIFACT = {"6327", "174"}
PRIV = ("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.3")
EXCLUDE = {1015491, 7764}


def main():
    lut = {}
    h = pd.read_csv(os.path.join(HERE, "hop_annotations.csv"))
    for _, r in h.iterrows():
        lut[r.ip] = (str(int(r.asn)) if pd.notna(r.asn) else "",
                     r.cc if pd.notna(r.cc) else "")
    for ip, v in json.load(open(os.path.join(HERE, "_cymru_bulk_result.json"),
                                encoding="utf-8")).items():
        if v.get("asn") and v["asn"] != "NA":
            lut[ip] = (v["asn"], v.get("country", ""))
    for ip, v in json.load(open(os.path.join(HERE, "_rdap_result.json"),
                                encoding="utf-8")).items():
        if v.get("country"):
            lut[ip] = (lut.get(ip, ("", ""))[0], v["country"])

    cls = pd.read_csv(os.path.join(HERE, "targets_corrected.csv")) \
        .set_index("target")["cls_corrected"]
    pk = set(cls[cls == "Pakistan"].index)
    meas = json.load(open(os.path.join(RES, "a", "measurements.json"), encoding="utf-8"))
    msm = {v: k for k, v in meas["trace"].items()}
    print("loading raw archive...")
    arch = json.load(gzip.open(os.path.join(RES, "a", "raw_a_20260718_201113.json.gz"),
                               "rt", encoding="utf-8"))

    VARIANTS = [
        ("geolocation only, no artifact list, no floor", False, False, False),
        ("no artifact list, no floor, 500 ms ceiling kept", False, False, True),
        ("artifact list only, no 40 ms floor", True, False, True),
        ("40 ms floor only, no artifact list", False, True, True),
        ("both, the published rule", True, True, True),
    ]
    n = 0
    hits = collections.Counter()
    for mid, rds in arch.items():
        if not mid.isdigit() or msm.get(int(mid)) not in pk:
            continue
        for rd in rds:
            if rd.get("prb_id") in EXCLUDE:
                continue
            hops = []
            for hh in rd.get("result", []):
                p = hh.get("result", [])
                ip = next((x.get("from") for x in p if x.get("from")), None)
                rr = [x["rtt"] for x in p if isinstance(x.get("rtt"), (int, float))]
                hops.append((ip, min(rr) if rr else None))
            if not hops:
                continue
            n += 1
            got = {v[0]: False for v in VARIANTS}
            for ip, rtt in hops:
                if not ip or rtt is None or ip.startswith(PRIV):
                    continue
                asn, cc = lut.get(ip, ("", ""))
                if not cc or cc == "PK":
                    continue
                for label, use_art, use_floor, use_ceil in VARIANTS:
                    if use_art and asn in ARTIFACT:
                        continue
                    if use_floor and rtt < FLOOR:
                        continue
                    if use_ceil and rtt > CEIL:
                        continue
                    got[label] = True
            for k, v in got.items():
                hits[k] += v

    print("\n%d unique traceroute measurements to Pakistani-hosted sites\n" % n)
    print("%-48s %8s %8s" % ("rule", "tromboned", "rate"))
    print("-" * 66)
    for label, _, _, _ in VARIANTS:
        print("%-48s %8d %7.2f%%" % (label, hits[label], 100 * hits[label] / n))
    print()
    base = hits["both, the published rule"]
    print("what each clause is worth, against the published rule:")
    print("  dropping the artifact list alone adds %+d rounds (%+.2f points)"
          % (hits["40 ms floor only, no artifact list"] - base,
             100 * (hits["40 ms floor only, no artifact list"] - base) / n))
    print("  dropping the 40 ms floor alone adds  %+d rounds (%+.2f points)"
          % (hits["artifact list only, no 40 ms floor"] - base,
             100 * (hits["artifact list only, no 40 ms floor"] - base) / n))
    print("  dropping both adds                   %+d rounds (%+.2f points)"
          % (hits["no artifact list, no floor, 500 ms ceiling kept"] - base,
             100 * (hits["no artifact list, no floor, 500 ms ceiling kept"] - base) / n))


if __name__ == "__main__":
    main()
