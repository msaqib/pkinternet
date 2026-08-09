#!/usr/bin/env python3
"""
Exp 07 - v2 reclassification, reproducing Rayan's proposed detector fix
(analysis/running_draft_recommendations.md, section 2.4) directly against the raw dump, side by
side with the detector as it's always been run, so the comparison isn't done by hand.

Computes TWO verdicts per trace, from the same hop data, in one pass:

  type2 ("RTT-physics-inclusive", what census_sweep.py / panel_monitor.py / reclassify_raw.py
    already compute): trombone_hop OR trombone_rtt. Only Shaw (AS6327) excluded as a known
    registration-vs-physical-location artifact. A round can be flagged tromboned from RTT alone
    (a >=60ms hop-to-hop jump, or any hop >=70ms) even with no foreign hop ever resolving.

  type1 (Rayan's fix): hop-only, no RTT-alone fallback at all. A round is tromboned only if an
    actual hop resolves to a foreign IP. Two more known artifacts excluded on top of Shaw:
      - Cogent (AS174): a router physically inside Pakistan despite US registration
      - any hop whose ASN name matches the paper's own CDN_KEYWORDS list
        (site_collection/classify_pk_hosting.py: Cloudflare, Akamai, Fastly, CDN77, ... - these
        are known, systematically, to have local PoPs inside Pakistan despite foreign registration)
    A round with no confirmed foreign hop is 'local' (reached, low max RTT) or 'inconclusive'
    (elevated RTT, no hop evidence) - never 'trombone' from RTT alone.

Site list: Pakistan-class = the ORIGINAL 40-site design set minus toptop.net/youth.cn (dropped
entirely - confirmed foreign-content reseller sites). phf.gop.pk STAYS Pakistan: its "abroad" read
elsewhere traces to a ping-vs-traceroute DNS split (the ping leg resolved to an unrelated US
shared-hosting IP; the traceroute leg, which is what the trombone detector actually uses, correctly
hits the real PITB-owned PK IP) - so it does not belong in Abroad here.

    python reclassify_v2.py
"""
import os, sys, csv, gzip, json, glob
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

sys.path.insert(0, os.path.join(HERE, "..", "04_path_tromboning"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "measurement"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "site_collection"))

from tromboning_sweep import hop_geo, FOREIGN_RTT_FLOOR, JUMP_THRESH, HIGH_RTT, LOCAL_CEIL
import pk_multi_probe as pk
from classify_pk_hosting import CDN_KEYWORDS

QUEUE_CEIL = 500.0
ARTIFACT_ASN_BASE = {"6327"}          # Shaw only - type2 / current shared code
ARTIFACT_ASN_V2 = {"6327", "174"}     # + Cogent - type1

DROP_SITES = {"toptop.net", "youth.cn"}
EXCLUDE_PROBES = {7764, 1015491}
LABEL_FIX = {1015491: "zcom"}


def is_cdn_name(name):
    return any(kw in (name or "").upper() for kw in CDN_KEYWORDS)


def isp_of(pid, label):
    return LABEL_FIX.get(pid) or (label.split(".")[0] if "." in label else label)


def classify_both(res):
    """One pass over hops -> (type1_status, type2_status)."""
    hops_info = []
    for hop in res.get("result", []):
        pkts = hop.get("result", [])
        ip = next((p.get("from") for p in pkts if p.get("from")), None)
        rtts = [p["rtt"] for p in pkts if isinstance(p.get("rtt"), (int, float))]
        rtt = min(rtts) if rtts else None
        if not ip:
            continue
        a, name, cc = hop_geo(ip)
        hops_info.append((rtt, ip, a, name, cc))

    # ---- type2: original two-tier, Shaw-only excluded ----
    max_rtt2 = 0.0; prev = None; max_jump = 0.0; exit_cc2 = None
    for rtt, ip, a, name, cc in hops_info:
        if rtt is not None and rtt <= QUEUE_CEIL:
            max_rtt2 = max(max_rtt2, rtt)
            if prev is not None and rtt - prev > max_jump:
                max_jump = rtt - prev
            prev = rtt
        elif rtt is not None and prev is None:
            prev = min(rtt, QUEUE_CEIL)
        artifact2 = a in ARTIFACT_ASN_BASE
        foreign2 = (cc not in ("PK", "") and not pk.PRIVATE(ip) and not artifact2
                    and rtt is not None and FOREIGN_RTT_FLOOR <= rtt <= QUEUE_CEIL)
        if foreign2 and exit_cc2 is None:
            exit_cc2 = cc
    if exit_cc2:
        status2 = "trombone_hop"
    elif max_jump >= JUMP_THRESH or max_rtt2 >= HIGH_RTT:
        status2 = "trombone_rtt"
    else:
        status2 = "local" if (max_rtt2 and max_rtt2 < LOCAL_CEIL) else "inconclusive"

    # ---- type1: Rayan's hop-only fix, Shaw+Cogent+CDN-name excluded, no RTT fallback ----
    max_rtt1 = 0.0; exit_cc1 = None
    for rtt, ip, a, name, cc in hops_info:
        if rtt is None or rtt > QUEUE_CEIL:
            continue
        max_rtt1 = max(max_rtt1, rtt)
        artifact1 = (a in ARTIFACT_ASN_V2) or is_cdn_name(name)
        foreign1 = (cc not in ("PK", "") and not pk.PRIVATE(ip) and not artifact1
                    and FOREIGN_RTT_FLOOR <= rtt <= QUEUE_CEIL)
        if foreign1 and exit_cc1 is None:
            exit_cc1 = cc
    status1 = ("trombone_hop" if exit_cc1 else
               "local" if (max_rtt1 and max_rtt1 < LOCAL_CEIL) else "inconclusive")

    return status1, status2


def main():
    raw_paths = sorted(glob.glob(os.path.join(RESULTS, "a", "raw_*.json.gz")))
    if not raw_paths:
        sys.exit("no raw_*.json.gz found under results/a - run dump_raw.py first")
    raw_path = raw_paths[-1]
    with gzip.open(raw_path, "rt", encoding="utf-8") as f:
        raw = json.load(f)
    meta = raw.pop("_meta", {})
    probes = meta.get("probes", {})
    design_cls = meta.get("class", {})           # original 40/40/20 design labels
    trace_ids = {str(mid): host for host, mid in (meta.get("trace") or {}).items()}

    sector = {}
    for r in csv.DictReader(open(os.path.join(HERE, "targets.csv"), encoding="utf-8")):
        sector[r["target"]] = r["cisa_sector"]

    rows = []
    for mid, results in raw.items():
        host = trace_ids.get(str(mid))
        if host is None or host in DROP_SITES:
            continue
        cls = design_cls.get(host, "")
        for r in results:
            prb = r.get("prb_id")
            try:
                s1, s2 = classify_both(r)
            except Exception as e:
                s1, s2 = "inconclusive", "inconclusive"
            rows.append(dict(probe_id=prb, target=host, cls=cls,
                             sector=sector.get(host, "?"), type1=s1, type2=s2))

    out = os.path.join(RESULTS, "a", "reclassified_v2.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        cols = ["probe_id", "target", "cls", "sector", "type1", "type2"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"wrote {out} ({len(rows)} trace rows, {len(DROP_SITES)} sites dropped)")

    pk_rows = [r for r in rows if r["cls"] == "Pakistan" and int(r["probe_id"]) not in EXCLUDE_PROBES]
    print(f"\nPakistan-class rows (38-site def, 14-probe roster): {len(pk_rows)}")

    def rate(rows_, key, want):
        c = Counter(r[key] for r in rows_)
        t = sum(c.values())
        return 100 * c.get(want, 0) / t if t else 0.0, t

    r1, n = rate(pk_rows, "type1", "trombone_hop")
    r2_hop, _ = rate(pk_rows, "type2", "trombone_hop")
    c2 = Counter(r["type2"] for r in pk_rows)
    r2_combined = 100 * (c2["trombone_hop"] + c2["trombone_rtt"]) / n

    print(f"\nOVERALL (n={n})")
    print(f"  type1 (Rayan: hop-only, Shaw+Cogent+CDN excluded)      : {r1:.2f}%")
    print(f"  type2 (RTT-physics-inclusive, Shaw-only, hop-only part): {r2_hop:.2f}%")
    print(f"  type2 (RTT-physics-inclusive, Shaw-only, hop+rtt)      : {r2_combined:.2f}%")

    print(f"\n{'ISP':14s} {'n':>7s} {'type1 hop%':>11s} {'type2 hop%':>11s} {'type2 hop+rtt%':>15s}")
    byisp = defaultdict(list)
    for r in pk_rows:
        isp = isp_of(int(r["probe_id"]), probes.get(r["probe_id"], "?"))
        byisp[isp].append(r)
    for isp, rs in sorted(byisp.items(), key=lambda x: -len(x[1])):
        t = len(rs)
        c2 = Counter(r["type2"] for r in rs)
        r1v = 100 * sum(1 for r in rs if r["type1"] == "trombone_hop") / t
        r2h = 100 * c2["trombone_hop"] / t
        r2c = 100 * (c2["trombone_hop"] + c2["trombone_rtt"]) / t
        print(f"{isp:14s} {t:7d} {r1v:10.2f}% {r2h:10.2f}% {r2c:14.2f}%")

    print(f"\n{'sector':32s} {'n':>7s} {'type1 hop%':>11s} {'type2 hop%':>11s} {'type2 hop+rtt%':>15s}")
    bysec = defaultdict(list)
    for r in pk_rows:
        bysec[r["sector"]].append(r)
    for sec, rs in sorted(bysec.items(), key=lambda x: -sum(1 for r in x[1] if r["type1"] == "trombone_hop")):
        t = len(rs)
        c2 = Counter(r["type2"] for r in rs)
        r1v = 100 * sum(1 for r in rs if r["type1"] == "trombone_hop") / t
        r2h = 100 * c2["trombone_hop"] / t
        r2c = 100 * (c2["trombone_hop"] + c2["trombone_rtt"]) / t
        print(f"{sec:32s} {t:7d} {r1v:10.2f}% {r2h:10.2f}% {r2c:14.2f}%")


if __name__ == "__main__":
    main()
