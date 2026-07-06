# The Local Path Not Taken: Measuring Domestic-Traffic Hairpinning and PKIX Underuse in Pakistan

**Rayan Atif** · supervised by Dr Saqib Ilyas (LUMS) · funded by the APNIC Foundation

*Working draft. Structure follows `paper/paper_structure.md`; register follows
`paper/style_notes_ixp.md` and `paper/style_notes_p1.md`. Numbers are from the committed
experiments; single-snapshot results are flagged and will be range-bounded by Exp 4.2/07.*

---

## Abstract

Pakistan operates an Internet Exchange (PKIX) at four locations with dozens of connected
members, yet its route server appears in **zero** of the BGP paths we observe to Pakistani
destinations. We ask, with active measurement from inside the country, whether this
underuse actually costs Pakistani users — and find that it does, twice over. Using RIPE
Atlas probes in 14 Pakistani networks, we (i) census where the top Pakistani websites are
hosted, (ii) introduce a **geo-IP-proof, RTT-physics detector** for path *tromboning*
(domestic traffic that leaves the country and returns) and run a **complete block-level
census of every small Pakistani ISP**, and (iii) measure the latency and resilience cost of
the resulting routing. We find that **~40% of the top sites are not on a Pakistani server**,
that **11% of small-ISP address space is reachable only by hairpinning abroad** — a rate
driven far more by *which ISP you measure from* than by the destination — and that the
hairpin path is a **choice**: the same address is reached locally from one transit and
abroad from another. The penalty is a **3–9× latency increase** that is stable and
structural (no diurnal cycle), and during a real submarine-cable fault (SMW5, July 2026)
international paths degraded — chiefly as **+31% jitter** — while domestically-routed traffic
was untouched. The through-line is a single sentence: *the local path exists but is not
taken*, and PKIX is the instrument that would take it.

## 1. Introduction

Only two operators — **PTCL (AS17557)** and **Transworld (AS38193)** — are licensed to sell
international transit in Pakistan; every other ISP buys upstream from them. A consequence is
that two domestic ISPs with no direct peering typically reach each other *through* an
international operator, and domestic traffic frequently **hairpins** abroad and back even
when both endpoints sit in the same city. An Internet Exchange is the standard remedy, and
Pakistan has one: PKIX runs at Islamabad, Karachi, Lahore, and a PTCL datacenter, with
21/14/18 members listed per site (PTA, 2026). Its own figures show inter-ISP latency
collapsing from 100–144 ms internationally to **1–31 ms** through the exchange. And yet the
PKIX route server (AS140307) is absent from every BGP path we see to Pakistani networks — the
exchange is built but, for most members, not *used*.

This paper measures the consequences of that underuse from the data plane. Our contributions:

1. A **hosting census** of the top Pakistani websites (where content physically lives).
2. A **geo-IP-proof RTT-physics detector** for tromboning, and a **complete census** of
   hairpinning across the entire small-ISP population — who hairpins whom, through which
   international operator, to where.
3. The **cost**: the latency penalty of offshore/hairpin routing (stable and structural),
   evidence that a **domestic path exists but is not chosen**, and the **resilience** loss
   during a live submarine-cable fault.

Framed in the language of prior IXP work: we quantify how often Pakistani ISPs make the
*wrong routing choice* — sending domestic traffic abroad when a local path is available.

## 2. Related work

Di Bartolomeo et al. (ISCC 2015) compare IXP vs upstream paths for Italian ISPs using RIPE
Atlas and controlled BGP announcements, finding IXP paths give better, more stable latency
and preserve traffic locality; our study mirrors their vantage (national probes → national
targets) and their locality-as-sovereignty framing, but replaces hand-picked targets with a
**complete prefix census** and a detector that does not trust geo-IP. Gupta et al. (PAM
2014) show African ISPs that do not peer locally send domestic traffic **detouring through
Europe** — precisely the tromboning we measure in Pakistan. Prefix-based target selection
follows the TASS approach (Klick et al., IMC 2016): all IPs in an announced prefix share one
BGP route, so a few IPs per block is routing-complete. Large-IXP studies (Ager et al.,
SIGCOMM 2012; Chatzis et al.) motivate why peering matters. We build on RIPE Atlas, RIPEstat
announced-prefixes, and Team Cymru / RDAP for ASN and registry resolution.

## 3. Data and vantages

We measure from **14 connected RIPE Atlas probes** inside Pakistani networks, spanning both
international operators and their downstreams: PTCL (×3, incl. a LUMS anchor), Transworld and
its retail arm TES, Cybernet (×3, two cities), Nayatel (×2), Nova/TPCPL (transits
Transworld), Fasttel, Orbit, and Z-Com. Two probes (a PTCL anchor and a Transworld backbone
probe) are **ICMP-filtered** — their path is invisible, so we use ping for their RTT — and one
PTCL probe runs in a container that exposes only two hops (valid RTT, opaque path). We flag
these throughout. Targets vary per experiment: the top-100 Pakistani websites (hosting), 8
spread IPs in every announced /24 of every small ISP (tromboning census), a fixed
local/offshore panel (longitudinal), and a balanced CDN/Abroad/PK sample during the outage.

## 4. Method: an RTT-physics tromboning detector (DETECT)

**The problem with geo-IP.** Registration country lies at exactly the hops that matter. A
"Canadian" Shaw address (AS6327) and a "US" Cogent address (AS174) both sit **physically in
Pakistan** at ~2 ms — Cogent even runs a domestic PoP used as an interconnect fabric — so a
country-of-ASN test flags in-country hops as foreign. Conversely a genuinely foreign exit
hop often does not resolve in BGP at all (Transworld's international egress at Equinix
Singapore is unannounced; only RDAP/hostname reveals it). A detector that trusts geo-IP is
wrong in both directions.

**The detector.** We decide tromboning by **RTT physics**, not hop country. A trace **left
Pakistan** if any responding hop is foreign with RTT ≥ 40 ms, **or** there is a ≥ 60 ms jump
between consecutive hops, **or** any hop RTT ≥ 70 ms; a path whose maximum RTT stays < 45 ms
is **local**. We ignore RTTs > 500 ms (queuing / ICMP-error-generation artefacts, endemic on
filtered probes — there we use ping min-of-N) and exclude the Shaw/Cogent artefact ASNs. The
40 ms floor is the physical round-trip to the nearest foreign exchange; the jump backstop
catches invisible foreign hops.

**Validation.** On our first target (Worldcall) a naïve geo-IP test flagged **53/53** paths
as foreign; the RTT-physics detector reduces this to a clean **16/52**, matching manual
inspection of the hop-by-hop RTTs. We report this agreement before quoting any rate.

## 5. Where Pakistani content lives (HOST)

Combining our two hosting censuses (Exp 01, 91 sites; Exp 1.4, top-100), across **172 sites**
we find **60% hosted in Pakistan, 31% on an anycast CDN (almost all Cloudflare), and 8% on a
real server abroad** (Fig `fig_hosting_split`). The split is strongly **sector-driven**:
government and education stay in-country, while news, banking, and e-commerce have largely
left — Pakistani banks host in the US, Singapore, and Dubai; several news sites on Hetzner in
Finland. Read the CDN slice with care: a low traceroute RTT proves the *network edge* is
local, not that the *content* is — `shaukatkhanum.org.pk` traces to a Cloudflare node at
~4 ms yet serves from Singapore (`colo=SIN`). So the honest reading is that **~40% of top
sites are not on a Pakistani server**, and an unknown fraction of the "local" CDN slice is
served abroad.

Two supporting results. Per-ISP DNS resolution (Exp 1.1) changes little — only 8 of 103 sites
resolve to different IPs per ISP — so a central lookup is representative for ~92% of sites, and
the census stands. And most large global content (Google, Meta, Apple) is reached at
**regional** latency (~20–50 ms), not from inside Pakistan; only Cloudflare and X were served
locally, and only on Nayatel (Exp 1.2) — an ISP-specific peering advantage we return to below.

## 6. Tromboning at scale (TROMB)

**Proof on one ISP.** From a Pakistani vantage to **Worldcall (AS38710)**, **16 of 52
announced /24s (31%) trombone to Equinix Singapore** via Transworld and back; the rest stay
local via the in-country Cogent PoP. The decisive result is RQ4: the *same* Worldcall address
`115.186.61.254` is **local (~46 ms) from PTCL** — whose path never touches Transworld — but
**trombones (~134 ms) from Transworld**. A domestic route exists; Transworld chooses the
hairpin. This is the whole thesis in one measurement.

**The national census.** Scaling to **every announced /24 of every small (FLL) Pakistani
ISP** — 747 blocks × 8 spread IPs × 7 route-visible probes = **18,260 traces** — we find
**~11% hairpin abroad and ~85% stay local** (807 inconclusive). Three findings stand out:

- **The source ISP dominates the outcome** (Fig `fig_trombone_by_source`). Trombone rate
  depends far more on *where you measure from* than on the destination: **Cybernet-Haripur
  46%** and **PTCL-Karachi 38%** hairpin most small ISPs, while every other vantage routes
  mostly local (4–10%), and **Nayatel is cleanest at 4%**. The same Cybernet ISP hairpins 46%
  from Haripur but 10% from Karachi — a **per-PoP**, not merely per-ISP, property.
- **The two licensed operators split the hand-off almost evenly** (Fig
  `fig_trombone_transit_exit`): Transworld 589 and PTCL 566 of the attributable trombones,
  then Cybernet's own backbone and Cogent. Exits are **China-heavy (347), then US (259), then
  Singapore (107)** — more scattered than Worldcall's single Singapore exit.
- **A /24 is a usable but imperfect routing atom:** with 8 IPs per block, **82%** of
  (source, block) pairs are uniform; the remaining ~18% split, though seconds-apart timing
  means some of that is intermittency rather than true per-host routing.

Of the sparse targets that actually reply, **325 are live hosts reached *via* an
international hairpin** — clean proof cases where a packet demonstrably enters the destination
ISP's own network only after leaving and re-entering Pakistan (Brain Telecom dominates).

*Caveat: the census is a single snapshot; verdicts flip minute-to-minute, so the 11% is a
snapshot rate that Exp 4.2/07 will report as a range.*

## 7. The latency cost and the unused local path (PENALTY)

The hairpin has a price, and it is stable. Re-tracing a fixed panel every 15 minutes over
days (Exp 03), local Pakistani sites sit at **2–40 ms** while two banks sit at **127 ms** (MCB,
served from Singapore) and **200 ms** (HBL, New Jersey) — a **3–9× penalty** that holds on
every ISP. The distribution is stark (Fig `fig_rtt_cdf`): paths that stay local remain under
~45 ms, while hairpinned paths pile up at **100–300 ms** — Singapore, China, and Europe
distances. The penalty shows **no diurnal cycle** and the routes are essentially static, so
it is **structural** — a hosting and peering choice, not evening congestion — and the fix is
local hosting and better peering, not more bandwidth. Routing quality is also unequal *within*
the country: the same local site is **1.6 ms on Z-Com but 42 ms on Cybernet**.

Why does the hairpin happen even between domestic parties? Because the transit structure
forces it: downstream ISPs route ~100% of paths through an international operator (Z-Com
91/91, Nova 65/65), whereas **Nayatel is only ~40%** — the most independent, reaching CDNs and
peers directly and using an operator only for genuinely foreign destinations. A direct
probe-to-probe test (Exp 3.1) isolates the mechanism: **PTCL peers with Transworld
domestically in 100% of local measurements but never (0%) for abroad-hosted traffic** — the
peering exists, but only for local exchange. The domestic path is there; it is simply not the
one chosen for most flows.

## 8. The resilience cost: a submarine-cable fault (CUT)

On 2 July 2026 a fault on the **SMW5** submarine cable degraded Pakistan's international
capacity; traffic was rerouted onto surviving cables. We monitored ping + traceroute every
15 minutes for 12 hours from all 14 probes to a balanced CDN/Abroad/PK sample. It was a
**latency degradation, not a blackout**, and it **eased over the window** — worst-hit paths
collapsed from the outage peak (e.g. `shophive.com` via PTCL **646 → 278 ms**), improving even
as measurement moved into peak business hours, so the recovery is genuine and not diurnal.

Quantified — outage peak (first 3 h) vs recovered state (last 3 h), international targets — the
fault hit as **instability, not a uniform latency step**: **average RTT +2%, jitter +31%,
path length flat**, concentrated on **PTCL-sourced paths (RTT +12%, jitter +50%)**. Path
changes were **load-balancing within the same transit** (e.g. alternating between two
Etisalat-UAE ingress IPs), *not* a reroute onto a different cable — the exit country stayed
constant, consistent with congestion on the SMW5-era detour easing rather than a repair.
Crucially, **local/PK-hosted targets showed no increase** — the disruption was confined to the
international leg. *(One unexplained local event: `pbs.gov.pk` spiked chaotically across all
probes at ~08:00–10:00 PKT, unrelated to the submarine path.)* The single practical lesson:
a cable cut badly hurts the offshore-hosted majority and barely touches anything hosted in
Pakistan and exchanged locally.

## 9. Discussion

The four results compose one argument. Content is largely offshore (HOST); even domestic
traffic hairpins abroad, by choice, through the two international operators (TROMB); this
costs a stable 3–9× latency penalty and forgoes an available local path (PENALTY); and it
removes a resilience margin that local exchange would keep during a cable fault (CUT). PKIX
is the instrument that closes all four — its own latency table (1–31 ms vs 100–144 ms) shows
the gain — and the obstacle is not construction but **use**: physical presence at PKIX is not
route exchange. In the three-set framing (Set 1 absent, Set 2 present but not peering, Set 3
actively exchanging), Wateen is a measured Set-2 example — listed at all three PKIX sites yet
routing to Cloudflare's Hong Kong PoP at 25 ms while Nayatel reaches it at 3 ms. Our
tromboning map is, in effect, a map of Set-1/2 behaviour at national scale. We do not yet
quantify forex saved (deliverable #1): RIPE Atlas cannot see byte volume, so we report
latency and resilience, and leave a traffic-weighted cost estimate to future work.

## 10. Conclusion and future work

Measured from inside Pakistan, the country's Internet exchange is underused in a way that is
visible on the wire and costly to users: ~40% of top content is offshore, 11% of small-ISP
space is reachable only by hairpinning abroad, the hairpin is a routing choice with a stable
3–9× latency penalty, and it forfeits resilience during a cable fault. The local path exists
but is not taken. **Next:** repeat the census over days to range-bound the 11% and separate
per-host from time-flipping routing (Exp 4.2); run a 20-day, all-probe longitudinal panel over
CDN/Abroad/PK sites and known tromboning IPs to produce per-ISP RTT distributions, diurnal
and weekly stability, and a normal-day baseline that captures the next cable fault with a true
before/during/after (Exp 07).
