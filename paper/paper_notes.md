# Paper notes — planning, style templates, and consistency review

Combined from the four planning documents (2026-07-18); the canonical draft is
`paper_draft.tex`. Sections below are kept verbatim from the originals.

## Drafting plan: thesis, structure, merge/drop, gaps  
*(original: `paper_structure.md` — How to draft the paper — structure, merge/drop, gaps)*

Working plan for turning our experiments into one coherent paper. Companion to
`style_notes_ixp.md` (structural template) and `style_notes_p1.md` (register/voice).

## 1. The thesis (one sentence)

> **Pakistani domestic traffic needlessly leaves the country because PKIX is underused —
> a routing *choice*, not a connectivity limit — and this costs users measurable latency
> under normal conditions and measurable instability during a submarine-cable fault;
> local hosting + active PKIX peering fixes both.**

Everything in the paper is evidence for one of the three clauses: **it hairpins**, **it
costs (normal)**, **it costs (outage)** — and the throughline **"the local path exists
but is not chosen."** That last framing is lifted from the IXP paper's "wrong choice"
analysis and is our strongest rhetorical move.

## 2. Recommended narrative arc

1. **Motivation** — PKIX exists (4 sites, dozens of members) yet is invisible in routing
   (route server AS140307 in *zero* BGP paths). Why? Because (a) most PK content is hosted
   offshore, and (b) even domestic traffic hairpins abroad.
2. **Method** — the geo-IP-proof **RTT-physics tromboning detector** (our methodological
   contribution) + RIPE-Atlas vantages + TASS-style prefix census. *Validate the detector
   before quoting any rate.*
3. **The phenomenon at scale** — the national tromboning census: how much, from whom,
   through which LDI, to where.
4. **The cost, normal conditions** — the offshore/hairpin latency penalty is real, stable,
   and structural; and a domestic path usually exists but is not chosen.
5. **The cost, resilience** — a real cable cut degrades international paths (jitter) while
   domestic traffic is untouched.
6. **Implication** — local hosting + active PKIX peering.

## 3. Proposed section outline (experiment → section)

Name each experiment with an acronym and thread **method→results** per experiment (IXP-paper style).

| § | Section | Built from | Acronym |
|---|---|---|---|
| 1 | Introduction (thesis, PKIX context, contributions) | 02 framing + BGP finding | — |
| 2 | Related work | IXP-value (Di Bartolomeo), African detours (Gupta PAM'14), TASS, IXP anatomy | — |
| 3 | Data & vantages | probe roster, target sets | — |
| 4 | Method: RTT-physics tromboning detector **+ Validation** | 04 detector, Shaw/Cogent fixes | **DETECT** |
| 5 | Where PK content lives (hosting census) | **01 + 1.4** (+1.1/1.2 as support) | **HOST** |
| 6 | Tromboning at scale (national census) | **04 + 4.1** | **TROMB** |
| 7 | The latency cost & the unused local path | **03 + 3.1** (+04-RQ4) | **PENALTY** |
| 8 | The resilience cost (cable cut) | **06** | **CUT** |
| 9 | Discussion (forex, policy, PKIX sets) | 02 sets + synthesis | — |
| 10 | Conclusion & future work | — | — |

## 4. Merge / demote / drop

**MERGE (into the sections above):**
- **HOST = 01 + 1.4** — same hosting census; 1.4 adds the clean CDN/Abroad/PK taxonomy and
  the Transworld hairpin-to-gov result. One section, not two.
- **TROMB = 04 + 4.1** — 04 is the *validated method on one ISP* (Worldcall); 4.1 is the
  *national census*. Present as method → scale, one section.
- **PENALTY = 03 + 3.1** — the measured offshore penalty (stable, structural) plus the
  transit/peering structure that produces it.

**DEMOTE to a paragraph (no standalone section):**
- **1.1 (DNS/GeoDNS)** → one methods sentence: "central resolution is representative for
  ~92% of sites, so the hosting census stands."
- **1.2 (CDN caches)** → 1–2 sentences inside HOST: big global content is reached
  *regionally*, not from inside PK (only Cloudflare/X local, only on Nayatel).
- **1.3 (Nayatel)** → the illustrative "multi-homed exception" example inside PENALTY.

**DROP from the paper (keep in the repo):**
- **02's probe-deployment plan** — operational, not a result. The **Set 1/2/3 framework**
  survives, but only as *framing* in the Intro and a *lens* in Discussion (we have not yet
  measured every ISP into a set, so don't over-claim it).

## 5. Foreground the method contribution

The **RTT-physics detector** is what makes this novel vs the IXP paper (they trust ASN
country + known IXP peering IPs; we prove tromboning by RTT physics, which survives the
Shaw/Cogent geo-IP lies and invisible foreign hops). Give it:
- its own **Method** subsection (the three RTT rules + the artifact exclusions), and
- a short **Validation** subsection *before* any rate (53/53 false positives → 16/52 clean
  on Worldcall; the geo-IP-vs-RTT disagreement cases). Validation-before-evaluation is the
  IMC norm (see `style_notes_p1.md`).

## 6. Figure plan (CDF-first, IXP-paper style)

1. **HOST**: stacked bar — CDN/Abroad/PK by sector (gov/edu/news/banking/…).
2. **DETECT**: the geo-IP-vs-RTT disagreement table/example (validation).
3. **TROMB (money figure)**: **CDF of RTT, local vs hairpinned** paths.
4. **TROMB**: bar — trombone rate **per source ISP** (the "source dominates" result).
5. **TROMB**: bar — **% of trombones by transit (PTCL/Transworld) and exit country** (the
   IXP paper's "% foreign AS traversed" analog).
6. **PENALTY**: the "local-path-exists-but-unused" case — same Worldcall IP local from PTCL
   vs trombone from Transworld (04-RQ4); + the offshore-penalty CDF from Exp 03.
7. **CUT**: RTT-over-time (PKT) from `rtt_timeseries.ipynb` + the jitter/impact bars
   (`outage_impact.md`).

## 7. Gaps to close before submission (be honest, then fix)

- **TROMB is a single snapshot** → run **repeat census rounds** to quote rates as ranges
  (intermittency is real). *Highest priority — it's the centerpiece.*
- **CUT has no pre-event baseline** → capture a **normal-day baseline** now (outage over)
  from the same 14 probes / 18 targets, so the resilience delta is vs *normal*, not vs
  *recovered*. Cheap and strengthens §8 a lot.
- **Forex/cost (deliverable #1)** is not yet measured — either scope it out honestly
  ("we quantify latency/resilience, not bytes; RIPE Atlas can't see volume") or add a
  rough active-address-weighted estimate and label it clearly as a proxy.
- **RQ1/RQ2** — 4.1's "source ISP dominates" and "82% intra-block" partially answer
  "do same-ISP customers get the same service"; frame them as such rather than as separate
  open questions.
- **Figures** — the CDFs (Fig 3, 6) don't exist yet; generate from Exp 03/04/4.1 data.

## 8. Venue & length

- **Best fit:** a PAM / IMC-short / IEEE-ISCC-style measurement paper (**8–12 pp**), census
  as the centerpiece — same venue family as our two template papers.
- **If we must split:** (a) *"A national census of domestic-traffic hairpinning in
  Pakistan"* (DETECT+HOST+TROMB+PENALTY) as the main paper; (b) a short note on the
  **submarine-outage resilience** (CUT). But one coherent paper tells the stronger story —
  prefer that for the first output.

## 9. What NOT to do

- Don't give every mini-experiment (1.1/1.2/1.3) its own section — reviewers read that as
  padding. Fold them in as evidence.
- Don't quote the census rate as a single number without the range/caveat once repeat
  rounds are in.
- Don't lead with rates before the detector is validated.
- Don't over-claim the Set 1/2/3 classification — we measured the *phenomenon*, not yet a
  full per-ISP set assignment.

---

## Experiment consistency review (what drifted across experiments)  
*(original: `experiment_consistency.md` — Are our experiments uniformly designed? (a strict review))*

Honest assessment of how consistently we ran things, so the paper's Method section can be
*one* framework rather than ten ad-hoc setups. Companion to `paper_structure.md`.

## The design matrix (what actually varied)

| Exp | Vantages | Targets / selection | Stack + protocol | RTT def. | Metrics | Cadence | Classifier |
|---|---|---|---|---|---|---|---|
| **01** hosting | 5 probes | 100 **curated** websites | requests, **ICMP** Paris | single-packet 1st reply (noisy) | hops, RTT, ASN path, serving-loc | snapshot | geo-IP + serving-location |
| **1.1** DNS | 5 | 103 curated | requests, DNS (probe resolver) | — | resolved IP/ISP | snapshot | GeoDNS diff |
| **1.2** CDN | **3** | content services | requests, ping | ping | RTT tier | snapshot | RTT threshold |
| **1.4** hosting | Pass A central + Pass B **1 probe** (64078) | **PK100** (diff. curation) | cousteau, traceroute | — | hosting class + hairpin | snapshot | ASN/geo + RTT |
| **03** longitudinal | **8** | 10 fixed sites | requests, **ICMP** Paris + ping | ping min-of-N | RTT, path-change, loss | **15 min / 24–48 h** | path-change |
| **3.1** peering | PTCL probe → probes | targeted | ptcl\_peering.py | RTT | peering y/n | snapshot | path inspection |
| **04** Worldcall | 1 (Nova) +RQ4 4 | Worldcall IPs, **RIPEstat** prefixes → live-IP sweep | cousteau/sagan, **TCP/80** Paris | max-hop RTT | trombone verdict | snapshot | **RTT-physics** |
| **4.1** census | **7** | 747 blocks × 8 IPs, **RIPEstat** + spread | cousteau/sagan, **TCP/80** Paris | max-hop RTT | trombone verdict | snapshot | RTT-physics |
| **06** outage | **14** | 18 websites (6/6/6), liveness-checked | cousteau/sagan, **ICMP** Paris + ping, periodic | ping avg | **RTT, jitter, hops, loss** | 15 min / 12 h | RTT-physics + impact |
| *07 (planned)* | 14 | ~30 mixed + trombone IPs | cousteau, trace+ping periodic | ping + hop | RTT, jitter, hops, loss | 1 trace/h + 1 ping/30 min / **20 d** | RTT-physics |

## What drifts (and whether it's fixable or inherent)

**Fixable — these hurt cross-experiment comparison and should be standardised:**
1. **Vantage set changes every time** (5 → 3 → 8 → 1 → 7 → 14, never the same). Partly forced
   (probes go offline), but not *planned*. → Fix: declare one **canonical roster** (the 14),
   report per-experiment availability, and prefer the full set.
2. **Traceroute protocol is inconsistent** — ICMP (01, 03, 06) vs TCP/80 (04, 4.1). We *proved*
   ICMP undercounts (Exp 04: 12/52 responded on ICMP) yet Exp 06 used ICMP again. → Fix:
   standardise on **TCP/80 Paris** for path/reachability (ping for clean end-to-end RTT).
3. **RTT is defined three different ways** — single-packet first reply (01, noisy), ping
   average/min-of-N (03, 06), max-hop RTT (04, 4.1). These are not comparable. → Fix: one
   definition — **ping min-of-N for end-to-end RTT**, max-hop RTT only as the detector's input.
4. **The metric set is inconsistent** — only Exp 06 carries the full **RTT / hop-count / jitter
   / loss** set (the IXP-paper KPIs); 01/03/4.1 lack jitter and loss. → Fix: carry all four
   everywhere (Exp 07 does).
5. **Website selection is not reproducible** — hand-curated in 01/1.4/03 (two *different* 100s).
   Only the IP-space selection (RIPEstat + 8-spread, TASS-justified) is principled. → Fix:
   a reproducible website pipeline (Tranco → filter .pk → resolve → Team Cymru), which is
   exactly what the team member drafted.
6. **Hosting uses a weaker classifier than tromboning** — geo-IP + serving-location (01/1.4) vs
   RTT-physics (04+). → Acceptable *if* labelled, but note hosting is DNS/geo, not RTT-proven.

**Inherent / acceptable — don't over-correct:**
- **Hosting is a snapshot property** (where a domain resolves) — a one-time DNS+geo census is fine.
- **The census's value is completeness** (every /24) — a single pass is defensible; Exp 4.2 adds
  repeat rounds for intermittency.
- Some **probe drift is forced** by availability.

## The root cause (state it plainly)

The experiments were **built incrementally as the method matured**: we started hand-rolling the
RIPE REST API with ICMP traceroute, single-packet RTT, and geo-IP classification (01–03), then
moved to cousteau/sagan + TCP/80 Paris + the RTT-physics detector (04 onward). That is a normal
research trajectory, **but the paper must not present it as one uniform campaign.** Present the
*mature* framework and the results measured under it; use the early experiments as
method-development and preliminary evidence.

## How to structure the paper given this

1. **One canonical Method section** that fixes: the 14-probe roster (with availability windows),
   **two** reproducible target-selection methods (website-population via Tranco+CISA;
   address-space via RIPEstat + 8-spread), **TCP/80 Paris + ping**, the **four KPIs**, and the
   **RTT-physics detector**. Everything else is an instance of this.
2. **Reposition each experiment by role**, not chronology:
   - **Method / validation:** Exp 04 (detector on Worldcall, 53/53→16/52) — folds into Method.
   - **Primary results:** **Exp 4.1** (complete census — unique value is coverage) and **Exp 07**
     (the only *uniform* longitudinal dataset — per-ISP KPI distributions, diurnal/weekly).
   - **Hosting:** Exp 01 + 1.4 as a snapshot census (adopt the Tranco pipeline for reproducibility).
   - **Preliminary → superseded:** Exp 03's penalty result is the **pilot** that Exp 07 confirms
     and extends at scale; present it as motivation, quote final numbers from Exp 07.
   - **Event study:** Exp 06 (the SMW5 outage) — keep; note the baseline gap Exp 07 closes.
   - **Support:** 1.1, 1.2, 1.3, 3.1 as paragraphs.
3. **Lean on Exp 07 for the KPI table** (RTT/hops/jitter/loss per ISP) because it is the only
   experiment that carries all four uniformly across all 14 vantages — the earlier snapshots
   corroborate but don't need re-running.

## Action items
- [ ] Standardise the Method framework as above; write it once.
- [ ] Adopt the reproducible **Tranco** website pipeline (replaces two curated 100s).
- [ ] Make **Exp 07** carry the full four-KPI set from all 14 probes (it is designed to).
- [ ] Re-quote Exp 03's penalty from Exp 07's uniform data once it runs; keep 03 as the pilot.
- [ ] In every results section, label which framework version produced it (legacy ICMP/geo-IP
      vs mature TCP/RTT-physics) so numbers are not silently compared across methods.

---

## Style template A: Di Bartolomeo ISCC'15 (structural model)  
*(original: `style_notes_ixp.md` — Writing-style notes — "Is It Really Worth to Peer At IXPs?" (our closest template))*

**Paper:** Di Bartolomeo, Di Battista, di Lallo, Squarcella — *"Is It Really Worth to
Peer At IXPs? A Comparative Study"*, **IEEE ISCC 2015** (6 pages, short-paper format).

**Why this is our best structural model** (more than p1/Sanchez): it does *exactly our
kind of study* — RIPE Atlas probes **inside one country**, measuring to **in-country
targets**, to ask **"does the IXP keep local traffic local, and is it better?"** Same
tool, same national framing, same metrics, even the **same caveats**. Match this shape.

## 1. Structure — organised BY NAMED EXPERIMENT
`Title → Abstract → I Introduction → II Related Work → III Methodology → IV Analysis →
V Conclusions & Future Work → References`.
- **Two experiments, each given an acronym** — **CIS** (Crucial Internet Services) and
  **SBA** (Selective BGP Announcements) — and **each appears twice**: once in
  Methodology (III.A, III.B) and once in Analysis (IV.A, IV.B). Method and results are
  threaded per-experiment, not globally. *We should name our experiments and mirror them
  method→results the same way.*
- Short-paper length (6 pp), no separate Data/Validation sections (folded into
  Methodology). Contrast with p1/IMC's 15 pp with standalone Validation.

## 2. The two experiments (and their analogues in our work)
- **CIS** = pick two target sets — **CRITICAL** (46 banking/gov/health/webmail sites) and
  **VISITED** (top-100 Alexa) — resolve each to an in-country IP, traceroute from all
  national probes, and **flag whether the path traverses the IXP** (using the IXP's known
  peering IPs). Report rtt, hop count, and **% of paths that cross a foreign AS**.
  → *Directly our Exp 01 + 1.4 (hosting/QoS to crucial + popular PK sites) and our
  tromboning locality analysis.* Their "crucial vs popular" split = our sector split.
- **SBA** = partner with 3 ISPs, have them announce a reserved prefix selectively
  (`UPSTREAM` / `IXP` / `MIX` / `NAMEX` / `ALL`) so the **same probe-target pair** is
  measured both via-IXP and via-upstream, then compare. The clean controlled comparison.
  → *We can't control ISP BGP, but our **natural-experiment** substitutes are Exp 3.1
  (PTCL↔Transworld probe-to-probe) and Exp 04 RQ4 (the same Worldcall IP is local from
  PTCL but trombones from Transworld) — the same "same endpoint, two paths" logic.*

## 3. The metrics and the figure language
- **KPIs:** round-trip time, hop count, packet loss, jitter — *with vs without the IXP*.
- **Every result is a CDF** ("cumulated fraction of probes" on Y, the metric on X), two
  curves per plot (IXP vs upstream). This is THE figure type for this genre — e.g.
  *"70% of IXP probes have rtt ≤ 30 ms vs only 20% of upstream probes."*
  → *We should ship CDFs of RTT: local vs hairpinned, and per-transit (PTCL vs
  Transworld). We already have the data (Exp 03/04/4.1).*
- A second figure type: **"% of paths traversing foreign ASes"** bar chart, per AS,
  IXP vs upstream (their Fig 4). → *This is exactly our per-transit tromboning bar
  (China/US/SG exits via PTCL/Transworld).*
- **Per-upstream restriction:** they re-plot the same CDF restricted to one upstream
  (AS174 Cogent, AS3356 Level3) to show which upstream drives the penalty. → *We do the
  per-transit version (restrict to PTCL, to Transworld).*

## 4. Framing & voice
- **Locality as a sovereignty/security issue**, stated plainly: do citizens' packets to
  critical services *"remain inside the country"* or *"cross ISPs of different countries
  or continents"*. → *This is our headline framing too — use it in the Introduction.*
- **First-person plural, past tense for what was done** ("We asked each ISP to
  announce…", "We computed four values…"), present tense for standing claims.
- **Motivated by a real event:** the paper opens from *"recent news of major ISPs
  de-peering"*. → *Our live hook is the SMW5 cable cut (Exp 06) and PKIX's documented
  underuse.*
- Cite the **African-IXP-detour paper** (Gupta et al., *"Peering at the Internet's
  frontier"*, PAM 2014) — African ISPs not peering locally, so local traffic **detours
  through Europe**. That is *literally our tromboning result*; it must be in our Related
  Work as the closest prior finding.

## 5. Honesty — the caveats they state (we share them)
Right after the first positive result they write *"such results must be considered very
carefully, because of the following three reasons"* and list:
1. the two CDFs are **disjoint probe sets** (a probe either uses the IXP or not);
2. **rtt/hop count refer to the last hop that replied, which is often not the target**
   (*40 of 53*, *59 of 94*) — **the identical caveat to ours** (`reached=True` vs the
   spread target IP);
3. a **router may reply from a non-peering interface**, misclassifying the path.
→ *State ours the same way, inline, right where the number is — the target-vs-last-hop
caveat, intermittency/single-snapshot, and geo-IP unreliability (our RTT-physics fix).*

## 6. The killer analysis to copy — "wrong path" choice
In the `ALL` phase (both routes available) they measure how many probes took the
**suboptimal** path — quantifying that a real, avoidable performance loss is being chosen.
→ *This is our central thesis in their language: **a local/PKIX path exists but is not
chosen.** Our Exp 04 RQ4 (PTCL local vs Transworld trombone to the same IP) is exactly
this. Frame our tromboning census as "how often the domestic path exists but is not
taken."*

## 7. What to borrow vs where we go further
- **Borrow:** named-experiment structure, CDF figures, foreign-AS bar chart, locality
  framing, inline caveats, per-transit restriction, "wrong choice" analysis.
- **We go further than them:** (a) a **complete block-level census** of every small ISP
  (they hand-pick sites) via TASS-style prefix sampling; (b) a **geo-IP-proof RTT-physics
  detector** (they trust ASN country + IXP peering IPs); (c) a **submarine-outage /
  resilience** measurement (Exp 06) they don't have; (d) **hosting census** (where content
  physically lives), which they only touch via target-IP-in-country filtering.

---

## Style template B: Sanchez IMC'14 (register and voice)  
*(original: `style_notes_p1.md` — Writing-style notes — how "p1" is written (for our paper))*

**Paper:** Sanchez, Bustamante, Krishnamurthy, Willinger, Smaragdakis, Erman —
*"Inter-Domain Traffic Estimation for the Outsider"*, **ACM IMC 2014**.
(15 pages, ~11,800 words, 84 references.) One of our Exp 03 source papers.

Notes on *how it is written* — structure, voice, wording, evidence, references — so we
can match the register when we write ours.

## 1. Overall structure (IMC measurement-paper template)
`Title → Abstract → 1 Introduction → 2 Related Work → 3–4 Methodology (the named
approach) → 5 Data → 6 Validation → 7 Evaluation/Results → 8 Discussion → 9 Conclusions
& Future Work → References`.
- **Method and evaluation are separate sections** (build the technique first, then
  prove it). Data gets its own short section (what, how much, provenance).
- **Validation before Evaluation:** they first show the method agrees with ground
  truth, *then* apply it. We should do the same — establish the detector is right
  (our RTT-physics validation) before quoting rates.

## 2. Abstract anatomy (copy this 5-move shape)
1. **Why it matters** (broad): *"Characterizing the flow of Internet traffic is
   important in a wide range of contexts, from network engineering … to … business
   relationships."*
2. **The impediment/gap:** *"the nearly impossible task of collecting large-scale …
   data has severely constrained …"*
3. **"In this paper, we introduce …"** — one-sentence statement of the contribution.
4. **The key insight, plainly:** *"the popularity of a route … can serve as an
   informative proxy for the volume of traffic it carries."*
5. **Name it + validate it with a number:** they brand it **"Network Syntax"** and
   close with hard evidence: *"strong correlation (r² up to 0.9) …"*.
→ For us: matter → (PK traffic-data / vantage gap) → "we measure tromboning/hosting
across PK from RIPE Atlas" → the insight (RTT physics beats geo-IP; route popularity /
hairpin detection) → a headline number (e.g. "X% of small-ISP prefixes hairpin abroad").

## 3. Introduction pattern
- Opens with the **research area and its history**, prior work **bracket-cited in
  clusters** (`[10, 17, 48]`), then pivots on *"There is, however, a growing consensus
  on the need to shift focus …"* — i.e. *established field → the missing piece → our
  angle*.
- Names the **central obstacle** ("The major impediment … has been the scarcity of
  publicly available traffic data") and frames the paper as removing it.
- Contributions are stated as what they *do*, not adjectives.

## 4. Voice, tense, register
- **First-person plural throughout:** "We introduce…", "We apply…", "We demonstrated…".
- **Present tense** for the method/claims ("Network Syntax applies structural
  analysis…"); **past tense** for the experiments done ("We evaluated four … datasets").
- **Formal but plain** — short declarative sentences, minimal adverbs, no hype words.
  Precision over flourish.
- **Analogy as a teaching device:** they anchor an abstract method in a familiar
  domain (*urban-planning "Space Syntax" → city grids and traffic*). A single, carried-
  through analogy makes a method memorable — worth one good analogy in ours.

## 5. Evidence & honesty
- **Quantitative everywhere** — correlations (r²), percentages, "two months of data
  collected two years apart", "a Tier-1 ISP and a large IXP".
- **Ground-truth validation is the backbone** — the claim is only as strong as the
  agreement with real data; they lead with it.
- **Explicit hedging, stated as a judgement call:** *"we acknowledge that order of
  magnitude is a coarse approximation, [but] we argue this is a valuable …"* — name the
  limitation, then justify why the result still matters. (This matches how we write our
  caveats — do it in the paper too, don't hide them.)

## 6. Figures / tables
- Figures carry the argument (distributions, correlation plots, percentage bars);
  prose refers to them by number ("as we show in Section 7.1 …"). Every quantitative
  claim is backed by a figure/table, not asserted.

## 7. References (ACM numbered style)
- **Numbered `[n]`**, dense (84 refs), cited in clusters.
- Entry format: `Author, A., and Author, B. Title. In Proc. of VENUE (Year).`
  e.g. *"Ager, B., Chatzis, N., … Anatomy of a large european IXP. In Proc. of ACM
  SIGCOMM (2012)."*
- **Datasets/tools cited as references with URLs** (RouteViews, RIPE RIS, PeeringDB,
  PCH). → We should cite RIPE Atlas, RIPEstat, Team Cymru, CAIDA pfx2as, ip-api, and the
  TASS paper this way.

## 8. Actionable checklist for our paper
- [ ] Abstract = the 5 moves above, ending on a headline number.
- [ ] Separate **Method** and **Evaluation**; put **Validation** (detector correctness:
      RTT gate vs geo-IP, the Shaw/Cogent false-positive fixes) *before* the rates.
- [ ] First-person "we"; present for method, past for measurements.
- [ ] One carried-through framing (tromboning / hairpinning / "the local path exists but
      is not used").
- [ ] Every number → a figure/table; state caveats openly and justify relevance.
- [ ] Cite tools & datasets as numbered references with URLs; cluster related cites.
- [ ] Aim IMC-length (~12–15 pp) with the standard section order.

---
