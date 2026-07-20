# Evidence file — RQ3 "flapping" pairs: what's genuine, what's noise, and why

**Claim being checked:** paper §RQ3 — *"193 (43%) of pairs flap... 83% of the pairs that ever
trombone are also served by a domestic path during the week — for the overwhelming majority of
hairpinning traffic, the international detour is a routing choice, not a necessity."*

**Verdict: the arithmetic (43%, 83%) is correct. The interpretation is not.** Checking the actual
AS-path behind every trombone-flagged round shows that for most of these pairs, the "hairpin"
verdict fires without the underlying route changing at all — it's RTT measurement noise crossing a
classification threshold, not evidence of an alternate path being taken. The number that should be
cited as evidence of "choice" is **33%, not 83%** — see below.

This file exists so the claim can be checked directly, not taken on trust: what happened, on which
probe/target/timestamp, why (mechanism), and what the raw data looks like.

---

## The method, precisely

For every pair that was ever flagged `tromboned=True` at least once (233 pairs, on the paper's
14-probe roster, Pakistan-class targets, ≥50 rounds), each trombone-flagged round was checked
against the round immediately before it, using the actual hop-IP sequence mapped to ASNs (not the
verdict, the real path):

- **Genuine:** the AS-path differs between the two rounds, and the difference isn't explainable by
  hops merely failing to respond (the same "visibility artifact" test used in `route_changes.md`'s
  Mechanics section — is one round's responding hops a subsequence of the other's?).
- **Noise:** the AS-path is identical, or the apparent difference is just some hops going quiet —
  the packets took the same route; only the measured RTT (and therefore the verdict) changed.

Reproduced from `.paths_series.json` (built from the raw archive) joined to the panel CSV's
verdict column; the classification script is ad hoc, output saved to
`evidence_rq3_pairs_classified.csv` (233 rows, one per pair, with noise/genuine counts).

## The numbers

| | count | share |
|---|--:|--:|
| Ever-trombone pairs checked | 233 | — |
| Pairs with **≥1 genuine** (AS-path-confirmed) hairpin | **77** | **33.0%** |
| Pairs where **every** trombone flag is noise | **156** | **67.0%** |
| Total trombone-flagged rounds | 10,756 | — |
| ...of which genuine | 1,202 | **11.2%** |
| ...of which noise | 9,495 | **88.3%** |

**By ISP** (share of a probe's ever-trombone pairs that have ≥1 genuine confirmation):

| ISP | genuine pairs / total | share |
|---|--:|--:|
| Fasttel | 27 / 36 | 75% |
| Cybernet | 16 / 33 | 48% |
| Nayatel | 9 / 21 | 43% |
| PTCL | 6 / 37 | 16% |
| TES | 4 / 26 | 15% |
| **Transworld** | **0 / 13** | **0%** |
| **Z-Com** | **0 / 17** | **0%** |

## Where and why — two distinct mechanisms, both making the same mistake possible

### Mechanism 1: near-zero path visibility (Transworld)

**Where:** probe `transworld.62224` → `fgeha.gov.pk`. 44% of this pair's 168 rounds are flagged
trombone; **87 verdict flips** across the week. Every single one is noise — the pair has exactly
**one** AS-path for the entire week.

**What it looks like** (raw hop IPs, consecutive rounds):
```
16:59 PKT  10.102.76.1 -> 172.25.3.14 -> * -> * -> * -> * -> * -> 203.101.184.78
17:59 PKT  10.102.76.1 -> 172.25.3.14 -> * -> 203.101.184.78
18:59 PKT  10.102.76.1 -> 172.25.3.14 -> * -> 203.101.184.78
```
**Why:** Transworld's probe is already documented elsewhere in this project as fully ICMP-filtered
— no intermediate hop ever responds. The only thing the classifier has to work with is destination
RTT, which apparently sits close enough to the 40/60/70 ms cutoffs that ordinary jitter flips the
verdict on roughly every other round. Nayatel (also independently documented as mostly-timeout)
shows the same pattern and is the next-worst ISP by genuine-confirmation rate (43%).

### Mechanism 2: full path visibility, still noise (Z-Com)

This is the more important one, because it rules out "it's just the blind probes." **Where:**
probe `zcom.7613` → `careers635.com.pk`. Every round, all 7 hops, resolves to a real IP — no `*`
anywhere:
```
192.168.100.1 -> 110.93.205.184 -> ... -> 10.253.20.226   (identical, every round, hop_count=7)
```
Out of ~168 rounds this pair is flagged trombone exactly **once** — 15 July, 21:00 PKT — with
`hop_count` still 7 and `exit_cc` unresolved (`?`). The path is provably unchanged; only that one
round's RTT crossed the line. **Why:** even a fully visible, completely stable path has ordinary
internet jitter, and a hard RTT cutoff will occasionally be crossed by chance alone, with zero
routing explanation. Z-Com's 0% genuine-confirmation rate (same as Transworld, for a completely
different reason) shows this isn't only a blind-probe problem — it's an inherent property of any
threshold classifier applied to noisy RTT.

### The genuine cases do exist, and look completely different

**Where:** probe `fasttel.1014872` (75% genuine-confirmation rate, the best of any ISP) —
already documented in `route_changes.md` §Mechanics: at 12:00 PKT on 11 July this pair's path was
`... -> PTCL AS17557 -> PTCL-bb AS9557 -> ... -> CYBERNET AS9541`; one hour later, `... -> TWA
AS38193 -> TWA backbone (unannounced) -> CYBERNET AS9541`. Different gateway operator, different
ASNs, same destination. This is what a genuine hairpin-vs-local (or gate-vs-gate) switch actually
looks like in the raw data — nothing like the Transworld/Z-Com examples above, where the "switch"
is invisible in the path and only visible in a noisy RTT reading.

## What this means for the paper's claims

- **The 43%/83% arithmetic stands** — those are correctly computed from the verdict column.
- **The interpretive claim does not stand as written.** "83% of ever-trombone pairs are also
  served locally... the detour is a routing choice" implies the flip demonstrates the network
  choosing between two real paths. For 67% of those pairs, no such choice is demonstrated — the
  path never changed; the reading did.
- **The defensible replacement claim: 33% (77/233)** of ever-trombone pairs have at least one
  AS-path-confirmed instance of actually taking a different route — this is the number that
  supports "the detour is sometimes a choice," and it should be cited instead of 83%.
- The **23 pairs carried by both PTCL and Transworld** (already in the paper, from
  `route_changes.md`) are a subset of this genuine-77 group and remain the strongest single piece
  of evidence — a literal gate change, unambiguous in the AS-path.
- The **49% "genuinely re-route at the AS level"** figure already in the paper (from
  `route_changes.md`'s Mechanics section) was computed with almost this same discipline already —
  it is a *different, broader* population (all pairs, not just Pakistan-class ever-trombone pairs)
  and a *looser* per-round-pair test, which is why it doesn't match 33% exactly; the two numbers
  are not measuring identical things and should not be casually swapped for one another without
  checking, which is exactly why this file exists.

## Reproducing this

```bash
cd experiments/07_longitudinal_panel/analysis
# requires .paths_series.json (built earlier from the raw archive) and hop_annotations.csv
# classification logic is currently ad hoc; see this file's history for the script,
# or the CSV output: evidence_rq3_pairs_classified.csv
```
