# Pakistan sweep, results by ISP

**Run 2026-09-08 to 2026-09-09.** Every figure below is produced by
`6_analysis/build_isp_summary.py` and rendered by `6_analysis/write_isp_summary.py`.
Re-run both after any new sweep and this file updates itself.

---

## The short version

We took every address Pakistan announces or is registered to hold, sampled it for
live hosts, traced routes to the ones that answered, and kept the traces clean
enough to analyse.

| step | result |
|---|---|
| Addresses in the universe | **5,774,336** across 22,556 /24 blocks, 352 networks |
| Addresses actually checked | 844,102 (14.6% of the space) |
| Live hosts found | **43,737** (5.2% of checks answered) |
| Blocks with at least one live host | 5,887 of 22,556 (26%) |
| Blocks that reached 8 live hosts | 4,406 (75% of live blocks) |
| Traceroutes attempted | 43,765 |
| Traces that reached their target | **36,214** (83%) |
| Targets kept after the quality gate | **34,191** in 5,508 blocks, 217 networks |
| Hops annotated with country and operator | **217,255** |

We did not check all 5.7 million addresses. Sampling is adaptive: 8 addresses per
block, escalating to 64 only where something answered, stopping after two empty
draws where nothing did. That is why 14.6% of the space
was enough to find life in 26% of blocks.

## Reading the table

* **blocks** is /24-equivalents the network announces.
* **with life** is blocks where at least one address answered.
* **live hosts** is distinct addresses that answered, from either vantage point.
* **blk >=8** is blocks that reached 8 live hosts, the panel target for Exp 16.1.
* **reached** is traces whose last hop is the target itself. This is the route
  visibility number: it says how far into that network we can actually see.
* **selected** is targets passing the gate `reached AND at least 5 hops answered`.
* **median hops** is the median count of hops that answered, per selected trace.

## Every network with a live host, top 40 by live hosts

| ASN | network | blocks | with life | live hosts | blk >=8 | traces | reached | selected | median hops |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| AS17557 | Pakistan Telecommunication | 14,573 | 3,979 | 29,536 | 3,077 | 29,544 | 24,909 (84%) | 23,593 | 5 |
| AS9541 | Cyber Internet Services (Pvt)  | 876 | 164 | 1,301 | 139 | 1,301 | 792 (61%) | 777 | 8 |
| AS23674 | Nayatel (Pvt) Ltd | 560 | 149 | 1,187 | 134 | 1,187 | 680 (57%) | 663 | 7 |
| AS38264 | National WiMAX/IMS env | 684 | 162 | 1,182 | 126 | 1,184 | 1,095 (92%) | 1,088 | 9 |
| AS9260 | Multinet Pakistan Pvt. Ltd. | 119 | 77 | 610 | 72 | 610 | 558 (91%) | 554 | 8 |
| AS24499 | Telenor Pakistan | 80 | 56 | 461 | 49 | 461 | 435 (94%) | 405 | 8 |
| AS38193 | Transworld Associates (Pvt.) Ltd | 93 | 57 | 451 | 49 | 451 | 388 (86%) | 377 | 7 |
| AS135407 | Trans World Enterprise Servic | 90 | 47 | 409 | 46 | 409 | 397 (97%) | 363 | 8 |
| AS138423 | CMPak Limited | 79 | 66 | 373 | 19 | 386 | 342 (89%) | 325 | 8 |
| AS132165 | Connect Communications | 136 | 39 | 368 | 21 | 372 | 314 (84%) | 207 | 8 |
| AS136384 | Optix Pakistan (Pvt.) Limited | 88 | 37 | 351 | 26 | 351 | 328 (93%) | 244 | 7 |
| AS17563 | Autonomous System Number for | 119 | 42 | 311 | 32 | 311 | 264 (85%) | 264 | 9 |
| AS17911 | Brain Telecommunication Ltd. | 49 | 25 | 268 | 5 | 268 | 78 (29%) | 66 | 10 |
| AS23966 | LINKdotNET Telecom Limited | 277 | 46 | 256 | 15 | 256 | 203 (79%) | 199 | 7 |
| AS59257 | CMPak Limited | 182 | 36 | 252 | 23 | 252 | 195 (77%) | 189 | 9 |
| AS45773 | PERN AS Content Servie Provi | 47 | 30 | 232 | 27 | 232 | 184 (79%) | 182 | 8 |
| AS23888 | National Telecommunication Corpo | 95 | 34 | 228 | 21 | 228 | 151 (66%) | 151 | 8 |
| AS7590 | Commission on Science and Technolo | 56 | 30 | 226 | 18 | 226 | 181 (80%) | 170 | 8 |
| AS24435 | Supernet Limited T | 73 | 28 | 210 | 23 | 210 | 191 (91%) | 189 | 9 |
| AS23750 | GERRYS INFORMATION TECHNOLOGY | 61 | 24 | 186 | 20 | 186 | 175 (94%) | 173 | 9 |
| AS38713 | Broadband ISP, FTTH and Ca | 47 | 24 | 177 | 19 | 177 | 164 (93%) | 164 | 9 |
| AS59323 | Punjab Information Technolo | 5 | 5 | 169 | 4 | 169 | 17 (10%) | 9 | 9 |
| AS135523 | Multinet Broadband | 25 | 21 | 160 | 9 | 160 | 136 (85%) | 113 | 7 |
| AS136030 | Redtone Telecommunications P | 30 | 20 | 143 | 15 | 143 | 129 (90%) | 129 | 8 |
| AS55501 | 141-143 Maulana Shaukat Ali R | 30 | 18 | 141 | 14 | 141 | 132 (94%) | 129 | 8 |
| AS136969 | KK Networks (Pvt) Ltd. | 27 | 17 | 129 | 14 | 129 | 123 (95%) | 119 | 8 |
| AS133495 | Vision telecom Private limite | 18 | 13 | 108 | 8 | 108 | 102 (94%) | 77 | 9 |
| AS150371 | Pace Telecom and Brodcasting  | 21 | 17 | 107 | 6 | 107 | 98 (92%) | 84 | 9 |
| AS150750 | IN CABLE INTERNET (PRIVATE) LIM | 46 | 14 | 101 | 10 | 101 | 90 (89%) | 88 | 9 |
| AS17539 | NetSol Connect | 42 | 16 | 98 | 9 | 98 | 85 (87%) | 85 | 10 |
| AS18053 | Special Communication Organizat | 27 | 12 | 92 | 9 | 92 | 92 (100%) | 87 | 7 |
| AS152605 | Z COM NETWORKS | 24 | 11 | 88 | 11 | 88 | 85 (97%) | 85 | 9 |
| AS142647 | Nasstec Airnet Networks Private  | 15 | 11 | 86 | 4 | 86 | 82 (95%) | 62 | 9 |
| AS140607 | Sign In (PVT) LTD | 24 | 14 | 83 | 7 | 83 | 72 (87%) | 65 | 9 |
| AS58470 | IX Peering for Mobi | 21 | 10 | 81 | 8 | 81 | 69 (85%) | 57 | 6 |
| AS55453 | House # 39 Street 38 F10  | 16 | 11 | 80 | 9 | 80 | 72 (90%) | 69 | 5 |
| AS24440 | Cyber Internet Services Paki | 23 | 9 | 76 | 9 | 76 | 50 (66%) | 46 | 7 |
| AS45669 | PMCL /LDI IP TRANSIT | 415 | 12 | 74 | 7 | 74 | 61 (82%) | 42 | 5 |
| AS58895 | Ebone Network (PVT.) Limited | 154 | 10 | 70 | 6 | 70 | 68 (97%) | 67 | 8 |
| AS9387 | SHARP TELECOM (PRIVATE) LIM | 23 | 9 | 70 | 8 | 70 | 62 (89%) | 62 | 8 |

The remaining **196** networks with live hosts hold 3,206 live hosts
across 485 blocks, of which 278 reached 8, and they contributed
2,373 selected targets. 116 of the
352 networks produced no live host at all.

Full machine-readable table, all 352 networks: `6_analysis/isp_summary.csv`.

---

## What stands out

**PTCL is the country.** AS17557 holds 65% of
Pakistan's /24 blocks, 68% of the live hosts we found,
and 69% of the selected targets. Any country-level
statistic that is not weighted by network is a statistic about PTCL. The top 27
networks hold 90% of all live hosts.

**Route visibility is high and fairly even.** 83% of
traces reached their target. Where a network's reach rate sits well below that, the
likely cause is filtering at that operator's edge rather than our tracer, since the
same tracer from the same vantage point reached 8 in 10 targets elsewhere in the
same hour. That is an inference, not a measurement: we have not confirmed filtering
with any operator.

**Registry space that nobody announces is nearly empty.** 1,209 blocks sit
in Pakistan's registry allocation with no BGP announcement covering them, and they
produced 60 live hosts between them. Registered space is not used space.
This refines the universe finding, which reported zero registry-only space at the
level of whole collapsed networks: at /24 granularity the unannounced holes are real
and they are almost entirely empty.

## Where the routes go

Of 217,255 annotated hops:

| | hops | share |
|---|--:|--:|
| Pakistan | 202,812 | 93.4% |
| Private or CGNAT | 10,702 | 4.9% |
| Foreign country | 3,741 | 1.72% |

2,060 of 34,191 traces (6.0%) contain at least one hop
outside Pakistan. Those are candidates for tromboning analysis, not the finding
itself: a foreign hop becomes evidence only once the latency rules in `RULES.md`
are applied to it.

Two structural features of the hop set are worth recording:

* **21,192 hops sit in address space that carries no BGP announcement.** Almost
  all of it is Transworld (`110.93.252.0/22`, `119.63.136.0/23`) and Wateen
  (`58.27.172.0/22`) backbone infrastructure. Operators routinely number their
  backbones out of space they do not announce, which is normal practice, but it
  means a hop cannot be attributed to an operator through BGP alone. We attribute
  these through whois instead.
* **342 hops are on internet exchange fabrics**: DE-CIX Frankfurt, Equinix
  Singapore, Equinix Muscat, EMIX Dubai, HKIX Hong Kong. A hop on an exchange LAN
  belongs to the exchange, not to either peer, so it must not be counted as a
  foreign network hop for the Pakistani side.

## Quality of the selected traces

The gate was `reached the target AND at least 5 hops answered`. Within the
selection, timeouts per trace are distributed as:

| timeouts in the trace | traces | share |
|--:|--:|--:|
| 0 | 39 | 0.1% |
| 1 | 615 | 1.8% |
| 2 | 2,303 | 6.7% |
| 3 | 3,066 | 9.0% |
| 4 | 6,217 | 18.2% |
| 5 | 11,357 | 33.2% |
| 6 | 9,877 | 28.9% |
| 7 | 480 | 1.4% |
| 8 | 174 | 0.5% |

Median answered hops per trace is 6. Timeouts in the middle of a path
are normal: 43% of TTL slots across the selection are silent.
Every selected trace still has a confirmed endpoint and at least 5 identified hops.

### The 5-hop gate binds almost entirely on PTCL

This matters for anything built on the selection, so it is stated plainly rather
than buried in the table.

| | PTCL AS17557 | every other network |
|---|--:|--:|
| Selected traces | 23,593 | 10,542 |
| Median TTL slots probed | 11 | 12 |
| Median hops that answered | **5** | **8** |
| Silent TTL slots | 48% | 31% |

PTCL paths are not shorter. They are the same length and far quieter: the tracer
probes about as many TTL slots, but roughly half of them return nothing against
31% elsewhere, and no other network in the top ten
exceeds 40%.
14,307 of 23,593 selected PTCL traces
(61%) answered exactly 5 hops, sitting
precisely on the gate floor.

Three consequences:

1. **The gate is not a mild filter, it is the binding constraint on PTCL.** Raising
   it to 6 hops would drop most PTCL traces and shrink the largest network in the
   study to a fraction of its size. The threshold was chosen before this was
   measured, so it is not tuned to a result, but any change to it is effectively a
   decision about how much PTCL to keep.
2. **Selected traces are not uniformly clean.** A PTCL trace that passed is
   typically minimally qualified, while a Nayatel or Wateen trace that passed
   usually cleared the bar comfortably. Per-network comparisons of path detail
   must account for this, and cannot treat all selected traces as equivalent.
3. **The cause is not established.** Fewer answering hops at equal path length is
   consistent with ICMP TTL-expiry rate limiting or suppression inside PTCL's
   core, and also with MPLS tunnels that hide interior hops from traceroute. We
   have not distinguished these. Treat it as an observed property of PTCL paths
   from this vantage pair, not as a mechanism.

   It is worth noting that two independent measurements now single out the same
   network. The liveness re-probe put PTCL's miss rate near 35% against 22% to 25%
   elsewhere (`SWEEP_FINDINGS.md` section 5C), and hop silence here is 48% against
   31%. Those measure different things, host replies
   and TTL-expiry replies, and both are suppressed on PTCL relative to its peers.
   That is consistent with ICMP rate limiting being the common cause and is not
   consistent with MPLS alone, which would hide interior hops without affecting
   whether end hosts answer. This raises the standing of the rate-limiting reading
   from one candidate among several to the better-supported one. It remains a
   hypothesis: neither measurement observes a rate limiter directly, and a
   controlled test at varying probe rates against PTCL would be needed to confirm it.

---

## Limits you must carry into any claim made from this table

1. **Live host counts are floors, and the floors are not equally tight.** Adaptive
   sampling stops at 64 addresses per block, so no block can report more than 64
   live hosts regardless of true occupancy. Separately, re-probing measured a miss
   rate near 35% on PTCL against 22% to 25% on other networks (`SWEEP_FINDINGS.md`
   section 5C), so densities are comparable within a network over time, not between
   networks.

2. **A second vantage point does not agree with the first.** Roughly 9% of hosts
   that answer from AS135407 do not answer from AS45669, at every concurrency
   tested. That asymmetry is a property of Pakistani interconnection rather than a
   fault in the scan, and it means "live" is vantage-relative. Counts in this table
   are the union of both vantages.

3. **Selection is biased toward dense blocks by construction.** A block needs live
   hosts before it can be traced at all, and the gate then prefers clean traces.
   Blocks with 1 to 3 live hosts are held as a control group to measure how large
   that bias is. That comparison has not been run yet, so the size of the bias is
   currently unknown, not small.

4. **This is one vantage pair, one country, IPv4 only, over two days.** No ISP has
   confirmed any of it. Nothing in this file is ground truth from an operator, and
   the route shape of a network can change on any day.

5. **A network's reach rate mixes two causes**: filtering at that operator's edge,
   and blocks whose live hosts were themselves marginal. This table does not
   separate them.
