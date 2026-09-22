# Selection of CDN sites

24 sites, 6 per group, picked from the Ahrefs top 100 sites in Pakistan (Aug 2026). Full list in `Selection_of_CDN_sites.csv`.

## Fastly and Akamai
- The Ahrefs top 100 has exactly 6 sites on each, so all 6 are taken. No sampling.

## Hyperscaler
- 7 available, 6 needed.
- Dropped **instagram.com**. It is the most redundant, since facebook.com is the same company and the same Ahrefs category (Online Communities).
- All four hyperscalers are still covered: Google (youtube.com, google.com), Meta (facebook.com, whatsapp.com), Apple (apple.com) and Microsoft (microsoft.com).

## Cloudflare
- 38 available, 6 needed.
- Rule: one site per sector, highest-ranked in that sector. This spreads the picks across sectors instead of taking the top 6 by rank.

| Sector | Site | Ahrefs rank |
|---|---|---|
| Government | bisp.gov.pk | 18 |
| Health | dvago.pk | 27 |
| Finance | wise.com | 75 |
| Jobs and Education | fiverr.com | 85 |
| Shopping | priceoye.pk | 10 |
| Computers and Electronics | chatgpt.com | 2 |

