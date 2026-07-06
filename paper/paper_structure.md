# How to draft the paper — structure, merge/drop, gaps

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
