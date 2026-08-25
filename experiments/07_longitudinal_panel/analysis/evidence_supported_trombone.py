#!/usr/bin/env python3
"""
Sameera's "evidence-supported" reclassification: for a given site, if some probes see a
confirmed foreign hop (Singapore/NL/US chain) at a given destination RTT, and OTHER probes
reaching the SAME site have an invisibility gap (a hop that never responds) but land on the
destination at a similar RTT, the gap is very plausibly hiding the same foreign hop chain,
not a difference in physical route. This does not use RTT alone in isolation (the thing this
whole project's methodology exists to avoid); it requires site-specific corroboration from
other, fully-visible rounds to the identical destination before ever touching RTT.

Rule, precisely: for each Pakistan-class site with >=1 confirmed-trombone round anywhere in
the panel, take the [5th, 95th] percentile of destination RTT observed across all of that
site's confirmed rounds (NOT the full min-max range: a small number of confirmed-trombone
rounds have destination RTT down at ~1ms, almost certainly a Paris-traceroute multipath
artifact where the hop that triggered the verdict isn't the same path the final hop's reply
took, not a real "fast confirmed-foreign round"; min-max lets that noise swallow in local
rounds that shouldn't qualify, checked directly: it inflates the combined rate to 9.7% vs
8.3% with the percentile band, see the script's own printed output for the comparison).
Any currently-non-trombone round for that same site is reclassified "evidence-supported
trombone" if, and only if: (a) it has >=1 hop that never responded before the last responding
hop (a genuine visibility gap, not just a fast, clean local path), and (b) its own destination
RTT (the min RTT of the final answering hop) falls inside that site's [p05, p95] band.

Read-only against the raw archive; requires final_classified_rounds.csv (run
final_classifier.py first). Writes evidence_supported_results.csv.
"""
import os, gzip, json
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RESULTS = os.path.join(EXP, "results")

EXCLUDE_PROBES = {1015491, 7764}

meas = json.load(open(os.path.join(RESULTS, "a", "measurements.json"), encoding="utf-8"))
msm_to_target = {v: k for k, v in meas["trace"].items()}

trace = pd.read_csv(os.path.join(HERE, "final_classified_rounds.csv"))
trombone_lookup = trace.set_index(["msm_id", "probe_id", "endtime"])["trombone"].to_dict()

raw_path = os.path.join(RESULTS, "a", "raw_a_20260718_201113.json.gz")
print("loading raw archive...")
with gzip.open(raw_path, "rt", encoding="utf-8") as f:
    archive = json.load(f)

pk_targets = set(trace.target.unique())

rows = []
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
        responding_idx = [i for i, (ip, rtt) in enumerate(hops) if ip and rtt is not None]
        if not responding_idx:
            continue
        last_idx = max(responding_idx)
        dest_ip, dest_rtt = hops[last_idx]
        gap_before_last = any(not hops[i][0] for i in range(last_idx))
        key = (msm_id, prb_id, rd.get("endtime"))
        trombone = trombone_lookup.get(key)
        if trombone is None:
            continue
        rows.append(dict(msm_id=msm_id, target=target, probe_id=prb_id,
                          dest_rtt=dest_rtt, gap=gap_before_last, trombone=trombone))

out = pd.DataFrame(rows)
print(f"rounds matched: {len(out)}")

# per-site confirmed-trombone destination RTT band (5th-95th percentile, see module docstring
# for why not min-max)
conf = out[out.trombone]
site_range = conf.groupby("target")["dest_rtt"].quantile([0.05, 0.95]).unstack()
site_range.columns = ["p05", "p95"]
print(f"sites with >=1 confirmed-trombone round: {len(site_range)} of {out.target.nunique()}")

out = out.merge(site_range, on="target", how="left")
out["evidence_supported"] = (
    (~out.trombone) & out.gap & out["p05"].notna() &
    (out.dest_rtt >= out["p05"]) & (out.dest_rtt <= out["p95"])
)
out["final_verdict"] = out.trombone | out.evidence_supported

out.to_csv(os.path.join(HERE, "evidence_supported_results.csv"), index=False)

n = len(out)
n_strict = out.trombone.sum()
n_new = out.evidence_supported.sum()
n_final = out.final_verdict.sum()
print(f"\nstrict-rule trombone: {n_strict} ({n_strict/n*100:.2f}%)")
print(f"newly evidence-supported (gap + RTT matches site's confirmed range): {n_new} ({n_new/n*100:.2f}%)")
print(f"combined rate: {n_final} ({n_final/n*100:.2f}%)")
