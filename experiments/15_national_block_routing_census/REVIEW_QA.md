# Review questions, and answers

**Questions from Dr Saqib's handwritten review, 13 September 2026.** Each question is
reproduced as transcribed, so misreadings can be corrected. Where a question is quoted in
`"quotes"` it is a phrase from our own documents that he flagged as unclear.

Status on each answer:

| | |
|---|---|
| **Answered** | resolved from data or code, with the file named |
| **Partly** | answered as far as the data goes, with the remainder stated |
| **Open** | a genuine gap, not just an explanation gap |
| **Action** | he is right and something must change |

---

## A. Open threads

### A1. PERN, Fasttrack, Nova, Z Com etc — which are PTCL customers and which are TWA customers?

**Partly answered.** We cannot see commercial relationships, but we can see which transit
network our packets actually cross to reach each destination. From the 34,191 selected
traces, taking the last different ASN before entering the destination network:

| destination | traces | transit we observed |
|---|--:|---|
| PERN (AS45773) | 182 | **Transworld 99%** |
| Z Com (AS152605) | 85 | **Transworld 99%** |
| Cybernet (AS9541) | 777 | **Transworld 88%**, Mobilink 9% |
| Nayatel (AS23674) | 663 | Transworld 76%, **PTCL 16%** |
| Wateen (AS38264) | 1,088 | Transworld 56%, CMPak 26%, LinkDotNet 12% |
| Multinet (AS9260) | 554 | Cogent 53%, Transworld 44% |
| Connect (AS132165) | 207 | **PTCL 63%**, Transworld 28% |
| Optix (AS136384) | 244 | LinkDotNet 59%, Multinet 39% |
| Transworld (AS38193) | 377 | Mobilink peering 99% |
| PTCL (AS17557) | 23,593 | Mobilink peering 100% |

**Two caveats that limit this.** It is the **forward path from one vantage** (Mobilink),
so it shows the route our packets took, not a customer relationship: an ISP can buy from
several transits and we would only see the one chosen for our traffic. And PTCL and
Transworld appear at the top of the table partly because they *are* the two big transits,
so a high share is expected rather than informative.

**Fasttrack (AS7605) and Nova produced no traces.** Fasttrack had no live host selected;
"Nova" does not match any holder string in `1_universe/asn_holder.json`, so the ASN needs
naming before it can be looked up.

*Source: `3_routes/selected_annotated.json`, `1_universe/block_to_asn.json`.*

### A2. Pending analysis on routing changes for Cybernet in July

**Open.** Not started. This experiment is a single snapshot taken 8 to 10 September 2026
and holds no July data. The longitudinal comparison belongs in the follow-on experiment.

### A3. RIS vs RouteViews — confirm

**Open, and worth stating plainly.** Everything in this experiment that touches BGP comes
from **RIPEstat**, which is fed by **RIS**. RouteViews has not been consulted at all, so
we have no cross-check on route origin. This matters directly for A4 and B3 below, where
a RIS-only view is currently doing load-bearing work.

### A4. Announcing foreign IPs — is it automatic or manual?

**Answered.** Manual. A network announces a prefix only if its operators configure BGP to
originate it. Nothing about holding or leasing address space causes it to be announced.
That is what makes the distinction in B3 meaningful: announcement is a deliberate
operational act, registration is paperwork.

### A5. "What is observers?" — the RIS sense

**Answered, and it turned out to be the key to C2.**

In RIS, an **observer** is a **route collector** (`rrc00` to `rrc26`) together with the
**peer ASNs that feed it**. A prefix is not simply "announced" or "not announced": it is
announced *as seen by some number of peers*. RIPEstat currently reports **324 IPv4 RIS
peers**.

This matters because **different RIPEstat endpoints apply different visibility rules and
disagree with each other.** For `149.40.192.0/19` today:

| endpoint | what it says |
|---|---|
| `routing-history` | originated by **both AS174 and AS45669**, continuously through 2026-09-13 |
| `prefix-overview` | `announced: true`, origin **AS174 only** |
| `routing-status` | **0 of 324** peers seeing it, origins `[]` |
| `announced-prefixes` for AS45669 | does **not** list it |

All four describe the same prefix at the same moment. `routing-history` reports every
origin any peer ever saw; the others report a single origin filtered by visibility.

**Consequence for this experiment.** Our universe was built from `announced-prefixes`,
which is one of the filtered views. Announcement should be recorded as a **count of
observers, not a boolean**, and the origin should be recorded as a **set**, since a
lessee's more-specific and the registrant's covering prefix are frequently both announced.
Neither is currently done.

This also bears on A3: with a single collector system we cannot tell "few peers see it"
from "it is not announced". RouteViews would be an independent set of observers.

## B. The write-up generally

### B1. Write a narrative like a research paper, e.g. "rules, not thresholds"

**Action, and already partly done.** `5_detector/RULES.md` now opens with exactly that
framing: *"A rule here is a procedure, not a number."* Every threshold is derived from
measurement, and the one remaining constant is the speed of light in fibre. What is still
missing is a single narrative document; the material is spread across `EXPLAINER.md`,
`SWEEP_FINDINGS.md`, `RULES.md` and `WORKED_EXAMPLE.md`.

### B2. Blocks ≠ hosts, so comparison becomes weird. Add IPs

**Action. He is right, and it is a real defect.** We report block counts and host counts
side by side without their denominators, which invites the wrong comparison.

The three quantities are different and should always appear together:

| | count | what it is |
|---|--:|---|
| Addresses in the universe | 5,774,336 | every IP in Pakistan's announced ∪ registered space |
| Addresses actually tested | 844,102 | 14.6% of the above; the rest were never probed |
| Live hosts found | 43,737 | **5.2% of what was tested**, not 0.76% of the space |
| /24 blocks | 22,556 | the routing unit, 256 addresses each |
| Blocks with any life | 5,887 | 26% of blocks |

A block is not a host and neither is a proxy for the other: block counts measure how much
*address space* is affected, host counts measure how many *machines* we found, and the
second is a floor bounded by our sampling. `ISP_SUMMARY.md` was corrected to carry
`checked` beside `live hosts`; the same correction is still needed elsewhere.

### B3. "Neither contains the other": one might think announced is a subset of assigned. Why isn't that true?

**Answered.** The two sets are built from different sources and neither is a subset:

* **Assigned but not announced.** A block registered to a Pakistani holder that nobody
  currently originates in BGP. We found **1,209 such /24 blocks**, holding 60 live hosts
  between them. Registered space is not used space.
* **Announced but not assigned to Pakistan.** A Pakistani network originating space whose
  registry country is elsewhere, usually because it was leased or transferred faster than
  the registry was updated. **252,672 addresses**, 4.4% of the routed country.

The intuition that announced ⊆ assigned assumes an operator can only announce what is
registered to it. BGP has no such rule. Origin validation is advisory, and plenty of
legitimately leased space is announced by a holder other than the registrant.

*Source: `1_universe/UNIVERSE_FINDING.md`, `1_universe/unannounced_blocks.json`.*

---

## C. UNIVERSE_FINDING

### C1. Include the registered owners of the prefixes as well

**Action, not done.** The table lists only the announcing party. It should carry both
columns, registrant and announcer, since the whole point is that they differ.

### C2. Verify these prefixes are not also announced by their original owner. Careful about route summarisation

**Answered, and the answer is yes: the original owner does also announce them.** His
concern is correct, though not in the way I first reported it.

Checking `routing-history`, which lists every origin any RIS peer saw rather than a single
filtered one:

| prefix | we credited | confirmed? | also announced by registrant |
|---|---|---|---|
| `154.192.0.0/16` | AS23674 Nayatel | **yes**, to 2026-09-13 | no |
| `154.80.0.0/17` | AS45669 | **yes**, to 2026-09-13 | no |
| `149.40.192.0/19` | AS45669 | **yes**, to 2026-09-13 | **AS174 Cogent** |
| `205.164.128.0/19` | AS136384 Optix | **yes**, to 2026-09-13 | **AS174 Cogent** |
| `154.57.208.0/20` | AS135407 TES | **yes**, to 2026-09-13 | **AS174 Cogent** |

**Our attribution is confirmed in all five cases.** An earlier draft of this document said
four of five failed; that was wrong, and it was wrong because it used `prefix-overview`
and `routing-status`, which report a single visibility-filtered origin and returned AS174
or nothing. `routing-history` shows both origins running in parallel.

**What is actually happening, and it refines the finding.** In three of five cases the
Pakistani network announces a **more-specific inside the registrant's covering
announcement**. Cogent announces the covering space as the registered holder; the
Pakistani lessee announces the smaller block it actually uses. Both are live at once, and
traffic follows the more-specific.

So the phrasing "announced from Pakistan but registered elsewhere" is accurate but
incomplete. It should read: *announced from Pakistan as a more-specific, often inside a
covering announcement still originated by the registrant.*

**Two things to fix, both real:**

1. **Record the origin as a set, not a single ASN**, and derive it from `routing-history`
   rather than a filtered endpoint. `build_pk_universe.py` does not record which ASN
   announced which prefix at all, so the table's attribution could not be checked from our
   own artifacts, only re-derived.
2. **Record observer counts** per prefix (see A5), so "announced" carries its visibility.

**The headline figure is not affected.** All 192 `announced_only` prefixes totalling
exactly 252,672 addresses remain in the set, since membership depends on a Pakistani ASN
originating the prefix, which `routing-history` confirms.

*Source: RIPEstat `routing-history`, `routing-status`, `prefix-overview`,
`announced-prefixes`; `1_universe/universe_split.json`.*

### C3. I do not get "the distinction is sharp and checkable"

**Answered — and the sentence should be rewritten.** It refers to telling *leasing* apart
from *squatting*. Both look like "a Pakistani network using foreign-registered space", but:

| | leased | squatted |
|---|---|---|
| Announced in BGP by the Pakistani network | **yes** | **no** |
| Example | `149.40.192.0/19` | `149.40.227.0/24` |
| Interpretation | ordinary address leasing | internal use of space nobody announces |

"Checkable" means the test is mechanical: look for a matching BGP announcement. Given C2,
the worked example in that sentence is now itself in doubt, which is an argument for
rewriting the passage around a case we have re-verified.

### C4. "the pair is more informative than either alone"

**Answered.** It refers to the two RTT measurements of `149.40.227.0/24`. From Z Com it
answers in 1.1 ms; from our vantage the median is 59.5 ms. Both are correct and the
combination says something neither says alone: an address that is one hop from Z Com and
many hops from Mobilink is infrastructure *inside* Z Com's reach, not a host in Ashburn.
The sentence assumes the reader has both figures in view and should say so.

### C5. The blocks we pick — are they 1-to-1 matched to announced and assigned prefixes?

**Answered. No, and the mapping is one-to-many.**

| | count |
|---|--:|
| Prefixes in the universe | 932 |
| /24 units we scan | **22,556** |
| Prefixes exactly /24 | 246 |
| Prefixes larger than /24, split into many blocks | **686** |
| Prefixes smaller than /24 | 0 |

Everything larger than a /24 is cut into /24-sized units so that sampling density is
uniform. Without that, a /16 and a /24 would each receive the same 8 samples despite
being 256 times different in size. So one announced prefix commonly becomes dozens or
hundreds of blocks, and **a per-block count is not a per-prefix count**.

*Source: `1_universe/pk_universe.json`, `2_liveness/scan_all_pk.py`.*

---

## D. Sampling and liveness

### D1. Convert the rule in `scan_all_pk.py` to proper pseudocode

**Action, done here:**

```
for each /24 block B:
    seen  <- addresses of B already probed by any earlier scan
    live  <- live hosts already known in B
    pool  <- shuffle(hosts(B) \ seen)           # WITHOUT replacement
    rounds <- 0
    while pool nonempty and |seen| < 64 and live < 8:
        batch <- take 8 from pool
        rounds <- rounds + 1
        for ip in batch:
            result <- check(ip)                 # ICMP, else TCP/80, else TCP/443
            seen <- seen + {ip}
            if result is alive: live <- live + 1
            append (ip, result) to disk         # dead results are kept too
        if live = 0 and rounds >= 2: break      # two empty draws, abandon
    record live count for B
```

Note the target is re-tested **per draw, not per address**, so a block can finish above 8.
Measured: 1,012 blocks (17.2% of live blocks) ended above 8, one at 92.

### D2. Why does exp 16.1 "need" 8 panel size?

**Open. It is an assumption, not a derivation.** The stated reason is that a longitudinal
experiment re-measuring the same addresses over months needs spares as hosts go away, and
8 gives redundancy. **No decay measurement supports the number 8.** What would settle it
is measuring how many of a block's live hosts still answer after one month, and choosing
the panel size from that. Not done.

### D3. Is sampling with replacement or without?

**Answered: without.** `scan_all_pk.py` builds `pool` by excluding every address already
in `seen`, and `seen` is loaded from all prior scan files. No address is ever probed twice
by the sampler. The top-up pass does the same, which is why its live hosts sit on
addresses the first pass never tried rather than on addresses it got wrong.

### D4. Can we calculate the probability of 16 consecutive dead IPs?

**Answered, and the answer is uncomfortable.** Sampling is without replacement, so this is
hypergeometric over 254 usable addresses:

| true live hosts in block | density | P(all 16 draws dead) |
|--:|--:|--:|
| 1 | 0.4% | **93.7%** |
| 2 | 0.8% | 87.8% |
| 3 | 1.2% | 82.2% |
| 5 | 2.0% | 72.0% |
| 8 | 3.1% | **59.0%** |
| 13 | 5.1% | 42.0% |
| 26 | 10.2% | 16.8% |
| 51 | 20.1% | 2.4% |

**The two-empty-draw rule abandons a block holding 8 live hosts 59% of the time.** This
is a much larger effect than the write-up implies, and it is a property of the design, not
of the network. Any statement about "blocks with no life" must carry it: we measured
**16,669 blocks as empty**, and a substantial share of them are not.

This does not bias the tromboning result, which conditions on blocks that were traced, but
it does mean **block-level coverage figures are badly understated** and should be
presented with this table beside them.

### D5. What is "mean per block"?

**Answered.** The arithmetic mean of *addresses checked* per block, used to show where
effort went:

| | blocks | checks | mean per block |
|---|--:|--:|--:|
| Blocks that turned out empty | 16,669 | 364,972 | **21.9** |
| Blocks that had life | 5,887 | 479,130 | **81.4** |

It is 21.9 rather than the 16 the rule implies because part of the space had already been
scanned under an earlier, non-adaptive method and those checks are counted here too. The
phrase should be spelled out as "mean addresses checked per block".

### D6. Easier to follow if we describe the ping + TCP test first

**Action.** Agreed, and the ordering is wrong in both `EXPLAINER.md` and
`SWEEP_FINDINGS.md`. The unit should be defined before the sampling rule that uses it:

> A **check** tests one address by trying, in order, ICMP echo, then TCP connect to port
> 80, then TCP connect to port 443, stopping at the first answer. A refused TCP connection
> counts as alive, because something was there to refuse. One check may therefore send up
> to three packets and still counts as one check.

### D7. Squatted vs others: how can a provider ping squatted space?

**Answered, and it is a good question because it exposes a real asymmetry.** Squatted
space is only reachable **from inside the network that uses it**. Those addresses are not
announced globally, so no route to them exists on the public internet.

We never ping squatted space as a *destination*. We see it only as **intermediate hops**:
a router inside a Pakistani network replies to a TTL-expired packet using an interface
address numbered out of somebody else's space. The reply reaches us because it is a reply,
not because we can route to that address.

This is testable and worth doing: a direct ping to `149.40.227.189` from outside that
network should fail, while the same address answers as a hop. **Not yet run.**

### D8. I do not get the concurrency

**Answered, and concurrency turned out to matter more than we thought.**

| stage | threads | why |
|---|--:|---|
| Liveness sweep | 100 | throughput plateaus above this, so more buys nothing |
| Top-up | 50 | at the throughput knee |
| Route sweep | 120 | chosen for speed |
| **RTT re-measurement** | **6 to 8** | deliberately low, see below |

The route sweep's 120 threads **destroyed its own latency data**. One packet per hop under
that load gave readings inflated by a median of 30 to 41 ms, with 22% of adjacent hop
pairs showing time falling deeper into the path, which distance cannot do. Re-measuring
the same addresses at 6 to 8 threads gives 1 to 2 ms of dispersion. Concurrency is safe
for *counting* live hosts and fatal for *timing* them.

*Source: `5_detector/RULES.md` R0, `3_routes/measure_rtt_ttl.py`.*

### D9. First pass and second pass are not clear

**Action.** They are two different scans from two different networks, and the naming is
inconsistent across documents. Fixed terminology:

| | what | from | scope |
|---|---|---|---|
| **Main sweep** | the national liveness scan | AS135407 TES | all 22,556 blocks |
| **Top-up** | a second pass over thin blocks | AS45669 Mobilink | blocks with 1 to 7 live hosts |

The top-up tests only addresses the main sweep never tried, so its hosts are **additional
coverage, not corrections**. Totals are a union over disjoint address sets.

### D10. What is miss rate, here?

**Answered.** The share of addresses we recorded as dead that answer when re-probed.
Measured by re-probing our own dead verdicts at low concurrency:

| network | miss rate | observations |
|---|--:|--:|
| PTCL | **~35%** | 629 |
| Others | 22% to 25% | 32 each, **not quotable as point estimates** |

It is a property of our measurement, not of the network being measured, and it differs by
network, which is why per-network densities cannot be ranked against each other.

*Source: `SWEEP_FINDINGS.md` section 5C.*

### D11. What does "compare networks" mean — the vantage or the destination?

**Answered: the destination.** The comparison is between *destination* networks, ranking
them by live-host density. The warning is that such a ranking is not supported, because
the miss rate in D10 differs by destination network, so two networks measured at similar
densities cannot be ordered.

The vantage is a separate axis entirely, covered by the ~9% cross-vantage disagreement.
The documents use "network" for both and should not.

### D12. "Not supported" needs to be explained

**Action.** It means the data cannot carry the inference, not that the inference is false.
Concretely, for density comparisons:

* **Supported:** Gerry's at 13.31% against Broadband Vision at 0.02%. A factor of 600; no
  miss-rate difference of 13 points closes that.
* **Not supported:** two ISPs at 5% and 6%. The gap is smaller than the uncertainty in
  their respective corrections, so they cannot be ordered.
* **Not supported:** a single national correction factor, since D10 shows the miss rate is
  not uniform.

---

## E. Routes and rules

### E1. Stage 3 is describing the traceroute

**Taken as an observation rather than a question.** Section 3 of `EXPLAINER.md` does
describe the traceroute stage. If the point is that it should be *labelled* as such, agreed.

### E2. The trace could be described as pseudocode

**Action, done here:**

```
trace(target):
    hops <- []
    silent <- 0
    for ttl in 1 .. 30:
        reply <- icmp_echo(target, ttl, timeout=1000ms)   # ONE packet per TTL
        if no reply:
            hops.append(nothing); silent <- silent + 1
            if silent >= 5: break                          # give up on a dead path
        else:
            hops.append((reply.source, reply.rtt)); silent <- 0
            if reply is an echo reply: break               # target itself answered
    drop trailing silent entries
    return hops
```

`reached` means the final entry's source equals the target. The one-packet-per-TTL choice
is what R0 later rejects for latency work; it remains adequate for topology.

### E3. "Median TTL slots probed" is unclear

**Action.** Replace with plain language. A **TTL slot** is one position in the trace: the
tracer sets a hop limit of 1, then 2, then 3, and each is a slot whether or not anything
answers. "Median TTL slots probed = 11" means the typical trace tried 11 hop distances
before stopping. The companion figure is how many of those **answered**, which is the
number that matters:

| | PTCL | every other network |
|---|--:|--:|
| Median slots tried | 11 | 12 |
| Median slots that answered | **5** | **8** |
| Silent slots | 48% | 31% |

### E4. ✓ "Expected maximum domestic round trip" is hard to defend

**He is right, and it has been removed.** This was 34.2 ms, computed as Pakistan's
1,659 km span × 2.1 ÷ the speed of light in fibre, and used as a **ceiling**.

Two independent problems:

1. **The 2.1 is a typical-case rule of thumb**, from Bozkurt et al. on US long-haul fibre,
   not an upper bound. The same paper reports only **11%** of real fibre links come within
   25% of what their length predicts, and that servers in the same city often sit 10 to
   30 ms apart. A typical value cannot act as a maximum.
2. **The model is the wrong shape for a country this size.** Regressing clean RTT against
   straight-line distance over 346 domestic destinations gives **R² = 0.013** with a
   slightly negative slope. The median domestic path is ~470 km, worth 4.6 ms, against 25
   to 35 ms of fixed access overhead. Distance does not drive domestic latency here, so no
   multiplier over distance can describe it.

**Replaced by R4′**, which is a procedure rather than a number: each vantage builds its own
domestic distribution from destinations whose paths never left the country, and flags
anything past the Tukey far fence, `p75 + 3 × IQR`. Scale-free, so a slow vantage gets a
high baseline *and* a high fence. Ours is 80 ms from 347 references, flagging 1.4% of
domestic and missing 0 of 10 known detours.

*Source: `5_detector/RULES.md`, `5_detector/derive_constants.py`.*

### E5. FINDINGS.md: impossible to figure out what it is describing

**Action, not yet done.** Agreed. `15.1_data_plane/FINDINGS.md` predates the current
structure and does not say what run it covers, what question it answers, or how it relates
to `SWEEP_FINDINGS.md` and `TROMBONE_FINDINGS.md`. It should either be rewritten with that
context or removed in favour of the newer documents.

---

## What this review changes

**One genuine error found:**

* **D4**, the two-empty-draw rule abandons a block holding 8 live hosts 59% of the time,
  which is far larger than anything the write-up admits.

**One methodological gap, found by chasing C2 and A5 together.** Announcement is recorded
as a boolean taken from a single visibility-filtered endpoint. It should be a set of
origins plus an observer count, because RIPEstat's own endpoints disagree about the same
prefix at the same moment. Our attributions turned out to be correct, but we could not
have demonstrated that from our own artifacts, and an earlier draft of this document
wrongly reported them as errors for exactly that reason.

**One confirmation of a correction already made:** E4, the domestic ceiling, which had been
independently challenged and replaced before this review arrived.

**Three open measurement gaps:** A2 (July routing changes), A3 (no RouteViews cross-check),
D2 (panel size of 8 is an assumption with no decay measurement behind it).

**The rest are explanation gaps**, and most are already answered above; they need moving
into the documents themselves.
