# PK Internet Project — Summary of Experiments

**Author:** Rayan Atif

**Overarching goal:** assess how effectively **Pakistan's Internet Exchange (PKIX)**
is used — i.e. how much "Pakistani" web traffic actually stays in-country vs exiting
to foreign infrastructure, and how that shapes the latency a real PK user sees.

Two methods recur throughout: **RIPE Atlas ICMP Paris traceroutes** from PK probes,
and an IP→operator→location stack (**Team Cymru ASN + RDAP fallback + ip-api geo**).

---

## At a glance

| Exp | Question | Status | Headline |
|-----|----------|--------|----------|
| **01** | Where are PK websites hosted, and how is traffic routed there? | ✅ done | ~75% of top PK sites are **not** on a PK server; traffic exits to foreign IXPs → PKIX underused. |
| **1.1** | Does per-ISP DNS (GeoDNS) change the hosting picture? | ✅ done | Only **8/103** sites are GeoDNS → Exp 01's central lookup is valid for ~92%. |
| **1.2** | Is the big global content (Google/Meta/…) cached inside PK? | ✅ done | Mostly **no** — reached at regional latency; only Cloudflare & X served locally, only via Nayatel. |
| **1.3** | What does Nayatel actually transit? | ✅ done | **~40%** of paths use an LDI (the foreign tail); **~59%** bypass via direct peering — Nayatel is multi-homed. |
| **02** | Classify ISPs by PKIX participation; plan probe coverage. | 🟡 plan / deploying | Set 1/2/3 from PTA deck + Exp 01; **~21 new probes + 5 existing + volunteers**. |
| **03** | Does the route/RTT to a site **change over time**? | 🟡 24 h done, 48 h running | Local 2–40 ms vs **offshore 130–200 ms**; **no diurnal cycle, stable routes** → the inefficiency is *structural*. |

---

## Experiment 01 — Where are Pakistani websites hosted?
*(91 sites, 5 probes/ISPs, all 10 batches — `findings/01_hosting_and_routing_analysis.md`)*

- **Hosting census:** 23 sites (25%) on a real **PK** server, 26 (29%) on a real
  server **abroad**, 42 (46%) on **anycast CDN** (almost all Cloudflare). → ~75% not
  PK-hosted.
- **By sector:** **government** mostly stays in-country (13/18); **news, banking,
  e-commerce** have largely left — many PK companies host abroad *by choice* (banks
  to US/Singapore/Dubai; news on Hetzner Finland).
- **Transit hierarchy (most robust finding):** downstream ISPs route ~100% through
  the two LDIs (**PTCL / Transworld**); **Nayatel** is the most independent.
- **Domestic routing is ISP-dependent:** Nayatel reaches local content in single-digit
  ms; others much higher. Same Cloudflare site = 3–4 ms (Nayatel) vs hundreds of ms.
- **Hairpinning is concentrated** (only 5 of 23 PK-hosted sites leave the country),
  and traffic was seen exiting via **Equinix Singapore / DE-CIX Frankfurt / EMIX UAE**
  — direct evidence **PKIX is underused**.

### 1.1 Per-ISP DNS resolution
Resolving each site from every ISP's own resolver: only **8/103** return different IPs
per ISP (GeoDNS) → the central lookup was representative for ~92%; the census stands.

### 1.2 CDN presence in Pakistan
Most big content (Google, Meta, Apple, Microsoft) reached at **regional latency
(~20–50 ms), not inside PK**; only **Cloudflare & X** served locally, and only via
**Nayatel**. Undercounts (cache-hosting ISPs not yet probed) → **motivates Exp 02**.

### 1.3 Nayatel routing
**~40%** of Nayatel paths use an LDI (almost all Transworld) — essentially the
**foreign-hosted tail**; **~59%** bypass the LDIs via direct peering with Cloudflare /
Microsoft / AWS and alternative transit (SingTel, NTT). Nayatel is effectively
**multi-homed**, which is why everyday sites are ~3 ms.

---

## Experiment 02 — ISP classification (PKIX Set 1/2/3) + probe deployment
*(`experiments/02_isp_classification/` — plan, deployment in progress)*

- Builds on the **PTA "Pakistan Peering Roadshow" deck** + Exp 01's data-plane
  evidence to sort ISPs into: **Set 3** present *and* exchanging at PKIX (8),
  **Set 2** present but not shown to exchange (~26), **Set 1** absent (~59 FLL
  licensees, incl. TPCPL/Nova, Optix, Fiberlink…).
- **Probe plan:** ~21 new probes + 5 existing + Karachi volunteers, to cover the sets
  and fix the coverage gap Exp 1.2 exposed. Separates **hosts** (PK-hosted servers used
  as destinations) from **probes** (vantage points).
- **Status:** planning/deploying — the probe rollout feeds Exp 03's vantage coverage.

---

## Experiment 03 — Longitudinal routing (the time axis)
*(`experiments/03_longitudinal_routing/`, findings in `findings/03_*`)*

Where Exp 01 is a one-off snapshot, Exp 03 re-traces the **same sites every 15 min**
from multiple PK ISPs over days, recording whether **path / RTT change over time** —
per (site, probe). Uses **Paris** traceroute (so a "change" is a real reroute, not
load-balancer noise) + a 1/min (or 1/5min) ping companion. Each probe's egress ASN is
**measured live** each round (for multi-homed/campus probes).

| Run | Setup | Findings |
|-----|-------|----------|
| `run_20260610_2h` | 1 probe (Nayatel) × 5 sites, 2 h | Baseline + pipeline validation. |
| **`run_20260611_24h`** | 5 probes × 5 sites, 24 h | **The main result so far** — see below. |
| `run_20260612_48h` | 8 probes × 10 sites, 48 h | Running — two diurnal cycles, +PTCL vantage, CDN-PoP-flip candidates. |

**24 h findings** (`findings/03_longitudinal_routing_24h.md`):
- **Offshore penalty quantified:** local PK sites **2–40 ms** vs banks **127 ms
  (MCB→Singapore) / 200 ms (HBL→New Jersey)** — a 3–9× latency cost, on *every* ISP.
- **Huge per-ISP gap on local sites:** the *same* site is **1.6 ms on Z-Com vs 42 ms
  on Cybernet** — ISP routing quality matters as much as hosting.
- **No diurnal cycle:** latency was flat all day → the penalty is **structural
  (hosting/peering), not peak-hour congestion**.
- **Routes were stable** (~0 genuine path changes) — confirming the Paris method and
  that the inefficiency is structural.
- **Bonus — the method caught a real outage:** a ~**5.7 h thunderstorm outage** of one
  ISP (TPCPL/Nova) showed up cleanly as a gap across all targets.

---

## The through-line

Exp 01 establishes **where** PK content lives (mostly offshore, PKIX underused). 1.1/1.2/1.3
shore up and explain that picture (DNS valid, content not cached locally, *why* Nayatel
is fast). Exp 02 plans the **probe coverage** to classify ISPs by PKIX use. Exp 03 adds
the **time axis** and shows the offshore penalty is **stable and structural** — so the
fix is **local hosting / better peering through PKIX**, not more bandwidth. That is the
case this project is building, with data, for using PKIX.
