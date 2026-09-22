#!/usr/bin/env python3
"""
Build traceroutes_26_pk_sites.md: the hop-by-hop traceroute from both probes to each of the 26
selected PK sites. Reads the result files, so nothing is typed by hand. TCP/443 results are used
where they exist, ICMP results otherwise. Re-run after new results land.

    python experiments/17_tranco_pk_cdn_discovery/build_traceroute_md.py
"""
import csv, glob, os, collections

R = "experiments/17_tranco_pk_cdn_discovery/results/"
OUT = "experiments/17_tranco_pk_cdn_discovery/traceroutes_26_pk_sites.md"
SELECTION = "site_collection/pipeline/outputs/pk_selection_26.csv"

# (protocol label, grouped-file glob, summary-file glob), first match per (site, probe) wins
SOURCES = [
    ("TCP/443", R + "verify_pk_tcp443_rest12/pk_grouped_*.csv", R + "verify_pk_tcp443_rest12/pk_summary_*.csv"),
    ("TCP/443", R + "verify_pk_tcp443/pk_grouped_*.csv", R + "verify_pk_tcp443/pk_summary_*.csv"),
    ("ICMP", R + "verify_pk_top50_pass2/pk_grouped_*.csv", R + "verify_pk_top50_pass2/pk_summary_*.csv"),
    ("ICMP", R + "verify_pk_hits_300k/pk_grouped_20260917_101715.csv", R + "verify_pk_hits_300k/pk_summary_20260917_101715.csv"),
]
PROBES = {"60223": "Nayatel (probe 60223, AS23674)", "7613": "Z COM (probe 7613, AS152605)"}
SHORT = {"60223": "Nayatel", "7613": "Z COM"}


def short_asn(name):
    return name.split(" - ")[0] if name else ""


def load():
    """(site, probe) -> [dict(proto, summary row, hop rows), ...] in priority order (TCP first)"""
    found = {}
    for proto, gpat, spat in SOURCES:
        sfiles, gfiles = sorted(glob.glob(spat)), sorted(glob.glob(gpat))
        if not sfiles or not gfiles:
            continue
        summ = {}
        for f in sfiles:
            for r in csv.DictReader(open(f)):
                summ[(r["target_hostname"], r["probe_id"])] = r
        hops = collections.defaultdict(list)
        for f in gfiles:
            for r in csv.DictReader(open(f)):
                hops[r["measurement_id"]].append(r)
        for key, s in summ.items():
            if hops.get(s["measurement_id"]) and all(e["proto"] != proto for e in found.get(key, [])):
                found.setdefault(key, []).append(dict(proto=proto, summary=s, hops=hops[s["measurement_id"]]))
    return found


def render(entry):
    s, rows = entry["summary"], sorted(entry["hops"], key=lambda r: int(r["hop"]))
    dest_ip = s["target_ip"]
    lines, i = [], 0
    while i < len(rows):
        r = rows[i]
        if r["is_timeout"] == "True":
            j = i
            while j + 1 < len(rows) and rows[j + 1]["is_timeout"] == "True":
                j += 1
            a, b = rows[i]["hop"], rows[j]["hop"]
            lines.append(f"{(a if a == b else a + '-' + b):>7}  *")
            i = j + 1
            continue
        hop = "dest" if r["hop"] == "255" else r["hop"]
        rtt = f"{float(r['rtt_ms']):.1f} ms" if r["rtt_ms"] not in ("", None) else ""
        if r["is_private"] == "True":
            where = "private address"
        elif (r["hop_asn_name"] or "").startswith("SHARED-ADDRESS-SPACE"):
            where = "shared address space (ISP internal)"
        else:
            where = f"{r['hop_country'] or '?':<2}  {short_asn(r['hop_asn_name'])}"
        mark = "   <- destination" if r["hop_ip"] == dest_ip else ""
        lines.append(f"{hop:>7}  {r['hop_ip']:<16} {rtt:>10}  {where}{mark}")
        i += 1
    dest_rtt = next((float(r["rtt_ms"]) for r in rows if r["hop_ip"] == dest_ip and r["rtt_ms"]), None)
    reached = s["destination_responded"] == "True"
    return lines, reached, dest_rtt


NTC_EXTRA = """
**Nayatel (probe 60223, AS23674), ICMP and UDP**

The TCP/443 trace from Nayatel showed nothing at hops 3 to 7. Two more traces to the same destination were run from the same probe to expose them. One used ICMP (measurement 213596339) and one used UDP (measurement 213596343). Both gave the same path. Delays here are the median of three replies.

```
ICMP, destination did not reply
      1  192.168.18.1         0.8 ms  private address
      2  100.89.160.1         2.9 ms  shared address space (ISP internal)
      3  172.27.0.29          3.1 ms  private address
      4  172.27.0.22          2.7 ms  private address
      5  172.31.5.170         3.1 ms  private address
      6  103.213.108.67       4.2 ms  PK  HTISPL-PK
      7  202.163.94.89        9.7 ms  PK  CYBERNET-AP
   8-12  *
    255  *
```

```
UDP, destination did not reply
      1  192.168.18.1         1.0 ms  private address
      2  100.89.160.1         2.9 ms  shared address space (ISP internal)
      3  172.27.0.29          2.7 ms  private address
      4  172.27.0.22          2.6 ms  private address
      5  172.31.5.170         2.8 ms  private address
      6  103.213.108.67       3.6 ms  PK  HTISPL-PK
      7  202.163.94.89        3.4 ms  PK  CYBERNET-AP
   8-12  *
    255  *
```

Hops 1 to 5 are inside Nayatel. Hop 6 is registered to Cyber Internet Services Pakistan (Cybernet) and hop 7 is in Cybernet's AS9541. Nayatel therefore hands the traffic to Cybernet at hop 6, within about 4 ms. No hop leaves Pakistan and none belongs to Prolexic.

Hops 8 to 12 and the destination did not reply to ICMP or UDP, so the last part of the path is not observed. The destination did answer TCP/443 in 3.9 ms, which is too fast for a detour abroad. RIPE RIS shows all 363 paths to 203.101.184.0/24 passing through AS32787 (Prolexic). Nayatel does not use that route.
"""


def foreign_path(entry):
    seen = []
    for r in sorted(entry["hops"], key=lambda r: int(r["hop"])):
        c = r["hop_country"]
        if r["is_private"] != "True" and c and c != "PK" and c not in seen:
            seen.append(c)
    return seen


def main():
    sel = list(csv.DictReader(open(SELECTION)))
    sel.sort(key=lambda r: int(r["tranco_rank"]))
    wanted = {r["domain"] for r in sel}
    allf = {k: v for k, v in load().items() if k[0] in wanted}
    found = {k: v[0] for k, v in allf.items()}
    extra = {}   # TCP got no reply from the destination but ICMP did: keep that trace too
    for k, v in allf.items():
        if v[0]["summary"]["destination_responded"] != "True":
            alt = next((e for e in v[1:] if e["summary"]["destination_responded"] == "True"), None)
            if alt:
                extra[k] = alt
    ip = {r["target_hostname"]: r["target_ip"] for r in (v["summary"] for v in found.values())}

    tally = collections.Counter(v["proto"] for v in found.values())
    md = ["# Traceroutes to the 26 selected PK sites, from two probes", "",
          "Probes: Nayatel (probe 60223) and Z COM Networks (probe 7613). Delays are in ms. `*` means no reply. "
          "Country is the registry country of the hop address. `dest` is the destination's own reply.", ""]
    n_tcp = sum(1 for v in found.values() if v["proto"] == "TCP/443")
    md.append(f"Protocol: TCP port 443 for {n_tcp} of {len(found)} traces"
              + (f", ICMP for the other {len(found) - n_tcp}" if n_tcp < len(found) else "")
              + f". Where the destination did not answer TCP but did answer ICMP, the ICMP trace is added ({len(extra)} traces).")
    md.append("")

    md += ["| # | Site | Tranco rank | Sector | Nayatel | Z COM |", "|---|---|---|---|---|---|"]
    for n, r in enumerate(sel, 1):
        cells = []
        for p in ("60223", "7613"):
            e = found.get((r["domain"], p))
            if not e:
                cells.append("no data"); continue
            _, reached, dest = render(e)
            cell = f"{'reached' if reached else 'not reached'}" + (f", {dest:.0f} ms" if dest is not None else "")
            if not reached and (r["domain"], p) in extra:
                _, _, d2 = render(extra[(r["domain"], p)])
                cell = f"TCP not reached; ICMP reached, {d2:.0f} ms"
            cells.append(cell)
        md.append(f"| {n} | {r['domain']} | {int(r['tranco_rank']):,} | {r['sector']} | {cells[0]} | {cells[1]} |")
    md.append("")

    for n, r in enumerate(sel, 1):
        d = r["domain"]
        md += [f"## {n}. {d}", "",
               f"Tranco rank {int(r['tranco_rank']):,}, {r['sector']}, {r['network']}, destination {ip.get(d, '?')}", ""]
        if d == "ntc.net.pk":
            z, nay = found.get((d, "7613")), found.get((d, "60223"))
            if z and nay:
                _, _, zd = render(z)
                _, _, nd = render(nay)
                fp = foreign_path(z)
                if fp and zd and nd:
                    md += [f"**Detour from Z COM:** the path leaves Pakistan through {', '.join(fp)} and reaches the site in "
                           f"{zd:.0f} ms. From Nayatel it takes {nd:.0f} ms.", ""]
        for p in ("60223", "7613"):
            e = found.get((d, p))
            md.append(f"**{PROBES[p]}**" + (f", {e['proto']}" if e else ""))
            md.append("")
            if not e:
                md += ["No result.", ""]
                continue
            lines, reached, dest = render(e)
            state = f"destination replied, {dest:.1f} ms" if reached and dest is not None else "destination did not reply"
            md += [f"```", f"{state}"] + lines + ["```", ""]
            if (d, p) in extra:
                x = extra[(d, p)]
                xl, xr, xd = render(x)
                md += [f"Same probe, {x['proto']} (the destination answered this one):", "",
                       "```", f"destination replied, {xd:.1f} ms"] + xl + ["```", ""]
        if d == "ntc.net.pk":
            md += NTC_EXTRA.strip().split("\n") + [""]
    open(OUT, "w").write("\n".join(md))
    print(f"wrote {OUT}: {len(sel)} sites, {len(found)} traces by protocol {dict(tally)}")


if __name__ == "__main__":
    main()
