# Experiment 06 — Routing during a submarine-cable outage

**Author:** Rayan Atif

## The event

**SMW5 (SEA-ME-WE 5) submarine-cable fault**, reported by PTA on **2 Jul 2026**.
Transworld (TWA) is coordinating with the SMW5 consortium on root cause + ETTR; **traffic
is being rerouted through alternate international links** to keep service up. PTCL and
Transworld are the two LDIs carrying all of Pakistan's international traffic (SMW3/4/5,
AAE-1, IMEWE, PEACE, TW1). Because traffic is **rerouted, not blacked out**, we hunt for
the **degradation signature** (RTT spikes on the longer alternate paths), not an outage —
a **natural experiment** for our PKIX thesis.

## The question

When international capacity is scarce, do PK ISPs **fall back to local / PKIX routing**,
or does the tromboning persist (or worsen)?
- If hairpinned destinations start routing **locally** during the outage → proof the
  domestic path *exists* and is normally underused **by choice** (the strongest PKIX
  argument).
- If they stay abroad at **higher RTT** or go **unreachable** → the local path genuinely
  isn't there / isn't used even under duress.

## What we watch (during vs baseline)

1. **Foreign exit points** — which trombone exit *disappears* (tells us which cable is
   down); do exits shift onto other cables (PTCL via ChinaNet/PEACE, Transworld via
   Equinix-SG on SMW/AAE)?
2. **RTT to offshore anycast/banks** — spikes (traffic on longer surviving cables) /
   loss.
3. **Hairpin behaviour** — do previously-tromboned PK destinations route **local**,
   stay abroad at higher RTT, or go unreachable?
4. **Local paths (control)** — pure-domestic routes should not move; if they do it is
   congestion spillover.
5. **Probe liveness** — do PTCL/Transworld probes drop (timestamps the impact; see the
   probe-status dashboard).

## Method

RIPE Atlas **periodic** measurements (ICMP Paris traceroute + ping), **every 15 min for
12 h**, from **all 14 connected Pakistani probes** to a balanced website sample. PTCL and
Transworld are the affected LDIs; the other ISPs' probes act as comparison vantages (some
transit PTCL/Transworld upstream and should degrade too, others may be insulated).
Because these are **server-side periodic** measurements (created once with a 12 h
start/stop window), **RIPE runs them on its own infrastructure on schedule — the laptop
can be shut off and the run continues.** `schedule` just registers them and exits;
`fetch` pulls the accumulated rounds whenever we reconnect (same design as the Exp 03
`trace_monitor` / multi-probe scripts). Tiny footprint (36 measurements), no clash with
the running census. Baseline = the first rounds of this run (+ Exp 03 / 04 / 4.1).
Detector reused from Exp 04 (RTT-physics), so a "change" is a real reroute.

- **Source probes (all 14 connected PK probes):** PTCL `7764` (anchor), `1015210`,
  `1016126`; Transworld `62224`, `64078` (TES retail); Cybernet `1016036`, `1016143`,
  `1016154`; Nayatel `60223`, `65892`; Nova `1015679`; Fasttel `1014872`; Orbit `64535`;
  Z-Com `7613` (anchor).
- **Targets — balanced, liveness-checked sample (6 each) from the Exp 1.4 hosting
  census:** we probe websites we labelled **CDN / Abroad / PK** so the three hosting
  classes are directly comparable during the cut:
  - **CDN (6):** telenor.com.pk, shophive.com, aku.edu, express.com.pk, outfitters.com.pk,
    telemart.pk.
  - **Abroad (6):** wateen.com, daraz.pk, alfatah.com.pk, dailypakistan.com.pk,
    sapphireonline.pk, balochistan.gov.pk.
  - **Pakistan (6):** isra.edu.pk, punjab.gov.pk, nab.gov.pk, pbs.gov.pk, maju.edu.pk,
    yansrhr.org.

## What to look for (analysis)

A submarine cut with reroute produces a **specific pattern, not a blackout**:

1. **International RTT spikes, local RTT stays flat.** Abroad/CDN targets (traffic that
   leaves the country) should show **2–3× RTT** vs baseline as it takes the longer
   alternate cables; **PK-hosted** targets should be **stable**. Divergence between the
   two = the cut's fingerprint. (`spike_x` column = dest_RTT ÷ baseline; baseline = the
   first two rounds.)
2. **Per-link delay localisation.** Compute the **RTT difference between consecutive
   hops** in each traceroute; the hop with the largest jump is **the link introducing
   the delay** (`max_hop_delta` + `delta_link` columns, and a `d-prev` column in the
   routes txt). This pinpoints *which* local/international link degraded, per ISP — a
   PTCL egress link vs a Transworld egress link will show different delaying hops.
3. **2–3× thresholds vs baseline** flag the degraded links; a foreign hop appearing where
   there wasn't one (or an exit shifting to another cable/country) flags a **reroute**.
4. Complement with the **control plane**: RIPEstat routing-history / RIS to see if PK
   prefixes' AS-paths reroute or withdraw during the outage.

## Run

```bash
python experiments/06_submarine_outage/outage_monitor.py schedule   # start periodic measurements
python experiments/06_submarine_outage/outage_monitor.py fetch      # pull results -> CSV + routes txt
python experiments/06_submarine_outage/outage_monitor.py stop       # stop early
```
Output: `results/measurements.json` (ids), `results/outage_<ts>.csv` (per round:
probe, target, RTT, tromboned, exit), and `results/routes_outage_<ts>.txt`.

## Status

Scheduled 2026-07-03 (SMW5 outage ongoing): 18 targets × traceroute+ping, every 15 min
for 12 h, from the 4 PTCL/Transworld probes. Runs server-side (laptop-independent);
`fetch` any time. Pin the exact SMW5 down/up times from Cloudflare Radar / CAIDA IODA /
PTA notice to align the series.
