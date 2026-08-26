#!/usr/bin/env python3
"""
THE final trombone classifier for running_draft.tex: 5-condition AND rule,
FOREIGN_RTT_FLOOR=40ms, ARTIFACT_ASN={Shaw 6327, Cogent 174}, no RTT-alone
backstop path. Reprocesses the raw archive once, extracts everything RQ1/RQ2/RQ3
need: per-round verdict, exit country, handoff ISP (attribution), hop index of
the triggering foreign hop (divergence-location), and AS-path (for reroute
detection). Read-only against raw data; writes final_classified_rounds.csv here.
"""
import os, gzip, json
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RESULTS = os.path.join(EXP, "results")
OUT = HERE

QUEUE_CEIL = 500.0
FOREIGN_RTT_FLOOR = 40.0
ARTIFACT_ASN = {"6327", "174"}  # Shaw + Cogent, physically in PK despite foreign registration
PRIVATE_PREFIXES = ("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.3")


def is_private(ip):
    return ip.startswith(PRIVATE_PREFIXES)


# ---- hop -> (asn, country) lookup, same merged sources as rerun_floor_sensitivity.py ----
hopdf = pd.read_csv(os.path.join(HERE, "hop_annotations.csv"))
hop_lookup = {}
for _, r in hopdf.iterrows():
    asn = str(int(r.asn)) if pd.notna(r.asn) else ""
    cc = r.cc if pd.notna(r.cc) else ""
    hop_lookup[r.ip] = (asn, cc)

cymru_bulk = json.load(open(os.path.join(HERE, "_cymru_bulk_result.json"), encoding="utf-8"))
for ip, v in cymru_bulk.items():
    if v.get("asn") and v["asn"] != "NA":
        hop_lookup[ip] = (v["asn"], v.get("country", ""))

rdap_result = json.load(open(os.path.join(HERE, "_rdap_result.json"), encoding="utf-8"))
for ip, v in rdap_result.items():
    if v.get("country"):
        prev_asn = hop_lookup.get(ip, ("", ""))[0]
        hop_lookup[ip] = (prev_asn, v["country"])

print(f"hop lookup: {len(hop_lookup)} IPs, {sum(1 for a,c in hop_lookup.values() if c)} with country")


def hop_geo(ip):
    return hop_lookup.get(ip, ("", ""))


# ---- ASN -> ISP name (for handoff attribution), from Table 4's roster ----
ASN_TO_ISP = {
    "9541": "Cybernet", "150683": "Fasttel", "23674": "Nayatel", "136174": "Nova",
    "151983": "Orbit", "17557": "PTCL", "135407": "TES", "38193": "Transworld",
    "152605": "Zcom",
}

meas = json.load(open(os.path.join(RESULTS, "a", "measurements.json"), encoding="utf-8"))
msm_to_target = {v: k for k, v in meas["trace"].items()}
probes_meta = meas["probes"]  # {probe_id_str: "isp.probeid"}

cls_corrected = pd.read_csv(os.path.join(HERE, "targets_corrected.csv")).set_index("target")["cls_corrected"]
pk_targets = set(cls_corrected[cls_corrected == "Pakistan"].index)
print(f"Pakistan-class targets: {len(pk_targets)}")

targets_meta = pd.read_csv(os.path.join(EXP, "targets.csv")).set_index("target")
sector_of = targets_meta["cisa_sector"].to_dict()

EXCLUDE_PROBES = {1015491, 7764}


def isp_of(pid):
    label = probes_meta.get(str(pid), str(pid))
    return label.split(".")[0] if "." in label else label


def classify_round(hops):
    """Returns (trombone, exit_cc, handoff_asn, foreign_hop_index, as_path).
    Mirrors census_sweep.classify() exactly, AND-only (no OR/jump/high_rtt backstop)."""
    exit_cc = ""
    handoff_asn = ""
    foreign_idx = None
    as_path = []
    prev_pk_asn = ""
    for idx, (ip, rtt) in enumerate(hops):
        if not ip:
            as_path.append(None)
            continue
        a, cc = hop_geo(ip)
        as_path.append(a or None)
        foreign = (cc not in ("PK", "") and not is_private(ip) and a not in ARTIFACT_ASN
                   and rtt is not None and FOREIGN_RTT_FLOOR <= rtt <= QUEUE_CEIL)
        if foreign and not exit_cc:
            exit_cc = cc
            handoff_asn = prev_pk_asn
            foreign_idx = idx
        if a and a not in ARTIFACT_ASN and (cc == "PK" or (rtt is not None and rtt < FOREIGN_RTT_FLOOR)):
            prev_pk_asn = a
    trombone = bool(exit_cc)
    return trombone, exit_cc, handoff_asn, foreign_idx, as_path


rows = []
raw_path = os.path.join(RESULTS, "a", "raw_a_20260718_201113.json.gz")
print("loading raw archive...")
with gzip.open(raw_path, "rt", encoding="utf-8") as f:
    archive = json.load(f)
print(f"measurements in archive: {len(archive)}")

n_seen = 0
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
        n_seen += 1
        trombone, exit_cc, handoff_asn, foreign_idx, as_path = classify_round(hops)
        rows.append(dict(
            msm_id=msm_id, target=target, probe_id=prb_id, isp=isp_of(prb_id),
            sector=sector_of.get(target, "?"), endtime=rd.get("endtime"),
            n_hops=len(hops), trombone=trombone, exit_cc=exit_cc,
            handoff_isp=ASN_TO_ISP.get(handoff_asn, ""), foreign_hop_index=foreign_idx,
            as_path=json.dumps(as_path),
        ))

out = pd.DataFrame(rows)
out.to_csv(os.path.join(OUT, "final_classified_rounds.csv"), index=False)
print(f"\nrounds classified: {len(out)} (n_seen: {n_seen})")
print(f"\n=== HEADLINE ===")
print(f"trombone rate: {out.trombone.mean()*100:.2f}%  ({out.trombone.sum()}/{len(out)})")
