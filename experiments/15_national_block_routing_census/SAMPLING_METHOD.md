# Sampling method — national block-routing census (standalone)

**Status:** design frozen, unrun. **Owner:** Rayan Atif. **Revised:** 2026-09-01.
**Prior work:** Exp 4.1 (`../04.1_small_isp_tromboning/`) — designed this
census and **ran it once** on 2026-06-27. That run's data is the baseline (§4).
**Execution plan:** `EXP41_CENSUS_PLAN.md` (probes, phases). **Deck:** `make_slides.py`.

Exploratory run. Sweep the small-ISP address space once, *properly*, and see what the data says.
No claim is committed to in advance.

---

## 1. Sources vs destinations — the thing that is easy to misread

Two different sets of ISPs, chosen for opposite reasons.

|  | **Destinations (targets)** | **Sources (vantages)** |
|---|---|---|
| Who | **48 small/local ISPs** — PTA Fixed Local Loop licensees | 7 RIPE Atlas probes, mostly at **large** ISPs |
| What | Their **747 announced blocks** — the thing being censused | The place we measure *from* |
| Chosen for | **Completeness** — every block of every small ISP | **Transit diversity** — one probe per distinct upstream |
| Count driver | Whatever RIPEstat says they announce | However many distinct transits we can reach |

**We are targeting small ISPs.** PTCL, Nayatel, Cybernet, Nova and Z-Com appear in these documents
only as *vantage points we measure from* — never as targets. The question is "when a packet is sent
toward a small ISP's block, does it stay in Pakistan?", and it must be asked from several different
upstreams because the answer depends on the sender's transit.

---

## 2. Selection flow — every number, and where it came from

### 2A. Destinations: how 747 blocks are arrived at

| Stage | Count | How that number was obtained |
|---|---|---|
| PTA FLL licensee roster | **77** | `data/pk_isp_fll_list.csv` — every row is `license_type = FLL`. This is the licence roster, the legal definition of "small/local ISP" in Pakistan. |
| …with an ASN on record | **71** | Rows with a non-empty `asn` field, cross-checked against the `ripe_name` / `ripe_description` columns. 6 licensees have no ASN recorded at all. |
| …distinct ASNs | **66** | Deduplicating those 71 rows by ASN. 5 rows share an ASN with another licensee — related or renamed companies. One row per ASN becomes `isp_summary.csv` (66 rows). |
| …that actually announce prefixes | **48** | RIPEstat announced-prefixes API, queried per ASN — see §2C for the full provenance. **18 announce nothing at all** — defunct, or sub-allocated from a parent. Excluded from probing, kept as a finding: a licensed ISP with no address space of its own is a result. |
| Announced blocks | **747** | Union of every prefix those 48 ASNs announce → `results/blocks_all.csv`, one row per block. Verified: 747 rows, 48 distinct ASNs. |
| Total addresses | **206,592** | Sum of the `num_addresses` column across all 747 rows. |
| Block sizes | **725** × /24, **17** × /23, **4** × /22, **1** × /19 | Value counts of the `prefix_len` column. **Not all /24** — see §5.6 for how the larger prefixes are sampled. |
| Targets probed | **K per block** | K evenly spaced addresses inside each block. For a /24 at K=8 the June run used `.28 .56 .85 .113 .142 .170 .199 .227` — i×256/9, not the `.16 .48 …` spacing quoted in `04.1/notes.md:82`. **The notes are wrong about this**; the run is the authority. |

**Concentration.** Sorting `isp_summary.csv` by block count: Connect Communications 132, Optix 88,
CMPak LDI 85, Broadband Vision 78, Brain Telecom 49 — the **top 5 hold 432 of 747 blocks (58%)**. A
block-level average is therefore mostly an average of five operators. **Per-ISP rates lead; block
aggregates are secondary.**

### 2B. Sources: how 7 vantages are arrived at

| Stage | Count | How that number was obtained |
|---|---|---|
| Atlas probes in Pakistan known to the project | **16** | Union of Exp 4.1's source roster (`notes.md:62`) and the Exp 07 panel map (`probe_label_map.csv`). Not every PK probe in existence — every one this project has used or evaluated. |
| …connected | **12** | RIPE Atlas probe API, `status`, checked 2026-09-01. Disconnected: 64535 Orbit, 1016153 TES, 1016154 Cybernet Karachi, 1016393 PTCL Mianwali. |
| …path-visible under TCP/80 | **10** | Excludes 7764 and 62224, recorded as ICMP-filtered. **Provisional** — that verdict was reached with ICMP, and TCP/80 may see paths ICMP cannot. Re-tested in Phase 1. |
| …deduplicated by upstream transit | **7** | One probe per distinct AS/transit. Drops 65892 (same AS as 60223) and 64078 (same AS as 64722) — same upstream, no new information. |

Selection rule: **one probe per distinct transit**, plus two deliberate exceptions — a second
Transworld-transit source and a second Cybernet source. Those exist to *test* the assumption that
behaviour clusters by transit rather than assume it. Per-probe justification: `EXP41_CENSUS_PLAN.md` §1.

---

### 2C. Where the BGP data comes from

Enumerated by `04.1_small_isp_tromboning/enumerate_small_isps.py`, one HTTP call per ASN.

| | |
|---|---|
| Endpoint | `https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS<n>` |
| Underlying data | **RIPE NCC Routing Information Service (RIS)** — its global route-collector fleet |
| Cost | free; no API key, no measurement credits |
| Filter | **IPv4 only** — the enumerator keeps `net.version == 4` and drops IPv6 announcements |
| ASN handling | `asn` column, `AS` prefix stripped, must be all-digits; **first company name wins on a duplicate ASN**, which is the 71 → 66 step in §2A |
| Snapshot | **2026-06-27** |

Three things this means, and they should be said out loud rather than discovered by a reviewer:

**1. "Announced" means *visible to RIS*.** RIS learns a prefix only if one of its peers is told
about it. A prefix propagated only to domestic peers, and never further, may never reach a
collector — and that is precisely the class a study of *domestic* interconnection would most want
to see. The 747 is best described as "globally visible announced blocks," not "all announced
blocks."

**2. It is IPv4-only.** Any IPv6 deployment in this population is outside the census by
construction. Worth one sentence in any write-up rather than silence.

**3. It is a snapshot, now over two months old.** Prefixes are stable relative to individual
addresses (this is the TASS argument in §5), but 747 is not guaranteed to still be 747.
**Re-enumerate immediately before the census** — it is free and takes minutes.

**Cross-check worth doing in Phase 1:** run the same enumeration against **RouteViews** and compare.
Agreement on 747 makes the universe solid; if RouteViews sees prefixes RIS does not, the census was
under-counting and the gap itself is interesting.

## 3. Detection rules — and what justifies each one

### 3.1 The phenomenon and its literature

"Tromboning" here is what the measurement literature calls a **routing detour**: a path between two
endpoints in one country that leaves that country and returns.

- **Edmundson et al. (2016)**, *Characterizing and Avoiding Routing Detours Through Surveillance
  States* [`edmundson2016characterizing`] — establishes the detour as a measurable, systematic
  property of interdomain routing rather than an anomaly, and the method of identifying it from
  traceroute paths.
- **Gupta et al. (PAM 2014)**, *Peering at the Internet's Frontier: A First Look at ISP
  Interconnectivity in Africa* [`gupta2014`] — the direct regional antecedent: intra-continental
  African traffic detouring via Europe because local interconnection was missing. This census is
  that study's question asked of Pakistan.

### 3.2 Why we do not trust geolocation alone

A hop's country code comes from a geolocation lookup, and **those are unreliable for routers
specifically**:

- **Gharaibeh et al. (IMC 2017)**, *A look at router geolocation in public and commercial databases*
  [`gharaibeh:imc:2011`] — public and commercial databases disagree substantially on router
  locations. Router interfaces are exactly what a traceroute returns.

So a foreign country code is **never sufficient** on its own. It must be corroborated by RTT.

### 3.3 Why RTT is the corroborating evidence

- **Gueye et al. (2006)**, *Constraint-based geolocation of Internet hosts* [`gueye2006cbg`] —
  establishes the principle that a measured RTT places a hard upper bound on how far away a host
  can be. This is what the RTT gate implements: a hop claiming to be in Frankfurt at 3 ms is not in
  Frankfurt.
- **Bozkurt et al. (2018)**, *Dissecting latency in the Internet's fiber infrastructure*
  [`bozkurt:dissecting:2018`] — measures how far real fibre latency sits above the great-circle
  floor. This is why the thresholds are set well above the theoretical minimum rather than at it.
- **Robusto (1957)**, *The cosine-haversine formula* [`robusto:1957:cosine`] — geodesic distance for
  the speed-of-light floor itself.

### 3.4 The rules as implemented

From `04_path_tromboning/tromboning_sweep.py`. The **principles** are from the literature above; the
**specific millisecond values** are ours, calibrated to observed Pakistani RTTs.

| Constant | Value | Rule | Rationale |
|---|---|---|---|
| `FOREIGN_RTT_FLOOR` | 40 ms | A hop counts as foreign only if geolocated non-PK **and** RTT ≥ 40 ms | The RTT gate on the geolocation claim (§3.2, §3.3). Domestic PK RTT tops out around 40 ms, so a "foreign" hop below it is a mis-geolocation. |
| `ARTIFACT_ASN` | AS6327 | Excluded from foreign detection | Shaw. **Not a mis-geolocation** — the address genuinely is Shaw's, genuinely Canadian-registered, and Shaw's announcement is RPKI-valid. Nova is using live Shaw space on its own access network, so the hop is physically in Pakistan (336 observations, fastest 0.9 ms against a 109 ms floor to Vancouver — 121× below possible). The RTT gate catches **address squatting**, which no geolocation database could get right. See `trello/05_other_cybernet_prefixes.md` addendum. |
| `JUMP_THRESH` | 60 ms | A ≥ 60 ms step between consecutive hops = an international leg | PK→Singapore measures ~60–90 ms. A jump that size cannot be domestic. |
| `HIGH_RTT` | 70 ms | Any hop at ≥ 70 ms means the packet left PK | Above the domestic ceiling by a clear margin; PK→Europe measures ~100–130 ms. |
| `LOCAL_CEIL` | 45 ms | A path whose max RTT stays under this never left PK | The domestic ceiling plus headroom for queueing. |

**Per-hop RTTs are inflated and non-monotonic — do not read them as path cost.** A hop's RTT is
an independent round-trip from the probe to that router, produced by the router generating an ICMP
TTL-exceeded reply, which routers deprioritise. They are **not additive**, and they routinely exceed
the RTT to the destination beyond them. Measured example (Trello 04, 2026-09-02, PTCL Karachi →
EFU Life): the three Omantel hops read **194.7 / 177.3 / 169.5 ms** while the destination two hops
later reads **98.7 ms** and an ICMP ping to it reads **88.8 ms**.

Two consequences:

1. **The cost of a detour is the end-to-end difference against a comparable vantage**, not the peak
   hop RTT. For that PTCL case it is 88.8 − 20.4 ≈ **68 ms**, not 194 ms.
2. **The `any hop ≥ 70 ms` rule reads an inflated quantity.** A slow-answering domestic router can
   trip it without the packet leaving the country. This is a second false-positive mechanism
   alongside the one below, and Phase 2 must quantify both. Where a foreign hop is *named*
   (`trombone_hop`), the geolocation carries the claim and the inflated RTT only gates it — that
   path is sound. Where the RTT rule alone fires (`trombone_rtt`), it is exposed.

**Squatted foreign address space — the largest false-positive class, measured.** Pakistani ISPs
use foreign-registered address space on their own internal networks. Two confirmed cases: **Nova
uses Shaw (CA) space**, and **PTCL uses CHINANET Shandong (CN) space** (`182.45.51.22`, in
`182.32.0.0/12`, genuinely announced by AS4134 from China). The address is domestic; only the
internal path to it is slow.

The RTT gate does not catch this. From PTCL that hop sits at **42.3 ms** — just over the 40 ms
floor — so every trace through it scored as a detour to China. From Z-Com the same address answers
in **2.2 ms**, and the hop immediately before it (PTCL's own `10.253.8.39`) differs by **±0.4 ms**
in both traces. A packet cannot reach China and return in 0.4 ms.

**Measured impact on the June census:**

| Measure | As computed | Corrected |
|---|---|---|
| Overall detour rate | 11.0% | **9.1%** |
| PTCL Karachi | 38.4% | **16.1%** |
| PTCL → Brain Telecom | 97.6% | **0.0%** |
| Verdicts resting on this one address | — | **347 of 2,002 (17.3%)** |

**Required fix before Experiment 15 runs.** Raising the threshold would only lose real detours. The
multi-vantage design supplies the answer, but it must be applied as a **median over repeated
observations, never as a minimum.** A single anomalous packet is enough to mark a genuinely foreign
address as domestic: `192.33.4.12` (C-root) has a 143 ms median across 63 observations with one
3.4 ms sample, and `27.111.230.170` (Equinix Singapore) has a 95.5 ms median with one 3.5 ms sample.
A minimum-based rule clears both, wrongly.

```
DOMESTIC_OBSERVED = { ip : some vantage v has >= 3 observations of ip
                           AND median(rtt of ip from v) < 10 ms }
foreign(hop) := cc != PK  AND  rtt >= FOREIGN_RTT_FLOOR  AND  ip not in DOMESTIC_OBSERVED
```

One pre-pass over the hop table, no extra measurement. On the 4.1 census the two rules give the same
headline (8.9%), but the minimum rule admits 433 addresses against the median rule's 110, and the
extra 323 include the anycast roots and the Singapore peering address. **Use the median form.**

**Implication for probe design:** the rule needs repeat observations of the same hop address, so
Phase 2 must not collapse repeated traces before the pre-pass runs.

Full working: `trello/FINDING_address_squatting.md`. **Implemented** as
`15.1_data_plane/detector.py:build_domestic_observed()`, validated by
`15.1_data_plane/validate_against_41.py`.

**Combined effect of both corrections on the 4.1 census:** detour rate **11.0% to 8.6%**, and the
foreign-hop tier **811 to 422**, a 48% reduction.

**A false-positive class to separate out.** The RTT backstop fires on a large inter-hop jump. A
router that rate-limits its own ICMP/TCP replies produces exactly that signature without the packet
going anywhere — and it shows up as a spike on a *repeated final hop* (hop 8 and hop 9 are the same
IP, 3.0 ms then 211.7 ms). Real example, `122.129.80.227` from Nova. Traces whose only evidence is a
repeated-final-hop spike must be counted separately from those with a sustained multi-hop elevation
across distinct routers, which is the genuine detour signature.

**Implemented and validated.** `15.1_data_plane/detector.py:rate_limit_artifact()` fires when the
triggering jump falls between two **adjacent hops carrying the same address**: the router answered
twice and was slow the second time, so nothing moved. On the 4.1 archive it matches **71 of the
1,191 RTT-evidence detours**. Only 11 of those reached the destination ISP, so `reached` must not be
required, and 33 end on an RFC1918 address, which cannot be abroad at all.

Worked case, Nova to Brain Telecom: hop 8 is `203.128.7.75` at **3.0 ms**, hop 9 is the same address
at **211.7 ms**, verdict `rtt(jump=209,max=212)`.

**Verdicts:** `trombone_hop` (a foreign hop was seen), `trombone_rtt` (the foreign hop did not reply
or failed lookup, but the RTT profile proves the excursion), `local`, `inconclusive`. Inconclusive is
reported, never folded into local.

**The RTT backstop matters** because a hairpin is often invisible: the foreign hop returns `*` or has
no ASN/geo record. `trombone_rtt` catches those from the latency profile alone — 1,191 of 4.1's 2,002
tromboning verdicts came from this rule, so without it the count would be roughly 40% of the truth.

**Physics anchor:** Karachi↔Islamabad cannot round-trip below ~11 ms in fibre. Anything at 70 ms+ has
left the subcontinent whatever a registry claims.

---

## 4. What Exp 4.1's run found — and why it needs redoing

The 2026-06-27 run (`results/run_20260627_192918/census_20260627_192918.csv`) is a real census pass:
**18,260 traces, 7 probes, 696 of 747 blocks, 45 of 48 ISPs.** All figures below are value counts
over that file.

| Verdict | Count | Share |
|---|---|---|
| local | 15,451 | 84.6% |
| trombone (RTT backstop) | 1,191 | 6.5% |
| trombone (foreign hop seen) | 811 | 4.4% |
| inconclusive | 807 | 4.4% |
| **tromboning, combined** | **2,002** | **11.0%** |

Only **2,007 of 18,260** targets answered (11%), confirming the sparseness the method assumes.

**The spread**, grouping the same file by `company` and by `source` (ISPs with ≥100 traces):

- **By destination ISP:** 0.6% (LINKdotNET) to **64.5% (Bliss Communication)** — two orders of
  magnitude. Not a uniformly broken market; a handful of badly-connected operators.
- **By source vantage:** 4.0% (Nayatel Islamabad) to **46.3% (Cybernet Haripur)**, with **PTCL
  Karachi at 38.4%**. The source's transit matters as much as the destination — which is precisely
  what the source × destination matrix exists to separate.

### The flaw that motivates re-running

Counting rows per source in the same file:

| Source | Probes |
|---|---|
| zcom.lhe | 4,609 |
| nova.lhe | 4,264 |
| nayatel.isb | 3,204 |
| cybernet.khi | 2,084 |
| orbit.fsd | 2,012 |
| ptcl.khi | 1,525 |
| **cybernet.hrp** | **562** |

An 8× range. Cybernet Haripur's 46.3% rests on 562 traces against Z-Com's 4,609, and each source saw
a different, non-random subset of blocks — **so those rates are not comparable.** K also varied from
1 to 8 across blocks; only 594 of 696 got the full K=8.

4.1's numbers are suggestive, not quotable. The re-run exists to fix exactly this: **equal coverage
per source, every block, repeated rounds.**

---

## 5. The sampling method

**5.1 — The unit is the BGP prefix, not the address.** Routing decisions are made per prefix; every
address inside an announced block shares one route. The block is what we census. This is the
principled answer to "why these IPs and not others?"

**5.2 — Every announced block is kept.** All 747 probed; none ranked, pruned or sampled away. A
census claim needs completeness at block level. Reduction happens *inside* blocks, never across them.

**5.3 — Within a block, K evenly spread addresses.** Deterministic and reproducible across rounds. How large K must be is settled by measurement, not preference — see §5.5.
**Routing-complete, not host-complete** — we learn how the block is routed, not who lives in it.
Right trade, because the question is about routes. ~89% of targets stay silent; a hairpin still
appears *mid-path, before* the target, so detection survives a dark destination. Every trace carries
`reached=` so this is explicit.

**5.4 — Density comes free.** `density = responders / K` per block, the active-address weight. No
separate liveness campaign.

**5.5 — How large K has to be: measured, not assumed.**

The whole design rests on "every address in a block shares one route." The June run lets us test
that directly. Over the **1,758 (block, vantage) pairs that received the full K=8**, classifying each
probed address as detour / local / inconclusive:

| Outcome | Pairs | Share |
|---|---|---|
| All probed addresses agree | 1,396 | **79.4%** |
| Addresses disagree — the block is split | 351 | **20.0%** |
| No usable answer (all silent/inconclusive) | 11 | 0.6% |

**One block in five is genuinely split** — part of it routes abroad while the rest stays domestic.
So "the route to a block" is not always a well-defined object. Worked example: `122.129.94.0/24`
from Nova Lahore returns seven addresses local at 3.3–20.2 ms and one, `.199`, exiting via **Omantel
at 113.8 ms**. Contrast `203.128.7.0/24` from PTCL Karachi, where all eight exit via CHINANET at
~42 ms and the block is unambiguous.

The tempting inference — "so use a small K" — is wrong, and the same data shows why. On the 1,396
pairs where K=8 *is* unambiguous, a randomly chosen K=2 reproduces the K=8 verdict **98.6%** of the
time. K=2 therefore gets the **verdict** right and the **picture** wrong: with two samples there is
nothing to compare, so a split block is invisible and gets recorded as whatever the two picks
happened to be.

**Decision: K stays at 8.** A 20% split rate is too large to sample away, and split detection is
itself one of the more publishable things here. If the run has to shrink, drop a vantage or a
round — both are losses you can name and report. Cutting K is a loss you cannot see.

Caveat: the 20% is measured on the 1,758 pairs that got full K=8 out of an unbalanced run, so it is
an estimate on a subset. Phase 2 re-measures it on a clean, balanced sample before the census
commits.

**5.6 — Blocks that are not /24.**

725 of the 747 blocks are /24s. The other 22 are not, and they need explicit handling:

| Size | Blocks | Addresses each | Who holds them |
|---|---|---|---|
| /23 | 17 | 512 | CMPak LDI (12), Worldcall (2), Wise Communication, New Millennium |
| /22 | 4 | 1,024 | Gemnet (2), Connect Communications, Multinet |
| /19 | 1 | 8,192 | Connect Communications — `151.123.224.0/19` |

**Target positions generalise by formula, not by table.** For a prefix of size *S* and *K* targets:

```
target_i = network_address + int(i × S / (K + 1))     for i = 1 … K
```

For a /24 at K=8 this yields `.28 .56 .85 .113 .142 .170 .199 .227` — exactly the positions the June
run used, which confirms the formula is what the code already implements. It also never lands on the
network or broadcast address at either end, for any size, because i runs from 1 to K rather than 0
to K.

**The rule, stated simply: one target per 32 addresses — at every block size.**

| Prefix | Addresses | /24-equivalents | **K** | Density |
|---|---|---|---|---|
| /24 | 256 | 1 | **8** | 1 per 32 |
| /23 | 512 | 2 | **16** | 1 per 32 |
| /22 | 1,024 | 4 | **32** | 1 per 32 |
| /19 | 8,192 | 32 | **256** | 1 per 32 |

Worked example — `115.186.20.0/23` (Worldcall), K=16. The offsets run past 255, so the targets
cross into the second /24 of the prefix, which is the point:

```
115.186.20.30   .60   .90   .120   .150   .180   .210   .240
115.186.21.15   .45   .75   .105   .135   .165   .195   .225
```

**K scales with the block, it does not stay flat.** A flat K=8 would put the same 8 targets into a
/19 as into a /24 — 8 samples across 8,192 addresses, a 32× thinner sample, at exactly the size
where a block is *most* likely to be internally inhomogeneous. Since §5.5 measured 20% of /24s
splitting, a /19 sampled at /24 density is close to worthless for that question.

So sample at **constant density: 8 targets per /24-equivalent.**

| | Targets |
|---|---|
| Flat K=8 per block | 5,976 |
| **8 per /24-equivalent** | **6,456** (+8.0%) |

The correction costs 8% because only 22 blocks are affected. The breakdown: 725 /24s → 5,800
targets; 17 /23s → 272; 4 /22s → 128; and the single /19 → 256 targets, as many as 32 ordinary
blocks. That one prefix is 4% of the whole run and belongs to Connect Communications, already the
largest ISP in the population.

**Aggregate rates must be counted in /24-equivalents, not blocks.** Otherwise Connect's /19 counts
once — the same weight as somebody's lone /24 — despite being 8,192 addresses. The block universe is
747 prefixes but **807 /24-equivalents**, and the second number is the honest denominator for any
"share of address space" claim.

**Reporting caveat:** "this block is split" is not the same claim at /24 and at /19. A split /19
may simply mean two of its constituent /24s are routed differently, which is ordinary. Report the
split statistic at /24-equivalent granularity, and carry prefix length alongside every block-level
verdict so the two are never silently pooled.

**Provenance.** Prefix-as-unit and density are from **TASS** (Klick et al., IMC 2016
[`klick2016`]). We take the principle and **invert the rule**: TASS *drops* low-density prefixes to
shrink a full-space scan; we *keep every* prefix and reduce within. Shared: the topology-aware ethos,
the density measure, and the "good Internet citizen" footprint discipline. Not shared: the pruning
step. The within-block argument (one prefix = one route) is ours — `04.1/notes.md:49` currently
credits it to TASS and should be corrected.

---

## 6. Sizing the run

Measured in traceroutes, the unit that determines both footprint and elapsed time.

`traceroutes = 747 blocks × K × S vantages`

| Stage | Design | Traceroutes |
|---|---|---|
| Pilot, once | K=8, 150 stratified blocks, 6 vantages | 7,200 |
| Census round × 3 | 8 per /24-equivalent → 6,456 targets, 6 vantages | 38,736 each |
| **Total** | | **123,408** |

The census round is 6,456 targets rather than 5,976 because the 22 oversized blocks are sampled at
constant density (§5.6).

K is held at 8 for the reason in §5.5 — a 20% split rate cannot be sampled away. The levers for
shrinking the run, in the order they should be pulled:

1. **Drop a vantage.** Costs you one transit's view; you can say exactly which.
2. **Drop a round.** Costs you intermittency coverage; you report a narrower range.
3. **Never cut K.** Costs you split detection, silently, with no way to tell it happened.

Paced under RIPE's 100-concurrent cap with randomised inter-launch delay — the good-citizen
discipline TASS argues for, which also dodges throttling.

---

## 7. Experiment flow

```
Phase 1  Freeze sources        validate 7 probes, TCP/80 path visibility
   │                           exit: frozen source list
   ▼
Phase 2  Split-rate pilot      K=8, 150 stratified blocks, 6 vantages
   │                           exit: split rate confirmed on a balanced sample
   ▼
Phase 3  Census × 3 rounds     all 747 blocks, K from Phase 2,
   │                           EQUAL coverage per source
   │                           exit: 3 complete, balanced passes
   ▼
Phase 4  Detect                rules of §3, run locally
   ▼
Phase 5  Aggregate             per-ISP rates as ranges over rounds,
   │                           source × destination × transit matrix,
   │                           density-weighted Q2
   ▼
Phase 6  Write up findings
```

**Equal coverage per source is a hard requirement**, not a nice-to-have — it is the single thing that
made 4.1's cross-source numbers unusable. Enforce it in the sweeper: a round is not complete until
every source has probed every block.

---

## 8. What we might find

1. **A per-ISP trombone rate and its real spread.** 4.1 hints at 0.6%–64.5%; a balanced run makes it
   quotable. A few bad operators versus a uniformly broken market are different policy stories.
2. **Whether the source or the destination dominates.** 4.1's source range (4%–46%) is as wide as its
   destination range. If it is the *pair*, the fix is bilateral peering; if the destination, that
   ISP's transit contract. Different remedies.
3. **Who the hairpin transits through** — PTCL vs Transworld, per destination ISP.
4. **Which foreign exchange it surfaces at** — Equinix Singapore, DE-CIX. Pakistani domestic traffic
   at a named foreign IXP is concrete and quotable.
5. **How often a single block splits across two routes.** The June data already says **one in
   five** (§5.5) — measured nowhere else, for anywhere. A balanced run makes it a headline rather
   than a by-product, and it complicates "the route to a prefix" as a unit of analysis.
6. **How sparse small-ISP address space really is.** 4.1 says 11% of targets answer; the full density
   distribution is unpublished for Pakistan.
7. **Whether any trace touches PKIX or PIE — now answered twice.** The 7-day panel found 0 of
   222,944. Re-tested on the 4.1 census (131,075 hop observations, structurally different data):
   **also 0**, against **282 crossings of Equinix Singapore** by the same networks. The census
   should now aim to *quantify* this rather than establish it. Peering LANs: PKIX `100.128.0.0/24`,
   PIE `58.181.127.0/24`.
8. **Announced-but-dark blocks**, and the **18 licensed ISPs announcing nothing at all**.

Findings 5–8 exist only because the sweep is complete.

---

## 9. Limits, stated up front

- **Density is an active-address proxy, not traffic.** Atlas cannot see bytes; NAT and dynamic
  addressing distort counts. Report "% of active address space," never "% of traffic."
- **A single round is a snapshot** — quote per-ISP rates as a range across rounds, never one number.
- **Geolocation is used, but never alone.** Every foreign-hop verdict is gated by RTT (§3.2). The
  residual risk is a hop that is both mis-geolocated *and* genuinely slow.
- **Source-transit clustering is an assumption**, partly tested by carrying two Transworld sources.
- **The FLL roster includes a few large / LDI members** (Connect, CMPak LDI, Optix, Broadband Vision,
  Multinet, TES) — flagged in output, not silently dropped.
- **Block sizes are not uniform** — 22 of 747 are larger than /24, up to a /19.
- **Every run emits a human-readable `routes_*.txt`** alongside the CSV. No computed verdict ships
  without the paths to check it against.
