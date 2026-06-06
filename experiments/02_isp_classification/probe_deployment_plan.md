# Probe Deployment Plan — 20 Probes for ISP Classification

## Purpose

We are preparing **20 RIPE Atlas probes** to send to volunteers on different
Pakistani ISPs. Where these probes land *is* the experimental design — it
determines which research questions we can answer. This document records the
design options so we can choose deliberately.

(These 20 are in addition to the **5 existing probes**: Transworld ×2
[AS38193, AS136174], PTCL [AS17557], Nayatel [AS23674], Z-Com [AS152605].)

## What the deployment must serve

| Goal | What it needs from probe placement |
|------|------------------------------------|
| **Set 1/2/3 classification** (is an ISP at PKIX, and does it actually peer?) | A vantage (probe) on as **many distinct PKIX-member ISPs** as possible — breadth |
| **RQ1** — is Set-3 customers' experience better than Set-1/2? | Probes spread across a **mix of Set-2 and Set-3 ISPs**, measuring to common local servers — breadth |
| **RQ2** — do all customers of the *same* ISP get similar service? | **Multiple probes on the same ISP**, in different homes/cities — depth |

The central tension: classification + RQ1 want **breadth**; RQ2 wants **depth**.
20 probes cannot maximise both — the breadth/depth ratio is the key decision.

## Two design principles (hold regardless of the option chosen)

1. **Concentrate in the IXP cities — Islamabad, Karachi, Lahore.** Local exchange
   is only testable where a PKIX node exists. A probe in a non-IXP city can still
   measure hairpinning but cannot test "did A and B peer locally." Keep only 1–2
   non-IXP-city probes as contrast.
2. **Probes on PKIX members unlock probe-to-probe.** Holding probes on both ISP A
   and ISP B gives a clean **two-way** inter-ISP test (A→B and B→A) with no need
   for a found host, and lets us build a full **peering matrix** among placed
   probes. This favours clustering probes on PKIX members in the *same* city —
   within-city pairs are exactly where IXP exchange should occur.

---

## The three allocation options

### Option A — Balanced (recommended)
```
Breadth: 12 distinct PKIX members (1 probe each)
Depth:    2 anchor ISPs × 3 probes (different customers/cities)  → RQ2
Control:  2 non-PKIX (Set-1) ISPs                                → baseline
```
- Covers ~15 of ~21 members (3 existing + 12 new).
- Answers set-classification and RQ1 well; RQ2 **partially** (2 anchor ISPs).
- Best all-rounder.

### Option B — Breadth-first
```
Breadth: 18 distinct PKIX members (1 probe each)
Control:  2 non-PKIX (Set-1) ISPs
```
- Covers ~21 of ~21 members → near-complete peering matrix, strongest Set 2/3
  classification.
- **RQ2 not answerable** — no within-ISP replication.

### Option C — Depth-first
```
Depth: ~5 ISPs × 4 probes (different cities/customers)
```
- Strong RQ2 (intra-ISP consistency) on a few ISPs.
- Covers only ~5 of ~21 members → weak classification and RQ1.

**Decision pending.** Trade-off summary:

| | ISP coverage | Set 2/3 classification | RQ1 | RQ2 |
|---|---|---|---|---|
| A — Balanced | ~15/21 | good | good | partial (2 ISPs) |
| B — Breadth | ~21/21 | strongest | strong | none |
| C — Depth | ~5/21 | weak | weak | strong |

---

## PKIX member roster (from PTA Peering Roadshow slide, May 2026)

Physical presence = Set 2/3 candidate. Any FLL licensee **not** listed = Set 1.

| Islamabad (HEC, 2017) | Karachi (HEC, 2019) | Lahore (PITB, 2023) |
|---|---|---|
| Cybernet | Connect | Brain Net |
| HEC/PERN | Cybernet | Cybernet |
| Multinet | GCS | KK Networks |
| Nayatel | HEC/PERN | Multinet |
| PTCL/Ufone | Multinet | Nexlinx |
| Telenor | Satcom | PITB |
| Transworld (TWA) | Telenor | SIGN IN |
| Virtury (?) | Transworld (TWA) | Transworld (TWA) |
| Wateen | Connect | Wateen |
| Wi-Tribe | | Web Concepts |
| Worldcall | | Well Networks |
| | | WIDE Project Japan* |
| | | Ylinx |

\* WIDE Project Japan = the M-Root DNS operator (research infra, not a commercial ISP).
Multan node is "in pipeline" (2025).

**Unconfirmed / to verify:** slide colour coding (Cybernet/PTCL/Transworld blue,
Telenor green — meaning unknown); whether **Z-Com** is actually a PKIX member
(not on this slide, though an earlier text list placed it at Lahore); OCR-uncertain
names "Virtury", "SIGN IN", "Satcom".

## Current measurement coverage

| PKIX member | Have a PROBE? | Have a HOST? (from exp-01) |
|---|---|---|
| Transworld | ✅ ×2 | — |
| PTCL | ✅ | — |
| Nayatel | ✅ | — |
| Multinet | — | ✅ pseb, dunyanews |
| HEC/PERN | — | ✅ hec.gov.pk |
| PITB | — | ✅ punjab.gov.pk |
| Cybernet | — | ⚠️ moitt/pakistan/railways (but these hairpin via US Prolexic — bad targets; need a clean Cybernet-hosted host) |
| Telenor, Wateen, Wi-Tribe, Worldcall, Connect, GCS, Satcom, Brain Net, KK Networks, Nexlinx, SIGN IN, Web Concepts, Well Networks, Ylinx, Virtury | ❌ | ❌ |

So today we can only classify the few ISPs where we hold a probe or a clean host.
The ~14 uncovered members are the gap the 20 probes should fill.

## Recruitment wishlist (volunteer-driven)

Because probes go to volunteers, the practical output is a **prioritised wishlist**
— "we most want volunteers on these ISPs in these cities" — and we slot probes as
volunteers appear. Priority order:
1. Big consumer ISPs that are PKIX members and we don't yet cover (Cybernet/
   StormFiber, Wateen, Telenor, Multinet, Nayatel-extra).
2. City-specific members in their IXP city (Nexlinx/Brain Net/KK/Ylinx in Lahore;
   GCS/Connect/Satcom in Karachi).
3. A couple of **non-PKIX** ISPs as Set-1 controls.
4. For RQ2: 2–3 extra probes on each chosen anchor ISP, in different
   homes/cities.

## Open decisions

- [ ] Choose allocation option (A / B / C).
- [ ] If A or C: which ISPs are the depth "anchors"?
- [ ] Confirm Z-Com's PKIX membership status.
- [ ] Obtain **PKIX peering-LAN prefixes** per location — the single external
      input that lets a traceroute *prove* direct IXP exchange (Set 3) rather than
      infer it from RTT. (Sources: PeeringDB IX record, IXP operator, or PTA.)
- [ ] Decide directionality rule (require both-direction evidence for Set 3?) and
      whether ISP-level result is binary or graded ("peers with N of M members").
