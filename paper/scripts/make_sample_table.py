#!/usr/bin/env python3
"""
Emit the merged sample table for running_draft.tex: candidate pool and sampled
sites by CISA sector, plus the hosting concentration behind them. Replaces the
two separate tables tab:hosting-providers and tab:cisa-sectors.

Computed from source, not transcribed:
  experiments/07_longitudinal_panel/targets.csv        the 100 sampled sites
  site_collection/pipeline/outputs/site_candidates_cisa.csv   the 1,814-site pool

toptop.net and youth.cn are dropped, matching Data Cleaning, which leaves the
98-site sample and 38 Pakistani-class sites (not 40).

    python paper/make_sample_table.py            # print LaTeX
    python paper/make_sample_table.py --write    # also write figures/tab_sample.tex
"""
import collections
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = os.path.join(ROOT, "experiments", "07_longitudinal_panel", "targets.csv")
POOL = os.path.join(ROOT, "site_collection", "pipeline", "outputs", "site_candidates_cisa.csv")
OUT = os.path.join(ROOT, "paper", "tab_sample.tex")

DROPPED = {"toptop.net", "youth.cn"}

SHORT = {
    "Government Services & Facilities": r"Govt.\ Services \& Facilities",
    "Healthcare & Public Health": r"Healthcare \& Public Health",
}

# provider strings in targets.csv that are the same operator
ALIAS = {
    "Pakistan Telecommuication company limited": "PTCL",
    "PTCL Triple Play Project": "PTCL",
    "NAYATEL-PK - Nayatel (Pvt) Ltd, PK": "Nayatel",
    "Nayatel (Pvt) Ltd": "Nayatel",
    "AWS CloudFront": "AWS",
    "Microsoft/Azure": "Azure",
    "Cyber Internet Services (Private) Limited": "Cybernet",
    "Punjab Information Technology Board": "PITB",
    "Hetzner Online GmbH (FI)": "Hetzner (FI)",
    "Hetzner Online GmbH (DE)": "Hetzner (DE)",
}


def load():
    rows = [r for r in csv.DictReader(open(TARGETS, encoding="utf-8"))
            if r["target"] not in DROPPED]
    pool_rows = csv.DictReader(
        (l for l in open(POOL, encoding="utf-8") if not l.startswith("#")))
    pool = collections.Counter(r["cisa_sector"] for r in pool_rows)
    return rows, pool


def provider_line(rows, cls):
    c = collections.Counter(ALIAS.get(r["isp_cdn"], r["isp_cdn"])
                            for r in rows if r["class"] == cls)
    n_sites, n_hosts = sum(c.values()), len(c)
    top = c.most_common()
    if cls == "CDN":
        # group the equal-sized tail so the row fits one column
        big = [(k, v) for k, v in top if v >= 3]
        tail = [(k, v) for k, v in top if v < 3]
        by_n = collections.defaultdict(list)
        for k, v in tail:
            by_n[v].append(k)
        parts = [f"{k} {v}" for k, v in big]
        for v in sorted(by_n, reverse=True):
            parts.append("/".join(sorted(by_n[v])) + f" {v}")
        detail = ", ".join(parts)
    else:
        head = [(k, v) for k, v in top if v >= 3]
        named = ", ".join(f"{k} {v}" for k, v in head)
        rest = n_hosts - len(head)
        detail = f"{named}, {rest} others at 1--2 sites"
    return n_sites, n_hosts, detail


def build():
    rows, pool = load()
    sect = collections.defaultdict(collections.Counter)
    for r in rows:
        sect[r["cisa_sector"]][r["class"]] += 1
    order = sorted(pool, key=lambda s: -pool[s])

    L = []
    L.append(r"\begin{table}[t]")
    L.append(r"\small")
    L.append(r"\caption{The 98-site sample: candidate pool and sampled sites by CISA "
             r"sector, and the hosting providers behind them.}")
    L.append(r"\label{tab:sample}")
    L.append(r"\begin{tabular}{@{}lrrrrr@{}}")
    L.append(r"\toprule")
    L.append(r"\textbf{CISA Sector} & \textbf{Pool} & \textbf{Sampled} & "
             r"\textbf{PK} & \textbf{CDN} & \textbf{Abroad} \\")
    L.append(r"\midrule")

    tot = collections.Counter()
    for s in order:
        c = sect[s]
        n = sum(c.values())
        tot["pool"] += pool[s]; tot["n"] += n
        for k in ("Pakistan", "CDN", "Abroad"):
            tot[k] += c[k]
        name = SHORT.get(s, s)
        p = f"{pool[s]:,}".replace(",", "{,}")
        L.append(f"{name:<30}& {p:>7} & {n:>2} & {c['Pakistan']:>2} & "
                 f"{c['CDN']:>2} & {c['Abroad']:>2} \\\\")

    L.append(r"\midrule")
    p = f"{tot['pool']:,}".replace(",", "{,}")
    L.append(r"\textbf{Total} & \textbf{" + p + r"} & \textbf{" + str(tot["n"])
             + r"} & \textbf{" + str(tot["Pakistan"]) + r"} & \textbf{"
             + str(tot["CDN"]) + r"} & \textbf{" + str(tot["Abroad"]) + r"} \\")

    L.append(r"\midrule")
    L.append(r"\multicolumn{6}{@{}l}{\emph{Hosting providers behind the sampled sites}} \\")
    for cls, label in (("Pakistan", "Pakistani"), ("CDN", "CDN"), ("Abroad", "Abroad")):
        n_sites, n_hosts, detail = provider_line(rows, cls)
        L.append(f"{label} ({n_sites}) & "
                 f"\\multicolumn{{5}}{{@{{}}p{{0.60\\columnwidth}}@{{}}}}"
                 f"{{{n_hosts} hosts: {detail}}} \\\\")

    L.append(r"\bottomrule")
    L.append(r"\end{tabular}")
    L.append(r"\end{table}")
    return "\n".join(L)


if __name__ == "__main__":
    tex = build()
    print(tex)
    if "--write" in sys.argv:
        open(OUT, "w", encoding="utf-8").write(tex + "\n")
        print(f"\n% wrote {os.path.relpath(OUT, ROOT)}", file=sys.stderr)
