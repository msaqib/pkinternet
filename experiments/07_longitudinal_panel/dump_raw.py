#!/usr/bin/env python3
"""
Exp 07 - archival raw dump.

Reads every results/<instance>/measurements.json (the periodic measurement IDs written by
`panel_monitor.py schedule`) and pulls the FULL raw RIPE JSON for each measurement, writing one
gzipped file per instance: results/<instance>/raw_<ts>.json.gz

This is the untouched RIPE output (every probe, every round), independent of RIPE staying
reachable. Run it ONCE after the 7-day window closes. Re-fetching costs no credits and the raw
results never expire, so it is safe to run at any time (and re-run).

    python dump_raw.py            # dump every results/*/measurements.json found
    python dump_raw.py a b        # only these instances

Each raw_<ts>.json.gz is a JSON object: {measurement_id: [ raw result dicts ], ...}
plus a "_meta" block echoing the class/ip/probe maps from measurements.json for self-containment.
"""
import os, sys, json, gzip, glob
from datetime import datetime, timezone
from ripe.atlas.cousteau import AtlasResultsRequest

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")


def measurement_ids(meta):
    """All (kind, host, msm_id) triples across the ping + trace maps."""
    for kind in ("trace", "ping"):
        for host, mid in (meta.get(kind) or {}).items():
            yield kind, host, mid


def dump_instance(mjson):
    inst_dir = os.path.dirname(mjson)
    inst = os.path.basename(inst_dir) or "(root)"
    meta = json.load(open(mjson))
    triples = list(measurement_ids(meta))
    if not triples:
        print(f"  [{inst}] no measurement ids in {mjson} - skipped"); return

    raw, n_res, n_err = {}, 0, 0
    for kind, host, mid in triples:
        try:
            ok, res = AtlasResultsRequest(msm_id=mid).create()
        except Exception as e:
            print(f"  [{inst}] {kind} {host} (msm {mid}): {e}"); n_err += 1; continue
        if not ok:
            print(f"  [{inst}] {kind} {host} (msm {mid}): request not ok"); n_err += 1; continue
        raw[str(mid)] = res
        n_res += len(res)

    raw["_meta"] = {k: meta.get(k) for k in ("class", "ip", "probes", "trace", "ping")}
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = os.path.join(inst_dir, f"raw_{inst if inst != '(root)' else 'root'}_{ts}.json.gz")
    with gzip.open(out, "wt", encoding="utf-8") as f:
        json.dump(raw, f)
    size_mb = os.path.getsize(out) / 1e6
    print(f"  [{inst}] {len(triples)} measurements, {n_res:,} raw results, {n_err} errors "
          f"-> {os.path.basename(out)} ({size_mb:.1f} MB)")


def main():
    wanted = set(sys.argv[1:])
    mjsons = sorted(glob.glob(os.path.join(RESULTS, "*", "measurements.json")))
    root = os.path.join(RESULTS, "measurements.json")
    if os.path.exists(root):
        mjsons.append(root)
    if wanted:
        mjsons = [m for m in mjsons if os.path.basename(os.path.dirname(m)) in wanted]
    if not mjsons:
        print(f"no measurements.json found under {RESULTS}"); sys.exit(1)
    print(f"dumping raw JSON for {len(mjsons)} instance(s):")
    for m in mjsons:
        dump_instance(m)
    print("done.")


if __name__ == "__main__":
    main()
