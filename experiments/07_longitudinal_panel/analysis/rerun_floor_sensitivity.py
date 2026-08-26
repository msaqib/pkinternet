#!/usr/bin/env python3
"""
Sensitivity test for the AND-clause trombone detector: reruns the exact classify()
logic from census_sweep.py (Exp 4.1 / reused for the whole Exp 07 panel) directly
against the raw per-hop RTT archive, with FOREIGN_RTT_FLOOR lowered from 40ms to
20ms, per Sameera's point that a nearby destination (e.g. Oman) could plausibly be
reached in under 40ms from a Karachi-area vantage, so a hop that's genuinely foreign
could be wrongly excluded by too-high a floor.

This reprocesses from the raw archive (not the panel CSV's exit_cc field), because
the panel CSV only records the verdict already computed under the 40ms floor, it
does not preserve per-hop RTT, so a different floor can't be tested by relabeling.

Read-only. Writes floor_sensitivity_results.csv (per-round verdict under both
floors, Pakistan-class only) for the record.
"""
import os, gzip, json
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RESULTS = os.path.join(EXP, "results")

QUEUE_CEIL = 500.0
ARTIFACT_ASN = {"6327", "174"}  # Shaw (physically in PK despite Canadian registration)
PRIVATE_PREFIXES = ("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.3")


def is_private(ip):
    return ip.startswith(PRIVATE_PREFIXES)


# ---- load hop -> (asn, country) annotations, merged from three sources ----
# 1) the existing hop_annotations.csv (906 IPs, only 61 had a country resolved)
# 2) a fresh bulk Team Cymru lookup on every hop IP appearing in PK-class traces that
#    lacked a resolved country (298 IPs -> 169 resolved)
# 3) RDAP fallback (rdap.org) for the remainder Cymru couldn't answer (129 IPs, all
#    resolved: 122 PK, 3 SG) -- the same registry_lookup() method pk_multi_probe.py uses
import json as _json
hopdf = pd.read_csv(os.path.join(HERE, "hop_annotations.csv"))
hop_lookup = {}
for _, r in hopdf.iterrows():
    asn = str(int(r.asn)) if pd.notna(r.asn) else ""
    cc = r.cc if pd.notna(r.cc) else ""
    hop_lookup[r.ip] = (asn, cc)

cymru_bulk = _json.load(open(os.path.join(HERE, "_cymru_bulk_result.json"), encoding="utf-8"))
for ip, v in cymru_bulk.items():
    if v.get("asn") and v["asn"] != "NA":
        hop_lookup[ip] = (v["asn"], v.get("country", ""))

rdap_result = _json.load(open(os.path.join(HERE, "_rdap_result.json"), encoding="utf-8"))
for ip, v in rdap_result.items():
    if v.get("country"):
        # RDAP gives no reliable numeric origin ASN for these (registry allocation
        # record, not a BGP announcement) -- leave asn blank, matching hop_geo()'s
        # own registry_lookup() fallback behaviour in pk_multi_probe.py
        prev_asn = hop_lookup.get(ip, ("", ""))[0]
        hop_lookup[ip] = (prev_asn, v["country"])

n_with_cc = sum(1 for a, c in hop_lookup.values() if c)
print(f"merged hop lookup: {len(hop_lookup)} IPs, {n_with_cc} with a resolved country")


def hop_geo(ip):
    return hop_lookup.get(ip, ("", ""))


# ---- msm_id -> target ----
meas = json.load(open(os.path.join(RESULTS, "a", "measurements.json"), encoding="utf-8"))
msm_to_target = {v: k for k, v in meas["trace"].items()}

# ---- Pakistan-class targets (corrected classification), matching every other script ----
cls_corrected = pd.read_csv(os.path.join(HERE, "targets_corrected.csv")).set_index("target")["cls_corrected"]
pk_targets = set(cls_corrected[cls_corrected == "Pakistan"].index)

EXCLUDE_PROBES = {1015491, 7764}


def classify_round(hops, floor):
    """hops: list of (ip, rtt_or_None) in hop order. Mirrors census_sweep.classify()."""
    exit_cc = ""
    max_rtt = 0.0
    prev = None
    max_jump = 0.0
    prev_pk = ""
    for ip, rtt in hops:
        if not ip:
            continue
        a, cc = hop_geo(ip)
        if rtt is not None and rtt <= QUEUE_CEIL:
            max_rtt = max(max_rtt, rtt)
            if prev is not None and rtt - prev > max_jump:
                max_jump = rtt - prev
            prev = rtt
        elif rtt is not None and prev is None:
            prev = min(rtt, QUEUE_CEIL)
        foreign = (cc not in ("PK", "") and not is_private(ip) and a not in ARTIFACT_ASN
                   and rtt is not None and floor <= rtt <= QUEUE_CEIL)
        if foreign and not exit_cc:
            exit_cc = cc
        if a and a not in ARTIFACT_ASN and (cc == "PK" or (rtt is not None and rtt < floor)):
            prev_pk = a
    trombone = bool(exit_cc)
    return trombone, exit_cc


rows = []
raw_path = os.path.join(RESULTS, "a", "raw_a_20260718_201113.json.gz")
print("loading raw archive (this is a one-time ~34MB decompress)...")
with gzip.open(raw_path, "rt", encoding="utf-8") as f:
    archive = json.load(f)
print(f"measurements in archive: {len(archive)}")

n_rounds = 0
for msm_id_str, rounds in archive.items():
    if not msm_id_str.isdigit():
        continue
    msm_id = int(msm_id_str)
    target = msm_to_target.get(msm_id)
    if target not in pk_targets:
        continue
    for rd in rounds:
        prb_id = rd.get("prb_id")
        if prb_id in EXCLUDE_PROBES:
            continue
        hops = []
        for hop_entry in rd.get("result", []):
            packets = hop_entry.get("result", [])
            ip = next((p.get("from") for p in packets if p.get("from")), None)
            rtts = [p["rtt"] for p in packets if isinstance(p.get("rtt"), (int, float))]
            rtt = min(rtts) if rtts else None
            hops.append((ip, rtt))
        if not hops:
            continue
        n_rounds += 1
        t20, cc20 = classify_round(hops, 20.0)
        t40, cc40 = classify_round(hops, 40.0)
        rows.append(dict(msm_id=msm_id, target=target, probe_id=prb_id,
                          endtime=rd.get("endtime"), trombone_20=t20, trombone_40=t40,
                          exit_cc_20=cc20, exit_cc_40=cc40))

out = pd.DataFrame(rows)
out.to_csv(os.path.join(HERE, "floor_sensitivity_results.csv"), index=False)

print(f"\nPakistan-class rounds reprocessed: {len(out)} (n_rounds seen: {n_rounds})")
print(f"\ntrombone rate @ 40ms floor (should match v2 exit_cc-based result): {out.trombone_40.mean()*100:.2f}%  (n={out.trombone_40.sum()})")
print(f"trombone rate @ 20ms floor: {out.trombone_20.mean()*100:.2f}%  (n={out.trombone_20.sum()})")
print()
newly_confirmed = out[(~out.trombone_40) & (out.trombone_20)]
print(f"rounds newly confirmed foreign ONLY because the floor dropped to 20ms: {len(newly_confirmed)}")
print("countries these newly-confirmed hops resolved to:")
print(newly_confirmed.exit_cc_20.value_counts())
