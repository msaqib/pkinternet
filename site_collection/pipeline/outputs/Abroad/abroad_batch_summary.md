# Abroad batch — Censys cert search summary

Manual Censys UI cert-CN search (`host.services.cert.parsed.subject.common_name`)
run against all 20 sites classified "Abroad" in Exp 07's corrected 98-site sample.
Goal: find a Pakistani-hosted server hiding behind a domain whose main website
resolves abroad. Raw per-IP data in `abroad_pk_ips.csv` (same folder).

## Results

| Domain | Result |
|---|---|
| 588wingames.pk | No cert found |
| 777sxgameapp.pk | No cert found |
| apkzone.pk | No cert found |
| enic.pk | No cert found |
| hopkicks.pk | Confirmed abroad only |
| hostpro.com.pk | No cert found |
| **insta.com.pk** | **7 real PK IPs found** (AS138368, INSTACOM, Multan) |
| nawaiwaqt.com.pk | Confirmed abroad only |
| pessi.gop.pk | No cert found |
| pgf.com.pk | No cert found |
| publicnews.com | No cert found |
| scouted-today.pk | Confirmed abroad only |
| en.dailypakistan.com.pk | Confirmed abroad only |
| duet.edu.pk | Confirmed abroad only |
| **uvas.edu.pk** | **2 real PK IPs found** (AS45773, PERN, Lahore) |
| ke.com.pk | Confirmed abroad only (57 IPs checked) |
| gbappsup.org.pk | No cert found |
| kppsc.gov.pk | Confirmed abroad only |
| ptea.org.pk | No cert found |
| serenepharma.com.pk | Confirmed abroad only |

**18 of 20** stayed abroad or had no indexed cert. **2 of 20** have real Pakistani
infrastructure behind them despite their public website being hosted overseas.

## New PK IPs found: 9 total

| Domain | PK IPs found | ASN | IPs |
|---|---|---|---|
| insta.com.pk | 7 | AS138368 (INSTACOM, Multan) | 103.131.215.2, .4, .5, .6, .9, .13, .14 |
| uvas.edu.pk | 2 | AS45773 (PERN, Lahore) | 111.68.105.203, .212 |

The other 18 sites contributed 0 PK IPs, either confirmed abroad only or no cert
indexed at all.

## The two sites with real PK infrastructure

**insta.com.pk — INSTACOM, an ISP in Multan.** Founded 2014, one of the larger
internet/data providers in Punjab (fiber, cable TV, phone, WiFi hotspots). The
public website sits on a US server, but 7 servers on the company's own network
(AS138368, Multan) run its actual operations: customer login/RADIUS auth, a VPN
panel, admin panels, tech support. The organization is domestic even though its
marketing site isn't.

**uvas.edu.pk — University of Veterinary and Animal Sciences, Lahore.** A public
research university, one of Pakistan's oldest institutions, ranked among the
country's top ten. The public website is hosted abroad via Hostinger (Vilnius),
but 2 servers on Pakistan's academic network PERN (AS45773, Lahore) run its
internal systems: a database server and a staff-facing web app.

## Location

`/Users/SameeraSalman/pkinternet/site_collection/pipeline/outputs/Abroad/abroad_batch_summary.md`
