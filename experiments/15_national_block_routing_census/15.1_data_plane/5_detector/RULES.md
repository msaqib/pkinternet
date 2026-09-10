# Detection rules

**A rule here is a procedure, not a number.** It is written as a statement that could be
false, tested against a vantage point's own data, and applied to that vantage only after
it survives. A rule proven for one probe says nothing about another until it is tested
there too.

**Every threshold is derived from measurement.** The only constant typed into this
experiment is the speed of light in fibre, and it appears in exactly one rule. Everything
else, including the boundary between "domestic" and "abroad", is computed from the
vantage's own traffic. That is what makes the set portable: another probe on another
network runs the same six procedures and gets its own numbers.

---

## The one constant

| | value | source |
|---|---|---|
| speed of light in fibre | **204,000 km/s** | Bozkurt et al., *Dissecting Latency in the Internet's Fiber Infrastructure*, §4.2 |

A detector cannot derive physics from its own traffic, so this one is cited rather than
measured. It is a property of glass, not a tuning knob.

### Two constants that used to be here, and why they are gone

**`ROUTING = 2.1`.** Bozkurt's rule of thumb: multiply line-of-sight distance by 2.1,
divide by the speed of light in fibre. It was being applied to Pakistan as though it were
a law. It is not. It is a *typical-case* estimate drawn from US long-haul fibre, and the
same paper reports that only **11%** of real fibre links come within 25% of what their
length predicts, and that servers in the *same city* often sit 10 to 30 ms apart.

Measured here, it is worse than inapplicable: it is the wrong *shape*. Regressing clean
RTT against straight-line distance over **346 domestic destinations** gives
**R² = 0.013** with a slightly negative slope. Distance explains essentially none of
Pakistani domestic latency, because the median domestic path is ~470 km (worth ~4.6 ms)
while fixed access overhead is 25 to 35 ms. A multiplier over distance cannot describe a
quantity that distance does not drive. See `derive_constants.py`.

**`LOCAL_CEIL` / `DOMESTIC_CEIL = 34.2 ms`.** Pakistan's span × 2.1 ÷ c, used as a
*ceiling*. It never was one; it was a typical value being asked to act as a bound. R4′
replaces it with a measured distribution.

---

## R0 — "The measurement can support a latency rule at all"

**Statement.** This RTT data is a measurement rather than noise.

**Test.** Two checks that need no external reference:
1. Does RTT ever *fall* as the path gets longer? Distance cannot decrease along a path.
2. Does one fixed router give a stable reading across repeats?

**Gate.** If either fails, **no latency rule may run on that data.** Fix the measurement;
do not retune thresholds to fit it.

**Result on this experiment.** The sweep data **failed**, and everything built on it had
to be redone:

| | sweep | clean re-measurement |
|---|--:|--:|
| Packets per hop | 1 | 20 to 30 |
| Threads | 120 | 6 to 8 |
| Adjacent pairs where RTT falls >20 ms deeper | **22%** | n/a |
| Spread on one fixed router | 4 to 853 ms | **1 to 2 ms** |
| Bias against clean measurement | **+30 to +41 ms** | — |

R0 exists because this was missed. `local_trace.py` was built to answer two topological
questions and returns `RoundTripTime` for free; that field was then used as if it were a
latency measurement. On that data the old hand-picked rules label **75.9%** of the country
as tromboning, which is a statement about thread count.

---

## R1 — "This vantage's access path is the chain C(v)"

**Statement.** Every trace from v begins with the same routers, until routes diverge.

**Test.** The address that dominates each early hop position, across all traces.
Parameter-free: the divergence point is measured, not chosen.

**Why it matters.** The access chain is a fixed cost paid before the measurement means
anything. It must be subtracted before any latency is attributed to a destination.

**Result, AS45669 Mobilink:** three routers present in ~99% of traces, diverging at hop 6.
**B_access = 20 ms.**

---

## R2 — "This address is not in the country its registry claims"

**Statement.** X is registered in country C. If X were in C, no Pakistani vantage could
observe it faster than `2 × distance ÷ 204,000 km/s`.

**Test.** Clean minimum RTT, measured **in-path**, against that floor.

**Derived inputs, not typed ones.**
* The claimed location comes from **per-address geolocation**, not a hand-written table of
  "the nearest hub" per country. That table invented facts: it guessed Singapore for
  `27.111.230.181`, which the geolocation databases place in Sydney.
* The vantage's own position comes from geolocating its egress address.
* No routing factor is applied. The floor is the straight-line bound, so falsifying it is
  a physical impossibility rather than a judgement.

**Gate: foreign claims only.** Domestically the distances are too short for physics to
decide anything, which is what R4′ is for.

**Minimum, not median, and why that differs from the old rule.** The old R2 took a median
across traces spread over hours, where one fast reading could be a routing change. These
samples are a controlled burst to one address over seconds, so the minimum is the correct
estimator: queuing, rate limiting and slow ICMP generation only ever *add* to a round trip.

**In-path, never direct.** A router must be measured by packets travelling toward the
original destination with a limited TTL, exactly as the trace saw it. Pinging a router
directly measures a different thing: routers deprioritise traffic addressed to themselves,
and the route *to* a router need not match the route *through* it.

**Result:** **79 addresses falsified** across 27 blocks, including seven US Department of
Defense addresses answering in about 3 ms, plus Cogent, Cloudflare, AT&T and T-Mobile
ranges. These are Pakistani routers numbered out of foreign address space.

**What R2 does NOT establish.** It falsifies a claim. "Not in Virginia" is not "in
Pakistan". R4′ decides that second question.

---

## R3 — "This vantage can observe paths, under this protocol"

**Statement.** v's traces contain public addresses.

**Test.** Proportion of traces with at least one public hop.

**Gate.** Proven per protocol, never universally. **A probe is not usable or unusable
absolutely; it is usable under a protocol.** In the 4.1 archive, `nayatel.isb` produced no
public hop in 100% of TCP traces and 11% of ICMP traces. The same device, two verdicts.

**Result:** holds for ICMP on this vantage. 3 of 43,765 traces were blind.

---

## R4′ — "This vantage's domestic normal is its own"

**Statement.** A destination whose clean RTT lies far outside this vantage's own domestic
distribution did not take a domestic path.

**Test, as a procedure any vantage runs on itself:**

```
1. take destinations whose observed path is entirely domestic
2. measure them cleanly (many packets, low concurrency), keep the minimum per destination
3. that distribution is this vantage's normal
4. flag anything beyond the Tukey far fence:  p75 + 3 x (p75 - p25)
```

**Why a Tukey fence rather than a chosen percentile.** It is the standard, scale-free
definition of an outlier, and nobody picks it to fit a dataset. A slow vantage gets a high
baseline *and* a high fence; a fast one gets both low. **The rule travels without being
retuned**, which a millisecond threshold cannot do.

**Gates.**
* At least ~100 reference destinations, or the shape of the distribution is noise.
* **If more than half the reference set is itself detouring, the baseline IS the detour**
  and the rule must be rejected for that vantage rather than quietly applied. This is the
  gate that fired and correctly killed the old geometric R4.
* R0 must pass first.

**Scope, stated honestly.** The reference set is chosen by topology, so R4′ can only catch
detours that the topological test missed. It is a second net under the first, not a
replacement.

**Result, AS45669 Mobilink:**

| | |
|---|--:|
| Reference destinations | 347 |
| Domestic median | 27 ms |
| p25 / p75 | 24 / 38 ms |
| **Fence, p75 + 3 × IQR** | **80 ms** |
| Domestic wrongly flagged | 1.4% |
| Known detours missed | 0 of 10 |

The data separates itself: the highest domestic reading below the fence is 69 ms, the
lowest tromboning destination is 90 ms. **That number is this vantage's answer, not the
rule.** Any other probe re-derives its own.

---

## R5 — "This trace left the country and came back"

**Only evaluated after R0 to R4′ are settled for that vantage under that protocol.**

**Statement.** The packet reached a domestic destination by way of a router outside the
country.

**Test, in order.** Anything explained by an earlier rule is subtracted first, and a
detour is what survives:

```
1. subtract C(v)                     the access chain is not a detour
2. apply R2                          strip squatted space: a foreign registry is not
                                     evidence, an impossible RTT is
3. apply R4' to what R2 falsified    "not in Virginia" is not "in Pakistan"
4. what remains foreign is a departure
```

**Two things that count as abroad.** A hop in a foreign country, and a hop on a **foreign
internet exchange fabric**. The exchange hop belongs to the exchange rather than to either
peer, but the packet is physically in Frankfurt or Singapore, so for departure it counts.

**This yields a FLOOR, not a rate.** With the latency arm limited to R4′'s scope, a detour
is only visible when a foreign router answers. Detours through silent routers or inside
MPLS tunnels are counted as domestic.

**Result:** **930 of 34,191 traces (2.72%)**, in **157 blocks** across 50 networks.

---

## R6 — "The verdict predicts something it was never given"

**Statement.** If R5 is detecting a real phenomenon, its verdicts should predict latency
that the topological test never saw.

**Test.** Compare clean RTT for destinations R5 calls tromboning against those it calls
domestic, within the same population.

**Result:**

| | n | median clean RTT |
|---|--:|--:|
| R5 says domestic | 347 | **26 ms** |
| R5 says tromboning | 10 | **147 ms** |

**+121 ms.** Two independent methods agreeing is stronger than either alone, and it means
the tromboning result does not rest on country annotations.

**Limit.** The tromboning sample here is 10 destinations. This is corroboration, not a
significance test, and it should be repeated with a larger deliberate sample.

---

## What is still a judgement, named honestly

* **The Gulf cannot be resolved by latency, and better measurement made this worse, not
  better.** Domestic paths run at a 27 ms median; Muscat's floor is 4.2 ms and Dubai's is
  7.0 ms. A Gulf detour and a slow domestic path are indistinguishable by RTT. Gulf
  detours are undercounted and **no threshold fixes it** — only topology can find them.
* **The 5-hop selection gate** upstream of all of this is a choice, and it binds almost
  entirely on PTCL.
* **Geolocation is a claim, not a fact.** R2 falsifies claims well, but where a falsified
  address actually sits is only bounded, never established.
* **Return-path asymmetry and MPLS are invisible to traceroute.** Not solvable here.
* **One vantage.** Every number above describes AS45669. Re-deriving per vantage is
  mandatory, not optional.
