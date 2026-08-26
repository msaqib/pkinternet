#!/usr/bin/env python3
"""
Step 2 of the evidence-based reclassification (see evidence_reclassification_plan.md).

Reads evidence_scan.csv (fresh ASN registration + traceroute hop evidence + geo-IP
for all 60 unicast sites) and targets_corrected.csv (the current, v1, RTT-threshold
classification), applies the evidence-based decision rules, and writes
targets_corrected_v2.csv with an explicit evidence tier and an Inconclusive bucket
where warranted. Prints a full diff against v1 -- every site, not just the 3 already
under discussion, so nothing is silently missed.
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EV = pd.read_csv(os.path.join(HERE, "evidence_scan.csv"))
TC = pd.read_csv(os.path.join(HERE, "targets_corrected.csv"))

df = EV.merge(TC[["target", "lat", "lon", "loc_source", "note"]], on="target", how="left")


def decide(row):
    """Returns (cls_v2, tier, rationale)."""
    design = row.cls_design
    asn_cc = row.fresh_asn_country if isinstance(row.fresh_asn_country, str) else ""
    geo_cc = row.geoip_cc if isinstance(row.geoip_cc, str) else ""
    n_hop = row.n_foreign_hop_confirmed
    ping = row.ping_rtt_min

    asn_resolved = asn_cc not in ("", "nan")
    asn_says_pk = asn_cc == "PK"
    asn_says_foreign = asn_resolved and not asn_says_pk
    geo_says_foreign = geo_cc not in ("", "PK", "nan")
    has_hop_evidence = n_hop > 0

    if design == "Pakistan":
        if not asn_resolved:
            # ASN lookup failed to answer -- no new evidence either way, defer to v1
            return row.cls_corrected_v1, "asn-unresolved", "fresh ASN lookup gave no answer; kept v1 label"
        if asn_says_pk:
            return "Pakistan", "confirmed-domestic", "fresh ASN registration is PK"
        # asn_says_foreign
        if has_hop_evidence or geo_says_foreign:
            tier = "asn+hop+geoip" if (has_hop_evidence and geo_says_foreign) else (
                   "asn+hop" if has_hop_evidence else "asn+geoip")
            note = f"ASN={asn_cc}, {n_hop} confirmed foreign-hop rounds, geoIP city={row.geoip_city or '?'}"
            return "Abroad", tier, note
        # ASN says foreign but nothing else corroborates it (no hop, no foreign geoIP city)
        return "Inconclusive", "asn-only-weak", f"ASN={asn_cc} but no hop or geoIP corroboration (ping_min={ping}ms)"

    else:  # design == "Abroad"
        if asn_says_pk:
            # candidate for relocation -- needs non-RTT corroboration (WHOIS-style), which
            # this automated pass cannot fetch; flag for manual review rather than silently
            # relocate on ASN alone (mirrors the "don't trust proximity alone" caution).
            return "Inconclusive", "abroad-flagged-pk-asn", "fresh ASN says PK; needs manual WHOIS check before relocating"
        return "Abroad", "confirmed-foreign", f"fresh ASN registration is {asn_cc or 'foreign/unresolved'}"


results = df.apply(lambda r: pd.Series(decide(r), index=["cls_v2", "evidence_tier", "v2_note"]), axis=1)
out = pd.concat([df, results], axis=1)
out.to_csv(os.path.join(HERE, "targets_corrected_v2.csv"), index=False)

print(f"wrote targets_corrected_v2.csv ({len(out)} rows)")
print()
print("=== v2 class counts ===")
print(out.cls_v2.value_counts())
print()
print("=== full diff: cls_corrected_v1 vs cls_v2 ===")
diff = out[out.cls_corrected_v1 != out.cls_v2]
if diff.empty:
    print("(no differences -- every site's v1 label survives the stricter evidence bar)")
else:
    print(diff[["target", "cls_design", "cls_corrected_v1", "cls_v2", "evidence_tier", "v2_note"]].to_string(index=False))
print()
print("=== evidence tier breakdown (all 60 sites) ===")
print(out.evidence_tier.value_counts())
print()
print("=== sites carrying a caveat worth stating in the paper (thin evidence) ===")
print(out[out.evidence_tier.isin(["asn-only-weak", "asn-unresolved", "abroad-flagged-pk-asn"])]
      [["target", "cls_design", "cls_v2", "evidence_tier", "v2_note"]].to_string(index=False))
print()
print("=== phf.gop.pk specifically (known thin hop-level evidence) ===")
print(out[out.target == "phf.gop.pk"][["target", "cls_v2", "evidence_tier", "n_foreign_hop_confirmed", "geoip_city", "geoip_cc"]].to_string(index=False))
