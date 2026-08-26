#!/usr/bin/env python3
"""
Evidence scan for the location-verification rework (see evidence_reclassification_plan.md).

For every unicast site (Pakistani- or Abroad-labelled, 60 total) collects, side by
side:
  - a FRESH Team Cymru ASN/country lookup on the site's current resolved IP
    (independent of the build-time classification; catches drift/staleness),
  - geo-IP city (from the existing cache, ip-api.com),
  - traceroute hop evidence aggregated across the full panel: how many rounds show
    a confirmed foreign hop (exit_cc a real country) vs RTT-only (exit_cc == "?")
    vs no trombone signal at all (exit_cc blank/local),
  - ping RTT summary (min, median) for reference.

Writes evidence_scan.csv. Read-only against the panel data; does not touch
targets_corrected.csv or any other canonical file.
"""
import os, sys, json, socket, csv
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
RESULTS = os.path.join(EXP, "results")

TARGETS_CORRECTED = os.path.join(HERE, "targets_corrected.csv")
IP_CACHE = os.path.join(HERE, ".cache_ip_geo.json")
TRACE_CSV = os.path.join(RESULTS, "a", "panel_20260718_195946.csv")
PING_CSV = os.path.join(RESULTS, "b", "panel_20260718_200355.csv")
OUT = os.path.join(HERE, "evidence_scan.csv")


def bulk_cymru_lookup(ip_list):
    query = "begin\nverbose\n" + "\n".join(ip_list) + "\nend\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect(("whois.cymru.com", 43))
    sock.sendall(query.encode())
    response = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    sock.close()
    return response.decode(errors="replace")


def parse_cymru(raw):
    out = {}
    for line in raw.strip().split("\n")[1:]:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 7:
            asn, ip, prefix, cc, registry, allocated, as_name = parts[:7]
            out[ip] = {"asn": asn, "country": cc, "as_name": as_name}
    return out


def main():
    tc = pd.read_csv(TARGETS_CORRECTED)
    uni = tc[tc.cls_design.isin(["Pakistan", "Abroad"])].copy()
    print(f"unicast sites: {len(uni)}")

    print("running fresh Team Cymru lookup on current resolved IPs...")
    cymru = parse_cymru(bulk_cymru_lookup(list(uni.ip)))
    print(f"  got {len(cymru)}/{len(uni)} answers")

    geo_cache = json.load(open(IP_CACHE, encoding="utf-8"))

    trace = pd.read_csv(TRACE_CSV)
    ping = pd.read_csv(PING_CSV)

    rows = []
    for _, r in uni.iterrows():
        t, ip, design, corrected = r.target, r.ip, r.cls_design, r.cls_corrected
        cy = cymru.get(ip, {})
        geo = geo_cache.get(ip, {})

        tsub = trace[trace.target == t]
        n_total_trace = len(tsub)
        n_foreign_hop = int(((tsub.exit_cc.notna()) & (tsub.exit_cc != "?")).sum())
        n_rtt_only = int((tsub.exit_cc == "?").sum())
        n_local = n_total_trace - n_foreign_hop - n_rtt_only
        foreign_countries_seen = sorted(
            tsub.loc[(tsub.exit_cc.notna()) & (tsub.exit_cc != "?"), "exit_cc"].unique().tolist()
        )

        psub = ping[ping.target == t]
        rtt_min = psub.rtt_min.min() if len(psub) else None
        rtt_median = psub.rtt_min.median() if len(psub) else None

        rows.append(dict(
            target=t, cls_design=design, cls_corrected_v1=corrected, ip=ip,
            fresh_asn=cy.get("asn", ""), fresh_asn_country=cy.get("country", ""),
            fresh_as_name=cy.get("as_name", ""),
            geoip_city=geo.get("city", ""), geoip_cc=geo.get("cc", ""),
            n_trace_rounds=n_total_trace, n_foreign_hop_confirmed=n_foreign_hop,
            n_rtt_only_no_hop=n_rtt_only, n_local_no_signal=n_local,
            foreign_countries_seen=";".join(foreign_countries_seen),
            ping_rtt_min=round(rtt_min, 1) if rtt_min == rtt_min and rtt_min is not None else "",
            ping_rtt_median=round(rtt_median, 1) if rtt_median == rtt_median and rtt_median is not None else "",
        ))

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(out)} rows)")

    # quick sanity summary
    print()
    print("design=Pakistan, fresh ASN country != PK (candidate: reclassify/flag):")
    print(out[(out.cls_design == "Pakistan") & (out.fresh_asn_country != "PK") & (out.fresh_asn_country != "")]
          [["target", "fresh_asn_country", "fresh_as_name", "n_foreign_hop_confirmed", "n_rtt_only_no_hop", "ping_rtt_min"]]
          .to_string(index=False))
    print()
    print("design=Abroad, fresh ASN country == PK (candidate: relocate/flag):")
    print(out[(out.cls_design == "Abroad") & (out.fresh_asn_country == "PK")]
          [["target", "fresh_asn_country", "fresh_as_name", "n_foreign_hop_confirmed", "n_rtt_only_no_hop", "ping_rtt_min"]]
          .to_string(index=False))


if __name__ == "__main__":
    main()
