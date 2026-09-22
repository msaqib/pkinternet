#!/usr/bin/env python3
"""
First-pass CISA sector tagging for the global CDN pool (cdn_hits.csv).
Unlike the original 98-site panel, this pool wasn't built from
PK-sector-curated sources, so sectors aren't known going in. This is
a cheap TLD + keyword classifier to find candidates worth a manual
look, not a final categorization, anything landing outside
"Commercial Facilities" should be eyeballed before trusting it.

Run from site_collection/pipeline/:
    python3 classify_cisa_sector.py
"""
import csv
import re
from collections import Counter, defaultdict

IN_FILE = "outputs/cdn_hits.csv"
OUT_FILE = "outputs/cdn_hits_cisa.csv"

TLD_SECTOR = {
    ".gov": "Government Services & Facilities",
    ".mil": "Government Services & Facilities",
    ".edu": "Education",
}

# (sector, [keywords]) checked against the registrable domain name.
# Order matters: first match wins, most specific sectors first so a
# generic word doesn't steal a hit that belongs to a narrower sector.
#
# Most keywords are word stems (e.g. "insur" for insurance/insurer) and
# are matched as a substring on purpose. A handful of short, complete
# English words below (SHORT_WORDS) turned out to false-positive when
# embedded in an unrelated fused compound — "gas" inside "gastromedix",
# "mobile" inside "automobile", "network" inside "basketballnetwork" —
# those are matched as whole words only. A hyphen/dot-delimited token
# that's genuinely just the wrong word (e.g. "irs-gov-ein-number.com")
# still gets through either way; that residual needs a manual look, no
# regex fixes a domain that's lying about what it is.
SHORT_WORDS = {
    "gas", "bank", "pay", "gov", "mobile", "network", "care", "loan",
    "isp", "oil", "rail",
}

KEYWORD_SECTORS = [
    ("Healthcare & Public Health", [
        "health", "hospital", "clinic", "medic", "pharma", "dental", "care",
    ]),
    ("Financial Services", [
        "bank", "credit", "invest", "insur", "capital", "finance", "pay",
        "wealth", "loan", "trading",
    ]),
    ("Energy", [
        "energy", "power", "electric", "utility", "solar", "gas", "petrol",
        "oil",
    ]),
    ("Transportation Systems", [
        "airline", "airport", "rail", "transit", "transport", "shipping",
        "cargo", "logistics", "freight",
    ]),
    ("Communications", [
        "telecom", "wireless", "broadband", "mobile", "isp", "voip",
        "network",
    ]),
    ("Government Services & Facilities", [
        "gov", "municipal", "ministry", "government",
    ]),
    ("Education", [
        "university", "college", "school", "academy", "edu",
    ]),
]


def _pattern_for(keywords):
    parts = [
        rf"\b{kw}\b" if kw in SHORT_WORDS else re.escape(kw)
        for kw in keywords
    ]
    return re.compile("|".join(parts))


SECTOR_PATTERNS = [(sector, _pattern_for(keywords)) for sector, keywords in KEYWORD_SECTORS]


def classify(domain):
    low = domain.lower()
    parts = low.split(".")
    for suffix, sector in TLD_SECTOR.items():
        if low.endswith(suffix) or f"{suffix}." in low:
            return sector
    # word-boundary match only — a fused compound like "gastromedix" or
    # "automobile" must not trip "gas" or "mobile"; a hyphen/dot-delimited
    # token still can (e.g. "irs-gov-ein-number"), those residual false
    # positives need a manual look, not a smarter regex.
    name = re.sub(r"[^a-z0-9]+", "-", parts[0])
    for sector, pattern in SECTOR_PATTERNS:
        if pattern.search(name):
            return sector
    return "Commercial Facilities"


def main():
    rows = list(csv.DictReader(open(IN_FILE)))
    for r in rows:
        r["cisa_sector"] = classify(r["domain"])

    with open(OUT_FILE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["domain", "ip", "asn", "as_name", "cisa_sector"])
        w.writeheader()
        w.writerows(rows)

    counts = Counter(r["cisa_sector"] for r in rows)
    print(f"{len(rows)} CDN domains classified -> {OUT_FILE}\n")
    print(f"{'sector':<32} count")
    print("-" * 45)
    for sector, n in counts.most_common():
        print(f"{sector:<32} {n}")


if __name__ == "__main__":
    main()
