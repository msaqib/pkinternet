# Start here: what this experiment does, and why it is built this way

**For someone opening this folder for the first time.** No prior context assumed. Every claim names
the file that produced it. Where something is a guess rather than a measurement, it says so.

Companion documents: [`ISP_SUMMARY.md`](ISP_SUMMARY.md) is the results,
[`SWEEP_FINDINGS.md`](SWEEP_FINDINGS.md) is the method in full detail,
[`5_detector/RULES.md`](5_detector/RULES.md) is the detection logic.

---

## 1. The question, in one paragraph

When you send a packet from one place in Pakistan to another place in Pakistan, does it stay in
Pakistan? Or does it leave the country, touch a router in Singapore or Frankfurt or Dubai, and come
back? That second case is called **tromboning**, or hairpinning. It is slow, it is expensive for
the operator paying for international transit, and it puts domestic traffic under foreign
jurisdiction on the way past.

We want to know how often that happens across **every Pakistani network**, not just one.

### Why anyone should care

* **Latency.** A Karachi to Lahore packet that detours through Singapore pays roughly 200 ms
  instead of roughly 20 ms. That is the difference between a usable video call and an unusable one.
* **Cost.** International transit is billed. Domestic peering is usually not. Traffic that leaves
  and returns is paid for twice, and the cost lands on the operator and then on the subscriber.
* **Sovereignty and exposure.** Domestic traffic on a foreign path is domestic traffic crossing a
  foreign legal boundary and a foreign operator's equipment.
* **Policy.** Pakistan has internet exchanges. Whether operators actually use them, and which ones
  do not, is a question that gets asked in policy discussions and answered mostly by assertion. We
  would like to answer it by measurement.

### The longer goal

This experiment produces **one snapshot**. The point of a snapshot is that you can take another one.

```
Exp 04     one ISP, in depth.                  Done, ../04_path_tromboning/.
Exp 4.1    first population-scale attempt.     Run once. Its detector was wrong.
Exp 15     THIS. National census, corrected.   One round, all networks.
Exp 16.1   the same design run repeatedly.     Needs a stable panel of targets.
```

**Experiment 16.1 is why the sampling looks the way it does.** To watch a network over months you
need a fixed panel of addresses that reliably answer, so that a change you observe is a change in
routing and not a change in which addresses happened to be up that day. That is the entire reason
this experiment tries to find **8 live hosts per block** rather than just one. Eight gives a panel
block enough redundancy to survive hosts going away.

---

## 2. The four stages, and what each one is for

```
1_universe   which addresses count as "Pakistan"?          -> 22,556 blocks
2_liveness   which of those addresses are switched on?     -> 43,737 live hosts
3_routes     what path does a packet take to each one?     -> 34,191 usable traces
5_detector   which of those paths left the country?        -> rules, not thresholds
```

Stage 6 (`6_analysis`) rolls all of it up per ISP. Stage 4 (`4_atlas`) is a separate, paid path
using RIPE Atlas hardware probes, not yet run for the census.

**Measurement and interpretation are deliberately separated.** Stages 1 to 3 produce a snapshot and
issue no verdicts at all. Stage 5 interprets it. This split exists because Experiment 4.1 baked its
detector into its collection, and when the detector turned out to be wrong the whole collection had
to be reinterpreted from raw JSON. Now a detector change never forces a re-measurement.

---

## 3. Stage 1: what counts as "Pakistan"

Harder than it sounds, and getting it wrong quietly loses 4.4% of the country.

There are two different answers to "which addresses are Pakistani":

| | source | what it means |
|---|---|---|
| **Registry view** | RIPEstat `country-resource-list?resource=PK` | address space **registered** to Pakistan on paper |
| **Routing view** | `announced-prefixes` for each Pakistani ASN | address space Pakistani networks actually **announce** |

Registration is paperwork. Announcement is operational reality. **Neither contains the other**, so
we use the union.

**252,672 addresses are announced from Pakistan but registered to another country.** That is 4.4% of
the routed space, and it includes large parts of Nayatel, Wateen, Optix and TES. Address space gets
leased and transferred far faster than registry country fields get updated. A study that defines its
universe by registration alone silently misses all of it.

Full detail and the reproduction command: [`1_universe/UNIVERSE_FINDING.md`](1_universe/UNIVERSE_FINDING.md).

**Result:** 5,774,336 addresses, 22,556 /24-equivalent blocks, 352 networks with announced space.

### Why /24 blocks

A /24 is 256 consecutive addresses. It is the smallest unit that is routed independently on the
public internet in practice, and operators tend to assign it as a unit to one place and one purpose.
So a /24 is a reasonable guess at "one chunk of network that probably shares a fate". Everything
larger is split into /24s so that sampling density is uniform: without that, a /16 and a /24 would
get the same 8 samples despite being 256 times different in size.

---

## 4. Stage 2: finding live hosts, and the sampling that makes it affordable

### The problem

5.77 million addresses. At the measured rate of roughly 55 checks per second, checking every one
takes about 29 hours of continuous probing, and most of it is wasted: the great majority of
Pakistani address space has nothing switched on in it.

### The adaptive sampler, and exactly why it is shaped this way

The rule, from [`2_liveness/scan_all_pk.py`](2_liveness/scan_all_pk.py):

```
For each /24 block:
  draw 8 random addresses, check them
    0 answered  -> draw 8 more. Still 0 -> stop, move on.   (16 checks spent)
    1 or more   -> keep drawing 8 at a time until either
                     8 live hosts found, or
                     64 addresses tried
```

**The reasoning behind each number:**

* **Why 8 per draw.** 8 is the panel size Exp 16.1 needs. Drawing the target size means a fully
  populated block is finished in one draw.
* **Why stop after two empty draws.** 16 random addresses out of 256 all failing to answer is
  reasonable evidence the block is sparse or dark. It is not proof. It is a deliberate trade: we
  accept missing some thinly populated blocks in exchange for not pouring effort into empty space.
  **This is a judgement, not a derived threshold.**
* **Why cap at 64.** Diminishing returns. A block that has not yielded 8 live hosts in 64 tries is
  unlikely to be a good panel block anyway.
* **Why random rather than sequential.** Sequential scanning hits `.1`, `.2`, `.3` first, which are
  disproportionately routers and gateways rather than ordinary hosts. Random draws give a less
  biased picture of what is actually in the block.

### Draws accumulate. Nothing is ever thrown away

A natural reading of "draw 8, then draw 8 more" is that each draw replaces the last. It does not.
**Results accumulate across draws, and no address is ever probed twice.**

If the first draw of 8 answers 6 times, those 6 are kept. The loop sees `6 < 8`, draws 8 fresh
addresses from the 248 not yet tried, and the block finishes the moment the running total reaches
8. From [`2_liveness/scan_all_pk.py`](2_liveness/scan_all_pk.py):

```python
live = found.get(u, 0)          # carries over from any earlier draw
while pool and len(seen) < 64 and live < 8:
    batch = pool[:8]            # 8 addresses NOT yet seen
    for ip in batch:
        if probe(ip): live += 1 # adds to the running total
```

Every address probed is written to disk with its result, so the addresses that did **not** answer
are kept too. They are evidence, and the re-probe validation in section 4 depends on having them.

**The loop overshoots on purpose, and it is worth knowing why.** The target is re-checked at the
top of each draw, not before each address, so a draw always runs to completion. Starting at 6, a
dense second draw can finish the block at 10 or 12 rather than stopping neatly at 8.

Measured across every block that produced life:

| live hosts in the block | blocks | what happened |
|---|--:|---|
| 1 to 7 | 1,481 | hit the 64-address cap, or ran out of addresses |
| **8** | **3,394** | 57.7%, stopped on the target |
| 9 to 14 | 975 | overshot inside a draw |
| 15 or more | 37 | dense blocks, up to 92 in one case |

So **1,012 blocks (17.2% of live blocks) ended above 8**. That is harmless: it is free extra data,
and it costs nothing beyond the draw that was already running.

**The two scanners differ here, and it matters if you ever read these counts as density.** The
top-up pass ([`2_liveness/topup_scan.py`](2_liveness/topup_scan.py)) tests the target before every
single address:

```python
if used >= A.extra or live >= A.target: break
```

so it stops exactly at 8 and never overshoots. The main sweep stops at the end of a draw; the
top-up stops at the address. **A block's live count is therefore shaped partly by which scanner
last touched it**, not only by what is in the block. Nothing downstream is affected today, because
the counts are used only as a floor and to decide which blocks qualify for a panel. It would matter
if anyone tried to read the distribution above as a distribution of true occupancy. It is not one.

**Effort follows signal.** Measured over the 844,102 checks actually performed:

| | blocks | checks spent | mean per block |
|---|--:|--:|--:|
| Blocks that turned out empty | 16,669 | 364,972 (43%) | 21.9 |
| Blocks that had life | 5,887 | 479,130 (57%) | 81.4 |

A live block receives nearly 4 times the attention of a dead one, which is the whole point. The
mean for empty blocks is 21.9 rather than the 16 the rule implies, because part of the space had
already been scanned under an earlier, non-adaptive method and those checks are counted here too.

The sweep covered 14.6% of the address space and found life in 26% of blocks. Checking every
address would have cost roughly 7 times more. **How much would have been gained is not known**: it
is exactly the quantity the sampler chooses not to measure. The re-probe miss rates in section 4
put a floor under it, but they do not bound it.

### What "a check" actually does

One check tries up to three things in order, and stops at the first answer:

```
1. ICMP echo         (ordinary ping)
2. TCP connect :80   (web port)
3. TCP connect :443  (secure web port)
```

A refused TCP connection **counts as alive**: refusal means a host was there to refuse. This
matters because many hosts drop ping but answer TCP, and vice versa. No single method is
sufficient: that is measured, in `SWEEP_FINDINGS.md` section 3.1, not assumed.

### Two vantage points, and a finding that came out of it

The main sweep ran from AS135407 (TES). A second pass ran from AS45669 (Wateen) over blocks that
had found 1 to 7 live hosts, to top them up toward 8.

That second pass found **10,352 live hosts the first vantage had missed**.

This is not simply the first scan being wrong. Re-testing the same known-alive addresses showed
**roughly 9% of hosts answer from one Pakistani network but not the other, at every concurrency
from 10 to 200 threads**. Concurrency was ruled out as the cause by testing across that range.

**What that means:** "alive" is not an absolute property of an address. It is a property of an
address *as seen from a particular network*. Filtering, peering relationships and routing policy
differ between Pakistani operators enough to change who can see whom. Counts in this study are the
**union of both vantages**, which is strictly better evidence than either alone.

Detail: `SWEEP_FINDINGS.md` section 5B.

### The honest limit on all liveness numbers

Live host counts are **floors, and the floors are not equally tight.**

Re-probing addresses previously marked dead showed a miss rate near **35% on PTCL** against **22% to
25% on other networks**. Different networks are undercounted by different amounts, so:

* Comparing one network to itself over time: **fine**.
* Comparing two networks with wildly different densities: **fine**, the gap swamps the error.
* Comparing two networks with similar densities: **not supported**.
* Applying one national correction factor: **not supported**, since the miss rate is not uniform.

Detail: `SWEEP_FINDINGS.md` section 5C.

---

## 5. Stage 3: tracing the routes

For each live host we run a **traceroute**: send packets with a deliberately small time-to-live so
that each router along the path is forced to announce itself, then increase the limit and repeat.
The result is an ordered list of the routers a packet passed through, with a round-trip time for
each.

### Selection: which traces we keep

Not every trace is usable. The gate is:

```
KEEP the trace if:
   it reached the target itself  AND  at least 5 hops answered
Then per block, keep at most 8 traces, ranked by fewest timeouts.
```

**Why "reached the target".** If the trace stopped short we do not know where the packet ended up,
so we cannot say anything about the path.

**Why 5 hops.** A traceroute with 2 answering hops tells you almost nothing about a route. 5 is
enough to see the shape of a path: the access link, the operator core, and the far end. It was
chosen before the effect on the ISP mix was measured, so it is not tuned to produce a result, but
**it is a judgement, not a derived value.**

**Result:** 34,191 traces across 5,508 blocks and 217 networks, out of 43,765 attempted.

### An important consequence of that gate

The gate turned out to bind almost entirely on one network. PTCL traces are the **same length** as
everyone else's but far quieter:

| | PTCL AS17557 | every other network |
|---|--:|--:|
| Median TTL slots probed | 11 | 12 |
| Median hops that answered | **5** | **8** |
| Silent slots | **48%** | **31%** |

**14,307 of 23,593 selected PTCL traces (61%) answered exactly 5 hops**, sitting precisely on the
floor. So selected traces are **not** uniformly clean: a PTCL trace that passed is typically
minimally qualified, while a Nayatel or Wateen trace that passed usually cleared the bar
comfortably. Raising the gate to 6 would remove most of the largest network in the study.

*Why PTCL is quieter is not established.* ICMP rate limiting is the best-supported reading, because
the same network is also undercounted in liveness, and those two measure different reply types
(end hosts answering, versus routers announcing themselves). MPLS tunnelling would explain the
hidden hops but not the liveness gap. **Neither measurement observes a rate limiter directly.**
This is a hypothesis. `SWEEP_FINDINGS.md` section 5D.

---

## 6. Reading a trace: four real examples

These are actual traces from `3_routes/selected_annotated.json`, not illustrations.

### Example A: a normal domestic path

```
target 103.115.198.39, block 103.115.198.0/24, 12 of 12 hops answered

  1  10.99.79.80       37 ms  private
  2  192.168.200.5     31 ms  private
  3  119.160.114.81    22 ms  PK  AS45669    Mobilink
  4  119.160.84.61     26 ms  PK  AS45669    Mobilink
  5  119.30.105.237    37 ms  PK  AS58470    Mobilink IX peering
  6  110.93.210.226    15 ms  PK  AS38193    Transworld
  7  110.93.255.186    29 ms  PK  (unannounced)  Transworld backbone
  8  110.93.252.157   106 ms  PK  (unannounced)  Transworld backbone
  9  110.93.252.190    97 ms  PK  (unannounced)  Transworld backbone
 10  110.93.205.185    48 ms  PK  AS38193    Transworld
 11  38.68.84.24       69 ms  PK  AS152605   Z Com Networks
 12  103.115.198.39    79 ms  PK  AS152605   Z Com Networks     <- target
```

Every hop is in Pakistan. It starts on a home or office network (hops 1 and 2 are private
addresses), crosses Mobilink, transits Transworld, and arrives at Z Com. **This path never leaves
the country.** Note that RTTs are not monotonic: hop 8 is 106 ms while hop 12 is 79 ms. That is
normal and does not indicate a detour. Intermediate routers deprioritise generating these replies,
so a hop's RTT is a weak signal on its own.

### Example B: a genuine trombone, Pakistan to Pakistan via Singapore

```
target 115.186.103.189, block 115.186.103.0/24, 9 of 14 hops answered

  3  119.160.114.81    15 ms  PK  AS45669    Mobilink
  5  119.30.105.237     7 ms  PK  AS58470    Mobilink IX peering
  7  110.93.202.20     45 ms  PK  (unannounced)  Transworld backbone
  9  110.93.252.246    57 ms  PK  (unannounced)  Transworld backbone
 10  27.111.228.83    208 ms  SG  IXP        Equinix Singapore    <- left the country
 11  *
 12  *
 13  *
 14  115.186.103.189  124 ms  PK  AS55414    Worldcall            <- target, back in Pakistan
```

**This is the phenomenon the whole experiment exists to measure.** A Pakistani source reaching a
Pakistani destination (Worldcall) by way of an internet exchange in Singapore. The 208 ms at hop 10
is consistent with genuinely being in Singapore: the physical floor for a Karachi to Singapore round
trip is 46.4 ms, so 208 ms is comfortably possible. The destination then answers at 124 ms, far
above what a domestic path should cost.

### Example C: a foreign address that cannot be where it claims

```
target 205.164.150.80, block 205.164.150.0/24, 8 of 10 hops answered

  7  110.93.202.20     52 ms  PK  (unannounced)  Transworld backbone
  8  149.40.227.189    32 ms  US  AS174      Cogent, Ashburn      <- registered USA
  9  202.141.224.74   175 ms  PK  AS9260     Multinet
 10  205.164.150.80    37 ms  PK  AS136384   Optix                <- target
```

Hop 8 is registered to Cogent in Ashburn, Virginia. **It answered in 32 ms.** The physical floor for
a Pakistan to Virginia round trip is about 117 ms at the speed of light in fibre. A packet cannot
reach Virginia and return in 32 ms, so **this address is not in Virginia.** It is Pakistani
infrastructure numbered out of somebody else's address space.

This is **address squatting**, and it is a different thing from the legitimate leasing described in
section 3. The distinction is checkable:

| | leased space | squatted space |
|---|---|---|
| Announced in BGP by the Pakistani network | **yes** | **no** |
| Example | `149.40.192.0/19`, Wateen | `149.40.227.0/24` |
| Interpretation | ordinary address leasing | internal use of space nobody announces |

A foreign registry country is **not by itself evidence of anything**, since 4.4% of Pakistan's
routed space is legitimately foreign-registered. The evidence is **an impossible round-trip time
plus the absence of a matching announcement.**

Across the selection, **218 hop observations in 12 different /24s** show a foreign-registered
address answering below the 34.2 ms domestic ceiling. Most are concentrated in
`149.40.226.0/24` and `149.40.227.0/24` (Cogent space), with a smaller set in
`28.255.129.0/24` and `11.184.245.0/24`, which are United States Department of Defense ranges, a
well-known target for internal squatting because they are never seen on the public internet.

### Example D: a PTCL trace sitting on the gate floor

```
target 119.154.30.254, block 119.154.30.0/24, 5 of 9 hops answered

  1  *
  2  *
  3  119.160.114.81    58 ms  PK  AS45669    Mobilink
  4  119.160.84.61     12 ms  PK  AS45669    Mobilink
  5  119.30.105.237     8 ms  PK  AS58470    Mobilink IX peering
  6  182.176.220.81    37 ms  PK  AS17557    PTCL
  7  *
  8  *
  9  119.154.30.254    35 ms  PK  AS17557    PTCL                 <- target
```

Nine TTL slots probed, four silent, five answered. We can see the packet entered PTCL at hop 6 and
arrived at hop 9, but **PTCL's interior is invisible to us**. This trace is kept because it reached
its target with exactly 5 answering hops, and it is representative of 61% of the PTCL selection.
It supports "the path stayed in Pakistan" and **does not** support any claim about PTCL's internal
topology.

---

## 7. How a detour is actually decided

The detector does **not** work by "a hop is registered abroad, therefore detour". Section 3 and
example C are the reasons why: registry country is unreliable in both directions.

It works from **physics**. Two constants, both measured, neither chosen by hand:

| | value |
|---|---|
| speed of light in fibre | 204,000 km/s |
| real fibre path vs straight-line distance | × 2.1 |

Pakistan's longest internal span, Gilgit to Gwadar, is 1,659 km. From that:

| | derived |
|---|---|
| absolute domestic round-trip floor | **16.3 ms** |
| expected maximum domestic round trip | **34.2 ms** |

So any address answering faster than the floor for its claimed location **is not at that location**.
This is not a heuristic, it is an upper bound on how fast information can travel.

Distances from Karachi, for reference:

| destination | km | fastest possible round trip |
|---|--:|--:|
| Muscat | 865 | 8.5 ms |
| Dubai | 1,183 | 11.6 ms |
| Singapore | 4,736 | 46.4 ms |
| Frankfurt | 5,681 | 55.7 ms |

**The rules are statements that can be false, tested per vantage point, and only then applied.** A
rule proven for Z Com says nothing about PTCL until it is tested on PTCL. Full set:
[`5_detector/RULES.md`](5_detector/RULES.md).

### The band where this method simply cannot decide

**Between roughly 12 and 34 ms, a Gulf detour and a long domestic path are indistinguishable by
round-trip time.** Dubai is only 11.6 ms away at best. A slow domestic path can easily take longer
than a fast Dubai round trip.

**Detours through the Gulf will therefore be undercounted, and no threshold fixes this.** It is a
permanent limit of latency-based detection, not a tuning problem. Detecting those requires evidence
traceroute does not carry.

---

## 8. What this study cannot tell you

Stated plainly, because every one of these has been mistaken for a result at some point.

1. **No ISP has confirmed any of it.** There is no ground truth here from any operator. Everything
   is inferred from the outside.
2. **Traceroute shows the forward path only.** The return path can be completely different and is
   invisible. A round-trip time is the sum of both, so a detour on the way back is attributed to the
   wrong place.
3. **MPLS tunnels hide hops.** Inside a tunnel, routers may not announce themselves at all, so a
   path can traverse equipment that never appears in the trace.
4. **Live host counts are floors** with per-network error, as described in section 4.
5. **"Alive" is vantage-relative**, roughly 9% disagreement between two Pakistani networks.
6. **Selection favours dense blocks.** A block needs live hosts before it can be traced, and the
   gate then prefers clean traces. Blocks with 1 to 3 live hosts are held as a control group to
   measure how large this bias is. **That comparison has not been run**, so the size of the bias is
   currently unknown, not small.
7. **IPv4 only.** No IPv6 anywhere in this study.
8. **One snapshot, two days.** Routing changes. This is 8 and 9 September 2026 and nothing else.

---

## 9. Vocabulary, fixed

These were used loosely in earlier drafts and it made the tables unreadable.

| term | means | never means |
|---|---|---|
| **probe** | a deployed vantage point, a device we measure *from* | a packet, a measurement, or a target |
| **vantage point** | the network a measurement runs from | the destination |
| **target** | one destination address sampled from a block | anything we measure from |
| **check** | one liveness test of one address, up to 3 methods tried | a packet or a trace |
| **draw** | one batch of 8 addresses picked from a block by the sampler | the addresses themselves |
| **trace** | one traceroute, from one vantage point to one target | the device |
| **block** | a /24-equivalent, 256 addresses | an ISP's whole allocation |
| **hop** | one router that answered inside a trace | a packet |
| **reached** | the trace's last hop is the target itself | the target is alive |

So this study is **34,191 traces to 34,191 targets from 2 vantage points**, not "34,191 probes".

---

## 10. Running it yourself

Every step is free except stage 4. Order matters: each stage reads the previous stage's output.

```bash
# 1. the universe, and who owns what
python 1_universe/build_pk_universe.py        # registry + routing union
python 1_universe/build_block_owners.py       # every /24 -> announcing ASN
python 1_universe/resolve_unowned.py          # blocks whose owner is not a PK-registered ASN

# 2. liveness, about 7 hours for the national sweep
python 2_liveness/scan_all_pk.py --threads 100
python 2_liveness/topup_scan.py  --threads 50   # run this from a DIFFERENT network

# 3. routes
python 3_routes/local_trace.py --threads 120
python 3_routes/render_selected_routes.py       # human-readable companion

# 4. results
python 6_analysis/build_isp_summary.py
python 6_analysis/write_isp_summary.py          # regenerates ISP_SUMMARY.md
```

**Every stage checkpoints atomically.** An interruption costs seconds of work, not hours. The route
tracer additionally halts if it detects the local link has gone down, because a disconnection
otherwise produces thousands of traces that look like universal unreachability and are silently
wrong.

**Nothing on RIPE Atlas fires without its credit cost being printed first.**
