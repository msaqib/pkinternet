  # National block-routing census — vantages, phases, slides

Execution plan for the standalone census. **Written:** 2026-09-01. **Owner:** Rayan Atif.

**Sampling rationale, selection flow & detection rules:** `SAMPLING_METHOD.md`.
**Prior work:** Exp 4.1 (`../04.1_small_isp_tromboning/`) — designed this
census and ran it once on 2026-06-27. Everything below is the re-run.

Two things force a re-scope: **the vantage roster is stale** (two of the seven planned probes are
disconnected; one written-off probe is back), and **4.1's coverage was unbalanced 8× across
vantages**, which is what makes its numbers unquotable.

---

## 1. Sources — the vantage points we measure FROM

> **These are not the ISPs being censused.** The targets are the 747 announced blocks of 48 small
> FLL ISPs (`SAMPLING_METHOD.md` §2A). The probes below are the seven places we send traceroutes
> *from*. PTCL, Nayatel, Cybernet, Nova and Z-Com appear here only as vantage points — they are
> never destinations. Tromboning depends on the **sender's transit**, which is why several
> different upstreams are needed to ask the question from.

Probe status checked against the RIPE Atlas probe API on **2026-09-01**.

### Changes since `notes.md:62` (roster dated 2026-06-27)

| Probe | ISP (ASN) | Then | **Now** |
|---|---|---|---|
| 1016154 | Cybernet (AS9541) Karachi | in the 7 | **DISCONNECTED** |
| 64535 | Orbit (AS151983) Faisalabad | in the 7 | **DISCONNECTED** |
| 1016143 | Cybernet (AS9541) Karachi | "recently offline" | **CONNECTED** — back |
| 64722 | TES (AS135407) Karachi | not listed | **CONNECTED** |
| 64078 | TES (AS135407) Rawalpindi | not listed | **CONNECTED** |
| 65892 | Nayatel (AS23674) Islamabad | not listed | **CONNECTED** |
| 1014872 | Fasttel (AS150683) Islamabad | not listed | **CONNECTED** (behind NAT) |
| 1016153 | TES (AS135407) | offline | still disconnected |
| 1016393 | PTCL (AS17557) Mianwali | — | disconnected |

**Orbit AS151983 has no replacement** — 64535 was the only probe in that AS. The "small ISP as a
vantage" transit class is lost unless Fasttel substitutes for it.

### Recommended vantage set

Chosen for **transit diversity** — one probe per distinct upstream — not for geography.

| # | Probe | ISP (ASN) | City | Why this vantage is in the set |
|---|---|---|---|---|
| 1 | **1016126** | PTCL (AS17557) | Karachi | Measuring from the incumbent's network. PTCL is the suspected hairpin transit for others, so seeing what *it* reaches directly is the control. Non-negotiable. |
| 2 | **1015679** | Nova/TPCPL (AS136174) | Lahore | Transworld-transit exemplar. |
| 3 | **7613** | Z-Com (AS152605) | Lahore | Second Transworld-transit vantage — this is what *tests* the transit-clustering assumption rather than assuming it (`notes.md:131`). |
| 4 | **1016036** | Cybernet (AS9541) | Haripur | Cybernet transit. Also 4.1's worst-covered probe (562 traces) — needs a fair run. |
| 5 | **1016143** | Cybernet (AS9541) | Karachi | Restores the intra-AS control that died with 1016154 — same AS, different city, isolates *transit* from *geography*. |
| 6 | **60223** | Nayatel (AS23674) | Islamabad | Independent multi-homed; the well-connected baseline. |
| 7 | **1014872** | Fasttel (AS150683) | Islamabad | Replaces dead Orbit as the small-ISP vantage. **Caveat: NAT.** Validate in Phase 1. |
| 8 | **64722** | TES (AS135407) | Karachi | *Optional.* A transit class absent from the original roster. |

**Deliberately excluded as vantages:** 7764 (PTCL anchor) and 62224 (Transworld) are recorded as
ICMP-filtered and path-invisible; 65892 and 64078 are same-AS duplicates of 60223 and 64722 and buy
no new transit.

Two flags to resolve in Phase 1:

- **62224's ASN disagrees.** `notes.md:73` calls it Transworld **AS38193**; the probe API reports
  **AS45773**. Both map to Transworld-associated registrations, so probably a re-homing — but do not
  quote an ASN we have not checked.
- **1014872 is behind NAT**, which the others are not. NAT does not break traceroute but it changes
  the first hop; confirm it does not confound the detector before promoting it.

---

## 2. Sizing the run

Measured in traceroutes — the unit that sets both probing footprint and elapsed time.

`traceroutes = 747 blocks × K addresses × S vantages`

| Stage | Design | Traceroutes |
|---|---|---|
| Pilot, once | K=8, 150 stratified blocks, 6 vantages | 7,200 |
| Census round × 3 | 6,456 targets, 6 vantages | 38,736 each |
| **Total** | | **123,408** |

**Targets, not blocks.** 725 of the 747 blocks are /24s; the other 22 run from /23 to a single /19.
Sampling at a constant 8 per /24-equivalent gives **6,456 targets** rather than 5,976 — 8% more,
because only 22 blocks are affected (`SAMPLING_METHOD.md` §5.6).

**Why K stays at 8.** The June run measured intra-block agreement directly: on the 1,758
(block, vantage) pairs that received a full K=8, **20.0% were split** — part of the block routes
abroad while the rest stays domestic (`SAMPLING_METHOD.md` §5.5). A smaller K still gets the
majority verdict right — a random K=2 reproduces the K=8 answer 98.6% of the time on unambiguous
blocks — but it cannot *see* that a block is split, because with two samples there is nothing to
compare.

Levers for shrinking the run, in the order to pull them:

1. **Drop a vantage** — costs one transit's view, and you can name which.
2. **Drop a round** — costs intermittency coverage; report a narrower range.
3. **Never cut K** — costs split detection, silently, with no way to tell it happened.

Paced under RIPE's 100-concurrent cap with randomised inter-launch delay.

---

## 3. Phase-by-phase outline

### Phase 0 — Enumerate ✅ *done*
FLL roster → RIPEstat announced-prefixes → **747 blocks** across **48 ISPs**. Full derivation of
every number in `SAMPLING_METHOD.md` §2A. Output: `blocks_all.csv`, `isp_summary.csv`.

### Phase 1 — Freeze and validate the vantage set *(~1 day)*
- **Re-enumerate the block universe.** The 747 blocks are a 2026-06-27 RIPEstat snapshot; it is
  free to refresh and must not be stale when the census starts (`SAMPLING_METHOD.md` §2C).
- **Cross-check the universe against RouteViews.** RIPEstat reflects what RIPE NCC RIS collectors
  can see; a locally-scoped prefix may never reach one. Agreement confirms the universe; a
  discrepancy is itself a finding.
- Re-pull live probe status; freeze the 7 vantages from §1.
- Resolve the 62224 ASN discrepancy and the 1014872 NAT question.
- Smoke-test **TCP/80 Paris traceroute** from each candidate — the ICMP-filtered verdicts on 7764
  and 62224 were reached with ICMP, and TCP/80 may see paths ICMP cannot.
- **Exit criterion:** a frozen, justified vantage list with each probe's path visibility confirmed.

### Phase 2 — Split-rate pilot *(7,200 traceroutes, ~3 days)*
- Stratified sample of **150 blocks** (spread across ISP size and block count), K=8, 6 vantages.
- **Confirms the 20% split rate on a clean, balanced sample.** The June figure comes from the
  1,758 pairs that happened to get a full K=8 inside an unbalanced run, so it is an estimate on a
  subset — good enough to set the design, not good enough to publish.
- Also checks the Exp 04 detector behaves on this target population — in particular, **separates
  genuine detours from last-hop rate limiting**, which produces the same RTT-jump signature
  (`SAMPLING_METHOD.md` §3.4). This may move the 11% headline.
- **Exit criterion:** a split rate measured on balanced data, and confirmation that per-block
  reporting must be three-way (all-local / split / all-detour) rather than binary.

### Phase 3 — Census rounds *(38,736 traceroutes × 3, spread over weeks)*
- All 747 blocks at **8 targets per /24-equivalent** (6,456 targets), 6–7 vantages,
  **R=3 rounds** spaced to catch intermittency.
- **Equal coverage per vantage is a hard requirement.** A round is not complete until every vantage
  has probed every block. This is the single thing that made 4.1's cross-vantage numbers unusable.
- Paced under RIPE's 100-concurrent cap with randomised inter-launch delay.
- **Every run must emit a human-readable `routes_*.txt` alongside the CSV** — never a computed
  verdict without the underlying paths to check it against.

### Phase 4 — Detect *(local)*
Rules and their justification in `SAMPLING_METHOD.md` §3 — geolocation gated by RTT, with an RTT
backstop for invisible foreign hops:
- **trombone** if a hop is geolocated non-PK **and** RTT ≥ 40 ms; **or** a ≥ 60 ms inter-hop jump;
  **or** any hop ≥ 70 ms
- **local** if max RTT stays < 45 ms
- **inconclusive** otherwise — reported, never folded into local
- Carry `reached=` on every trace: the aimed-at IP is usually *not* the last responding hop, because
  small-ISP /24s are sparse. Tromboning is still detectable — the foreign hop appears mid-path,
  before the target.

### Phase 5 — Aggregate *(local)*
- Per-(vantage, block, IP) verdict → per-block consistency → per-ISP trombone rate.
- **Q1:** the vantage × destination × transit matrix — who hairpins whom, through whom, to where.
- **Q2:** `Σ_blocks (trombone?) × (block density)`, density = responders/K from the same pass.
  Report as **"% of active address space,"** never "% of traffic."
- Quote per-ISP rates as a **range across R rounds**, not a single number.

### Phase 6 — Write up what we found
A findings document, not a submission: the matrix, per-ISP rates with round-to-round ranges, the
density distribution, and whatever turned up that we did not plan for (`SAMPLING_METHOD.md` §8 lists
what to look for). Decide about a venue afterwards, on the strength of the results.

---

## 4. Slides

The deck is generated, not hand-maintained. **Edit `make_slides.py` (the `SLIDES` list) and re-run**
— both outputs regenerate together and cannot drift apart:

```
python make_slides.py
```

| File | Use |
|---|---|
| `slides.html` | Present in a browser — arrow keys navigate; prints one slide per page |
| `slides.pptx` | 16:9 PowerPoint, every slide plain editable text boxes |

**27 slides.** The HTML version carries nine SVG figures plus four annotated real traceroutes, all drawn from run data: what a detour
is (a real Lahore-to-Lahore path exiting via Omantel), the destination funnel, what K means on a
256-address block, two real blocks showing agreement vs a split, Brain Telecom's detour rate across
seven vantages, the vantage × destination heatmap, and the six-phase flow with exit criteria.

**Slides 8–10 explain K** from real blocks: what K is, two actual blocks that disagree, and the
measured 20% split rate that settles K=8.

**Slides 18–22 explain the spread**, which is the part that needs the most care: why one headline
percentage hides two independent axes, Brain Telecom seen from seven networks (0.0% from PTCL,
3.8% from Nova — same blocks), why a per-ISP average describes nobody, the full matrix, and the
three worlds the matrix could be describing.

Slide 5 gives the BGP provenance; slide 11 covers the 22 non-/24 blocks; slides 14–16 show real traces — a visible detour through China, the split block side by side, and one the RTT backstop caught with no foreign hop visible. Slide 3 stops the targets-versus-vantages
confusion; slide 19 carries the argument for re-running.

Regenerate HTML only with `python make_slides.py --html` — the PPTX is left alone.
