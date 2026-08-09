#!/usr/bin/env python3
"""
Exp 07 - reclassify tromboning verdicts directly from the archival raw dump.

dump_raw.py pulls every raw traceroute result RIPE has for this panel into
results/<instance>/raw_<instance>_<ts>.json.gz (run that first if it doesn't exist yet - no
credits spent, re-fetchable anytime). This script re-runs each raw trace through the same
classifier panel_monitor.py uses live (census_sweep.classify, i.e. tromboning_sweep.py's
RTT-physics constants: FOREIGN_RTT_FLOOR=40ms, JUMP_THRESH=60ms, HIGH_RTT=70ms, LOCAL_CEIL=45ms,
QUEUE_CEIL=500ms) to produce a fresh, from-scratch status per (probe, target, round):

  trombone_hop - a hop actually resolved to a foreign IP (hard evidence - "foreign hop only")
  trombone_rtt - no foreign hop seen; inferred only from an RTT jump/ceiling (soft evidence)
  local        - reached, and stayed under the RTT-physics floor for ever leaving PK
  inconclusive - neither confirmed (e.g. path never resolves far enough)

isp_asn is passed as "0" (never matches), same as panel_monitor.py's live fetch() - Exp 07 isn't
testing reachability of one target ISP's own ASN like Exp 4.1's census does, so the `reached`
signal is irrelevant here and "local" falls back to the RTT ceiling alone.

    python reclassify_raw.py                  # every raw_*.json.gz found under results/
    python reclassify_raw.py results/a/raw_a_20260718_120000.json.gz
"""
import os, sys, csv, gzip, json, glob
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "04.1_small_isp_tromboning"))
import census_sweep as cs

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")


def latest_raw_dumps():
    return sorted(glob.glob(os.path.join(RESULTS, "*", "raw_*.json.gz")))


def reclassify_dump(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        raw = json.load(f)
    meta = raw.pop("_meta", {})
    probes = meta.get("probes", {})
    cls_of = meta.get("class", {})
    trace_ids = {str(mid): host for host, mid in (meta.get("trace") or {}).items()}

    rows = []
    for mid, results in raw.items():
        host = trace_ids.get(str(mid))
        if host is None:
            continue  # a ping measurement id - nothing to classify
        for r in results:
            try:
                v = cs.classify(r, "0")
            except Exception as e:
                v = dict(status="inconclusive", evidence=f"parse_error:{e}",
                          exit_cc="", transit="", max_rtt="")
            prb = r.get("prb_id")
            ts = r.get("timestamp")
            rows.append(dict(
                ts_utc=(datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                        if ts else ""),
                msm_id=mid, probe_id=prb, probe=probes.get(str(prb), prb),
                target=host, cls=cls_of.get(host, ""),
                status=v["status"], tromboned=v["status"] in ("trombone_hop", "trombone_rtt"),
                exit_cc=v.get("exit_cc", ""), transit=v.get("transit", ""),
                max_rtt=v.get("max_rtt", "")))
    return rows


def main():
    targets = sys.argv[1:] or latest_raw_dumps()
    if not targets:
        print(f"no raw_*.json.gz found under {RESULTS} - run dump_raw.py first")
        sys.exit(1)
    for path in targets:
        rows = reclassify_dump(path)
        if not rows:
            print(f"  {path}: no trace rows"); continue
        rows.sort(key=lambda x: (x["target"], str(x["probe"]), x["ts_utc"]))
        out = path.replace("raw_", "reclassified_").replace(".json.gz", ".csv")
        cols = ["ts_utc", "msm_id", "probe_id", "probe", "target", "cls", "status", "tromboned",
                "exit_cc", "transit", "max_rtt"]
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
        n_hop = sum(1 for r in rows if r["status"] == "trombone_hop")
        n_rtt = sum(1 for r in rows if r["status"] == "trombone_rtt")
        n_loc = sum(1 for r in rows if r["status"] == "local")
        n_inc = sum(1 for r in rows if r["status"] == "inconclusive")
        print(f"  {os.path.basename(path)}: {len(rows)} traces -> {os.path.basename(out)} "
              f"(trombone_hop {n_hop}, trombone_rtt {n_rtt}, local {n_loc}, inconclusive {n_inc})")


if __name__ == "__main__":
    main()
