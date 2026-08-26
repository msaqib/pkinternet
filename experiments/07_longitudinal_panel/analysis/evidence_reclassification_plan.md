# Evidence-based location reclassification: plan

**Trigger:** Dr. Saqib's review comment on the location-verification step (paraphrased):
RTT alone, in either direction, is not sufficient evidence to move a site's class.
A site labelled Pakistani with high RTT from every probe cannot be reclassified Abroad
without corroborating evidence (e.g. a foreign IP in the traceroute). A site labelled
Abroad with a low RTT from one probe cannot be claimed Pakistani without considering
where that probe sits (a Karachi probe can have a low RTT to Oman/UAE too). Any
RTT threshold used for "quite high"/"quite low" needs justification, which is hard.
Inconclusive sites should be dropped, and downstream results recomputed.

**What we already confirmed before writing this plan** (see conversation, not repeated
in full here):
- `geo.py`'s Pakistani→Abroad rule (`cls == "Pakistan" and best > T_LOCAL`) uses ping
  RTT only. No hop-level or ASN check is consulted.
- The trace-level trombone detector (`census_sweep.classify`, reused by
  `panel_monitor.py` for the whole panel) already distinguishes two kinds of trombone
  evidence internally (`exit_cc` a real country vs `exit_cc == "?"`) but this
  distinction is discarded before it reaches the paper: **38.4% of all trombone
  verdicts to Pakistani-class sites (6,050 / 15,742) are RTT-only, no foreign hop ever
  found.** This is bigger than the 6 site-classification corrections; it touches the
  RQ1 headline rate directly.
- Checking traceroutes to the 3 already-reclassified sites shows they mostly do NOT
  have a confirmed foreign hop either (phf.gop.pk: 1 of 2,236 traces), because
  Pakistani transit backbone hops are frequently unresponsive/unannounced (already
  documented elsewhere in this project). A strict "foreign IP in the traceroute" bar
  would fail to confirm sites we have strong independent reason to believe are
  genuinely abroad. So the corroborating signal needs to include the **destination
  IP's own ASN registration**, not just intermediate-hop country, since that's
  available regardless of whether backbone hops respond.
- For the 3 sites relocated Abroad→Pakistan by multilateration, WHOIS already gives
  independent, non-RTT corroboration (a PTCL block registered "Karachi"; a registrant
  address in Latifabad, Hyderabad) that rules out the Oman/UAE confound for those
  specific three. That check needs to be made systematic, not ad hoc.

## Goal

Replace both RTT-only decision rules (the 20ms site-reclassification threshold, and
the RTT-only branch of the trace-level trombone detector) with an evidence-tiered
approach, apply it to the full panel (not just the 6 already-flagged sites), quantify
how much changes, and recompute every downstream number that depends on
classification or trombone rate.

## Evidence sources to combine (in order of strength)

1. **Physics impossibility** (existing, unchanged): measured RTT below the physical
   floor for the claimed location. A hard proof; already used for the CDN/multilateration
   corrections. Not RTT-threshold-based, so not in scope for revision, only for reuse
   as the strongest tier.
2. **Destination-ASN registration** (new signal, always available): Team Cymru/RIPEstat
   country of the ASN the resolved destination IP itself belongs to. Independent of
   RTT and of intermediate-hop responsiveness. This is what the *original*
   classification was based on — using it again here is a consistency check
   ("is the ASN-registration answer stable"), not a new independent method, but it
   costs nothing and catches stale/contradictory registrations (as it did for
   phf.gop.pk, where a second ASN pull already disagreed with the first).
3. **Confirmed foreign/domestic hop in traceroute** (existing signal, currently
   discarded): `exit_cc` a real, non-PK country code, OR (for the domestic direction)
   every hop that responds resolving to PK/private space.
4. **Geo-IP city** (existing, weakest, known unreliable below country level per
   Gharaibeh et al., already cited in the paper): kept as corroborating-only, never
   decisive alone.
5. **RTT threshold** (existing, now demoted): necessary but not sufficient on its own
   for reclassification in either direction. Still used to *flag candidates for review*
   and to set the trace-level trombone/local split, just not to unilaterally relabel.

## Decision rules (replacing the current binary threshold)

**Site classified Pakistani, RTT high from every probe:**
- Reclassify **Abroad** only if destination-ASN registration is non-PK **and** (a
  confirmed foreign hop exists in at least one traceroute, **or** geo-IP city is a
  real foreign city consistent with the RTT). Physics-impossibility, if present,
  settles it outright regardless of the above (already true today).
- If destination-ASN registration is non-PK but neither a foreign hop nor a
  consistent geo-IP city is available (the phf.gop.pk situation): still reclassify
  Abroad, but flag it explicitly as "ASN-only, no hop-level corroboration" in the
  output so the paper can say so rather than imply hop-level proof exists.
- If destination-ASN registration is PK (i.e. only the RTT looks wrong, nothing else
  agrees): do **not** reclassify. Mark **Inconclusive** if RTT is far enough above
  the local ceiling to be implausible, otherwise leave as Pakistani. This is the
  direct fix for Saqib's first bullet — RTT alone, ASN still PK, no longer moves
  the label.

**Site classified Abroad, RTT low from at least one probe (impossibility not
triggered, i.e. not already physics-proven):**
- Reclassify/relocate only with non-RTT corroboration: WHOIS registrant address or
  ASN-block description naming a Pakistani place, or destination-ASN registration
  itself PK. Do not rely on "nearest probe is close" alone, since a Karachi probe
  can be close to Oman/UAE too (Saqib's second bullet).
- If no such corroboration exists: mark **Inconclusive**, do not relocate.

**Trace-level trombone detector, applied to every round, all sites — decided, not
left open:**
- **Trombone requires both**: a confirmed foreign IP hop **and** RTT in the
  high/plausible-foreign range (`exit_cc` a real, non-PK country — this already
  implies a qualifying RTT by construction, since the `foreign` check in
  `census_sweep.classify` only sets `exit_cc` when `FOREIGN_RTT_FLOOR <= rtt <=
  QUEUE_CEIL`). This is the existing `exit_cc`-confirmed branch, unchanged.
- The current RTT-only branch (`elif max_jump >= JUMP_THRESH or max_rtt >=
  HIGH_RTT: trombone = True; exit_cc = "?"`) **no longer sets trombone = True**.
  A round that lands here (elevated RTT, no foreign hop ever found) becomes
  **Inconclusive** rather than trombone or local — it isn't proven to have left
  the country, but it isn't confirmed local either.
- Recompute RQ1/RQ2/RQ3 under this stricter definition: trombone rate = confirmed-
  foreign-hop traces only; report the Inconclusive share explicitly (already
  quantified once: 38.4% of what used to count as trombone) rather than silently
  dropping it from the denominator or the narrative.

## Threshold justification (Saqib's third point)

Keep the existing Khunjerab–Gwadar physical derivation for the 20ms site-level
distance ceiling (that part is a real physical bound and doesn't change). Add an
explicit statement that the ceiling is now used only as a *candidate filter*, not a
sole reclassification trigger, which is the direct answer to "thresholds are hard to
justify" — the threshold no longer has to carry the full evidentiary weight by
itself. The trace-level 40/60/70/45ms thresholds keep their existing (already
physically-motivated, per the paper's Tromboning Classification section)
justification, unchanged; what changes is that RTT-only verdicts are now labelled
as such rather than pooled silently into "trombone."

## Work plan (execution order)

1. Build `evidence_scan.py` (or a new `geo.py` subcommand): for every unicast site
   (Pakistani + Abroad class, all 60 of them, not just the 6 already touched), pull
   destination-ASN registration (fresh Team Cymru/RIPEstat pull, not reused from the
   stale build-time record), scan every traceroute round in the panel for a
   confirmed foreign hop, and note geo-IP city. Output: one row per site with all
   four evidence signals side by side plus the current class and RTT.
2. Apply the decision rules above to produce `targets_corrected_v2.csv`. Diff
   against the current `targets_corrected.csv`: how many sites change class, how
   many move to Inconclusive, which ones.
3. Recompute the Latency Ratio (`ratio_corrected.csv`) and the CDN cross-section
   numbers with v2 classes, Inconclusive sites dropped from all class-dependent
   analysis. Quantify movement in the headline ratio numbers (medians, tail %,
   the regression R² figures).
4. Rebuild the trace-level trombone tiering for the full panel (all classes, not
   just Pakistani, since RQ1/RQ2/RQ3 also touch Abroad/CDN framing indirectly).
   Recompute RQ1's per-ISP/per-sector rates, RQ2's causal within-pair cost, and
   RQ3's flip counts under both the hop-confirmed-only and combined definitions.
5. Update `main_draft.tex` and `main_draft_polished.tex`: methodology text
   describing the evidence-tiered approach, any changed sample counts/numbers,
   and the RQ1 tier disclosure. Update figures that embed the old numbers
   (ratio CDF, distance regression, trombone-by-ISP) if they moved.
6. Log the before/after numbers and the methodology change in
   `paper/review_comments.md`.

## What "done" looks like

A single evidence table for every unicast site, a v2 classification with an
Inconclusive bucket, every headline number in the paper recomputed against v2 (or
confirmed unchanged, with the diff shown), and the paper's methodology text
describing evidence tiers instead of a bare RTT threshold, in both directions.
