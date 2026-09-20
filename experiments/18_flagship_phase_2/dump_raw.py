#!/usr/bin/env python3
"""
Exp 18 (flagship phase 2) - archival raw dump.

Reads every results/<instance>/measurements.json (the periodic measurement IDs written by
`panel_monitor.py schedule`) and pulls the FULL raw RIPE JSON for each measurement, writing one
gzipped file per instance: results/<instance>/raw_<instance>_<ts>.json.gz

This is the untouched RIPE output (every probe, every round). Re-fetching costs no credits and
the raw results do not expire, so it is safe to run at any time and to re-run. Suggested: once
partway through the week as a safety copy, and once after the 7-day window closes.

    python dump_raw.py              # every results/*/measurements.json found
    python dump_raw.py rep_a rep_b  # only these instances

Each file is a JSON object {measurement_id: [raw result dicts], ...} plus a "_meta" block with the
class / ip / mode / probe maps from measurements.json.
"""
import os, sys, json, gzip, glob
from datetime import datetime, timezone

from ripe.atlas.cousteau import AtlasResultsRequest

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")


def measurement_ids(meta):
    """All (kind, host, msm_id) triples across the ping and trace maps."""
    for kind in ("trace", "ping"):
        for host, mid in (meta.get(kind) or {}).items():
            yield kind, host, mid


def dump_instance(mjson):
    inst_dir = os.path.dirname(mjson)
    inst = os.path.basename(inst_dir) or "root"
    meta = json.load(open(mjson))
    triples = list(measurement_ids(meta))
    if not triples:
        print(f"  [{inst}] no measurement ids in {mjson} - skipped")
        return

    raw, n_res, n_err = {}, 0, 0
    for kind, host, mid in triples:
        try:
            ok, res = AtlasResultsRequest(msm_id=mid).create()
        except Exception as e:
            print(f"  [{inst}] {kind} {host} (msm {mid}): {e}")
            n_err += 1
            continue
        if not ok:
            print(f"  [{inst}] {kind} {host} (msm {mid}): request not ok")
            n_err += 1
            continue
        raw[str(mid)] = res
        n_res += len(res)

    raw["_meta"] = {k: meta.get(k) for k in ("class", "ip", "mode", "probes", "trace", "ping", "trace_port")}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = os.path.join(inst_dir, f"raw_{inst}_{stamp}.json.gz")
    with gzip.open(out, "wt", encoding="utf-8") as f:
        json.dump(raw, f)
    print(f"  [{inst}] {len(triples)} measurements, {n_res:,} raw results, {n_err} errors "
          f"-> {os.path.basename(out)} ({os.path.getsize(out) / 1e6:.1f} MB)")


def main():
    wanted = set(sys.argv[1:])
    mjsons = sorted(glob.glob(os.path.join(RESULTS, "*", "measurements.json")))
    root = os.path.join(RESULTS, "measurements.json")
    if os.path.exists(root):
        mjsons.append(root)
    if wanted:
        mjsons = [m for m in mjsons if os.path.basename(os.path.dirname(m)) in wanted]
    if not mjsons:
        print(f"no measurements.json found under {RESULTS}")
        sys.exit(1)
    print(f"dumping raw JSON for {len(mjsons)} instance(s):")
    for m in mjsons:
        dump_instance(m)
    print("done.")


if __name__ == "__main__":
    main()
