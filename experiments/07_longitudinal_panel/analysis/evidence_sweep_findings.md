# Evidence-based reclassification sweep: findings log

**Trigger:** Dr. Saqib's review comment questioning whether RTT alone (in either direction) is
sufficient evidence to classify a site's location or a trace's tromboning verdict. Plan document:
`evidence_reclassification_plan.md`. This file tracks the actual numbers found, how each was
derived, and what still needs deciding, kept up to date as the sweep progresses.

**Do not edit `running_draft.tex`** (the uploaded reference copy of the paper) directly from this
work; changes get folded into `main_draft.tex` / `main_draft_polished.tex` separately, once agreed.

---

## 1. Site-level classification (Pakistani / CDN / Abroad)

**Question:** does the 20ms RTT-threshold site reclassification (geo.py) survive requiring
non-RTT corroboration?

**Method:** built `evidence_scan.py` — for every one of the 60 unicast sites (40 Pakistan-design +
20 Abroad-design), pulled a *fresh* Team Cymru ASN/country lookup on the current resolved IP
(independent of the original build-time classification), the traceroute panel's own `exit_cc`
aggregated per site (how many rounds show a confirmed foreign hop vs RTT-only vs no signal), and
geo-IP city. `apply_decision_rules.py` then requires: non-PK ASN **and** (a confirmed foreign hop
**or** a foreign geo-IP city) before reclassifying Pakistani→Abroad; PK ASN with no corroboration
before relocating Abroad→Pakistan.

**Result:** all 6 existing corrections (3 reclassified Pakistani→Abroad, 3 relocated by
multilateration) survive unchanged. No new site needs reclassifying; no site needs an Inconclusive
label. Output: `evidence_scan.csv`, `targets_corrected_v2.csv`.

**Caveat found:** `phf.gop.pk` clears the bar on ASN + geo-IP agreement only — its traceroute
hop-level evidence is thin (1 confirmed foreign hop out of 2,236 rounds). Worth stating explicitly
in the paper rather than letting the tier label imply hop-level proof.

**Saqib's Oman/UAE-proximity concern (his 2nd point):** checked directly — no Abroad-labelled site
in the panel has a low enough RTT for this to be ambiguous. Lowest RTT among all 20 Abroad-design
sites is 78.4ms (`uvas.edu.pk`), far from anything Karachi-to-Gulf-plausible. Not an issue in this
data, though the underlying code gap (the multilateration-relocation branch in `geo.py` doesn't
gate on original class) is real and worth hardening defensively even though nothing currently hits
it — confirmed via direct check: zero Abroad-design rows have ever been touched by that branch.

---

## 2. RQ1 — headline tromboning rate

**Question:** how much of the 15.1% headline rate rests on a confirmed foreign hop vs RTT alone?

**Method:** the trace-level detector (`census_sweep.classify`, reused live for the whole panel)
already computes `exit_cc` per round: a real country code only when a hop resolves to a genuine
non-PK, non-artifact ASN **and** that hop's own RTT sits in a plausible range (40–500ms, the
existing `FOREIGN_RTT_FLOOR`/`QUEUE_CEIL`). The old rule (v1) also allowed RTT alone (a 60ms+ hop
jump or any hop ≥70ms) to set `tromboned=True` with no foreign hop ever found — that's the OR
branch removed per instruction ("tromboning criteria should be foreign IP hop visible + high
RTT"). Reproduced the paper's exact 75,600-trace Pakistani-class baseline first (confirmed exact
match, 15.14%) before comparing.

**Result:**

| | v1 (RTT threshold) | v2 (confirmed foreign hop) |
|---|--:|--:|
| Trombone rate | 15.14% | **7.50%** |
| Trombone traces | 11,449 | 5,667 |
| Moved to "no evidence" | — | 5,782 (7.65% of all PK traces) |

Per-ISP and per-sector breakdowns recomputed too (see conversation log / `apply_decision_rules.py`
output); notable changes: Nayatel and Transworld drop to exactly 0.0% confirmed (were 9.7%, 3.2%,
entirely RTT-only); PTCL's within-ISP ordering flips (Mianwali 46.4%→15.3%, Karachi 27.0%→19.2%,
Karachi becomes the worse vantage under confirmed evidence). Exit-country attribution (Singapore/
US/Hong Kong counts) is unaffected — always based on confirmed hops already.

---

## 3. RQ3 — pair-level flapping / local / hairpinned split

**Question:** does "83% of ever-trombone pairs are also served locally" hold under the same
standard, and were the paper's own 444/211/40/193 numbers even internally consistent?

**Reconciliation (three sources disagreed before this):** the analysis notebook's exploratory
cell used loose ≤5%/≥95% thresholds unfiltered by round count (518 pairs, 380/63/75); the paper
cites 444/211/40/193; `evidence_rq3_flapping.md` (an earlier, separate investigation, dated
~20 Jul) used 233 "ever-trombone" pairs. All three reconcile exactly once the documented ≥50-round
filter is applied (518→444) and **exact 0%/100% thresholds** are used instead of 5%/95%
(211/40/193 exactly, and 40+193=233, matching the evidence file). The notebook cell was simply
stale/exploratory, not the real pipeline.

**Rebuilt under v2 (same confirmed-hop standard as RQ1), three layers:**

| Standard | Local | Hairpinned | Flapping |
|---|--:|--:|--:|
| v1 (RTT threshold, current paper) | 211 (48%) | 40 (9%) | 193 (43%) |
| v2 (confirmed hop, per round) | 387 (87.2%) | 19 (4.3%) | 38 (8.6%) |
| v2 + confirmed AS-path change (path-verified) | — | — | **5 (1.1%)** |

Movement detail: of the old 193 flapping pairs, 163 turn out to have zero confirmed foreign hops
all week (pure noise, actually persistently local); of the old 40 persistently-hairpinned pairs,
13 also drop to local — every trombone verdict on them, all week, was unconfirmed.

**Path-confirmation method (closing the last gap):** reused the exact test already established in
`evidence_rq3_flapping.md` / `route_changes.md`'s Mechanics section — AS-path differs between two
rounds **and** the difference isn't explainable by hops merely failing to respond (one round's
responding-hop AS list is not a subsequence/projection of the other's). Built
`confirm_v2_flapping.py`, run against `.paths_series.json` (raw per-round hop/AS sequences, not
re-derived, reused as-is). Result: **only 5 of 38 v2-flapping pairs have >=1 genuine, path-
confirmed transition; 33 are visibility artifacts even after already requiring a confirmed hop.**
`tevta.gop.pk` is the strongest example, confirmed independently from 4 different ISP vantages
(PTCL, TES, Cybernet, Fasttel).

**Open framing decision (not yet resolved):** cite 8.6% (hop-confirmed, matches RQ1's standard) or
1.1% (path-confirmed, the strictest defensible number) as the paper's flapping/choice claim. Not
decided yet, flagged to the user, no answer received as of this writing.

---

## 4. RQ2 — causal within-pair cost

**Method:** reproduced the paper's own ping-to-trace matching (`merge_asof`, nearest within
40min, exact match on probe+target), then aggregated per pair to compare median ping RTT during
trombone rounds vs local rounds, requiring both states present. v1 reproduction landed close to
the paper's cited numbers (118 pairs, +0.75/+16.63ms vs paper's 121, +0.5/+15.3ms — small,
unchased methodology difference, not a real discrepancy).

**Result:**

| | v1 | v2 (confirmed hop) |
|---|--:|--:|
| Pairs with both states | 118 | **20** |
| Median delta | +0.75ms | +0.67ms |
| Mean delta | +16.63ms | **+0.89ms** |

The "cheap median, expensive tail" framing (used in the paper to argue for an *exposure* rather
than *latency* story) mostly disappears under confirmed evidence — mean collapses to near the
median. That specific paragraph in RQ2 needs rewriting, not just renumbering.

---

## 5. Sample-size correction: dropping the two Gerry's/S.B Link sites

**Context:** `toptop.net` and `youth.cn` were found earlier this session to have entered the
sample via a manual "ASN lookup" path (scanning a Pakistani ISP's — Gerry's/S.B Link Network's —
address space and pulling in whatever domains resolved there at the time), attributed to a
reseller relationship rather than genuine Pakistani hosting (Gerry's/S.B Link peers directly with
their real host, Meteverse Limited; see conversation log for the full BGP-neighbour finding). The
uploaded `running_draft.tex` reflects a decision to drop these two entirely (not relabel Abroad):
its sample-allocation table shows Commercial Facilities PK dropping by exactly 2 (24→22), total
100→98, matching removing exactly these two sites and nothing else.

**Corrected totals (computed directly, not yet in any paper draft):**

| | Full 100-site panel | After dropping toptop.net + youth.cn |
|---|--:|--:|
| Raw traces | 222,944 | **218,480** |
| Cleaned traces | 204,384 | **200,292** |
| Raw pings | 445,749 | **436,828** |
| Cleaned pings | 313,276 | **305,116** |
| Site classification | 37 PK / 40 CDN / 23 Abroad | **37 PK / 40 CDN / 21 Abroad** (=98) |
| Ratio intercity pairs (Fig. ratio-cdf) | 447 | **421** (Abroad 273→247) |

Note: RQ1/RQ2/RQ3's Pakistani-class-only numbers above (§2–4) are **unaffected** by this drop —
these two sites were never counted as Pakistani in the corrected classification either way, so
removing them doesn't change who's in the Pakistani-class denominator. Only totals that sum across
all three classes, or the Abroad-class side specifically, need the correction in this section.

---

## 6. Floor sensitivity: FOREIGN_RTT_FLOOR at 20ms vs 40ms

**Question (Sameera's point):** the current 40ms floor may be too conservative — a genuinely
foreign but nearby hop (e.g. an Oman landing point from a Karachi vantage) could plausibly answer
faster than 40ms and be wrongly excluded from "confirmed foreign," undercounting real tromboning.

**Method:** the panel CSV's `exit_cc` field only records the verdict already computed under the
original 40ms floor — it doesn't preserve per-hop RTT, so a different floor can't be tested by
relabeling existing data. Reprocessed directly from the raw archive (`raw_a_20260718_201113.json.gz`,
full per-hop, per-packet RTT) using the *exact* `classify()` logic from `census_sweep.py`,
parameterized by `FOREIGN_RTT_FLOOR`, comparing 20ms vs 40ms on identical input.

**Hop-country lookup gap found and fixed along the way:** the existing `hop_annotations.csv`
(906 unique hop IPs) only has a country code resolved for 61 of them — everything RDAP-registry-
only (unannounced-in-BGP hops, e.g. the Equinix Singapore hop this whole detector exists to catch)
was left blank, contrary to what its own commit message claimed ("all resolved"). Reusing it as-is
silently produced 0% trombone at *both* floors. Fixed by: (1) a fresh bulk Team Cymru lookup on
every hop IP appearing in Pakistani-class traces that lacked a resolved country (298 IPs, 169
resolved), then (2) RDAP fallback (`rdap.org`, matching `pk_multi_probe.py`'s own registry_lookup
method) for the remaining ~129 IPs Cymru couldn't answer (unannounced backbone / registry-only).

**Status: complete.** Result is the opposite of the hypothesis, and it surfaces a real bug.

| Floor | ARTIFACT_ASN | Rate | n |
|---|---|--:|--:|
| 40ms (current code) | {Shaw} only | 7.50% | 5,667 |
| 20ms | {Shaw} only | 12.94% | 9,786 |
| 40ms | {Shaw, **Cogent**} | **5.52%** | 4,170 |
| 20ms | {Shaw, Cogent} | 6.84% | 5,174 |

**Every single newly-confirmed hop at 20ms (naive) is "US".** Traced the specific IPs: the bulk
of them (4,119→1,004 after the fix below) are `149.40.227.129`, AS174 (Cogent), which this
project's own CLAUDE.md already documents as physically inside Pakistan (~2ms from a different
Cogent PK PoP IP) despite US registration. The code's `ARTIFACT_ASN` set only contains Shaw
(`{"6327"}`) — Cogent was never added, so it slips through the RTT floor by luck (its PK PoP
normally answers under 40ms) rather than by an explicit exclusion. **This means the established,
paper-cited 40ms/"confirmed foreign hop" number is itself contaminated**: adding Cogent to
`ARTIFACT_ASN` (matching how Shaw is handled) drops the 40ms baseline from 7.50% to **5.52%**.

Reran with Cogent added. The *remaining* 1,004 newly-confirmed-at-20ms hops (only 2 targets,
`trax.pk` and `sonic.pk`) all trace to `172.68.249.86`, confirmed via RIPEstat to be **AS13335,
Cloudflare** — a second, different registration-vs-physical-location artifact (a local/regional
Cloudflare PoP, ~22-25ms, mislabelled foreign purely because Cloudflare is US-registered; this
matches CLAUDE.md's own documented Cloudflare-PoP-inequality finding).

**Conclusion: in every case checked, lowering the floor to 20ms did not surface a genuine nearby-
foreign hop (no Oman, no Gulf country appeared at all). It resurfaced two different already-known
registration artifacts (Cogent, then Cloudflare) that the paper's own methodology exists to guard
against.** Recommend: do **not** lower `FOREIGN_RTT_FLOOR` to 20ms; instead **add Cogent (AS174)
to `ARTIFACT_ASN`**, a real, independently-justified fix regardless of the floor question, since
it's currently contaminating the established 40ms number too. This also means **RQ1's most
rigorous headline number should be 5.52%, not 7.50%** — §2 above needs updating with the
Cogent-excluded per-ISP/per-sector breakdown before anything goes in the paper.

Scripts: `rerun_floor_sensitivity.py` (reprocesses from the raw archive directly — the panel CSV's
`exit_cc` field can't be relabeled for a different floor since it doesn't preserve per-hop RTT).
Hop-country lookup gap found and fixed along the way: `hop_annotations.csv` (906 IPs) only had 61
with a resolved country despite its own commit message claiming "all resolved" — everything
RDAP-registry-only (unannounced-in-BGP hops) was blank. Filled via a fresh bulk Team Cymru pull
(298 IPs → 169 resolved) plus RDAP fallback (`rdap.org`, matching `pk_multi_probe.py`'s own
method) for the remaining 129 (122 PK, 3 SG).

---

## Open decisions, not yet made

1. RQ3 flapping headline: 8.6% (hop-confirmed) vs 1.1% (path-confirmed) — which to cite.
2. Whether to report an "Inconclusive" tier explicitly in RQ1/RQ3 tables (the underlying detector
   already computes this three-way status; only the exported panel CSV collapses it to a boolean).
3. Whether the 20ms floor result (pending) changes any of the above once available.
4. How `running_draft.tex`'s Tromboning Classification section (currently has a literal
   `COUNTRY_NAME_HERE` placeholder and doesn't state the real thresholds in its active text) gets
   reconciled with the actual methodology before any of this is written in.
