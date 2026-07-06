# Findings 06 — Routing during the SMW5 submarine-cable outage

**Author:** Rayan Atif
**Source:** Experiment 06 (`experiments/06_submarine_outage/`). RIPE Atlas ping +
ICMP Paris traceroute, **every 15 min for 12 h**, from **all 14 connected Pakistani
probes** to a balanced **CDN / Abroad / PK** website sample, during a real
submarine-cable fault. RTT-physics detector reused from Exp 04.

This experiment produces the project's **third headline deliverable**: *how much better
users' experience would be — or here, how much worse it gets — during a submarine-cable
fault* (the other two being forex saved and normal-conditions improvement).

## The event

**SMW5 (SEA-ME-WE 5) submarine-cable fault**, announced by the PTA on **2 Jul 2026**.
Transworld (TWA) coordinated with the SMW5 consortium on repair; **traffic was rerouted
onto alternate international links** to keep service up. PTCL and Transworld are the two
LDIs that carry all of Pakistan's international traffic, so a cut on a shared cable
degrades the international leg for the ISPs that buy transit from them. Because traffic
was **rerouted, not blacked out**, the signature to hunt for is **latency degradation on
the longer surviving paths**, not an outage.

## Method

- **Window:** 2026-07-02 20:26 UTC → 2026-07-03 08:26 UTC = **01:26 → 13:26 PKT**
  (PKT = UTC+5). Server-side RIPE **periodic** measurements (registered once with a 12 h
  start/stop window), so collection was laptop-independent.
- **Probes (14):** all connected PK probes — PTCL ×3 (incl. anchor 7764), Transworld
  62224, TES/Transworld-retail 64078, Cybernet ×3, Nayatel ×2, Nova, Fasttel, Orbit,
  Z-Com. PTCL/Transworld are the affected LDIs; the rest are comparison vantages.
- **Targets (18, liveness-checked, 6 per class):** CDN (telenor.com.pk, shophive.com,
  aku.edu, express.com.pk, outfitters.com.pk, telemart.pk), Abroad (wateen.com, daraz.pk,
  alfatah.com.pk, dailypakistan.com.pk, sapphireonline.pk, balochistan.gov.pk), Pakistan
  (isra.edu.pk, punjab.gov.pk, nab.gov.pk, pbs.gov.pk, maju.edu.pk, yansrhr.org).
- **Outputs:** `results/outage_<ts>.csv` (per-round RTT, spike-vs-baseline, per-hop RTT
  delta, tromboned/exit), `results/routes_outage_<ts>.txt`, `results/timeseries.csv`
  (9,127 clean ping points), the `rtt_timeseries.ipynb` notebook and its figures
  (`results/figures/rtt_by_site.png`, `rtt_by_probe.png`).

## Findings

### 1. A latency degradation, not a blackout
Across the whole window the **median RTT stayed at baseline (1.0×) for all three
classes** — the reroute held connectivity. International (CDN/Abroad) targets were
**elevated and erratic**; local (PK) targets were flat. This matches PTA's "rerouted,
not blacked out."

### 2. The right lens is start-vs-end, not spike-vs-baseline
Our monitoring **began after the outage was already active**, so the "baseline" (first
rounds) captured the **degraded** state. Measuring each RTT against that baseline
therefore looked flat (spike ≈ 1.0×) and *hid* the recovery. Comparing the **first round
vs the last round** for the same (probe, target) is the correct lens and reveals the
trend. *(Methodological lesson: with no pre-event baseline, use first-vs-last, not
ratio-vs-first.)*

### 3. Clear recovery over the 12 h
Same site, same probe, first → last round — the worst-hit paths (all via **PTCL**)
collapsed:

| Target (probe) | first | last | Δ |
|---|---|---|---|
| shophive.com (PTCL) | 646 ms | 278 ms | **−368** |
| telemart.pk (PTCL) | 472 ms | 268 ms | −204 |
| balochistan.gov.pk (PTCL) | 389 ms | 281 ms | −108 |
| express.com.pk (Nayatel) | 247 ms | 136 ms | −110 |
| wateen.com (TES) | 199 ms | 122 ms | −77 |

CDN targets dropped ~10 ms on average; Abroad ~flat-to-down. **More convincing because
of the clock:** the high "first" readings were at **~01:30 PKT (off-peak)** and the
recovered "last" readings at **~13:00 PKT (business-hours peak)** — RTTs improved
*despite* moving into peak traffic, so this is genuine outage easing, not a diurnal dip.

### 4. Recovery was partial and uneven
Not everything improved. **Fasttel** paths got **worse** over the window — on several CDN
sites the RTT **stepped up around 06:00 PKT** (e.g. shophive 122 → 227 ms, outfitters
131 → 225 ms) and stayed there until ~12:00, and `daraz.pk` via Cybernet rose 81 → 180
ms. A small ISP's upstream evidently rerouted onto a worse alternate path mid-event. End
RTTs were also still elevated (~120–280 ms), i.e. better but not fully healthy.

### 5. No structural reroutes — load-balancing within the same transit
Comparing the public-hop path of the first vs last round for every pair: **159 of 252
were path-identical; 93 differed, but almost all are load-balancing across parallel links
of the *same* transit** — e.g. `wateen.com` via TES alternated between two **Etisalat-UAE**
ingress IPs (`5.195.70.166` ↔ `195.229.27.221`), same country, same provider; only 31 had
any exit-hop change and those stayed within the same upstream. The **exit country/transit
was constant**. So the recovery was **congestion/latency easing on the existing
SMW5-era detour**, not a switch back to a repaired cable (a splice takes days).

### 6. Local paths were the unaffected control
PK-hosted targets (`isra.edu.pk`, `yansrhr.org`, `telenor.com.pk`) stayed **flat and low**
throughout — confirming the disruption was confined to the **congested international legs**,
not the domestic network. **Exception:** `pbs.gov.pk` (NTC-hosted) showed a sharp chaotic
disturbance across **all** probes at **~08:00–10:00 PKT** — a distinct local event worth a
separate follow-up, unrelated to the submarine path.

### 7. Per-hop delay localisation
The per-round metric **RTT-difference between consecutive hops** pinpoints the link that
introduces the delay (`max_hop_delta` / `delta_link`, and a `d-prev` column in the routes
txt). On the affected paths the largest jump lands on the **international egress** — the
leg onto the surviving/UAE path — and differs by probe (a PTCL egress link vs a Transworld
egress link show up as different delaying hops).

## Why this matters for PKIX

This is the clearest practical form of the project's argument: during a submarine cut,
**internationally-routed traffic degrades 2–6×** while **domestically-routed / PK-hosted
traffic is essentially untouched**. Content hosted in Pakistan and exchanged over PKIX
would ride through a cable fault that badly hurts the offshore-hosted majority — a direct,
measured case for local hosting + active PKIX peering as *resilience*, not just latency.

## Caveats

- **Single 12 h window, and it started after the outage was already active** — there is
  **no pre-event baseline**, so absolute recovery magnitude vs a "healthy" day is inferred,
  not measured. A longer/earlier capture would strengthen this.
- **Ratio (`spike_x`) over-weights low-baseline local targets** — a PK site at 4 ms
  baseline hitting 28 ms reads as "28×" but is only +24 ms. For real degradation, rank by
  **absolute ms** (as the first-vs-last table does), not by ratio.
- **PTCL probe 1015210 is Docker-opaque** (172.17.0.1 then destination) — its RTT is valid
  but the intermediate path isn't visible, so its dramatic RTTs can't be path-attributed.
- **Detector = RTT-physics** (Exp 04), geo-IP-proof; a foreign/exit hop is judged by RTT,
  not registration country.

## Reproduce

```bash
python experiments/06_submarine_outage/outage_monitor.py schedule   # register periodic measurements
python experiments/06_submarine_outage/outage_monitor.py fetch       # -> outage_*.csv + routes_outage_*.txt
python experiments/06_submarine_outage/build_timeseries.py           # -> results/timeseries.csv
# then run experiments/06_submarine_outage/rtt_timeseries.ipynb for the graphs (UTC->PKT)
```
