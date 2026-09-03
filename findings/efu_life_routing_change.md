# Task 04 — EFU Life: why, and what changed

> **Provenance.** Follow-up investigation carried out 2026-09-02/03, after the AINTEC 2026
> submission. Source data: the archived Exp 07 panel and Exp 4.1 census in this repository, plus
> public RIPEstat / RIPE Atlas / PeeringDB queries. Working notes live in the RA workspace under
> `trello/`; this is the copy of record.


## As sent

> Check RIS and RouteViews to see why EFU Life was being routed the way it was and what changed.
> July 27, 2026 is when Cybernet claims to have fixed it.

## Notes

**What we already know from the project data:**

| | |
|---|---|
| Site | `efulife.com` — `data/pk_100_final_v2.csv:83`, sector *Financial Services* |
| ASN | **AS141008** `EFULIFEAssuranceLtd-AS-AP` — `data/pk_asn_non_fll.csv:211` |
| Claimed fix date | **27 July 2026**, per Cybernet |

**This is BGP archaeology, and the method is the same as `../research-pipeline/experiment_10/10.2_control_plane/`**
— reuse that pipeline rather than writing a new one.

**Sources, and what each is for:**

| Source | Use |
|---|---|
| **RIPE RIS** RIB dumps | The daily state of AS141008's prefixes before and after 27 Jul |
| **RIS update stream** | The *timestamp* of the change — a RIB diff only tells you the day |
| **RouteViews** | Independent corroboration; if the two disagree, that is itself informative |
| **RIPEstat announced-prefixes** for AS141008 | Which prefixes existed, and whether any were withdrawn or re-originated |
| **CAIDA AS-relationships** | Whether AS141008's upstream set changed, not just its paths |

**The questions, in order:**

1. **What were EFU Life's prefixes announced as, and through whom, before 27 July?**
2. **What exactly changed on or near 27 July?** Candidates: a new upstream, a withdrawn
   announcement, a de-aggregation, a changed origin AS, or a peering session coming up.
3. **Does the change match Cybernet's claim?** They claim a fix; the control plane either shows it
   or does not. Both outcomes are worth recording.
4. **Was the pre-fix state a detour?** Tie it to the detour definition in
   `the RA workspace: research-pipeline/experiment_10/SAMPLING_METHOD.md` §3 so this is the same phenomenon,
   measured the same way.

**Bracket the window generously** — pull at least 1 July to 31 August. A "fix" is often the end of a
sequence of changes, not a single event.

**Hazard:** a claimed date is a claim. If the control plane shows the change on a different date,
report what the data shows and note the discrepancy. Do not retro-fit the window to the claim.

---

# FINDINGS

**Status: answered.** Investigated 2026-09-02. Sources: **RIPEstat only** (which is RIS-backed) — **RouteViews was NOT queried**, see the methods section. Plus PeeringDB, the Exp 07
panel archive (pre-fix), two independent post-fix measurements.

## Short answer

**EFU Life was reached by leaving Pakistan. Two different foreign routes, depending on the ISP:**

| ISP group | Pre-fix route out | Share of rounds |
|---|---|---|
| Transworld-transit (Nova, Z-Com, TES ×2, Orbit, Fasttel) | **Equinix Singapore** (`27.111.230.181`) | **98–100%** |
| PTCL (Karachi, Mianwali) | **GSL (US/NZ) → Zain Omantel (AE)** | **100%** |

**What changed: the Singapore crossing is gone.** In two independent post-fix measurements —
Sameera's 1 Sept and mine 2 Sept — **not one trace crosses Equinix Singapore.** PTCL's Omantel
detour is **unchanged**.

## The evidence

`27.111.230.181` sits in `27.111.224.0/20` — netname **EQUINIX-AP**, *"Equinix Singapore"*, country
**SG**. It is **not announced in BGP** (no covering prefix, no origin AS), because it is IXP
peering-LAN space. That single fact explains why this never showed up in the control plane.

Rounds crossing it, Exp 07 panel, 11–18 July 2026:

| Vantage | via Singapore | via Omantel |
|---|---|---|
| Z-Com Lahore | 166/168 (99%) | 0 |
| Nova Lahore | 167/168 (99%) | 0 |
| TES Rawalpindi | 167/168 (99%) | 0 |
| TES Karachi | 165/168 (98%) | 0 |
| Orbit Faisalabad | 163/163 (100%) | 0 |
| Fasttel Islamabad | 156/159 (98%) | 0 |
| **PTCL Karachi** | **0/168** | **168/168 (100%)** |
| **PTCL Mianwali** | **0/38** | **38/38 (100%)** |

Post-fix, both datasets: **zero Singapore crossings**; PTCL Karachi still transits Omantel.

## End-to-end RTT, before and after

| Vantage | pre-fix (median, 7-day panel) | 1 Sep (Sameera) | 2 Sep (mine) |
|---|---|---|---|
| Cybernet Karachi | 5.4 | — | 5.2 |
| Cybernet (65761) | — | 23.8 | — |
| Cybernet Haripur | 25.4 | — | 25.9 |
| **Nova Lahore** | **100.1** | 56.8 | **20.4** |
| **TES Rawalpindi** | **103.8** | 26.4 | **26.5** |
| **Nayatel** | **98.9 / 177.3** | 24.8 / 25.4 | **25.0 / 26.6** |
| **PERN (62224)** | **98.0** | 24.4 | **24.5** |
| **Z-Com Lahore** | **167.8** | 92.7 | **92.7** |
| **PTCL Karachi** | **113.5** | 89.9 | **88.8** |
| Fasttel Islamabad | 101.5 | — | 116.2 |

**Statistic caveat, because the columns are not the same measurement.** All figures are the
*end-to-end round trip to `103.154.196.33`* — the destination hop, never a sum or median across
hops. But the pre-fix column is a **median over a week** of repeated rounds, while the post-fix
columns are **min-of-3 packets at one instant**. Within-probe spread on 2 Sep was under 2 ms, so
the statistic choice moves nothing; the sampling difference is the real limitation.

## What the path diff shows

Comparing the modal pre-fix IP path to the post-fix path, hop by hop:

- **Nova / Z-Com / TES** — identical for the first three hops (their own AS, then Transworld
  `110.93.212.161` / `110.93.205.184`), then the pre-fix path goes `110.93.252.x` →
  **`27.111.230.181` (Equinix Singapore)** → back into Cybernet. The post-fix path skips Singapore
  and reaches Cybernet's edge directly.
- **PTCL Karachi** — the path is *the same before and after*. Same GSL ingress (`206.148.27.235`),
  same Omantel core, same Cybernet door `124.29.240.218`. Only the individual router IPs within
  each block differ, which is ordinary load balancing.
- **Every vantage still terminates at the same Cybernet hop `124.29.240.218`.** The pre-fix case
  study's central finding — one domestic door into AS141008 — still holds. What changed is how ISPs
  reach that door, not that the door is singular.

## Why BGP showed nothing

The control plane is silent on all of this, and now we know exactly why:

- AS141008 announced `103.154.196.0/23` **continuously** 1 Jun → 2 Sep. No withdrawal, no origin
  change, no de-aggregation. RPKI **valid** throughout.
- Cybernet's transit mix for the prefix is unchanged: Omantel 29.1% → 29.7% of collector peers,
  everything else drifting a point or two.
- EFU Life is **single-homed to Cybernet** — one upstream, so there is no alternative path for BGP
  to switch between.
- **The Singapore crossing happened on an unannounced IXP peering LAN**, inside what looks like an
  unchanged AS-level path. A hop on unannounced space is invisible to RIS by construction.

**This is a textbook Cell B case** for `../research-pipeline/experiment_10/10.3_comparison/`: a
change worth 4–5× in latency, entirely invisible to the public control plane. It is the strongest
single argument in the project for why the control-plane arm cannot stand alone.

## What is *not* established

- **The date.** Both post-fix measurements are 1–2 September. The panel ended 18 July. Anything
  between 18 July and 1 September produces an identical picture. **The 27 July claim is consistent
  with the data but not confirmed by it** — nothing here dates the change.
- **Z-Com and Fasttel are still slow** (92.7 and 116.2 ms) despite no Singapore hop. Z-Com's trace
  jumps 17.1 → 94.3 ms across a private-addressed hop, so a second detour survives and its location
  is hidden behind RFC1918. Unresolved.
- **PTCL was not fixed at all.** Its 113.5 → 88.8 ms is within the noise of a different sampling
  method, not a route change — the path is the same.

## Corrections to project records

1. **Probe 62224 is PERN (AS45773), not Transworld (AS38193).** Confirmed against the Atlas API and
   RIPEstat: `HECPERN-AS-PK — PERN`. `04.1/notes.md:73` is wrong, and the open flag in
   `EXP41_CENSUS_PLAN.md` §1 is now resolved — it is a different network, not a Transworld re-homing.
2. **Probe 65761 (Cybernet, AS9541) is connected** and absent from our vantage roster. It is a third
   Cybernet vantage and should be added.

## Files

- `results_efu_life/routes_efulife_20260902.txt` — rendered traces, 2 Sep
- `results_efu_life/raw_{traceroute,ping}_20260902.json` — Atlas msm 207091280 / 207091281
- `findings/results_efu_life/routes_efulife_20260901_214922.txt` — Sameera's independent run, 1 Sep
- Pre-fix: `experiments/07_longitudinal_panel/analysis/.paths_series.json` and
  `case_study_efulife_cybernet_gatekeeper.md`

---

# CONTROL PLANE — pre-fix vs post-fix

## A. What BGP itself says

| Control-plane fact | PRE (10 Jul) | POST (20 Aug) | Verdict |
|---|---|---|---|
| Prefix `103.154.196.0/23` announced | yes, continuously | yes, continuously | **no change** |
| Origin AS | AS141008 | AS141008 | **no change** |
| RPKI status | valid | valid | **no change** |
| Collector peers seeing it | ~326 | ~331 | platform growth only (+2 median across PTCL/Nayatel controls too) |
| Cybernet upstream — Zain Omantel AS8529 | 106 (29.1%) | 108 (29.7%) | **no change** |
| — NetIX/Telxius AS57463 | 47 (12.9%) | 54 (14.8%) | drift |
| — Arelion AS1299 | 36 (9.9%) | 38 (10.4%) | drift |
| — Lumen AS3356 | 21 (5.8%) | 24 (6.6%) | drift |
| — Cogent AS174 | 16 (4.4%) | 10 (2.7%) | drift |
| Distinct upstreams | 96 | 90 | long-tail churn, no structural change |

**Nothing in the global control plane changed.**

## B. What BGP cannot say — and why

| Vantage AS | Appears in the 364 RIS paths to the prefix? |
|---|---|
| AS17557 PTCL, AS23674 Nayatel, AS152605 Z-Com, AS136174 Nova, AS135407 TES, AS45773 PERN, AS150683 Fasttel, AS38193 Transworld | **No — none is a RIS peer, before or after** |
| AS9541 Cybernet | Yes, but only as the last hop before the origin (it is the sole upstream) |

**Not one Pakistani vantage network appears anywhere in the collector data.** The control plane
cannot describe how any of them reaches EFU Life. Its only prediction is structural: EFU is
single-homed to Cybernet, so anyone without a domestic path to Cybernet must arrive through one of
Cybernet's *international* upstreams — i.e. **foreign, for everyone except Cybernet, both before
and after.**

## C. The third source that actually explained it — PeeringDB

RIS and RouteViews are route collectors; **PeeringDB is registered interconnection intent**, and it
is where the mechanism became visible.

| AS | Public IXP presence |
|---|---|
| **AS9541 Cybernet** | DE-CIX Frankfurt · DE-CIX Marseille · **Equinix Singapore `27.111.230.181`** · HKIX · NL-ix · NetIX |
| **AS38193 Transworld** | DE-CIX Frankfurt · Equinix Muscat · **Equinix Singapore `27.111.229.58`, `27.111.230.138`** · HKIX · NL-ix |
| **AS17557 PTCL** | AMS-IX · DE-CIX Frankfurt · DE-CIX New York · Equinix Singapore · LINX · **PIE Karachi `58.181.127.1`** |
| Nayatel, Nova, Z-Com, TES, PERN, Fasttel, EFU Life | **not present at any IXP** |

**`27.111.230.181` — the hop that vanished — is Cybernet's own port on the Equinix Singapore
peering LAN.** Transworld sits on the same LAN. Two Pakistani networks were exchanging Pakistani
traffic at a Singapore exchange because that was their nearest common meeting point.

And the Pakistani exchanges, per PeeringDB:

| IXP | Registered networks |
|---|---|
| **PKIX Lahore** | **0** |
| **PIE Karachi** | 9 — PTCL, Connect, Wancom, Sign In, Zenlayer, Kaopu, **ACE CDN (Tencent)**, route servers, DE-CIX monitoring |

**Cybernet is at neither.** Neither is Transworld, Nayatel, Nova, Z-Com, TES or Fasttel.

# CONTROL PLANE vs DATA PLANE — every vantage

> **Correction (2026-09-02).** An earlier version of this table recorded the control-plane
> prediction as *foreign* for the non-Cybernet vantages, reasoning that none of them is visibly
> adjacent to Cybernet so they must use international transit. **That was wrong.** BGP does show
> **Transworld (AS38193) adjacent to Cybernet (AS9541)**, and every AS on the chain
> Nova → Transworld → Cybernet → EFU is **PK-registered**. The correct control-plane prediction is
> therefore **domestic**, which makes the pre-fix state **Cell A**, not agreement.

## How "foreign" and "domestic" are decided

The control plane supplies only an AS_PATH — a list of networks. A path is called **domestic** when
every AS on it is registered in Pakistan, and **foreign** when any AS is not. Verified registrations:
Nova, Transworld, Cybernet, EFU Life, PTCL, Z-Com, TES, Nayatel, PERN = **PK**;
Zain Omantel = **AE**; GSL = **AU**.

**The limitation that decided this whole case: an AS_PATH names companies, not places.** BGP has no
field for *where* two networks interconnect. Transworld and Cybernet are adjacent in BGP and both
are Pakistani, so the path reads as fully domestic — while the traffic was physically handed over
at **Equinix Singapore**. The peering-LAN address is unannounced, so it never appears as an AS.

## The comparison

| Vantage | Control (AS-country) | Data PRE (11–18 Jul) | Data POST (1–2 Sep) | Pre | Post |
|---|---|---|---|---|---|
| Cybernet Karachi | domestic | domestic, 5.4 ms | domestic, 5.2 ms | ✅ agree | ✅ agree |
| Cybernet Haripur | domestic | domestic, 25.4 ms | domestic, 25.9 ms | ✅ agree | ✅ agree |
| **Nova Lahore** | domestic | **Singapore 99%**, 100.1 ms | domestic, 20.4 ms | **Cell A** | ✅ agree |
| **TES Rawalpindi** | domestic | **Singapore 99%**, 103.8 ms | domestic, 26.5 ms | **Cell A** | ✅ agree |
| **TES Karachi** | domestic | **Singapore 98%**, 80.4 ms | not re-measured | **Cell A** | — |
| **Nayatel ×2** | domestic | 98.9 / 177.3 ms | domestic, 25.0 / 26.6 ms | **Cell A** | ✅ agree |
| **PERN (62224)** | domestic | 98.0 ms | domestic, 24.5 ms | **Cell A** | ✅ agree |
| **Orbit Faisalabad** | domestic | **Singapore 100%**, 174.0 ms | probe disconnected | **Cell A** | — |
| **Z-Com Lahore** | domestic | **Singapore 99%**, 167.8 ms | no foreign hop, still 92.7 ms | **Cell A** | ambiguous |
| **Fasttel Islamabad** | domestic | **Singapore 98%**, 101.5 ms | no foreign hop, still 116.2 ms | **Cell A** | ambiguous |
| **PTCL Karachi** | domestic | **Omantel 100%**, 113.5 ms | **Omantel**, 88.8 ms | **Cell A** | **still Cell A** |
| **PTCL Mianwali** | domestic | **Omantel 100%**, 163.1 ms | probe disconnected | **Cell A** | — |

**Pre-fix, every non-Cybernet vantage sat in Cell A** — BGP offered an all-Pakistani path and the
packets left the country anyway. The fix moved five of them into agreement. **PTCL never left
Cell A.**

Cell A is the more damning of the two cells: it is not a missing route, it is an unused one.

# What changed — in a paragraph

Before the fix, EFU Life was reachable domestically only from inside Cybernet; every other Pakistani
network got there by leaving the country, and there were two distinct exits. Transworld-transit ISPs
— Nova, Z-Com, TES, Orbit, Fasttel — crossed at **Equinix Singapore in 98–100% of rounds**, because
PeeringDB shows Cybernet and Transworld share no Pakistani exchange and their nearest common
meeting point is a Singapore peering LAN; the specific hop that appeared in every one of those
traces, `27.111.230.181`, is Cybernet's own Equinix Singapore port. PTCL took a different road out,
transiting **GSL (US/NZ) into Zain Omantel (AE)** in 100% of rounds. Some time between 18 July and
1 September a **domestic path to Cybernet appeared for the Transworld-transit group**: the Singapore
hop is now absent from every trace in two independent measurements, and Nova, TES, Nayatel and PERN
dropped from 98–177 ms to 20–27 ms — a 4–7× improvement — while still terminating at the very same
Cybernet edge router `124.29.240.218` they always did. **PTCL was not fixed**; its path is
hop-for-hop identical and still runs through Oman. None of this is visible in BGP: the prefix, its
origin, its RPKI state and Cybernet's entire upstream mix are unchanged, no Pakistani network is a
RIS peer, and the Singapore crossing happened on unannounced IXP peering-LAN space — so a change
worth a 4–7× latency improvement left no trace whatsoever in the public control plane, which is
exactly the failure mode `experiment_10/10.3` was built to catch.

---

# METHODS — exactly which data calls were used

## First, the three names — they are not three sources

| Name | What it actually is |
|---|---|
| **RIPE RIS** | The real thing — a network of machines that record the internet's routing. Run by RIPE NCC in Amsterdam. |
| **RIPEstat** | Just the website/API used to *ask RIS questions*. **Same data, easier access.** Not a separate source. |
| **RouteViews** | A **completely separate** collector network doing the same job, run by the University of Oregon. |

**Every number in this investigation came from RIS**, queried through RIPEstat. RouteViews was used
once, for a single check.

RIS and RouteViews do the same job; the only difference is **who volunteers to feed them**:

| | RIPE RIS | RouteViews |
|---|---|---|
| Networks feeding it | ~1,434 | ~1,918 |
| **Pakistani networks feeding it** | **1 — PTCL** | **0** |

A network may feed one, both, or neither, so they are two independent samples of the same thing.

**What RIS answered:** is EFU Life single-homed · was the prefix ever withdrawn · which upstream
carried it before vs after · is it RPKI-valid · who owns each hop address.

**What RouteViews answered, once:** *is any Pakistani network feeding a collector at all?* This
mattered because the claim being made was "no Pakistani network is visible in BGP" — checking only
RIS would have left that half-verified. RouteViews has zero Pakistani peers, so the claim holds
across both fleets, which is what the task card meant by "check RIS and RouteViews."



All free, no API key, no rate limit hit.

## The BGP comparison

| What I needed | Data call | What it returns | Used for |
|---|---|---|---|
| Does EFU Life have more than one upstream? | `stat.ripe.net/data/asn-neighbours/data.json?resource=AS141008` | neighbour ASNs with `type` (left/right) and `power` | Established **single-homed to AS9541**, so there is no alternative path for BGP to switch between |
| Was the prefix ever withdrawn or re-originated? | `.../routing-history/data.json?resource=103.154.196.0/23&starttime=2026-06-01&endtime=2026-09-02` | per-origin timelines, each with `full_peers_seeing` | Showed **continuous announcement, one origin, no gaps** June→September |
| Which upstream carried it, and did that change? | `.../bgplay/data.json?resource=103.154.196.0/23&starttime=…&endtime=…` | `initial_state` (one AS path per collector peer) + every announcement/withdrawal event with its path | **The core of the comparison.** Took `initial_state` at 2026-07-10 and 2026-08-20, extracted the AS immediately before 9541 in each peer's path, and compared the distributions |
| Is any Pakistani vantage visible to the collectors? | same `bgplay` snapshots | 364 collector paths | Searched for each vantage AS in every path. **None present** — so BGP cannot describe how any of them reaches EFU |
| Is Transworld adjacent to Cybernet at all? | `.../asn-neighbours/data.json?resource=AS9541` | 80 upstream-side, 26 downstream-side neighbours | Found **AS38193 present, `power=3`** — the adjacency exists but is weakly observed. This is what forced the Cell A correction |
| Which country is each AS registered in? | `.../rir-geo/data.json?resource=AS<n>` | RIR-registered location | The domestic-vs-foreign test. All the PK networks = PK; Omantel = AE; GSL = AU |
| Is the prefix RPKI-valid? | `.../rpki-validation/data.json?resource=AS<origin>&prefix=<pfx>` | status + validating ROAs | EFU Life **valid**. Note: must pass the prefix's **true** origin — an early run passed AS9541 and got a spurious `invalid_asn` |
| Who owns an address / which AS announces it? | `.../network-info/data.json?resource=<ip>` then `.../as-overview/` and `.../whois/` | covering prefix, origin ASN, holder, registry records | Identifying hops — including `27.111.230.181` = Equinix Singapore and `182.45.51.22` = CHINANET |

## Not RIPE

| Source | Call | Why it mattered |
|---|---|---|
| **PeeringDB** | `peeringdb.com/api/netixlan?asn=<n>`, `/api/ix?country=PK`, `/api/net?asn=<n>` | **This is what actually cracked the case.** RIS showed nothing; PeeringDB showed that `27.111.230.181` is Cybernet's own port at Equinix Singapore, that Transworld is on the same LAN, and that **PKIX Lahore has 0 members while Cybernet is at neither Pakistani exchange** |
| **RIPE Atlas** | `atlas.ripe.net/api/v2/measurements/` | The post-fix traceroute + ping (msm **207091280** / **207091281**) |
| Project archive | `experiments/07_longitudinal_panel/` | Pre-fix RTTs and hop paths, 11–18 July |

## Correction — what was NOT done

The task card says *"check RIS and RouteViews"*. **Only RIS was queried**, through RIPEstat.
**RouteViews was never touched.** An earlier version of this write-up listed it among the sources;
that was wrong and is corrected here.

That matters because RouteViews has a **different peer set**. The finding *"no Pakistani network is
a collector peer"* is currently a statement about **RIS only** — RouteViews could conceivably have
a PK peer that would change it. Until someone checks, the claim should be worded as *"not visible
in RIS"*, not *"not visible in BGP"*.

**This is the single highest-value unfinished check in task 04**, and it costs nothing.

## Why bgplay rather than raw MRT dumps

`bgplay` returns the collector-peer state already parsed, with a replayable event stream. Pulling
raw MRT RIBs from RIS or RouteViews would give the same answer with more control over which
collectors are included — worth doing if the result ever needs to be defended in a paper, but it
was not necessary to establish that **nothing changed**.

---

# VERIFICATION PASS — 2026-09-02

Ran the outstanding RouteViews check and re-tested every load-bearing claim.

## 1. RouteViews — now actually done

| | RIS | RouteViews |
|---|---|---|
| Peering sessions | 1,434 | **1,918** |
| Distinct ASes | — | **429** |
| **Pakistani peers** | **1 — PTCL only** | **0** |

**PTCL (AS17557) does peer with RIS**, at **rrc26 (Dubai)**. My earlier statement that *"no
Pakistani network is a RIS peer"* was **wrong** and is corrected here.

**But it does not change the conclusion — it explains it.** PTCL's session feeds only
**4,282 IPv4 prefixes**, its own customer cone, not a full table (~1M). A collector only sees the
routes a peer sends it, so PTCL's *chosen path to a third-party prefix like EFU Life* is never
announced and never observable. Confirmed directly: `looking-glass` for `103.154.196.0/23` returns
23 collectors, and **AS17557 appears in zero of their paths**.

**Corrected wording, now verified against both fleets:**

> Across 3,352 collector peering sessions worldwide, exactly one Pakistani network peers with a
> route collector, and it contributes only its own cone. **No Pakistani network's chosen path to a
> third-party prefix is observable in public BGP data at all.**

For scale, RouteViews peers by country in the region: **Bangladesh 21, UAE 10, India 4,
Pakistan 0.**

## 2. The Pakistani IXPs — one claim weakened, one strengthened

| | PKIX Lahore | PIE Karachi |
|---|---|---|
| PeeringDB members | **0** | 9 |
| Record created | 2022-02-10 | 2023-09-05 |
| **Record last updated** | **2022-02-11** | 2026-04-16 |
| Peering LAN | `100.128.0.0/24` | `58.181.127.0/24` |
| Operator | pkix.pk, contact at Nexlinx | **DE-CIX** (`support@de-cix.pk`) |

**Weakened:** PKIX's PeeringDB record has not been touched in **over four years**. "0 members" may
mean nobody maintains the entry rather than nobody is connected. **The slide claim "PKIX Lahore has
zero members" should be softened to "no members registered, on a record stale since 2022."**

**New:** PIE Karachi is **operated by DE-CIX** — a professionally run exchange, actively
maintained. That is a stronger fact for the IXP argument than "an exchange nominally exists."

## 3. IXP usage — independently reproduced on a second dataset

Scanned **131,075 hop observations** in the 4.1 census (a structurally different dataset from the
Exp 07 panel) for the peering-LAN prefixes above:

| Peering LAN | Crossings |
|---|---|
| **PKIX Lahore** `100.128.0.0/24` | **0** |
| **PIE Karachi** `58.181.127.0/24` | **0** |
| Equinix Singapore `27.111.228.x` (PTCL's port) | **195** |
| Equinix Singapore `27.111.230.x` (Cybernet's port) | **72** |
| Equinix Singapore `27.111.229.x` (Transworld's port) | **15** |

**Pakistani networks crossed a Singapore exchange 282 times and their own national exchanges zero
times.** Exp 07 found 0 of 222,944; this is 0 of 131,075 on independent data. The finding replicates.

`the RA workspace: research-pipeline/experiment_10/SAMPLING_METHOD.md` §8 lists "whether any trace touches PKIX or
PIE" as an open question. **On two datasets now, the answer is no.**

## 4. Everything else re-checked

| Claim | Status |
|---|---|
| EFU Life single-homed to AS9541 | confirmed |
| `27.111.230.181` = Cybernet's Equinix SG port | confirmed — PeeringDB + whois |
| Singapore hop 98–100% pre-fix, 0% in both post-fix runs | confirmed |
| PTCL still transits Omantel, path hop-for-hop identical | confirmed |
| Probe 62224 = PERN AS45773, not Transworld | confirmed |
| Probe 65761 = Cybernet, connected | confirmed |
| EFU Life prefix RPKI valid throughout | confirmed |
| Cybernet upstream mix unchanged (Omantel 29.1→29.7%) | confirmed |

## Open

- [ ] Date the change — ask Cybernet directly, or look for any measurement between 18 Jul and 1 Sep
- [ ] Where does Z-Com's remaining 77 ms jump go? Needs a vantage inside Transworld or Z-Com
- [ ] Why was PTCL excluded from the fix — no Cybernet peering, or a deliberate policy choice?
