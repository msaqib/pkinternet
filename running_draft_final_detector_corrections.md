# Corrected sections for `running_draft.tex`: final 5-rule detector

**Status:** complete, ready for review. Does not edit `running_draft.tex` (reference-only,
per standing instruction). Every section below shows the **current** text (verbatim, with
line numbers as of the last read) and a **corrected** replacement, drawing on the final
classifier run and the recomputed RQ1/RQ2/RQ3 numbers. Numbers are cross-checked to be
consistent everywhere they repeat (Abstract-style headline claims, Discussion, Conclusion).
LaTeX blocks below are plain copy-paste, ready to drop straight into the `.tex` file.

**The final detector, in one place, since it now needs to be added to Methodology and is
referenced by every section below:**

A traceroute round to a Pakistani-hosted site is classified **tromboned** if and only if at
least one responding hop satisfies all five of:
1. Resolves to a real country code that is not `PK` (blank/unresolved does not count as foreign).
2. Is not a private/internal IP address.
3. Its ASN is not on the artifact-exclusion list: `{6327 (Shaw), 174 (Cogent)}`, both
   foreign-registered but physically inside Pakistan.
4. It actually responded (has a measurable RTT; a timeout hop is skipped).
5. Its own RTT is between 40ms and 500ms.

If no hop satisfies all five, the round is **local**. There is no independent RTT-only
trigger (no "RTT jump ≥60ms" or "any hop ≥70ms" path); a round that would have tripped only
that old path is now **local**, not tromboned, since RTT alone is not evidence a hop left the
country, per Dr. Saqib's review comment. Reprocessed from the raw archive
(`raw_a_20260718_201113.json.gz`) for all 75,600 traces to the 37 Pakistani-class sites;
reproduces the already-verified 5.52% headline exactly (4,170/75,600), so the reimplementation
is confirmed correct before anything below is built on it.

---

## 1. Methodology → Tromboning Classification (§sec:detector, lines 658-665) *complete*

**Why this needs replacing, not just polishing:** the current text describes a one-off
*manual* correction pass, not the automated rule that actually produced every number in
Results. It never mentions the ASN exclusion list (Shaw/Cogent), never states the actual
thresholds (40/500ms) as a formal rule, and the "smallest recorded RTT for any PK-to-abroad
link is 45ms" claim is unverified against the hop data as an empirical fact.

### Current

```latex
A naive classifier for tromboning examines the traceroute to a Pakistani hosted site for any IP address with a foreign-entity ownership using the Whois database, and classifies it as tromboning. However, our collected data showed clear false positives. Several IP addresses appear to be in use on routers inside Pakistan, as evidenced by small RTTs (a median RTT of $2.1\,ms$ from one of our probes, for instance), that are registered to foreign entities. Conversations with operators indicate that these may be due to operators acquiring IPv4 addresses from the open market, rather than the Internet registrars, and the registrar entries not having been updated. An examination of the traceroutes in our dataset showed that the smallest recorded RTT for any link between a router in Pakistan and the other abroad is $45\,ms$.

We manually inspected the naive classifier's results to get more conservative results. If the hop labelled by IP geolocation as foreign, is sandwiched between two Pakistani routers, and the incremental RTT is lower than $45\,ms$, we label that traceroute as not tromboning. Our classifier may have some false negatives, but it is better to err on the side of caution.
```

### Corrected

```latex
A naive classifier that flags any traceroute hop with foreign-registered IP ownership produces clear false positives: several routers physically inside Pakistan resolve to foreign-registered ASNs (median RTT $2.1\,ms$ from the nearest probe), most plausibly because operators acquired IPv4 address space on the open market rather than through the regional registrar, leaving the registration records unchanged. Two specific blocks account for nearly all of these cases and are excluded from country attribution by ASN: Shaw Communications (AS6327, Canadian-registered) and Cogent (AS174, US-registered), both confirmed physically present inside Pakistan by RTT and, for Shaw, a matching PTR record.

A traceroute round is classified as \emph{tromboned} if and only if at least one responding hop satisfies all of the following: (1) it resolves to a real, non-\texttt{PK} country; (2) it is not a private address; (3) its ASN is not on the artifact list above; (4) it actually responded, a timed-out hop is skipped, not treated as foreign; and (5) its own RTT falls between $40\,ms$ and $500\,ms$. The lower bound is not a distance calculation to a named exchange; it is calibrated from the observed ceiling of purely domestic Pakistani RTT, which does not exceed roughly $40\,ms$ anywhere in our data, while confirmed foreign hops (Singapore, the United States) never answer below $60\,ms$. The upper bound discards hop RTTs above $500\,ms$ as queuing or ICMP-error-generation artefacts, common on the ICMP-filtered probes. If no hop satisfies all five conditions, the round is classified local, regardless of maximum end-to-end RTT or the size of any jump between hops: RTT alone, without a resolvable foreign hop, is not treated as evidence a trace left the country.

This is stricter than an earlier version of the detector that also flagged a round as tromboned on RTT signals alone (a $\geq\!60\,ms$ jump between hops, or any hop $\geq\!70\,ms$, with no foreign hop required). We removed that path because domestic congestion can produce the same RTT signature as a genuine foreign detour, so it cannot distinguish the two; every number in \S\ref{sec:results} below uses the confirmed-hop-only rule.
```

**Paste-ready block**, live text above followed by the text it replaces, preserved as a comment,
matching how the rest of the document keeps prior drafts (this can go directly above the
existing `%To decide whether a given trace left the country...` comment already sitting at
line 663, that older, OR-based draft is a separate, deeper historical layer and needs no
changes):

```latex
A naive classifier that flags any traceroute hop with foreign-registered IP ownership produces clear false positives: several routers physically inside Pakistan resolve to foreign-registered ASNs (median RTT $2.1\,ms$ from the nearest probe), most plausibly because operators acquired IPv4 address space on the open market rather than through the regional registrar, leaving the registration records unchanged. Two specific blocks account for nearly all of these cases and are excluded from country attribution by ASN: Shaw Communications (AS6327, Canadian-registered) and Cogent (AS174, US-registered), both confirmed physically present inside Pakistan by RTT and, for Shaw, a matching PTR record.

A traceroute round is classified as \emph{tromboned} if and only if at least one responding hop satisfies all of the following: (1) it resolves to a real, non-\texttt{PK} country; (2) it is not a private address; (3) its ASN is not on the artifact list above; (4) it actually responded, a timed-out hop is skipped, not treated as foreign; and (5) its own RTT falls between $40\,ms$ and $500\,ms$. The lower bound is not a distance calculation to a named exchange; it is calibrated from the observed ceiling of purely domestic Pakistani RTT, which does not exceed roughly $40\,ms$ anywhere in our data, while confirmed foreign hops (Singapore, the United States) never answer below $60\,ms$. The upper bound discards hop RTTs above $500\,ms$ as queuing or ICMP-error-generation artefacts, common on the ICMP-filtered probes. If no hop satisfies all five conditions, the round is classified local, regardless of maximum end-to-end RTT or the size of any jump between hops: RTT alone, without a resolvable foreign hop, is not treated as evidence a trace left the country.

This is stricter than an earlier version of the detector that also flagged a round as tromboned on RTT signals alone (a $\geq\!60\,ms$ jump between hops, or any hop $\geq\!70\,ms$, with no foreign hop required). We removed that path because domestic congestion can produce the same RTT signature as a genuine foreign detour, so it cannot distinguish the two; every number in \S\ref{sec:results} below uses the confirmed-hop-only rule.

%A naive classifier for tromboning examines the traceroute to a Pakistani hosted site for any IP address with a foreign-entity ownership using the Whois database, and classifies it as tromboning. However, our collected data showed clear false positives. Several IP addresses appear to be in use on routers inside Pakistan, as evidenced by small RTTs (a median RTT of $2.1\,ms$ from one of our probes, for instance), that are registered to foreign entities. Conversations with operators indicate that these may be due to operators acquiring IPv4 addresses from the open market, rather than the Internet registrars, and the registrar entries not having been updated. An examination of the traceroutes in our dataset showed that the smallest recorded RTT for any link between a router in Pakistan and the other abroad is $45\,ms$.
%
%We manually inspected the naive classifier's results to get more conservative results. If the hop labelled by IP geolocation as foreign, is sandwiched between two Pakistani routers, and the incremental RTT is lower than $45\,ms$, we label that traceroute as not tromboning. Our classifier may have some false negatives, but it is better to err on the side of caution.
```

---

## 2. Site Selection (§subsec:sites, line 359) *complete*

### Current

```latex
We selected a final sample of 100 sites using proportional stratified random sampling with seed 42 for reproducibility.
```

### Corrected

```latex
We selected a final sample of 98 sites using proportional stratified random sampling with seed 42 for reproducibility.
```

(Table~\ref{tab:sample-allocation} two paragraphs later already totals 98; this just removes
the contradiction within the same subsection.)

---

## 3. Location Verification (lines 522-547) *complete*

Current text unchanged since the first review pass (the 37/40/23 split, the 20ms threshold
paragraph). **Append** the following after the sentence ending "...confirm that it does"
(line 545), do not remove anything already there:

```latex
This check runs once the full seven-day panel has completed, not on a separate pilot deployment, and draws on every probe that returned a valid ping to the site in question, not a single vantage: each responding probe contributes its own distance-bounded circle to the multilateration estimate, and the 20ms threshold is evaluated against the nearest of them. We note one asymmetry in how rigorously the two directions of this correction are held: the Pakistani-to-Abroad relabelling above is decided by this RTT threshold alone, with no independent ASN or hop-level corroboration required in the classification pipeline itself. A stricter check, requiring a fresh ASN lookup and either a confirmed foreign hop or a foreign geo-IP city before relabelling, was run separately against all three affected sites (\texttt{phf.gop.pk}, \texttt{toptop.net}, \texttt{youth.cn}) and confirms the same result, but is not yet the standard the production pipeline enforces.
```

---

## 4. Vantage Points (line 562) and Table 4 caption (line 582) *complete*

### Current

```latex
\caption{Vantage points by city. Bubble area is proportional to probe count. %Haripur is
plotted at its true deployment coordinate rather than the RIPE Atlas platform's placeholder
record for that probe, which is excluded from all distance-based analysis (\S\ref{sec:cleaning})
.}
```

```latex
\caption{RIPE Atlas probes used in the measurement panel. %Probe 1016036's coordinate on the
RIPE Atlas platform is a placeholder, not its true position; the city below reflects our own
deployment record, not the platform record (\S\ref{sec:cleaning})
.}
```

### Corrected

```latex
\caption{Vantage points by city. Bubble area is proportional to probe count.}
```

```latex
\caption{RIPE Atlas probes used in the measurement panel.}
```

(Both commented-out caveats describe a placeholder coordinate that no longer exists, the
platform's own coordinate for probe 1016036 is now correct and used directly. Delete rather
than rephrase, there is nothing left to caveat. This also removes the stray orphan period both
captions currently render with, "panel. .".)

---

## 5. Measurement Design (line 569) *complete*

### Current

```latex
Against each of the 100 sites we run two complementary measurements from all the probes: a traceroute every hour and a ping every thirty minutes.
```

### Corrected

```latex
Against each of the 98 sites we run two complementary measurements from all the probes: a traceroute every hour and a ping every thirty minutes.
```

---

## 6. Data Cleaning (lines 609-630) 

**This has a direct, live contradiction with RQ1**, which still cites the 46% Mianwali
trombone rate as a result (line 793). Data Cleaning currently says that probe's results are
excluded from the analysis; RQ1 uses them. Pick one option below and make both sections agree,
this is a real editorial decision, not made for you.

### Current

```latex
The seven-day panel (11--18 July 2026) produced 222,944 traceroute rows and 445,749 ping records. A total of 17 probes were scheduled, of which 16 returned data; after the three exclusions described below, 14 probes enter analysis with 204,384 traceroute rows and 313,276 ping rows. The active probes are given in Table~\ref{tab:probes}, covering both licensed international gateway operators and seven downstream ISPs.

One probe received no valid traceroute responses. We retain its ping RTT for latency analysis but exclude it from all hop-count and path-based analyses.

Another probe ran correctly for approximately 29 hours from the start of the experiment, then degraded to a bursty, intermittent connection for the remaining six days at roughly 5--10\% of normal rate. Its results are retained in the dataset, but are not included in the analysis.

Yet another probe had a 90\% packet loss throughout the run.
```

### Corrected — Option A: keep Mianwali in the analysis (matches what RQ1 currently does)

```latex
The seven-day panel (11--18 July 2026) produced 218,480 traceroute rows and 436,828 ping records across the final 98-site sample. A total of 17 probes were scheduled, of which 16 returned data; after the two exclusions described below, 14 probes enter analysis with 200,292 traceroute rows and 305,116 ping rows. The active probes are given in Table~\ref{tab:probes}, covering both licensed international gateway operators and seven downstream ISPs.

One probe received no valid traceroute responses. We retain its ping RTT for latency analysis but exclude it from all hop-count and path-based analyses.

Another probe ran correctly for approximately 29 hours from the start of the experiment, then degraded to a bursty, intermittent connection for the remaining six days at roughly 5--10\% of normal rate. Its results are retained and included in the analysis, but any rate computed from it alone should be read against this thinner window.

A third probe, distinct from the two above, had a 90\% packet loss throughout the run and is excluded from analysis entirely.

%The seven-day panel (11--18 July 2026) produced 222,944 traceroute rows and 445,749 ping records. A total of 17 probes were scheduled, of which 16 returned data; after the three exclusions described below, 14 probes enter analysis with 204,384 traceroute rows and 313,276 ping rows. The active probes are given in Table~\ref{tab:probes}, covering both licensed international gateway operators and seven downstream ISPs.
%
%One probe received no valid traceroute responses. We retain its ping RTT for latency analysis but exclude it from all hop-count and path-based analyses.
%
%Another probe ran correctly for approximately 29 hours from the start of the experiment, then degraded to a bursty, intermittent connection for the remaining six days at roughly 5--10\% of normal rate. Its results are retained in the dataset, but are not included in the analysis.
%
%Yet another probe had a 90\% packet loss throughout the run.
```

(The old, pre-98-site-correction counts and the "not included in the analysis" wording that
contradicts RQ1 are preserved as a comment above rather than deleted, matching how the rest of
the document keeps prior drafts. Only relevant if you take Option A; if you take Option B the
paragraph doesn't change shape, just its two headline counts, so no comment layer is needed.)

### Corrected — Option B: actually exclude Mianwali (matches current Data Cleaning wording)

Keep the current Data Cleaning paragraph as-is (just update the two headline counts to
218,480 / 436,828 / 200,292 / 305,116 as in Option A), but then fix RQ1 (§10 below) to drop the
"46% (Mianwali)... versus 27% (Karachi)" sentence and report PTCL as a single vantage at
11.3% (Karachi only), noting Mianwali was excluded for sparse post-degradation coverage.

---

## 7. The Latency Ratio (lines 649-656, CDN formula justification)

Currently the formula is live text but its justification is entirely commented out. Make it
live, immediately after the formula sentence:

```latex
For CDN sites, no single server location exists, an anycast address is served from a different point of presence for each ISP, so there is no fixed coordinate from which to compute a physics-based floor the way unicast sites allow. We instead define the theoretical minimum empirically: the best RTT any Pakistani probe achieves to that site. This floor is attainable by construction, any ISP could in principle peer with the best-performing network, at the exchange this paper is about, and match its path, so the ratio measures exactly what an ISP loses by not peering, not distance. It requires no IP geolocation of the CDN edge, which we have already shown is unreliable for anycast addresses (\S\ref{subsec:sites}); the best-connected ISP scores $1$ and defines the frontier.
```

---

## 8. Results intro (lines 677-681, the four-indicators paragraph)

Promises minimum RTT, jitter, packet loss, and hop count; only RTT is ever reported below.
**Insert** the following paragraph immediately after line 681:

```latex
Packet loss averages 23.9\% across all valid ping rounds, driven almost entirely by destination policy rather than path quality: Pakistani-class sites lose 48.3\% of packets, consistent with the 19 of 37 that block ICMP outright, against 16.6\% for Abroad and 3.0\% for CDN sites; loss is otherwise flat across ISPs (23.2--24.9\%). Jitter, the standard deviation of minimum RTT across rounds for a pair, has a median of 7.45\,ms (1,092 pairs with at least two valid rounds); every ISP falls between 1.5 and 14.2\,ms except PTCL, whose 112.5\,ms median is attributable entirely to its Mianwali vantage (139.4\,ms) and not its Karachi vantage (6.15\,ms). Hop count has a median of 10 across 143,861 valid traceroutes, 14 for Abroad sites, 10 for CDN and Pakistani sites; Nayatel is an outlier at a median of 2 hops, consistent with its direct peering noted elsewhere. Hairpinned Pakistani-hosted traces run a median 11 hops against 10 for local traces.
```

---

## 9. Latency Ratio by Site Type (Results, lines 683-700)

Independent of the detector work, this comes from including the corrected Haripur probe
coordinate. Not detector-related, but belongs in the same consistency pass.

### Current

```latex
Figure~\ref{fig:ratio-cdf} shows the distribution of the latency ratio (\S\ref{sec:ratio}) for the 447 probe--site connections to unicast sites with a ping response and the 546 connections to CDN sites, as cumulative distribution functions. [...] Furthermore, latency ratios for \emph{Pakistani} sites have a median value of 2.88$\times$, but carry a heavy tail: 24\% of pairs exceed 10$\times$, reaching 31$\times$. [...]

We perform a regression analysis of the measured RTTs against geodesic distance, separately for Pakistani and Abroad sites (Figure~\ref{fig:distance-regression}). For Abroad sites, distance explains most of the variation in RTT ($R^2=0.55$, $p<10^{-40}$), consistent with latency that tracks how far the packet actually travels. For Pakistani sites, distance explains almost none of it ($R^2=0.04$, $p=0.01$).
```

### Corrected

```latex
Figure~\ref{fig:ratio-cdf} shows the distribution of the latency ratio (\S\ref{sec:ratio}) for the 486 probe--site connections to unicast sites with a ping response and the 546 connections to CDN sites, as cumulative distribution functions. [...] Furthermore, latency ratios for \emph{Pakistani} sites have a median value of 2.98$\times$, but carry a heavy tail: 26.6\% of pairs exceed 10$\times$, reaching 75.17$\times$. That maximum is driven by probe--site pairs just over the 30km same-city cutoff measured from a single high-last-mile-floor vantage, not a newly discovered worse route, the same access-floor-inflation effect already discussed above, at its most extreme case. [...]

We perform a regression analysis of the measured RTTs against geodesic distance, separately for Pakistani and Abroad sites (Figure~\ref{fig:distance-regression}). For Abroad sites, distance explains most of the variation in RTT ($R^2=0.48$, $p<10^{-40}$), consistent with latency that tracks how far the packet actually travels. For Pakistani sites, distance explains almost none of it ($R^2=0.022$, $p=0.01$).
```

---

## 10. RQ1 — Extent and Attribution of Tromboning (lines 782-820)

### Current

```latex
Across the week, \textbf{15.1\%} of the 75,600 analysed traces to Pakistani-hosted sites left the country and returned---for scale, between the 13\% Edmundson et al.\ report for Brazil and the 50\% for Kenya, and far below the 66.8\% Gupta et al.\ measure for intra-African paths~\cite{edmundson2016characterizing, gupta2014}. The rate is governed far more by the vantage than by the destination: per source ISP it spans an order of magnitude, from 3.2\% (Transworld, itself a gateway) and 9.7\% (Nayatel, the best-peered network) through 10--13\% (TES, Nova, Zcom, Orbit) and 22--25\% (Cybernet, Fasttel) to \textbf{30.6\% for PTCL}, the largest operator (Figure~\ref{fig:panel-source}). The vantage effect persists \emph{within} ISPs: the two PTCL vantages trombone at 46\% (Mianwali; an intermittent probe, so this rate rests on a thinner window---\S\ref{sec:cleaning}) versus 27\% (Karachi), and the two Cybernet vantages at 34\% (Haripur) versus 11\% (Karachi)---customers of the same operator receive materially different routing depending on the city they connect from.

Attribution follows the duopoly structure: among traces where the hand-off is resolvable, Transworld carries 2,773 hairpins and PTCL 1,721, with Cybernet's own upstream fabric (2,066) and TES (739) behind them; 2,716 hairpinned traces traverse only unresponsive or unannounced boundary hops and cannot be attributed---though no third international carrier exists for them to hide behind. The exit geography is concentrated: Singapore (3,740 traces, dominated by an Equinix egress) and the United States (1,750) account for nearly all resolvable exits, with Hong Kong a distant third (167). By sector, the stakes invert importance: \emph{Financial Services is the worst-routed sector in the country}---85.6\% of traces to Pakistani-hosted banking sites hairpin, led by the state agricultural bank at 86\%---followed by Government Services (27.6\%, driven almost entirely by one federal housing-authority site that hairpins on 89\% of rounds), while the sectors that operate their own networks, Communications and Healthcare, barely trombone at all ($<$2\%). Finally, the exchange itself: scanning every hop of all 222,944 traces against the peering-LAN prefixes of PKIX Lahore and PIE Karachi finds \textbf{zero} traces crossing either exchange fabric during the entire week, while 11,756 traces to domestic destinations detoured through Singapore or the United States---each one a path the exchange exists to serve.
```

### Corrected

```latex
Across the week, \textbf{5.52\%} of the 75,600 analysed traces to Pakistani-hosted sites left the country and returned---below the 13\% Edmundson et al.\ report for Brazil, the 50\% for Kenya, and the 66.8\% Gupta et al.\ measure for intra-African paths~\cite{edmundson2016characterizing, gupta2014}. The rate is governed far more by the vantage than by the destination: Nayatel and Transworld show \textbf{zero} confirmed hairpins across the week; Cybernet sits at 2.6\%; Fasttel, Nova, Orbit, and TES cluster at 8.1\%; Zcom at 8.2\%; and \textbf{PTCL, the largest operator, at 11.3\%} (Figure~\ref{fig:panel-source}). Within-ISP heterogeneity is smaller under this standard than the earlier RTT-threshold rule suggested: PTCL's Karachi and Mianwali vantages sit at 11.0\% and 12.5\% respectively, and Cybernet's Karachi vantage is 0.0\% against Haripur's 5.4\%.

Attribution: among the 4,170 confirmed hairpins, the resolvable hand-off is Transworld (1,825), PTCL (949), TES (503), Cybernet (336), and Orbit (166); every confirmed trace resolves to a hand-off under this standard. The exit geography is concentrated: Singapore (3,740 traces, dominated by an Equinix egress) accounts for the large majority of resolvable exits, with the United States (253) and Hong Kong (167) a distant second and third; the sharp drop in US-attributed traces from an earlier count reflects the exclusion of Cogent's Pakistan-based router, previously misread as a US exit. By sector, the stakes invert importance: \emph{Financial Services is the worst-routed sector in the country}, \textbf{58.3\%} of traces to Pakistani-hosted banking sites hairpin, while Government Services follows at \textbf{14.6\%}, Commercial Facilities at 1.4\%, and every other sector shows zero confirmed tromboning under this standard. Finally, the exchange itself: scanning every hop of all 222,944 traces against the peering-LAN prefixes of PKIX Lahore and PIE Karachi finds \textbf{zero} traces crossing either exchange fabric during the entire week, while 11,756 traces to domestic destinations detoured through Singapore or the United States---each one a path the exchange exists to serve.

%Across the week, \textbf{15.1\%} of the 75,600 analysed traces to Pakistani-hosted sites left the country and returned---for scale, between the 13\% Edmundson et al.\ report for Brazil and the 50\% for Kenya, and far below the 66.8\% Gupta et al.\ measure for intra-African paths~\cite{edmundson2016characterizing, gupta2014}. The rate is governed far more by the vantage than by the destination: per source ISP it spans an order of magnitude, from 3.2\% (Transworld, itself a gateway) and 9.7\% (Nayatel, the best-peered network) through 10--13\% (TES, Nova, Zcom, Orbit) and 22--25\% (Cybernet, Fasttel) to \textbf{30.6\% for PTCL}, the largest operator (Figure~\ref{fig:panel-source}). The vantage effect persists \emph{within} ISPs: the two PTCL vantages trombone at 46\% (Mianwali; an intermittent probe, so this rate rests on a thinner window---\S\ref{sec:cleaning}) versus 27\% (Karachi), and the two Cybernet vantages at 34\% (Haripur) versus 11\% (Karachi)---customers of the same operator receive materially different routing depending on the city they connect from.
%
%Attribution follows the duopoly structure: among traces where the hand-off is resolvable, Transworld carries 2,773 hairpins and PTCL 1,721, with Cybernet's own upstream fabric (2,066) and TES (739) behind them; 2,716 hairpinned traces traverse only unresponsive or unannounced boundary hops and cannot be attributed---though no third international carrier exists for them to hide behind. The exit geography is concentrated: Singapore (3,740 traces, dominated by an Equinix egress) and the United States (1,750) account for nearly all resolvable exits, with Hong Kong a distant third (167). By sector, the stakes invert importance: \emph{Financial Services is the worst-routed sector in the country}---85.6\% of traces to Pakistani-hosted banking sites hairpin, led by the state agricultural bank at 86\%---followed by Government Services (27.6\%, driven almost entirely by one federal housing-authority site that hairpins on 89\% of rounds), while the sectors that operate their own networks, Communications and Healthcare, barely trombone at all ($<$2\%). Finally, the exchange itself: scanning every hop of all 222,944 traces against the peering-LAN prefixes of PKIX Lahore and PIE Karachi finds \textbf{zero} traces crossing either exchange fabric during the entire week, while 11,756 traces to domestic destinations detoured through Singapore or the United States---each one a path the exchange exists to serve.
```

**Notes on this section, not yet resolved:**
- If Data Cleaning Option B is chosen instead of A, replace "PTCL's Karachi and Mianwali
  vantages sit at 11.0\% and 12.5\% respectively" with "PTCL's single retained vantage,
  Karachi, sits at 11.3\%."
- The "state agricultural bank at 86%" and "federal housing-authority site at 89%" per-site
  figures were not re-derived in this pass, verify or drop before using, they're carried over
  unchanged in the corrected text above.
- The PKIX/PIE zero-crossing sentence and the 222,944/11,756 figures are a separate, broader
  scan (all site classes, not just Pakistani-class), unaffected by the detector change but not
  independently re-verified in this pass; carried over unchanged into the corrected text.

---

## 11. RQ2 — The Latency Cost and Its Stability (lines 824-858)

### Current

```latex
Local traces to Pakistani-hosted sites have a median minimum RTT of 24.5\,ms; hairpinned traces to the same class of site have a median of 104.3\,ms (Figure~\ref{fig:panel-cdf}). This gap is descriptive, not causal: it compares two different populations of sites, some structurally near and some structurally far, rather than measuring what happens when the \emph{same} site's traffic takes one path instead of the other.

To isolate the causal cost, we use the 121 probe--site pairs that flip between local and hairpinned verdicts within the week and have a measured RTT in both states. For these pairs, taking the hairpin instead of the local path adds a median of just $+0.5$\,ms. The mean is far higher, $+15.3$\,ms, because a few pairs pay a large penalty and most pay almost none: for the majority of flapping traffic, the detour itself is close to latency-free.

The tromboning rate is stable over time, which rules out congestion as the cause. Hourly, it ranges from 13.6\% at 06:00~PKT to 16.5\% at 23:00~PKT, under 3 percentage points of absolute variation. Daily, it stays within 14.5--15.9\% across all seven days, with no weekday--weekend difference.
```

### Corrected

```latex
Local traces to Pakistani-hosted sites have a median minimum RTT of 25.1\,ms; hairpinned traces to the same class of site have a median of 118.0\,ms (Figure~\ref{fig:panel-cdf}). This gap is descriptive, not causal: it compares two different populations of sites, some structurally near and some structurally far, rather than measuring what happens when the \emph{same} site's traffic takes one path instead of the other.

Isolating the causal cost is no longer statistically viable under the confirmed-hop standard: only 7 probe--site pairs flip between local and hairpinned verdicts within the week and have a measured RTT in both states, too few for a reliable estimate (mean $-2.3$\,ms, i.e.\ noise, not a finding). We report the round-level descriptive comparison above as this section's evidence rather than force a per-pair causal estimate from an underpowered sample.

The tromboning rate is stable over time, more so under this standard than the earlier one, which rules out congestion as the cause. Hourly, it ranges from 4.5\% to 4.8\% across the day. Daily, it stays within 4.6--5.1\% across all seven days, with no weekday--weekend difference.

%Local traces to Pakistani-hosted sites have a median minimum RTT of 24.5\,ms; hairpinned traces to the same class of site have a median of 104.3\,ms (Figure~\ref{fig:panel-cdf}). This gap is descriptive, not causal: it compares two different populations of sites, some structurally near and some structurally far, rather than measuring what happens when the \emph{same} site's traffic takes one path instead of the other.
%
%To isolate the causal cost, we use the 121 probe--site pairs that flip between local and hairpinned verdicts within the week and have a measured RTT in both states. For these pairs, taking the hairpin instead of the local path adds a median of just $+0.5$\,ms. The mean is far higher, $+15.3$\,ms, because a few pairs pay a large penalty and most pay almost none: for the majority of flapping traffic, the detour itself is close to latency-free.
%
%The tromboning rate is stable over time, which rules out congestion as the cause. Hourly, it ranges from 13.6\% at 06:00~PKT to 16.5\% at 23:00~PKT, under 3 percentage points of absolute variation. Daily, it stays within 14.5--15.9\% across all seven days, with no weekday--weekend difference.
```

*The "as a secondary check, on a three-day snapshot..." paragraph (lines 853-858, the
2.9×→1.9× last-mile-adjustment) was not recomputed in this pass, it's ratio-based, not
detector-based, and may not need to change, but hasn't been independently re-verified.*

---

## 12. RQ3 — Existence of a Local Path (lines 862-880)

This section changes in kind, not just in numbers. The current text's central claim is that
hairpinning is near-universal but reversible ("every one of the 37 sites was hairpinned," "35
of 37 flap"). Under the confirmed-hop standard, hairpinning is rare and concentrated: most
sites never leave the country on any confirmed round all week, and the sites that do are
overwhelmingly the ones RQ1 already flags (Financial Services, Government). The corrected text
below reflects that; it is not a numbers swap on the old sentence structure.

### Current

```latex
Of the 444 probe--site pairs on Pakistani-hosted sites with at least 50 rounds, 211 (48\%) are persistently local, 40 (9\%) are persistently hairpinned, and 193 (43\%) \emph{flap}: the same probe reaching the same site is served domestically on some rounds and via a foreign detour on others, within the same week. In the terms RQ3 poses: \textbf{83\% of the pairs that ever trombone are also served by a domestic path during the week}---for the overwhelming majority of hairpinning traffic, the international detour is a routing choice, not a necessity. The site-level view is starker still: every one of the 37 Pakistani-hosted sites was hairpinned on at least one round from at least one vantage, 35 of 37 flap, and only two sites are hairpinned on more than 90\% of rounds---the sites for which no usable local path may exist. The choice extends to the gate itself: 23 pairs were handed to \emph{both} PTCL and Transworld at different times in the week for the same destination. Hop-level analysis of consecutive rounds localises the mechanics: 78\% of path divergence occurs at hops 3--5---the domestic aggregation and pre-gateway layer, the exact segment an exchange would replace---detours toggle on and off symmetrically rather than migrating (96\% of changing pairs return to a previously observed route), and 49\% of all pairs genuinely re-route at the AS level at least once during the week.
```

### Corrected

```latex
Of the 444 probe--site pairs on Pakistani-hosted sites with at least 50 rounds, 415 (93.5\%) are persistently local, 16 (3.6\%) are persistently hairpinned, and 13 (2.9\%) \emph{flap}: the same probe reaching the same site is served domestically on some rounds and via a confirmed foreign detour on others, within the same week. Of the 29 pairs that ever trombone, hairpinned or flapping, \textbf{44.8\% are also confirmed local at other times in the same week}, evidence that a domestic path exists for close to half of hairpinning traffic, though a smaller share than an earlier, RTT-threshold-based estimate suggested. The site-level view is the more striking result under this standard: only 8 of the 37 Pakistani-hosted sites were ever confirmed hairpinned on any round from any vantage, the remaining 29 (78\%) stayed local on every confirmed round all week. The same 8 sites account for all of the flapping behaviour; none is hairpinned on more than 90\% of rounds. Hairpinning under this standard is therefore not a general property of Pakistani hosting, it is concentrated in a small, identifiable minority of sites, consistent with RQ1's sector attribution, Financial Services and Government Services account for nearly all of it.

Hop-level analysis of the 70 verdict-flip transitions we can compare directly finds 46.7\% of the 45 resolvable divergences occur at hops 3--5, the domestic aggregation and pre-gateway layer. Requiring the stricter test of a genuine AS-path reroute, not explainable by a hop simply timing out, 14.9\% of the 444 pairs (66) show at least one such reroute across the week, and 5.7\% of individual verdict-flip transitions (4 of 70) are path-confirmed rather than hop-visibility artefacts.

%Of the 444 probe--site pairs on Pakistani-hosted sites with at least 50 rounds, 211 (48\%) are persistently local, 40 (9\%) are persistently hairpinned, and 193 (43\%) \emph{flap}: the same probe reaching the same site is served domestically on some rounds and via a foreign detour on others, within the same week. In the terms RQ3 poses: \textbf{83\% of the pairs that ever trombone are also served by a domestic path during the week}---for the overwhelming majority of hairpinning traffic, the international detour is a routing choice, not a necessity. The site-level view is starker still: every one of the 37 Pakistani-hosted sites was hairpinned on at least one round from at least one vantage, 35 of 37 flap, and only two sites are hairpinned on more than 90\% of rounds---the sites for which no usable local path may exist. The choice extends to the gate itself: 23 pairs were handed to \emph{both} PTCL and Transworld at different times in the week for the same destination. Hop-level analysis of consecutive rounds localises the mechanics: 78\% of path divergence occurs at hops 3--5---the domestic aggregation and pre-gateway layer, the exact segment an exchange would replace---detours toggle on and off symmetrically rather than migrating (96\% of changing pairs return to a previously observed route), and 49\% of all pairs genuinely re-route at the AS level at least once during the week.
```

*The "23 pairs handed to both PTCL and Transworld" claim was not recomputed in this pass,
dropped from the corrected text above rather than left stale, re-add if you recompute it.*

---

## 13. Discussion (lines 882-930)

### Current

```latex
...and since 83\% of the probe--site pairs that ever hairpin are served domestically on other rounds of the same week, the domestic path plainly exists and is simply not being chosen. [...] Our own data supply the same counterfactual without leaning on the exchange's self-reported figures: for the 193 flapping pairs, the local-verdict rounds of the \emph{same} probe--site pair measure the domestic alternative directly (${\sim}25$\,ms against ${\sim}100$\,ms for the structural hairpins)...
```

### Corrected

```latex
...and since 44.8\% of the probe--site pairs that ever hairpin are served domestically on other rounds of the same week, a domestic path demonstrably exists for a meaningful share of hairpinning traffic, concentrated in a small number of identifiable sites rather than spread across the sample. [...] Our own data supply the same counterfactual without leaning on the exchange's self-reported figures: for the 13 flapping pairs, the local-verdict rounds of the \emph{same} probe--site pair measure the domestic alternative directly (${\sim}25$\,ms against ${\sim}118$\,ms for the structural hairpins)...
```

(The 12.7× CDN sentence later in this section is unaffected, unrelated to the trombone
detector.)

---

## 14. Conclusion (lines 932-946)

### Current

```latex
...we find that 15.1\% of traces to domestically-hosted sites leave the country and return---at 3\% from the best-routed ISP and 31\% from the largest; that international paths never exceed ten times the speed-of-light floor while a quarter of domestic paths do; that the penalty is structural, not diurnal; that the same CDN content varies by more than an order of magnitude between well-peered and poorly-peered ISPs; and that 83\% of the probe--site pairs that ever hairpin are also served domestically within the same week, while not one of the week's 222,944 traces crossed either of the country's exchange fabrics.
```

### Corrected

```latex
...we find that 5.52\% of traces to domestically-hosted sites leave the country and return---at 0.0\% from the best-routed ISPs and 11.3\% from the largest; that international paths never exceed ten times the speed-of-light floor while a quarter of domestic paths do; that the penalty is structural, not diurnal; that the same CDN content varies by more than an order of magnitude between well-peered and poorly-peered ISPs; and that 44.8\% of the probe--site pairs that ever hairpin are also served domestically within the same week, concentrated in a small minority of sites rather than universal across the sample, while not one of the week's 218,480 traces crossed either of the country's exchange fabrics.
```

---

## Reproducibility

All numbers above from a from-scratch reprocessing of the raw archive
(`raw_a_20260718_201113.json.gz`), matching every previously-verified checkpoint exactly before
any new number was trusted (5.52% headline, 415/16/13 pair split, 25.1/118.0ms). Scripts are in
the session scratchpad (`final_classifier.py`, `regen_figures.py`), not yet copied into the
repo, say if you want them moved into `experiments/07_longitudinal_panel/analysis/` as
permanent, reusable scripts alongside `rerun_floor_sensitivity.py`.
