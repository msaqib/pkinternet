# Writing-style notes — "Is It Really Worth to Peer At IXPs?" (our closest template)

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
