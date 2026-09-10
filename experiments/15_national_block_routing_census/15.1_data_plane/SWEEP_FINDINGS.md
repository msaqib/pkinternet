# 15.1 — liveness sweep: method and findings

**Run 2026-09-09.** A complete scan of every announced address of every small Pakistani ISP, plus a
probe-type pilot on RIPE Atlas. This records exactly how both were done and what they found. Every
number is a count over the raw output files, not an estimate.

| output | contents |
|---|---|
| `1_universe/blocks_20260908.csv` | the block universe, 779 blocks |
| `2_liveness/local_scan.jsonl` | one record per address scanned, 205,780 lines |
| `2_liveness/isp_liveness.json` | per-ISP roll-up |
| `4_atlas/pilot_raw_20260908_150835.json` | 1,225 Atlas traceroute results |
| `4_atlas/pilot_routes_20260908_150835.txt` | the same, human readable |

---

## 1. The universe

### 1.1 Where the block list comes from

`1_universe/reenumerate.py` queries RIPEstat `announced-prefixes` for each ASN and keeps the IPv4
prefixes. This is **what each network tells the world it routes**, as seen by RIPE's collectors.

**FLL** is Pakistan's *Fixed Local Loop* licence class, issued by the PTA. Exp 4.1 selected the 48
FLL licensee ASNs as its universe, on the reasoning that these are the small ISPs whose
interconnection quality is in question.

| | |
|---|---|
| ASNs queried | 48, zero errors |
| **Blocks** | **779** |
| /24-equivalents | 811 |
| **Addresses** | **207,616** |
| ISPs still announcing | **46** |

Two ASNs now announce nothing at all and drop out: **AS135661 Superior Connections** and
**AS153321 Smart Net**. They still hold a licence; they have no routed address space.

Block sizes: 757 × /24, 17 × /23, 5 × /22. No block is larger than a /22.

### 1.2 Why 206,058 targets and not 207,616 addresses

Every block's **network** and **broadcast** address is excluded, because neither is assignable to a
host. `ipaddress.ip_network(...).hosts()` does this automatically. Across 779 blocks that removes
1,558 addresses, leaving **206,058**.

### 1.3 Who is NOT in this universe, and why

**PTCL, Transworld, Nayatel, Cybernet, Wateen and every other large operator are excluded.** The
FLL scope was a deliberate Exp 4.1 decision: the question was whether *small* ISPs have poor
interconnection. Large operators appear in this data only as **transit**, hops along the path,
never as destinations.

For reference, all of Pakistan is **466 ASNs and 5,521,664 IPv4 addresses**, 26.6× this universe.

---

## 2. Liveness scan: the method in full

`2_liveness/local_scan.py`, run from a machine on **AS135407 (Trans World Enterprise Services)**
inside Pakistan.

### 2.1 Target generation

Every host address of every block. **No sampling of any kind.** 206,058 targets.

This is the central difference from earlier work. Exp 4.1 sampled 8 addresses per /24, which at
realistic densities yields under one live host per block, and that sampling is why 76% of its
blocks came back empty.

### 2.2 Order, and why it is shuffled

Targets are shuffled with a fixed seed, `random.seed(20260909)`, before scanning.

Two reasons, both load-bearing:

1. **Politeness.** Walking a block sequentially sends 256 probes to one network in a few seconds,
   which looks like an attack. Shuffled, each network receives a thin trickle.
2. **Unbiased partial results.** If the run stops early, what you have is a uniform random sample
   of the whole country. Scanning in block order would give you a complete picture of the first few
   ISPs and nothing about the rest — and any statistic computed from it would describe those ISPs
   only.

The seed is fixed so the order is reproducible.

### 2.3 Probe sequence, per address

1. **ICMP echo** via the system `ping`: one packet, 1500 ms timeout, no console window.
2. If ICMP is silent, **TCP connect to port 80**, 1.5 s timeout.
3. If port 80 is silent, **TCP connect to port 443**, 1.5 s timeout.

The first method that answers wins and the rest are skipped. ICMP goes first because it has the
highest single-method hit rate, so it short-circuits most of the work. An address that answers
nothing costs the full 1.5 + 1.5 + 1.5 seconds, which is why the run is thread-bound rather than
bandwidth-bound.

**Why 1.5 seconds.** Every domestic Pakistani path measured in this project completes well under
250 ms, and the widest possible domestic round trip is about 34 ms of propagation
(`5_detector/RULES.md`). 1.5 s is roughly 6× the slowest observed *international* round trip, so a
host that has not answered by then is not slow, it is silent.

**Why only 80 and 443.** They are by far the most common open ports on customer equipment and
routers. A host running only SSH, DNS or a game server, and dropping ICMP, is missed. This is a
known and stated undercount, not an oversight.

### 2.4 What counts as alive

- **ICMP**: a reply containing `TTL=`.
- **TCP**: a completed connect **or a connection refused**.

The second half matters. An **RST** means "I am here, that port is shut" — the host is up. Treating
a refusal as failure, which a naive `connect()` wrapper does, undercounts live hosts substantially.

### 2.5 What "alive" does not mean

It means **this address answered one of three specific probes from one specific place at one
specific moment**. It does not mean a server is running, that the address is a customer, or that it
would answer from anywhere else. See §6.

### 2.6 Execution

300 threads, append-only JSONL, flushed every 2,000 records. Restarting skips addresses already
present in the output, so the run is resumable without loss. The shuffle seed is fixed, so a resume
continues the same order rather than re-randomising.

**Thread count does affect the verdict, and this was the wrong assumption going in.** The design
note here originally said concurrency changes only the rate, on the reasoning that each probe is an
independent request-response with a fixed timeout. That is false: the path rate-limits ICMP under
load, so probes are dropped and the host is silently recorded as dead. §2.10 measures the size of
the effect. Whether it does, and by how much, is **not settled** — see §2.10, which lays out the
conflicting measurements. 300 threads was used here; the all-Pakistan scan that followed uses 100,
on the precautionary reading, which cost nothing because throughput is flat above ~50 threads.

Load also inflates measured RTT, which is a separate reason the route sweep runs on its own rather
than alongside a scan.

Record format:

```json
{"t":"144.48.0.177","p":"144.48.0.0/23","a":"138423","m":["icmp"]}
```

target address, its block, the ASN announcing it, and the list of methods that answered.

### 2.7 Cost and duration

**50.2 minutes. Zero measurement credits.** 205,780 of 206,058 addresses completed, 99.87%. The
278 missing are the tail of the final batch.

### 2.8 Validation against independent ground truth

Before the full run the method was checked against 174 addresses whose status was already known
from RIPE Atlas traceroutes — a completely separate measurement platform, different vantage points,
different probe implementation.

| Atlas verdict | n | ICMP | TCP/80 | TCP/443 | **any method** |
|---|---|---|---|---|---|
| alive | 54 | 45 | 15 | 5 | **49 (91%)** |
| no reply | 120 | 3 | 1 | 0 | **3 (2%)** |

**91% agreement on alive, 2% false positives.**

The 9% missed are hosts that answer Atlas but not us, because reachability depends on the source
network. The 2% "false positives" are the reverse: hosts we reach that Atlas did not, which is not
necessarily an error on our side.

The scan is therefore a **lower bound**: every host it finds is alive; some it misses may still be
alive from elsewhere.

### 2.9 Could a middlebox answer on a host's behalf?

Yes, in principle, and it would inflate the count. A firewall doing "reply to ICMP for the whole
subnet" would light up an entire block. Nothing like that appears here: the distribution is uneven
within blocks, and 392 blocks answer nothing at all, which is not what a subnet-wide responder
produces. It remains a possibility for individual blocks and would be visible as a block at or near
100% density. None exists in this data — the maximum is 25+ live hosts in 8 blocks, far short of
254.

---

## 2.10 Accuracy: what is established, and what is not

**The earlier version of this section stated a 2.0% false-negative rate as measured fact. That
number is withdrawn.** It was measured under two confounds at once, and the true figure is not
currently known. This section replaces it with what the measurements actually support.

### The measurements

| # | what was re-probed | scanned from | re-probed from | machine | result |
|---|---|---|---|---|---|
| 1 | high-concurrency benchmark output (500-1200 threads) | TES | TES, 60 threads | idle | **18.5%** of "dead" answered |
| 2 | small-ISP scan (300 threads) | TES | **Mobilink**, 40 threads | **under load** | 2.0% |
| 3 | small-ISP scan, same 500 addresses, same seed | TES | **Mobilink**, 40 threads | idle | **11.8%** |
| 4 | all-PK scan (100 threads), by decile | TES | **Mobilink**, 40 threads | idle | **23.4%**, flat across all ten deciles |

### Two confounds, and they were mixed together

**Machine load.** Rows 2 and 3 are the same 500 addresses with the same random seed. The only
difference is that row 2 ran while another scan was saturating the connection. It reported 2.0%;
idle, the same test reports 11.8%. **A validator running through the same impaired path measures
its own impairment, not the scan's.** The 2.0% figure was worthless and should never have been
written down as fact.

**Vantage.** Rows 2, 3 and 4 re-probe from **AS45669 Mobilink** data that was scanned from
**AS135407 TES**. Any host reachable from one network and not the other appears as a "false
negative" when it is nothing of the kind.

### The vantage asymmetry, measured directly

250 addresses **known alive from TES**, re-probed from Mobilink at each concurrency:

| threads | recall | rate |
|---|---|---|
| 10 | 92.4% | 12/s |
| 25 | 90.4% | 21/s |
| 50 | 90.0% | 31/s |
| 100 | 86.8% | 31/s |
| 200 | 92.4% | 36/s |

**Roughly 8-10% of hosts that answer from TES do not answer from Mobilink, even at 10 threads on an
idle machine.** That is not measurement error. It is a real property of Pakistani interconnection,
and for a project about domestic reachability it is arguably a finding rather than a nuisance.

So a floor of about 8-10% of row 4's 23.4% is vantage, not error. The remainder is unattributed.

### Does thread count matter? Genuinely unresolved

**Two controlled tests say no.** Recall on known-alive addresses is flat within noise: 90-92%
across 100 to 800 threads on TES, and 87-92% across 10 to 200 threads on Mobilink. No trend in
either.

**One uncontrolled measurement says yes.** Row 1 above: output from a 500-1200 thread run, re-probed
same-vantage on an idle machine, showed 18.5% of "dead" addresses alive.

They can be reconciled, and the reconciliation is uncomfortable: **the controlled tests used
addresses already known to be alive.** Those are the robust hosts, the ones that answer quickly and
reliably. They survive load precisely because they are easy. The hosts that concurrency actually
loses are the marginal ones, and by construction the controlled tests contained none of them.

**So the controlled tests were probably measuring the wrong population, and the flat curve is an
artefact of that.** It is not proof that concurrency is safe.

### What this means in practice

- **Every count in this document is a floor.** By an unknown margin, plausibly 10-25%.
- **Relative comparisons survive.** Row 4 found the rate flat across all ten deciles of the scan,
  and target order was shuffled, so every ISP is affected equally. "Optix is denser than Broadband
  Vision" holds; the absolute densities do not.
- **Concurrency was reduced anyway.** The all-PK scan ran at 100 threads rather than 300+, on the
  precautionary reading. Throughput is flat above ~50 threads regardless, so this cost nothing.

### What would settle it

A same-vantage, idle-machine comparison: scan one fixed set of blocks at 25 threads and again at
400, from the same network, and compare live counts on identical addresses. That has not been done,
and until it is, the effect of concurrency on this measurement is an open question rather than a
established fact in either direction.

## 3. National findings

| | |
|---|---|
| Addresses scanned | 205,780 |
| **Live hosts** | **2,793** |
| **Density** | **1.36%** |
| **Blocks containing life** | **386 of 778 (50%)** |
| **ISPs containing life** | **46 of 46 (100%)** |

**All counts above are floors, by an unknown margin.** Re-probes of addresses marked dead return
between 11.8% and 23.4% alive, but every one of those re-probes ran from a **different network**
than the scan, so part of the gap is genuine vantage asymmetry rather than error. §2.10 sets out
what is established and what is not. Treat every count here as a lower bound of uncertain
tightness, and rely on comparisons between ISPs rather than absolute densities.

### 3.1 No single probe method is sufficient

| method | live hosts found | share |
|---|---|---|
| ICMP | 1,322 | 47% |
| TCP/80 | 1,063 | 38% |
| TCP/443 | 408 | 15% |

**ICMP alone finds fewer than half.** Any liveness study of this address space using ping only
undercounts by roughly 53%.

Note these are *first-answer* counts, not independent hit rates: TCP is only tried when ICMP is
silent, so the TCP figures are "hosts that ICMP missed and TCP caught". The true per-method hit
rates would require probing all three on every address, which would roughly triple the runtime for
information we do not need.

### 3.2 Live hosts per block

| live hosts | blocks |
|---|---|
| 0 | 392 |
| 1–4 | 165 |
| 5–9 | 136 |
| 10–24 | 77 |
| 25+ | 8 |

**140 blocks hold 8 or more live hosts.**

**Why 8 matters.** Experiment 16 is this design run longitudinally, and it needs a stable panel of
targets that respond repeatedly over months. Eight live hosts per block gives enough redundancy
that a block stays measurable when individual hosts go away. It is the same K used in the 4.1
sampling design, chosen there for split-block detection.

---

## 4. Per-ISP results

> **This table is the small-ISP universe only.** The sweep has since been widened to every
> Pakistani network. The current national table, covering all 352 networks with announced space
> and including route visibility, is [`ISP_SUMMARY.md`](ISP_SUMMARY.md), generated by
> `6_analysis/build_isp_summary.py`. The table below is kept because sections 4.1 and 4.2 reason
> from it; read it as the small-ISP slice, not as Pakistan.

Sorted by live hosts. `blk+` is blocks containing life; `≥8` is blocks holding at least eight.

| ASN | ISP | blocks | addresses | live | density | blk+ | ≥8 |
|---|---|---|---|---|---|---|---|
| 138423 | CMPak LDI Ltd. | 92 | 26,880 | **397** | 1.50% | 78 | 15 |
| 132165 | Connect Communications | 135 | 35,328 | **375** | 1.07% | 40 | 21 |
| 136384 | Optix Pakistan | 88 | 22,528 | **351** | 1.57% | 37 | **26** |
| 17911 | Brain Telecommunication | 49 | 12,544 | 268 | 2.15% | 25 | 5 |
| 59323 | Gerry's Information Technology | 5 | 1,280 | 169 | **13.31%** | 5 | 4 |
| 135523 | Multinet Pakistan | 22 | 6,400 | 160 | 2.52% | 21 | 9 |
| 150371 | Pace Telecom and Broadcasting | 22 | 5,632 | 126 | 2.25% | 18 | 7 |
| 133495 | Vision Telecom | 18 | 4,608 | 108 | 2.36% | 13 | 8 |
| 142647 | Nasstec Airnet Networks | 16 | 4,096 | 87 | 2.14% | 12 | 4 |
| 140607 | Sign In | 24 | 6,144 | 83 | 1.36% | 14 | 7 |
| 38584 | Cube XS Weatherly | 22 | 5,632 | 68 | 1.22% | 14 | 2 |
| 138655 | Trans World Enterprise Services | 29 | 7,424 | 65 | 0.88% | 7 | 5 |
| 133551 | Origin Net | 12 | 3,840 | 55 | 1.45% | 8 | 4 |
| 141711 | Fiber Beam | 23 | 5,888 | 54 | 0.92% | 9 | 3 |
| 58893 | Gemnet Enterprise Solutions | 16 | 5,632 | 51 | 0.91% | 5 | 4 |
| 135003 | Multan Cable & Internet Services | 8 | 2,048 | 49 | 2.41% | 8 | 2 |
| 131275 | Logon Broadband | 16 | 4,096 | 38 | 0.94% | 6 | 2 |
| 136174 | The Professional Communications | 10 | 2,560 | 32 | 1.26% | 7 | 2 |
| 137561 | Waylink | 9 | 2,304 | 28 | 1.22% | 8 | 0 |
| 140039 | Master Communication | 4 | 1,024 | 26 | 2.56% | 4 | 2 |
| 141778 | Dream Internet Services | 11 | 2,816 | 25 | 0.89% | 5 | 1 |
| 136610 | Wide Band Communications | 4 | 1,024 | 18 | 1.77% | 4 | 1 |
| 151648 | Alpines Internet | 4 | 1,024 | 16 | 1.57% | 3 | 0 |
| 141431 | Call 2 Phone | 2 | 512 | 14 | 2.76% | 2 | 1 |
| 149283 | Xtream Fiber | 1 | 256 | 10 | **3.94%** | 1 | 1 |
| 55414 | Worldcall Telecom | 6 | 2,048 | 10 | 0.50% | 3 | 0 |
| 141361 | Bliss Communication Network | 6 | 1,536 | 9 | 0.59% | 2 | 0 |
| 141347 | 7 Star Telecom | 1 | 256 | 9 | 3.54% | 1 | 1 |
| 140608 | TES Media | 2 | 512 | 8 | 1.57% | 2 | 0 |
| 142120 | McSol | 2 | 512 | 8 | 1.57% | 1 | 1 |
| 151848 | Logi-Tech Cable | 1 | 256 | 8 | 3.15% | 1 | 1 |
| 55714 | Fiberlink | 2 | 512 | 8 | 1.57% | 1 | 1 |
| 139087 | Fast Web & Wireless Communications | 3 | 768 | 7 | 0.92% | 2 | 0 |
| 150387 | Badar Enterprises Cable Network | 2 | 512 | 7 | 1.38% | 1 | 0 |
| 135567 | Air Max | 4 | 1,024 | 6 | 0.59% | 4 | 0 |
| 154086 | Tufa Telecommunication | 2 | 512 | 6 | 1.18% | 1 | 0 |
| 139302 | Ashiq Cable Network | 2 | 512 | 6 | 1.18% | 1 | 0 |
| 136225 | Smart Telecom | 3 | 768 | 5 | 0.66% | 2 | 0 |
| 149788 | Upnet | 1 | 256 | 5 | 1.97% | 1 | 0 |
| 150382 | **Broadband Vision** | **78** | **19,968** | **4** | **0.02%** | 3 | 0 |
| 152684 | The Wah Telecom | 2 | 512 | 3 | 0.59% | 1 | 0 |
| 64093 | Wise Communication Systems | 3 | 1,024 | 3 | 0.29% | 1 | 0 |
| 141377 | Faisal Cable Networks | 2 | 512 | 3 | 0.59% | 1 | 0 |
| 141380 | New Millennium Network | 4 | 1,280 | 2 | 0.16% | 1 | 0 |
| 141234 | Big Data Technologies | 1 | 256 | 2 | 0.79% | 1 | 0 |
| 133502 | **LINKdotNET Telecom** | **10** | **2,560** | **1** | **0.04%** | 1 | 0 |

### 4.1 Density spans a factor of 800

**Gerry's Information Technology: 169 live hosts in 1,280 addresses, 13.31%.**
**Broadband Vision: 4 live hosts in 19,968 addresses, 0.02%.**

Broadband Vision announces 78 blocks, one of the largest allocations in the set, and almost none of
it is in use. LINKdotNET is comparable: 10 blocks, 2,560 addresses, **one** live host.

**Consequence for any published rate.** Announced address space is a poor proxy for how much of a
network is in use. A per-ISP detour rate weighted by address count would be dominated by networks
that are almost entirely empty. Rates should be weighted by **live hosts** or reported per ISP
without weighting.

**Caution on the extremes.** Gerry's 13.31% rests on 1,280 addresses and one ISP; small
denominators produce unstable percentages. The ordering of the top few is reliable; the exact
percentages for ISPs with under 1,000 addresses are not.

### 4.2 Where the usable targets are

Three ISPs hold 40% of all live hosts: CMPak LDI, Connect Communications and Optix Pakistan, 1,123
of 2,793 between them. **Optix alone contributes 26 blocks with 8 or more live hosts**, the largest
single contribution to a panel.

Note that block count and live-host count diverge sharply. Connect announces the most blocks (135)
but has life in only 40 of them. CMPak announces 92 and has life in 78.

---

## 5. Probe-type pilot (RIPE Atlas)

`4_atlas/fire_probe_type_pilot.py` then `analyse_pilot.py`. 35 targets × 19 probes × 3 protocols,
**1,225 results**. Targets came in three groups: 20 reachable in the June census, 8 unreachable but
in a block with a reachable sibling, 7 in wholly unreachable blocks.

### 5.1 Protocols answer different questions

| protocol | hops answered | destinations reached |
|---|---|---|
| UDP | **73.2%** | 30.9% |
| ICMP | 70.2% | 32.4% |
| TCP/80 | 63.5% | **39.0%** |

UDP and ICMP reveal more of the path; TCP reaches more destinations. Path work should use UDP or
ICMP, with TCP as the reachability check.

### 5.2 A probe is usable *under a protocol*, not absolutely

| probe | ICMP | TCP | UDP |
|---|---|---|---|
| 60223 Nayatel | 34% public hops | **0%, every trace lacks a public address** | 34% |
| 62224 PERN | **0%** | 33% | **0%** |

Two probes fail completely under opposite protocols. Any single global protocol choice silently
discards one of them.

### 5.3 Probe roster

**7 of 19 probes returned nothing.** Of the 12 that worked, ranked by the share of answering hops
that are public addresses: TES 83%, Z-Com 74%, Nova 65%, ACL (AS138910) 50%, PTCL Lahore 50%, the
Cybernet probes and PTCL Karachi 43–48%, Nayatel 34%, PERN 33%, Cybernet spare 30%.

ACL is a network never previously used and it performs mid-pack, so it is worth keeping.

### 5.4 Liveness is not stable over months

**14 of the 15 targets that were unreachable in the June census responded in September** — and
mostly to TCP, the same protocol that failed in June. So this is not a protocol effect, it is
time: those hosts were down and are now up.

The exception is instructive: targets in blocks where *nothing* responded in June are still mostly
dark. Empty blocks stay empty; individual hosts come and go.

---

## 5A. Adaptive sampling: how it performed

The all-Pakistan scan (`2_liveness/scan_all_pk.py`) does not test every address. It draws 8 at a
time from each /24-equivalent and decides whether to keep going. Measured over 19,267 blocks and
**508,616 checks**:

**Terms.** A **check** is one liveness test of one address, which may send up to three packets
(ICMP, then TCP/80, then TCP/443) and still counts as one. A **draw** is a batch of 8 addresses
selected from a block. Neither is a *probe*, which in this project always means a deployed RIPE
Atlas device.

> **The tallies in this section are a mid-run snapshot** of 19,267 blocks and 508,616 checks. The
> completed sweep covers **22,556 blocks and 844,102 checks**, and 19.5% of blocks reached 8 live
> hosts rather than the 9% quoted below. The proportions here still describe how the rule behaves;
> the absolute counts are superseded by section 1 and `ISP_SUMMARY.md`.

### The rule

```
draw 8 addresses from the block
  0 live after 2 draws  -> stop; the block looks empty
  >=1 live              -> keep drawing until 8 live found, or 64 addresses checked
```

### Draws accumulate, and the loop overshoots

Two properties of the loop that are easy to misread from the rule as written.

**Draws accumulate; nothing is discarded.** A draw does not replace the previous one. If the first
draw of 8 answers 6 times, those 6 are kept, the next draw takes 8 addresses from the 248 not yet
tried, and the block closes when the running total reaches 8. No address is probed twice, and
addresses that did not answer are written to disk as well, which is what the re-probe validation in
section 5C depends on.

**The target is tested per draw, not per address, so blocks overshoot.** A draw always runs to
completion. Starting from 6, a dense second draw can close the block at 10 or 12.

| live hosts in the block | blocks | what happened |
|---|--:|---|
| 1 to 7 | 1,481 | hit the 64-address cap, or ran out of addresses |
| **8** | **3,394** | 57.7%, stopped on the target |
| 9 to 14 | 975 | overshot inside a draw |
| 15 or more | 37 | dense blocks, up to 92 in one case |

**1,012 blocks, 17.2% of live blocks, ended above 8.** The overshoot is free: it happens inside a
draw that was already running and costs no extra checks.

**The top-up pass does not overshoot**, which makes the two scanners asymmetric.
`2_liveness/topup_scan.py` tests `live >= target` before every individual address and breaks
immediately, so it stops exactly at 8. The main sweep stops at the end of a draw; the top-up stops
at the address.

**Consequence.** A block's live count is shaped partly by which scanner last touched it. This does
not affect any current result, because the counts are used only as a floor and as a panel-eligibility
test. It would matter to anyone reading the distribution above as a distribution of true occupancy.
It is not one, and cannot be corrected into one without knowing the per-network miss rates that
section 5C shows are not uniform.

### Where the effort went

| checks per block | blocks | share | checks | % of all checks |
|---|---|---|---|---|
| **stopped at ≤16** (looked empty) | 14,441 | **75%** | 230,584 | 45% |
| 17–32 | 539 | 3% | 15,420 | 3% |
| 33–48 | 553 | 3% | 24,473 | 5% |
| 49–63 | 272 | 1% | 15,219 | 3% |
| **hit the 64 cap** | 3,462 | **18%** | 222,920 | **44%** |

### It works

| | |
|---|---|
| Exhaustive scan of these blocks would cost | 4,893,818 checks |
| Adaptive actually cost | **508,616 (10.4%)** |
| **Saving** | **10×** |
| Checks per live host found | **19.0** (exhaustive would be 182) |

The early-stop rule carries it: **75% of blocks are dismissed after 16 checks**, and 14,373 of
those yielded zero live hosts. The two-draw rule almost never abandoned a populated block.

### A known inefficiency, not fixed

**18% of blocks hit the 64-check cap and consumed 44% of all checks.** Those blocks had some life
but never reached 8 live hosts, so escalation continued until the cap stopped it. Only **9% of
blocks reached the target of 8**.

So the rule spends its largest share of effort on blocks it ultimately fails at.

Whether that is waste depends on the purpose:

- **For selecting the Exp 16.1 panel it is waste.** A block that yields under 8 live hosts in 64
  checks is sparse and will never make a good panel block.
- **For estimating national density it is not.** Those extra draws are exactly what pins down
  density in moderately-populated blocks, which is where the uncertainty sits.

**Why it was not changed mid-run.** The sampling rule has to be constant across the dataset or
per-block figures stop being comparable between blocks scanned before and after the change.

**What a future run should do.** Add an expected-yield stop: after each draw, project the final
count from observed density and abandon the block when 8 is out of reach. For example, 2 live in
32 checks projects to about 4 at the cap. On this data that would cut roughly 40% of the check
budget with almost no loss of live hosts found.

## 5B. Finding: reachability differs by ~9% between two Pakistani networks

Not a measurement problem. A result.

250 addresses confirmed alive from **AS135407 (TES)** were re-probed from **AS45669 (Mobilink)**,
idle machine, five concurrency levels from 10 to 200 threads. **Recall never exceeded 92.4%.**

So roughly **one Pakistani host in eleven that answers from TES does not answer from Mobilink**,
using identical probes, at the same moment, with no load on either end.

### Why it matters here

The project's question is whether Pakistani networks reach each other well. This is a direct
measurement of the answer being **no, not uniformly**. Reachability is not a property of a host; it
is a property of the pair (source network, host).

### What it does to our method

- **Liveness is vantage-relative.** "2,793 live hosts" means "answered from TES". A different
  vantage gives a different number, and neither is wrong.
- **Cross-vantage validation is confounded by construction.** Re-probing a TES scan from Mobilink
  cannot distinguish a missed host from an unreachable one. This is exactly what contaminated the
  figures in §2.10.
- **The union is better data than either alone.** `topup_scan.py` deliberately runs from the second
  vantage and tags every record with its egress ASN, so the two stay separable and the union is
  available without silently merging them.

### What is not yet known

- Whether the asymmetry is symmetric: are ~9% of Mobilink-reachable hosts invisible from TES too?
  Untested; it needs a scan from each direction over the same address set.
- Whether it concentrates in particular destination ISPs, which would make it an interconnection
  finding rather than a general one. The data to check this exists and the analysis has not been run.

## 5C. The miss rate is not uniform across networks

Every count in this document is a floor (§2.10). This section measures whether that floor sits at
the same height for every network, because if it does not, per-ISP densities are not comparable
without correction.

### Method

900 addresses marked dead by the all-Pakistan scan were re-probed on an idle machine and grouped by
the network announcing them.

### Result

| network | re-probed | came back alive | **miss rate** | share of found hosts |
|---|---|---|---|---|
| **AS17557 PTCL** | 629 | 218 | **35%** | 73.5% |
| AS9541 Cybernet | 32 | 8 | 25% | 3.2% |
| AS38264 Wateen | 32 | 7 | 22% | 2.4% |
| unattributed | 50 | 2 | 4% | 1.3% |
| **overall** | **900** | **256** | **28.4%** | |

**Spread: 31 percentage points.** The miss rate is not uniform.

### Sample sizes, stated plainly

Only the PTCL figure rests on a usable sample. Cybernet and Wateen have **32 re-probes each**, so
their rates carry error bars wide enough to overlap almost anything: a 95% binomial interval on
8/32 runs roughly 12% to 43%. **They should not be quoted as point estimates.**

What the data supports is one claim: **PTCL is missed more often than the fleet average**, on 629
observations.

### Likely mechanism

PTCL's own access path costs **25.5 ms** before it reaches anything, against under 4 ms for every
other vantage measured (`5_detector/RULES.md` R1). A slower path means more probes exceed the
1.5 s timeout and more hosts are recorded as dead. That is consistent with the direction observed,
but it is a hypothesis: the test that would confirm it is re-probing PTCL space with a longer
timeout and seeing whether the gap closes. Not done.

### What this does and does not permit

**Permitted.** Comparisons where the gap is large relative to the correction. Gerry's Information
Technology at 13.31% against Broadband Vision at 0.02% is a factor of 600; no miss-rate difference
of 13 points closes that.

**Not permitted.** Comparisons between networks with similar densities. Two ISPs measured at 5% and
6% cannot be ordered, because the difference is smaller than the uncertainty in their respective
corrections.

**Not permitted.** A single national correction factor. Scaling every density by one number assumes
a uniform miss rate, which this measurement rejects.

**Unaffected.** Target selection for the route experiment. The pool is roughly 100 times larger than
the experiment needs, and PTCL alone contributes 2,159 blocks holding 8 or more live hosts.

### What a published figure should look like

A per-ISP density should carry its own correction factor **and the sample size that factor rests
on**, so a reader can tell a measured value from an extrapolated one. Densities for networks with
fewer than roughly 200 re-probes should be reported as observed values with the miss rate unknown,
not silently corrected.

## 5D. Hop silence singles out the same network the miss rate does

**Added after the route sweep.** Section 5C found PTCL's liveness miss rate near 35% against 22% to
25% elsewhere, and offered slow-path timeout as the likely mechanism. The route sweep provides a
second, independent measurement of the same network, and it points the same way.

### Result

Across the 34,191 selected traces:

| | PTCL AS17557 | every other network |
|---|--:|--:|
| Selected traces | 23,593 | 10,542 |
| Median TTL slots probed | 11 | 12 |
| Median hops that answered | **5** | **8** |
| Silent TTL slots | **48%** | **31%** |

PTCL paths are not shorter. The tracer probes about as many TTL slots and roughly half return
nothing. No other network in the top ten by trace count exceeds 40% silence.

### Why this is more than a repeat of 5C

The two measurements probe **different reply types**. Liveness measures whether an *end host*
answers ICMP echo or completes a TCP handshake. Hop silence measures whether a *router* emits an
ICMP TTL-exceeded message. These come from different devices under different code paths, and both
are suppressed on PTCL relative to its peers.

That pattern discriminates between the candidate mechanisms:

- **ICMP rate limiting** predicts both, and is now the better-supported reading.
- **MPLS tunnelling** predicts hidden interior hops but should not affect whether end hosts answer,
  so it does not account for 5C.
- **Slow path plus a 1.5 s timeout**, the 5C hypothesis, predicts both, and remains live.

Rate limiting and slow-path timeout are not exclusive and both survive. What has changed is that a
single-cause explanation confined to traceroute is now ruled out.

### Standing of this claim

**Observed**, on 34,191 traces: PTCL hop silence is 48% against 31% elsewhere. The sample is large
and the gap is wide, so unlike the 5C per-network rates this one does not rest on 32 observations.

**Hypothesis**, not established: that ICMP rate limiting is the cause. Neither measurement observes
a rate limiter. The test that would settle it is re-tracing PTCL space at deliberately varied probe
rates and longer timeouts, and seeing whether silence falls. Not done.

### Consequence for the selection

The 5-hop gate therefore binds almost entirely on PTCL: 14,307 of 23,593 selected PTCL traces (61%)
answered exactly 5 hops, sitting on the floor. Selected traces are **not** uniformly clean, and
per-network comparisons of path detail must account for it. Stated in full in
[`ISP_SUMMARY.md`](ISP_SUMMARY.md).

## 5E. Discovery and tracing ran from different networks

**The two halves of the study do not share a vantage point**, and any reader of the route results
needs to know which network produced them.

### The split, measured

| | AS135407, TES | AS45669, Mobilink |
|---|--:|--:|
| Liveness checks | **781,428** | 62,674 |
| Live hosts discovered | **33,316** | 10,421 |
| Traceroutes | 88 | **43,671** |

Hosts were found mostly from TES. Routes to them were traced almost entirely from Mobilink.

### The cutover is clean, not gradual

The route sweep started on TES and moved to Mobilink when the measuring machine changed networks.
Classifying every trace by its first public hop:

* traces 0 to 87 leave via `45.249.11.241` (AS135407, TES)
* traces 88 to 43,764 leave via the Mobilink chain (`119.160.114.81`, then `119.160.84.61`)
* no interleaving in either direction

So **99.8% of the route data is single-vantage.** Every reach rate and route-visibility figure in
`ISP_SUMMARY.md` is "as seen from Mobilink". It is not a property of the destination network alone,
and it is not an average over two vantages.

The 88 TES traces reached 19% against Mobilink's 83%, but that is the initial test batch on a small
sample and should not be quoted as a vantage comparison.

### Does the mismatch cost reach?

A host discovered from TES might simply not answer from Mobilink, which would appear as a trace
that fails to reach. Measured over the full sweep:

| host discovered from | traces | reached | rate |
|---|--:|--:|--:|
| Mobilink, the tracing network | 10,428 | 8,806 | **84%** |
| TES, a different network | 33,337 | 27,408 | **82%** |

**2 points.** Smaller than the ~9% cross-vantage disagreement in 5B would suggest.

**This is suggestive, not a controlled result.** The two groups are disjoint by construction, since
the top-up only probed addresses the main sweep had never tried, and the top-up targeted thin
blocks (1 to 7 live) while the main sweep covered everything. Block density and discovery vantage
are confounded, and this design cannot separate them.

### A claim to avoid

The top-up found 10,421 live hosts. **These are not hosts the first vantage missed.** The top-up
skipped every address already probed, so they sit on addresses TES never tried. The only place in
this study where the same addresses were tried from both networks is the controlled 250-address
re-test in 5B, and that is where the 9% figure comes from.

The headline counts are a **union of two vantages over disjoint address sets**: better coverage
than either alone, but not a two-vantage measurement of the same addresses.

## 6. Limitations

- **One vantage.** The scan runs from AS135407 (TES). Validation shows about 9% of Atlas-reachable
  hosts do not answer us. Results are a lower bound on liveness.
  A related risk: TES's own routing may favour some Pakistani networks over others, so per-ISP
  density could carry a source-network bias. The Atlas census from 12 different networks is the
  check on this.
- **A point in time.** See §5.4. The map has a short shelf life and should be refreshed before any
  run that depends on it.
- **Firewalls, not emptiness.** A silent address may host a device that drops ICMP and has no open
  TCP port. "Not alive" here means "did not answer three specific probes from one place".
- **Only ports 80 and 443 were tried.** Hosts serving other ports and dropping ICMP are missed.
- **IPv4 only.** Pakistani IPv6 deployment is not covered by this experiment at all.
- **The universe is small ISPs only.** PTCL, Transworld and every other large operator are absent
  as destinations. See §1.3.
- **Scanning etiquette.** 206,058 probes were sent across Pakistani address space from a single
  university-adjacent connection. Order was randomised and rates kept modest to avoid concentrating
  traffic on any one network. This is standard internet-measurement practice — the TASS paper in
  `papers/` is specifically about minimising the footprint of exactly this kind of scan — but it is
  worth stating plainly rather than leaving implicit.
