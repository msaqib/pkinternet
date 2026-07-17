# Finding 07 (PRELIMINARY) — Latency vs physics from the panel's partial window

**Experiment:** `experiments/07_longitudinal_panel/` (7-day panel, LIVE until 2026-07-18) ·
**Data here:** partial snapshot (ping half, first ~3–6 days, 16 probes × 100 sites) ·
**Status: preliminary — all numbers re-computed on the full week after the run closes.** Min-of-N
RTT is already stable, so these baselines should tighten, not overturn. Methods:
`experiments/07_longitudinal_panel/analysis/METHODOLOGY.md`; full EDA plan:
`findings/07_critical_review_and_eda_plan.md`.

## Headline (latency ratio = measured RTT ÷ speed-of-light theoretical minimum)

| Site type | median ratio | character |
|---|--:|---|
| Abroad (control group) | **2.5×** | tight; nothing beyond ~7× — normal routing |
| Pakistan | **2.9×** | typical matches Abroad, but ~⅓ tail out to 10–30× (domestic detours) |
| CDN (floor = best ISP's real path) | **8.4×** | bimodal: ~⅓ at ≈1× (peered), ~¼ beyond 40× |

> The closer the content, the worse the relative routing: foreign sites are reached uniformly
> near the physical optimum; domestic and CDN access carry the inefficiency tails.

## Physics-verified locations (the arbiter)

A ping faster than light-in-vacuum to a site's claimed location proves the location wrong.
Applied to the sample: **34/40 CDN geo-IPs invalidated** ("Toronto" sites answering in <3 ms) and
**6 unicast corrections** — 3 "Pakistan" sites actually offshore (incl. a provincial-government
site served from the US at ~233 ms) → reclassified Abroad; 3 relocated by latency
multilateration. Corrected split: 37 PK / 40 CDN / 23 Abroad. All results use corrected classes.

## CDN access = a per-ISP peering score

Anycast has no single location; each ISP reaches its own PoP. Score = share of CDN sites reached
locally (<15 ms), and the instructor ratio (measured ÷ best-achieved-in-PK):
**Nayatel 85% local / ratio 1.0× → Cybernet 41% / 2.0× → TES 20% → everyone else 0% local —
PTCL median 136 ms / 52×.** Same national content, ~40–50× slower by ISP choice; independent of
ISP size — it is local peering (the heatmap separates site-caused from ISP-caused distance).

## Slicing (instructor's questions)

- **By probe city:** Karachi/Lahore/Islamabad healthy and similar (2.4–2.8×); **Faisalabad 11.9×,
  N. Punjab 5.4×** — the domestic tail concentrates in second-tier-city vantages (one probe each;
  city and PoP confounded).
- **Karachi vs rest (the egress):** Karachi slightly better (Abroad 2.28× vs 2.52×) but only
  ~3 ms — the submarine leg dominates; being at the cable's doorstep buys little.
- **Excluding PTCL-Karachi:** PK median 2.94× → 2.69× (one anomalous vantage moves the national
  median ~9%; the tail survives).

## Key caveats (carried into the paper)

22/40 PK sites block ping (to be filled from the TCP/80 traceroute half); same-city pairs (<30 km)
reported in ms, not ratios (median ~6 ms — healthy); all probes fixed-line (no mobile networks);
ratio is raw (path-only variant after subtracting last-mile floors: PK median 1.9×, below
Abroad's 2.4× — the typical domestic *route* is efficient; the cost is access overhead + the tail).

## Pending (full-week run)

Raw archive (`dump_raw.py`), trace-half fill-in, tromboning intermittency, diurnal/weekly
decomposition, PKIX/PIE peering-LAN scan, robustness table — per the EDA plan.
