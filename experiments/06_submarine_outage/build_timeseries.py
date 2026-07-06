#!/usr/bin/env python3
"""
Exp 06: pull the per-round ping RTT for every (probe, target) from the RIPE
measurements and write a tidy long-format time series the notebook can plot
(no API needed at plot time).

    python experiments/06_submarine_outage/build_timeseries.py
Output: results/timeseries.csv  (epoch, ts_utc, probe_id, probe, cat, target, target_ip, rtt_ms)
"""
import os, json, csv
from datetime import datetime, timezone
from ripe.atlas.cousteau import AtlasResultsRequest
from ripe.atlas.sagan import PingResult

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
meta = json.load(open(os.path.join(OUT, "measurements.json")))
P = meta["probes"]

rows = []
for host, mid in meta["ping"].items():
    cat = meta["target_cat"][host]; ip = meta["target_ip"][host]
    try:
        ok, res = AtlasResultsRequest(msm_id=mid).create()
    except Exception as e:
        print(f"  {host}: {e}"); continue
    if not ok:
        continue
    for r in res:
        try:
            pg = PingResult.get(r)
        except Exception:
            continue
        if pg.rtt_median is None:          # destination didn't reply this round
            continue
        ts = r.get("timestamp", 0)
        rows.append(dict(epoch=ts,
                         ts_utc=datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                         probe_id=r.get("prb_id"), probe=P.get(str(r.get("prb_id")), r.get("prb_id")),
                         cat=cat, target=host, target_ip=ip, rtt_ms=round(pg.rtt_median, 1)))

rows.sort(key=lambda x: (x["target"], str(x["probe"]), x["epoch"]))
out = os.path.join(OUT, "timeseries.csv")
cols = ["epoch", "ts_utc", "probe_id", "probe", "cat", "target", "target_ip", "rtt_ms"]
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(f"wrote {out}  ({len(rows)} points, {len({r['target'] for r in rows})} targets, "
      f"{len({r['probe_id'] for r in rows})} probes)")
