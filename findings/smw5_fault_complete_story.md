# The SMW5 fault: the complete story, day by day

**What this document is:** a single chronological narrative of the July 2026 SMW5 submarine-cable
fault, assembled from four separate experiments (06, 6.1, 6.1.1, and cross-referenced against 07
and 09) run over several weeks. Every claim below is tagged with the experiment that supports it.
Nothing here is new analysis — it is the existing, verified findings from each experiment, ordered
into one timeline for the first time. Where a claim was tested and *failed* along the way, that is
included too: the story is more credible for showing what didn't survive scrutiny, not just what
did.

---

## Act 0 — The stage, before anything happened

**The structural fact that makes this story possible at all:** only two companies — PTCL and
Transworld (TWA) — are licensed to carry Pakistani traffic abroad. Every other Pakistani ISP is
their customer for international reach. *(Exp 09 — AS Hegemony, global BGP data: 90% of the 291
BGP-visible Pakistani networks depend on PTCL or TWA for the majority of their routes; median
hegemony TWA 0.50, PTCL 0.17.)*

Weighted by actual people rather than network count, this concentration is almost total: of
Pakistan's ~42.3M estimated internet users (APNIC Labs), **99.6% sit behind a network that
majority-depends on PTCL or TWA** — split roughly **70.3% (29.6M) PTCL-majority** and **29.7%
(12.5M) TWA-majority**. *(Exp 6.1.1, W1 — cross-referenced against the W4 population scan.)*

In the weeks before the fault, both operators' upstream carrier mix was stable and unremarkable —
Hurricane Electric sat at a low single-digit share for both (TWA ~2%, PTCL ~7%), with Cogent,
Sparkle, and others carrying the bulk of world-bound traffic. *(Exp 6.1.1, W3a/W3b baseline pulls,
15 May – 10 Jul.)* Pakistan's own RIPE Atlas anchors — external infrastructure, not something we
built — were logging a steady ~176 ms median round trip from roughly 1,000 vantage points
worldwide, with about 1.5% packet loss, day after day. *(Exp 6.1.1, W5 — RIPE Atlas anchor mesh
baseline, 28 Jun – 1 Jul.)*

---

## Act 1 — Onset: 1 July, ~17:00 PKT

The first measurable sign of trouble predates any public statement by roughly a day. **Independent
infrastructure we don't operate** — the worldwide RIPE Atlas anchor mesh, pinging Pakistan's
Z-Com anchor in Lahore continuously — shows its median RTT beginning to climb past anything seen
in the prior three clean days at **1 July, 17:00 PKT**. *(Exp 6.1.1, W5.)*

This is corroborated from a second, completely different data source: Pakistan's own BGP data
(via IIJ's IHR) shows PTCL's route churn already elevated on **1 July** (11.9%), a full day before
anything was announced — the same conclusion, reached independently, from routing-table data
rather than latency data. *(Exp 6.1, control-plane analysis.)*

Neither of these was a blackout. Nothing was withdrawn from BGP, and reachability held. This was
the leading edge of a slow-building congestion event, not a switch flipping off.

---

## Act 2 — Escalation: 2 July, the day of the public announcement

The Pakistan Telecommunication Authority announced the SMW5 fault on **2 July 2026**. By this
point the fault had already been active for roughly 32 hours. *(Exp 6.1.1, W5, comparing the 1 Jul
17:00 PKT onset to the announcement time.)*

**What the independent anchor data shows on the peak day:** the Z-Com anchor's median RTT more
than doubles — from a ~176 ms baseline to a 211 ms daily mean, with the single worst 3-hour bucket
hitting **323.9 ms** — a **78-sigma** event against the prior week's noise floor. Packet loss jumps
from ~1.5% to **7.3%**. *(Exp 6.1.1, W5.)* The PTCL anchor, by contrast, shows only a marginal
bump (statistically close to ordinary noise) — a first hint that the two operators were not
equally exposed, for reasons that become clearer below.

**What the control plane (BGP) shows the same day:** both gateway operators re-carriered a large
share of their world-bound paths — **~20.9% for Transworld, ~13.5% for PTCL** — swinging hard onto
Hurricane Electric as a substitute (TWA: 2% → 20.5%; PTCL: 0% → 14.2%) and away from Cogent and
Sparkle. *(Exp 6.1.)*

**What actual users' connections looked like:** the project's direct 12-hour monitoring window
(which itself started already inside the degraded period — a limitation revisited below) found
international destinations (foreign sites, CDN edges not cached locally) elevated and erratic,
while domestic Pakistani content stayed completely flat throughout. The damage was **concentrated
on PTCL-sourced paths** specifically — RTT +12%, jitter +50% relative to the later recovered
state — against a milder, more diffuse pattern elsewhere. *(Exp 06.)* This matches the anchor data:
PTCL's much larger population footprint (29.6M majority-dependent users, vs TWA's 12.5M) rode a
gateway whose customers' international paths were measurably worse during this window than TWA's.

**Did the underlying dependency structure move?** Almost not at all. Of Pakistan's BGP-visible
networks, only **1 exception out of 8 directly-probed ISPs** changed its majority gate: **Fasttel**
swapped from PTCL-majority (0.74) to TWA-majority (0.54) for about two days, then reverted. *(Exp
6.1.)* Scaled to the whole country, this pattern held: of 273 gate-dependent Pakistani networks
nationally, only **4 (1.5%) switched** their majority gate at all, with a further **12 (4.4%)**
showing a smaller Fasttel-like re-balance short of a full switch. *(Exp 6.1.1, W4.)* Weighted by
population rather than network count, the number is even more stark: **99.63% of Pakistan's
matched ~42.1M users** were on networks whose gate never moved — every one of the 15 largest
Pakistani ISPs by estimated population held its position throughout. *(Exp 6.1.1, W1.)*

**The headline shape of the day, in one sentence:** the disruption was absorbed almost entirely
*above* the duopoly — in the two operators' own choice of which foreign carrier to lean on — while
the relationship between ordinary Pakistani networks and their two gateways stayed essentially
fixed, and the resulting user-facing symptom was congestion and jitter on international paths
(concentrated on PTCL's much larger customer base), not an outage anywhere.

---

## Act 3 — Recovery: 3 July

By the next day, every independent signal points the same direction. The project's own 12-hour
monitor (running into the early hours of 3 July) shows the worst-hit PTCL paths collapsing:
`shophive.com` 646 ms → 278 ms, `telemart.pk` 472 ms → 268 ms, `balochistan.gov.pk` 389 ms →
281 ms — and, notably, this improvement happened *despite* the later readings falling in
business-hours peak traffic rather than the off-peak period of the earlier readings, which rules
out a simple diurnal effect. *(Exp 06.)*

The recovery was not uniform, though — worth stating honestly rather than rounding off. **Fasttel**
got *worse* mid-window on several sites (e.g. `shophive` 122 → 227 ms), consistent with a small
ISP's own upstream having rerouted onto a worse alternate path partway through the event. *(Exp
06.)*

The independent anchor data confirms full recovery by the next full day: Z-Com's median RTT is
back to 173.4 ms and loss back to 1.5% on **3 July**, and stays there on the 4th. *(Exp 6.1.1,
W5.)* The BGP data shows the same: the operators' carrier mix reverts, and Fasttel's gate swap
reverts, within the same window. *(Exp 6.1.)*

**Was this an actual repair, or a workaround?** Two independent lines of evidence, using two
different methods, agree it was the latter. First, the project's own hop-by-hop path comparison
found that of 252 (probe, target) pairs, the 93 whose path changed almost all did so *within the
same transit provider* — the same country, the same upstream, just a different load-balanced
link — with the exit carrier staying constant throughout. *(Exp 06, Finding 5.)* Second, entirely
independently, the anchor-mesh data shows the same recovery *speed* (full normalization within
~24–36 hours of onset) — far too fast for an actual undersea splice, which normally takes
considerably longer. *(Exp 6.1.1, W5 addendum.)* **Conclusion, stated as carefully as the evidence
allows: the network rerouted around the fault and stabilized quickly; nothing in this project's
data shows the cable itself being physically repaired in this window, and the fast recovery speed
is itself evidence against that reading.**

---

## Act 4 — Settling: the following weeks

There is an honest gap here: the anchor-mesh pull used for onset/recovery only runs through 5
July, so there is no independent RTT evidence, in this project, for 6–10 July specifically. *(Exp
6.1.1, W5 addendum — stated as an open gap, not closed.)*

What *is* available is a second, completely separate dataset: the project's flagship 7-day
panel, run **11–18 July** — more than a week after the fault — found the entire window
**event-free**. Daily tromboning rates across the whole week sat in a tight 14.5–15.9% band with
no anomalous days. *(Exp 07.)* This doesn't extend the anchor signal itself, but it is independent
confirmation, from a third data source and method, that whatever was happening 1–3 July had fully
settled well before this later measurement began.

---

## Act 5 — The stress test: what survived being checked, and what didn't

This part of the story matters as much as the timeline itself, because it's what makes the
surviving claims trustworthy rather than convenient. Exp 6.1's original control-plane analysis
produced one claim that did not hold up, and the process of finding that out is itself part of the
record.

**The claim that failed:** early analysis suggested the *size* of the operators' churn on 1–3 July
was itself unusual — TWA's fault-day churn ranked in the top 5% of a 56-day distribution. *(Exp
6.1.1, W3a.)* To test this properly, the same metric was run against four control operators: two
on other SMW5 landing branches (Oman, Sri Lanka — testing whether the fault was Pakistan-specific),
and two with **zero SMW5 exposure at all** (landlocked Nepal, and Vietnam on unrelated cables —
the strictest placebo available). Every single control, including the two with no SMW5 link
whatsoever, ranked at or near the top of its *own* churn distribution on the same two days — even
after correcting for a data-completeness gap that had already been shown to inflate exactly this
kind of number. **Verdict: the churn-magnitude elevation on 1–3 July was a global phenomenon, not
a Pakistan or SMW5 signal, and the claim was retracted everywhere it had been made.** *(Exp 6.1.1,
W3b.)*

**What survived, tested against the same controls:** decomposing each operator's carrier mix
carrier-by-carrier, the swing onto Hurricane Electric specifically was **2–8× larger** in the three
operators with a real physical link to SMW5 (TWA +9.1 points, PTCL +7.1 points, Sri Lanka's SLT —
itself an SMW5 landing country — +13.2 points) than in the two confirmed-unrelated controls
(Nepal +1.5 points, Vietnam +3.8 points). This carrier-specific, placebo-tested fingerprint is what
the SMW5 attribution now rests on — not the size of the churn, but the specific, disproportionate
identity of what replaced it. *(Exp 6.1.1, W3b.)*

**A related false lead, resolved separately:** the same baseline pull turned up an even *larger*
churn spike on 30–31 May, unconnected to SMW5. Decomposing it showed a real, one-day loss of
Hurricane Electric capacity on both operators, reverting exactly the next day — and a plausible
physical cause was found independently: a severe Lahore rainstorm and power outage on 30 May.
*(Exp 6.1.1, W3a addendum.)* This event has the *opposite* signature to the SMW5 fault (Hurricane
was lost, not gained) and is flagged as a candidate cause, not proven — but its existence, and the
fact that it was checked and distinguished rather than confused with the SMW5 event, is itself
evidence that this project's churn-spike detection tracks real physical incidents rather than
noise.

---

## What this story does and doesn't let us claim

**Solid, multiply-confirmed claims:**
- The fault was live from **1 July, ~17:00 PKT**, roughly 32 hours before the public announcement —
  confirmed independently by both BGP data (Exp 6.1) and external RTT infrastructure (Exp 6.1.1,
  W5).
- It was a **degradation, not a blackout** — reachability held throughout, only latency/jitter
  suffered, and only on international paths (Exp 06, Exp 6.1.1 W5).
- **Domestic dependencies stayed almost entirely frozen** at both the ISP level (Exp 6.1) and
  national, population-weighted scale (Exp 6.1.1, W1/W4) — the duopoly absorbed the shock upstream.
- **Recovery was a reroute, not a repair**, confirmed by two independent methods (Exp 06's hop-path
  tracing and Exp 6.1.1's anchor-mesh timing).
- **~29.6M PTCL-majority users** were behind the gateway whose paths our own direct measurement
  found most degraded; **~12.5M TWA-majority users** behind the other.

**Explicitly not claimed, and why:**
- **How many people actually experienced a worse two days** — as opposed to how many were
  *exposed* to the possibility — is not answerable with this data. RIPE Atlas measures paths and
  latency, not traffic volume, and "majority-dependent" ranges from near-100% down to barely-over-
  half for some networks, so the exposure estimate above is a bound, not a headcount of harm.
- **Whether the physical cable was actually spliced during this window** — the evidence points the
  other way (a reroute, recovering too fast for a real repair), and no carrier↔cable mapping exists
  yet to say definitively (Exp 6.1's W6, blocked on an external reply).
- **What happened 6–10 July specifically** — a genuine gap between the anchor-mesh pull and the
  next independent dataset (Exp 07's panel, starting 11 Jul).

**Sources, in one place:**
`findings/06_submarine_outage.md` (Exp 06, direct 12 h monitor) ·
`findings/06.1_submarine_hegemony.md` (Exp 6.1, control-plane) ·
`experiments/06.1.1_smw5_robustness/notes.md` (Exp 6.1.1, all robustness checks W1–W5) ·
`findings/09_as_hegemony.md` (Exp 09, structural duopoly) ·
`findings/07_longitudinal_panel.md` (Exp 07, the later clean-week cross-check).
