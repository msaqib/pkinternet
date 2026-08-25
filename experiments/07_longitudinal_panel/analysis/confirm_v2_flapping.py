#!/usr/bin/env python3
"""
Closes the last gap flagged in evidence_reclassification_plan.md: confirms that the
38 pairs classified "flapping" under the new v2 (confirmed-foreign-hop) trombone rule
show a genuine AS-path change between their trombone and local rounds, not just a
verdict flip on an unchanged path.

Reuses the exact test already established and used for the original 193-pair analysis
(evidence_rq3_flapping.md / route_changes.md's Mechanics section): AS-path differs
between two rounds AND the difference isn't explainable by hops merely failing to
respond (one round's responding-hop AS list is not a subsequence of the other's).

Reads .paths_series.json (raw per-round hop/AS sequences) and the panel CSV's exit_cc
column (already-computed live classification). Read-only; writes
v2_flapping_confirmation.csv for the record.
"""
import os, json
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RESULTS = os.path.join(EXP, "results")

trace = pd.read_csv(os.path.join(RESULTS, "a", "panel_20260718_195946.csv"), parse_dates=["ts_utc"])
EXCLUDE_PROBES = {"AS13335.1015491", "ptcl.7764"}
trace_clean = trace[~trace["probe"].isin(EXCLUDE_PROBES)].copy()
cls_corrected = pd.read_csv(os.path.join(HERE, "targets_corrected.csv")).set_index("target")["cls_corrected"]
trace_clean["cls"] = trace_clean["target"].map(cls_corrected)
pk = trace_clean[trace_clean.cls == "Pakistan"].copy()
pk["trombone_v2"] = (pk.exit_cc.notna()) & (pk.exit_cc != "?")
pk["probe_id"] = pk["probe"].str.split(".").str[-1]
pk["epoch"] = (pk["ts_utc"].astype("int64") // 10**9)

pair = pk.groupby(["probe", "probe_id", "target"])["trombone_v2"].agg(frac_v2="mean", n="count").reset_index()
pair50 = pair[pair.n >= 50]
flap = pair50[(pair50.frac_v2 > 0) & (pair50.frac_v2 < 1)].copy()
print(f"v2 flapping pairs to check: {len(flap)}")

paths = json.load(open(os.path.join(HERE, ".paths_series.json"), encoding="utf-8"))


def is_projection(a, b):
    """True if list a is a subsequence of list b or vice versa (visibility-artifact test)."""
    def subseq(short, long):
        it = iter(long)
        return all(x in it for x in short)
    return subseq(a, b) or subseq(b, a)


rows = []
for _, r in flap.iterrows():
    key = f"{r.probe_id}|{r.target}"
    series = paths.get(key)
    if not series:
        rows.append(dict(probe=r.probe, target=r.target, n_transitions=0, n_genuine=0, has_genuine=False, note="no paths_series entry"))
        continue
    # verdict per round, matched by exact epoch timestamp against the panel's exit_cc
    sub = pk[(pk.probe == r.probe) & (pk.target == r.target)][["epoch", "trombone_v2"]].drop_duplicates("epoch")
    verdict = dict(zip(sub.epoch, sub.trombone_v2))

    series_sorted = sorted(series, key=lambda x: x[0])
    n_transitions = 0
    n_genuine = 0
    for i in range(1, len(series_sorted)):
        t0, ips0, as0 = series_sorted[i - 1]
        t1, ips1, as1 = series_sorted[i]
        v0, v1 = verdict.get(t0), verdict.get(t1)
        if v0 is None or v1 is None or v0 == v1:
            continue  # only care about rounds where the v2 verdict actually flips
        n_transitions += 1
        if as0 != as1 and not is_projection(as0, as1):
            n_genuine += 1

    rows.append(dict(probe=r.probe, target=r.target, n_transitions=n_transitions,
                      n_genuine=n_genuine, has_genuine=n_genuine > 0, note=""))

out = pd.DataFrame(rows)
out.to_csv(os.path.join(HERE, "v2_flapping_confirmation.csv"), index=False)

print(f"\npairs with >=1 genuine AS-path-confirmed transition: {out.has_genuine.sum()} / {len(out)}")
print(f"pairs where every v2-verdict transition is a visibility artifact (noise): {(~out.has_genuine).sum()} / {len(out)}")
print(f"\ntotal v2-verdict transitions checked: {out.n_transitions.sum()}")
print(f"...of which genuine (AS-path confirmed different, not a projection): {out.n_genuine.sum()}")
print()
print(out.sort_values("has_genuine", ascending=False).to_string(index=False))
