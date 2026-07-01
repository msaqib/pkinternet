#!/usr/bin/env python3
"""
Exp 1.4 — combine the hosting results of Exp 01 (commercial/news/etc.) and Exp 1.4
(gov/edu/utility) into one census. Each site -> category (CDN / Pakistan / Abroad),
hosting ISP/operator, and where it is hosted.

    python experiments/01.4_pk100_hosting/combine_with_exp01.py
Output: results/combined_hosting.csv
"""
import os, csv, glob, re, collections

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..", "..")
E01 = os.path.join(ROOT, "experiments", "01_website_destinations", "results")
OUT = os.path.join(HERE, "results")

CDN_ASN = {"13335": "Cloudflare", "209242": "Cloudflare", "20940": "Akamai",
           "16625": "Akamai", "32787": "Akamai/Prolexic", "16509": "AWS", "14618": "AWS",
           "15169": "Google", "396982": "Google", "54113": "Fastly",
           "19551": "Imperva/Incapsula", "30148": "Sucuri", "8075": "Microsoft/Azure",
           "13238": "Yandex"}
CDN_WORDS = ("cloudflare", "akamai", "fastly", "amazon", "aws", "google", "microsoft",
             "azure", "incapsula", "imperva", "sucuri", "cdn", "prolexic", "cloudfront")


def isp_short(name):
    return re.split(r" - | -|,", name or "")[0].strip() or "?"


def classify(asn, name, cc, location):
    """-> (category, host, where)."""
    blob = f"{name} {location}".lower()
    if asn in CDN_ASN or any(w in blob for w in CDN_WORDS):
        cdn = CDN_ASN.get(asn) or next((w.title() for w in CDN_WORDS if w in blob), "CDN")
        return "CDN", cdn, (location or "")
    if cc == "PK" or re.search(r"\bPK\b|Pakistan", location or ""):
        return "Pakistan", isp_short(name), (location or "PK")
    return "Abroad", isp_short(name), (location or cc)


rows = {}   # hostname -> row

# --- Exp 01 (5-probe traceroutes; dest_location = serving city via serving_location) ---
e01 = {}
for f in glob.glob(os.path.join(E01, "*", "pk_summary_*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8")):
        if r.get("target_hostname"):
            e01[r["target_hostname"]] = r
for h, r in e01.items():
    cat, host, where = classify(r.get("target_asn", ""), r.get("target_asn_name", ""),
                                r.get("target_country", ""), r.get("dest_location", ""))
    rows[h] = dict(hostname=h, exp="01", exp_category=r.get("target_category", ""),
                   category=cat, host=host, where=where, asn=("AS" + r["target_asn"]) if r.get("target_asn") else "")

# --- Exp 1.4 Pass A ---
for r in csv.DictReader(open(os.path.join(OUT, "pass_a_hosting.csv"), encoding="utf-8")):
    h = r["domain"]
    where = r["geo_city"] + (", " + r["geo_country"] if r["geo_country"] else "") if r["category"] != "CDN" else r["host"]
    entry = dict(hostname=h, exp="1.4", exp_category="gov/edu/utility",
                 category=r["category"], host=isp_short(r["asn_name"]) if r["category"] != "CDN" else r["host"],
                 where=where or "PK", asn=r["asn"])
    if h in rows:
        rows[h]["exp"] = "01+1.4"          # in both lists
    else:
        rows[h] = entry

allrows = sorted(rows.values(), key=lambda x: (x["exp"], x["category"], x["hostname"]))
cols = ["hostname", "exp", "exp_category", "category", "host", "where", "asn"]
with open(os.path.join(OUT, "combined_hosting.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(allrows)

# ---- summaries ----
def split(subset):
    c = collections.Counter(r["category"] for r in subset)
    n = len(subset)
    return {k: (c.get(k, 0), round(100 * c.get(k, 0) / n) if n else 0) for k in ("CDN", "Pakistan", "Abroad")}, n

e01rows = [r for r in allrows if "01" in r["exp"]]
e14rows = [r for r in allrows if "1.4" in r["exp"]]
print(f"combined unique sites: {len(allrows)}  (Exp01 {len(e01rows)}, Exp1.4 {len(e14rows)}, overlap {sum(1 for r in allrows if r['exp']=='01+1.4')})")
for label, sub in [("COMBINED", allrows), ("Exp 01 (commercial/news/…)", e01rows), ("Exp 1.4 (gov/edu/utility)", e14rows)]:
    sp, n = split(sub)
    print(f"\n{label}  (n={n})")
    for k, (cnt, pct) in sp.items(): print(f"   {k:9} {cnt:3} ({pct}%)")
print(f"\nwrote {os.path.join(OUT,'combined_hosting.csv')}")
