# PK Internet Project - Summary of Experiments

**Author:** Rayan Atif

**Overarching goal:** find out how effectively **PKIX (the Pakistan Internet
Exchange, the local point where Pakistani ISPs can hand traffic to each other)** is
actually used. In plain terms: how much "Pakistani" web traffic stays inside the
country versus leaving to foreign infrastructure, and how that affects the latency a
real Pakistani user feels.

Two tools recur throughout:

1. **RIPE Atlas ICMP Paris traceroutes** from probes inside Pakistan. RIPE Atlas is a
   worldwide network of small measurement devices (called *probes*) hosted inside
   ISPs. A *traceroute* lists the routers a packet passes through on its way to a
   site. "Paris" is a variant that keeps the packet flow constant, so that
   load-balancing routers do not show up as fake route changes.
2. An **IP to operator to location** lookup: Team Cymru and an RDAP registry fallback
   to map each IP address to the network (ASN) that owns it, and ip-api to find where
   that IP is physically located.

A few terms used below:
- **RTT** = round-trip time, i.e. latency in milliseconds.
- **CDN** = Content Delivery Network, a service that caches a site on servers in many
  cities so users reach a nearby copy (Cloudflare is the common one here).
- **Anycast** = the same IP address announced from many cities at once.
- **LDI** = Long Distance and International operator, licensed to carry Pakistan's
  international traffic. The two big ones are PTCL and Transworld.
- **Hairpinning** = traffic between two points inside Pakistan that leaves the country
  and comes back.

---

## At a glance

| Exp | Question | Status | Headline |
|-----|----------|--------|----------|
| **01** | Where are Pakistani websites hosted, and how is traffic routed to them? | done | About 75% of top Pakistani sites are NOT on a Pakistani server. Traffic leaves to foreign exchange points, so PKIX is underused. |
| **1.1** | Does per-ISP DNS (GeoDNS) change the hosting picture? | done | Only 8 of 103 sites give different answers per ISP, so Exp 01's single DNS lookup was valid for about 92% of sites. |
| **1.2** | Is the big global content (Google, Meta, etc.) cached inside Pakistan? | done | Mostly no. It is reached at regional distance, not from inside Pakistan. Only Cloudflare and X were served locally, and only on Nayatel. |
| **1.3** | What does Nayatel's traffic actually pass through? | done | About 40% of Nayatel paths use an international operator (the foreign-hosted tail); about 59% bypass it with direct peering. Nayatel is multi-homed. |
| **02** | Classify ISPs by whether they use PKIX, and plan probe coverage. | planning / deploying | Sets 1/2/3 built from the PTA roadshow deck plus Exp 01; plan is about 21 new probes plus 5 existing plus volunteers. |
| **03** | Does the route and RTT to a site change over time? | 24h done, 48h running | Local sites 2 to 40 ms versus offshore 130 to 200 ms. No daily (diurnal) cycle and stable routes, so the inefficiency is structural, not congestion. |
| **3.1** | Where do PTCL paths jump in RTT, and does PTCL peer with Transworld? | done | A ~26 ms access floor then a +80–200 ms international exit; PTCL peers with Transworld **domestically** (100%) but never for abroad traffic (0%) — verified by direct probe-to-probe test. |
| **04** | How much of an ISP's address space hairpins (trombones) abroad, systematically? | Worldcall done | 31% of Worldcall's 52 /24s trombone to **Equinix Singapore via Transworld**; the same IPs are reached **locally by PTCL** — so a domestic route exists and Transworld chooses the hairpin. Prefix-sampled (TASS-style), RTT-physics detector. |

---

## Experiment 01: Where are Pakistani websites hosted?

*(91 sites, 5 probes on 5 ISPs, all 10 batches. Full writeup:
`findings/01_hosting_and_routing_analysis.md`.)*

- **Hosting census:** 23 sites (25%) sit on a real server inside Pakistan, 26 (29%) on
  a real server abroad, and 42 (46%) on an anycast CDN (almost all Cloudflare). So
  roughly three quarters are not hosted on a Pakistani server.
- **By sector:** government mostly stays in-country (13 of 18 sites). News, banking,
  and e-commerce have largely left. Many Pakistani companies host abroad by choice
  (banks in the US, Singapore, Dubai; several news sites on Hetzner in Finland).
- **The transit hierarchy is the most robust finding:** downstream ISPs route almost
  100% of their traffic through one of the two international operators (PTCL or
  Transworld). Nayatel is the exception and the most independent.
- **Domestic routing quality depends heavily on the ISP:** Nayatel reaches local
  content in single-digit milliseconds, while others are much higher. For the same
  Cloudflare-fronted site, Nayatel can be 3 to 4 ms where another ISP is hundreds of
  ms, for identical content.
- **Hairpinning is concentrated, not pervasive:** only 5 of the 23 Pakistan-hosted
  sites leave the country on their path. Traffic was seen exiting through foreign
  exchanges (Equinix Singapore, DE-CIX Frankfurt, EMIX UAE), which is direct evidence
  that PKIX is underused.

### 1.1 Per-ISP DNS resolution
Resolving each site from every ISP's own DNS resolver, only 8 of 103 sites returned
different IPs per ISP (this is called GeoDNS). The central lookup used in Exp 01 was
therefore representative for about 92% of sites, so the hosting census stands.

### 1.2 CDN presence inside Pakistan
Most big content (Google, Meta, Apple, Microsoft) was reached at regional latency
(about 20 to 50 ms), not from inside Pakistan. Only Cloudflare and X were served
locally, and only on Nayatel. This undercounts local caching, because the ISPs known
to host caches were not yet among our probes, which is exactly what motivates
Experiment 02.

### 1.3 Nayatel routing (what it passes through)
About 40% of Nayatel's paths use an international operator (almost all Transworld),
and this is essentially the foreign-hosted tail of sites. About 59% bypass the
international operators entirely by peering directly with Cloudflare, Microsoft, and
AWS, or by using alternative transit (SingTel, NTT). Nayatel is effectively
multi-homed (connected to several upstreams at once), which is why everyday sites are
about 3 ms.

---

## Experiment 02: ISP classification (PKIX Sets 1/2/3) and probe deployment

*(`experiments/02_isp_classification/`. This is a plan with deployment in progress.)*

- It builds on the PTA "Pakistan Peering Roadshow" deck plus Exp 01's measured
  evidence to sort ISPs into three sets: **Set 3** present at PKIX and shown to
  exchange traffic (8 ISPs), **Set 2** present but not shown to exchange (about 26),
  and **Set 1** not at any PKIX node (about 59 licensees, including TPCPL/Nova, Optix,
  Fiberlink, and others).
- **Probe plan:** about 21 new probes plus 5 existing plus Karachi volunteers, to
  cover the sets and close the coverage gap that Exp 1.2 exposed. It keeps *hosts*
  (Pakistani servers used as measurement destinations) separate from *probes* (the
  vantage points we measure from).
- **Status:** planning and deploying. The probe rollout feeds Experiment 03's vantage
  coverage.

---

## Experiment 03: Longitudinal routing (adding the time axis)

*(`experiments/03_longitudinal_routing/`, with results in `findings/03_*`.)*

Where Exp 01 is a single snapshot, Exp 03 re-traces the same sites every 15 minutes
from several Pakistani ISPs over days, and records whether the path and the RTT change
over time, per (site, probe). It uses Paris traceroute so that an observed change is a
real reroute and not load-balancer noise, plus a 1-per-minute (or 1-per-5-minute) ping
companion for fine latency and loss. Each probe's network (ASN) is measured live each
round, which matters for multi-homed or campus probes that can switch ISP.

| Run | Setup | Findings |
|-----|-------|----------|
| `run_20260610_2h` | 1 probe (Nayatel), 5 sites, 2 hours | Baseline and pipeline validation. |
| **`run_20260611_24h`** | 5 probes, 5 sites, 24 hours | The main result so far (below). |
| `run_20260612_48h` | 8 probes, 10 sites, 48 hours | Running. Two daily cycles, adds a PTCL vantage and CDN PoP-flip candidates. |

**24-hour findings** (`findings/03_longitudinal_routing_24h.md`):

- **The offshore penalty, measured:** local Pakistani sites sit at 2 to 40 ms, while
  the two banks sit at 127 ms (MCB, served from Singapore) and 200 ms (HBL, served
  from New Jersey, US). That is a 3 to 9 times latency cost, and it holds on every
  ISP.
- **A large per-ISP gap on local sites:** the same local site is 1.6 ms on Z-Com but
  42 ms on Cybernet. ISP routing quality matters as much as where the site is hosted.
- **No daily (diurnal) cycle:** latency was flat across the whole day, so the penalty
  is structural (caused by distance and hosting choice), not evening congestion.
- **Routes were stable:** essentially zero genuine path changes, which both confirms
  the Paris method and shows the inefficiency is structural.
- **The method also caught a real outage:** a roughly 5.7-hour ISP outage of one
  network (TPCPL/Nova) during an overnight thunderstorm showed up cleanly as a gap
  across all targets.

---

## The through-line

Exp 01 establishes where Pakistani content lives (mostly offshore, so PKIX is
underused). Exps 1.1, 1.2, and 1.3 reinforce and explain that picture (the DNS lookup
is valid, big content is not cached locally, and they show why Nayatel is fast).
Exp 02 plans the probe coverage needed to classify ISPs by their PKIX use. Exp 03 adds
the time axis and shows the offshore penalty is stable and structural, so the fix is
local hosting and better peering through PKIX, not more bandwidth. That is the case
this project is building, with data, for using PKIX.

---

## Figures

*(Graphs to be added here.)*
