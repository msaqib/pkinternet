# Tool register and evidence discipline

**Why this file exists.** In the task 04 write-up I stated that RouteViews had been checked when
it had not been. The claim was plausible, the task card asked for it, and nothing in the process
forced me to show the call. This file makes that failure mode structurally hard.

**The rule.** Every factual claim names the call that produced it. If no call was made, the claim
is deleted, not softened. A tool that was *considered* is not a tool that was *used*, and the two
are recorded in different places.

---

## 1. What each tool actually answers

The column that matters most is the third one. Most errors come from reading an answer to a
different question than the one asked.

| Tool | Call | Answers | Does NOT answer |
|---|---|---|---|
| **RIPEstat `announced-prefixes`** | `/data/announced-prefixes/data.json?resource=AS<n>` | which prefixes an AS announces, as RIS collectors see them | whether anyone accepts or uses them |
| **RIPEstat `routing-history`** | `/data/routing-history/data.json?resource=<r>` | per-origin visibility timelines, `full_peers_seeing` | why visibility changed |
| **RIPEstat `bgplay`** | `/data/bgplay/data.json?resource=<pfx>` | one AS path per collector peer at a time, plus events | any path not seen by a collector |
| **RIPEstat `looking-glass`** | `/data/looking-glass/data.json?resource=<pfx>` | live per-peer AS paths, by collector | the same thing at a past date |
| **RIPEstat `asn-neighbours`** | `/data/asn-neighbours/data.json?resource=AS<n>` | neighbours with left/right and `power`, aggregated over ALL prefixes | whether that neighbour carries *this* prefix |
| **RIPEstat `rpki-validation`** | `?resource=AS<n>&prefix=<p>` | is THIS ASN authorised for THIS prefix | who the ROA does authorise |
| **RIPEstat `rpki-history`** | `/data/rpki-history/data.json?resource=<p>` | daily `vrp_count` | the contents of the payloads |
| **RIPEstat `rir-geo`** | `/data/rir-geo/data.json?resource=AS<n>` | RIR *registration* country | where the equipment physically is |
| **RIPEstat `network-info`** | `/data/network-info/data.json?resource=<ip>` | covering prefix and origin ASN | physical location |
| **RIPE IPmap** | `https://ipmap-api.ripe.net/v1/locate/<ip>/best` | a measured city-level location, with the engine that produced it | anything for the 77% that return `null` |
| **PeeringDB** | `peeringdb.com/api/netixlan?asn=<n>`, `/api/ix?country=<cc>` | operator-declared IXP presence and LAN addresses | whether the peering is used, or is truthful |
| **RIPE Atlas** | `atlas.ripe.net/api/v2/...` | measurements we ran or others ran | anything not measured |
| **RouteViews** | separate collector fleet, Univ. of Oregon | an independent peer set for the same question | it is NOT RIPEstat, and must be queried separately |

## 2. The three names that are not three sources

- **RIS** is the collector network. The thing itself.
- **RIPEstat** is the API used to ask RIS questions. **Same data.** Saying "RIPEstat and RIS" as
  two sources is the error.
- **RouteViews** is a genuinely separate fleet with a different peer set. Checking both is what
  turns "not visible in RIS" into "not observable in public BGP".

## 3. Known coverage limits, measured not assumed

| Claim | Measured | Call |
|---|---|---|
| Pakistani presence in public BGP | **1 of 3,352 sessions** (PTCL, cone only) | RIS + RouteViews peer lists |
| Vantage ASes in paths to `103.154.196.0/23` | **0 of 364** | `bgplay` initial_state, 2 dates |
| IPmap coverage on our hop set | **14 of 60 (23%)** | 60 `locate/best` calls |
| IPmap precision where it answers | **3 of 3 disagreements were real** | same 60 calls |
| Commercial GeoDB reliability | >50% of DB-IP and IP2Location paths need correction | Klein et al. 2026 |

## 4. The discipline, in order

1. **Before writing a claim**, name the call. No call, no claim.
2. **Record the call, not the conclusion.** A SOURCES section lists URLs that were actually
   fetched, each verified to return HTTP 200 on a stated date.
3. **Keep "considered" separate from "used".** A tool named in a task card is not evidence.
4. **State coverage as a fraction, always.** "IPmap agrees" is not a finding; "IPmap answered for
   14 of 60 and agreed on 11, disagreed on 3, all 3 genuine" is.
5. **Say which question the call answered.** `rir-geo` answers registration, never location. That
   single confusion produced the three squatting false positives.
6. **When challenged twice, stop editing prose and re-run the call.** The first fix is usually
   cosmetic.

## 5. How you can check me

- Every document has a SOURCES section of clickable URLs. Open any of them.
- Numbers derived from local files name the file and the row count.
- Anything I could not verify is labelled **hypothesis** or **assumption** inline, with the
  specific check that would settle it.
- If a claim has neither a URL nor a file path, treat it as unsupported and say so.
