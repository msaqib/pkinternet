
## What this is

Financial-institution sites that look "abroad" or "CDN" from
the outside (Cloudflare, AWS CloudFront, Sucuri, etc.) may still run a real
local Pakistani server behind the CDN. That server terminates TLS with the
bank's own certificate before Cloudflare, but usually has no public DNS
record, so a normal hosting check never sees it.

Censys crawls all of IPv4 on port 443 and records every certificate it
finds, common name (CN) included. Searching Censys for
`host.services.cert.parsed.subject.common_name: "bankdomain.com"` surfaces
every host presenting that cert, origin server included, wherever it's
sitting. Searching for the literal wildcard form
(`"*.bankdomain.com"`) specifically targets hosts serving the bank's shared
wildcard cert, which tends to be the bank's central/production server pool
rather than a one-off test or DR box (see reasoning in-chat, not yet copied
into a findings doc).

## Manual discovery so far (before the script existed)

- **meezanbank.com**: Censys CN search turned up `gpt.meezanbank.com`,
  `lservices.meezanbank.com`, and others. `lservices.meezanbank.com` has no
  public DNS record but answers pings, the fingerprint of a hidden origin.
  IP not yet logged here, pull it from the original Censys session.
- **hbl.com**: multiple CN matches, ambiguous which is primary vs DR.
  Cross-check candidates against `103.111.84.5`, already confirmed as HBL's
  real domestically-reachable IP via a completely different method (BGP +
  RIPE Atlas traceroute, see
  `experiments/13_efulife_live_snapshot/OTHER_COMPANIES_RESULTS.md`). If a
  Censys candidate matches that IP, that's two independent methods agreeing.

## Target list

`data/financial_institutions_targets.csv`, seeded from:
- the 4 Financial Services rows already in `data/pk_100_final_v2.csv`
  (2 already Pakistani-hosted, 2 currently classified CDN and unverified)
- the Banking & Finance section of `data/PK100sites.md`
- the 2 manually-found domains above (meezanbank.com, hbl.com)

The broader scheduled-banks list in `data/List_of_Scheduled_Banks-new.pdf`
was pulled in as a second batch, see below.

## Manual UI queries

Run these at platform.censys.io (Search), one domain at a time. Skips
`ztbl.com.pk` and `efulife.com`, both already resolved by other methods per
the target CSV. For each domain, run both queries and note any hit whose IP
isn't already known to be the CDN edge:

| domain | exact/subdomain query | wildcard query |
|---|---|---|
| khushhalibank.com.pk | `host.services.cert.parsed.subject.common_name: "khushhalibank.com.pk"` | `host.services.cert.parsed.subject.common_name: "*.khushhalibank.com.pk"` |
| mcb.com.pk | `host.services.cert.parsed.subject.common_name: "mcb.com.pk"` | `host.services.cert.parsed.subject.common_name: "*.mcb.com.pk"` |
| adamjeeinsurance.com | `host.services.cert.parsed.subject.common_name: "adamjeeinsurance.com"` | `host.services.cert.parsed.subject.common_name: "*.adamjeeinsurance.com"` |
| alfalahamc.com | `host.services.cert.parsed.subject.common_name: "alfalahamc.com"` | `host.services.cert.parsed.subject.common_name: "*.alfalahamc.com"` |
| silkbank.com.pk | `host.services.cert.parsed.subject.common_name: "silkbank.com.pk"` | `host.services.cert.parsed.subject.common_name: "*.silkbank.com.pk"` |
| ubank.com.pk | `host.services.cert.parsed.subject.common_name: "ubank.com.pk"` | `host.services.cert.parsed.subject.common_name: "*.ubank.com.pk"` |
| ubldigital.com | `host.services.cert.parsed.subject.common_name: "ubldigital.com"` | `host.services.cert.parsed.subject.common_name: "*.ubldigital.com"` |
| meezanbank.com | `host.services.cert.parsed.subject.common_name: "meezanbank.com"` | `host.services.cert.parsed.subject.common_name: "*.meezanbank.com"` |
| hbl.com | `host.services.cert.parsed.subject.common_name: "hbl.com"` | `host.services.cert.parsed.subject.common_name: "*.hbl.com"` |

For each hit, record: IP, ASN, AS name, cert CN, cert expiry. Paste back
here or hand raw results to Claude to log into
`experiments/16_censys_origin_discovery/results/`.

## Second batch, 2026-09-13: scheduled-banks sample

Pulled all 29 domains out of `data/List_of_Scheduled_Banks-new.pdf` (never
used before), cross-checked against sites already in the pool, and
DNS/header-classified the 18 that were new. Results:

- **2 confirmed Pakistani-hosted directly, no Censys needed**:
  `sindhbankltd.com` (202.63.220.149, AS38584 CubeXS), `ubldirect.com`
  (103.8.14.36, AS56126, UBL's own ASN). Already logged in
  `data/financial_institutions_targets.csv` as `Pakistani`.
- **1 confirmed abroad, no CDN mask**: `bok.com.pk` on LiquidWeb (US),
  serving directly via Apache, not a hidden-origin case.
- **1 dead**: `summitbank.com.pk`, DNS times out.
- **3 uncertain**: `bankalfalah.com`, `bankalhabib.com`, `habibmetro.com`,
  all Azure-hosted, headers don't reveal whether it's a CDN (Azure Front
  Door) or a direct Azure App Service deployment. Deprioritized until that's
  resolved.
- **11 genuine CDN-fronted candidates**, this is the actual sample to run
  through the Censys UI method next, priority on `nbp.com.pk` (state-owned)
  and `bop.com.pk` (govt-linked, and it's Incapsula rather than Cloudflare,
  good to test the method against a different CDN vendor):

| domain | CDN | exact/subdomain query | wildcard query |
|---|---|---|---|
| nbp.com.pk | Cloudflare | `host.services.cert.parsed.subject.common_name: "nbp.com.pk"` | `host.services.cert.parsed.subject.common_name: "*.nbp.com.pk"` |
| bop.com.pk | Incapsula | `host.services.cert.parsed.subject.common_name: "bop.com.pk"` | `host.services.cert.parsed.subject.common_name: "*.bop.com.pk"` |
| abl.com | Cloudflare | `host.services.cert.parsed.subject.common_name: "abl.com"` | `host.services.cert.parsed.subject.common_name: "*.abl.com"` |
| akbl.com.pk | Cloudflare | `host.services.cert.parsed.subject.common_name: "akbl.com.pk"` | `host.services.cert.parsed.subject.common_name: "*.akbl.com.pk"` |
| albaraka.com.pk | Sucuri | `host.services.cert.parsed.subject.common_name: "albaraka.com.pk"` | `host.services.cert.parsed.subject.common_name: "*.albaraka.com.pk"` |
| bankislami.com.pk | Cloudflare | `host.services.cert.parsed.subject.common_name: "bankislami.com.pk"` | `host.services.cert.parsed.subject.common_name: "*.bankislami.com.pk"` |
| faysalbank.com | Cloudflare | `host.services.cert.parsed.subject.common_name: "faysalbank.com"` | `host.services.cert.parsed.subject.common_name: "*.faysalbank.com"` |
| fwbl.com.pk | Cloudflare | `host.services.cert.parsed.subject.common_name: "fwbl.com.pk"` | `host.services.cert.parsed.subject.common_name: "*.fwbl.com.pk"` |
| jsbl.com | Cloudflare | `host.services.cert.parsed.subject.common_name: "jsbl.com"` | `host.services.cert.parsed.subject.common_name: "*.jsbl.com"` |
| soneribank.com | Cloudflare | `host.services.cert.parsed.subject.common_name: "soneribank.com"` | `host.services.cert.parsed.subject.common_name: "*.soneribank.com"` |
| samba.com.pk | Cloudflare | `host.services.cert.parsed.subject.common_name: "samba.com.pk"` | `host.services.cert.parsed.subject.common_name: "*.samba.com.pk"` |

## Next steps

1. Run the manual UI queries above for each domain, log raw hits.
2. Review hits landing on a known Pakistani ASN (cross-check against
   `data/pk_asn_names.json`), drop anything with an expired cert.
3. For surviving candidates, verify like Exp 13 did: confirm the IP
   actually serves the real site (HTTPS request with the real Host header),
   then get a real reachability read from a Pakistani vantage point
   (RIPE Atlas / Globalping), not just a local ping.
4. Log confirmed origins in a results table matching the format of
   `experiments/13_efulife_live_snapshot/OTHER_COMPANIES_RESULTS.md`.
