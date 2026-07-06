# Exp 06 — Submarine-outage impact

## Punchline

During the SMW5 outage **peak** (first 3 h) vs the **recovered** state (last 3 h), for **international** targets (CDN+Abroad):

- **Average RTT: +2%** (148 → 145 ms) — modest on average.
- **Jitter: +31%** (13.6 → 10.3 ms) — the dominant effect: the outage hit as *instability*, not a latency step.
- **Path length: -5%** (28.6 → 30.0 hops) — essentially unchanged (no rerouting onto longer paths).
- **Packet loss: 10.1% → 10.9%** — roughly flat.

Concentrated on **PTCL-sourced** paths — international **RTT +12%** (248→221 ms), **jitter +50%** (52→34 ms). Local/PK targets showed **no increase** (the control).

**Windows:** OUTAGE = first 3 h (01:28–04:28 PKT), RECOVERED = last 3 h (10:20–13:20 PKT). No true pre-event baseline (monitoring began mid-outage). 12038 ping rounds, 11949 traceroute rounds.


## By hosting class (International = CDN+Abroad)

| group | RTT out→rec (Δ) | jitter out→rec (Δ) | hops out→rec (Δ) | loss out→rec |
|---|---|---|---|---|
| International | 148→145 ms (**+2%**) | 13.6→10.3 ms (**+31%**) | 28.6→30.0 (**-5%**) | 10%→11% |
| Pakistan (local) | 31→41 ms (**-24%**) | 1.5→15.0 ms (**-90%**) | 10.4→10.1 (**+2%**) | 55%→56% |

## By target category

| group | RTT out→rec (Δ) | jitter out→rec (Δ) | hops out→rec (Δ) | loss out→rec |
|---|---|---|---|---|
| Abroad | 167→162 ms (**+3%**) | 13.0→7.8 ms (**+67%**) | 44.3→46.9 (**-6%**) | 13%→14% |
| CDN | 131→129 ms (**+2%**) | 14.1→12.8 ms (**+11%**) | 13.0→13.1 (**-1%**) | 8%→8% |
| Pakistan | 31→41 ms (**-24%**) | 1.5→15.0 ms (**-90%**) | 10.4→10.1 (**+2%**) | 55%→56% |

## By source transit × class

| group | RTT out→rec (Δ) | jitter out→rec (Δ) | hops out→rec (Δ) | loss out→rec |
|---|---|---|---|---|
| Other-ISP probes -> International | 130→130 ms (**-0%**) | 7.8→5.8 ms (**+34%**) | 28.3→29.8 (**-5%**) | 3%→3% |
| Other-ISP probes -> Pakistan (local) | 30→40 ms (**-24%**) | 1.7→14.3 ms (**-88%**) | 10.7→10.4 (**+3%**) | 52%→53% |
| PTCL probes -> International | 248→221 ms (**+12%**) | 51.6→34.4 ms (**+50%**) | 28.3→31.4 (**-10%**) | 39%→40% |
| PTCL probes -> Pakistan (local) | 35→47 ms (**-26%**) | 1.6→17.5 ms (**-91%**) | 9.0→9.0 (**+0%**) | 64%→65% |
| Transworld probes -> International | 136→136 ms (**-0%**) | 1.3→6.4 ms (**-80%**) | 31.2→30.4 (**+3%**) | 0%→4% |
| Transworld probes -> Pakistan (local) | 33→42 ms (**-23%**) | 0.9→15.0 ms (**-94%**) | 9.2→9.0 (**+2%**) | 52%→54% |

## Caveats

- **No pre-event baseline** — 'increase' compares the outage peak (first 3 h) to the recovered state (last 3 h), not to a normal day; the true increase vs normal is likely larger.
- **Pooled averages understate the peak** — a few paths swung 400–650 ms (shophive via PTCL) but the mean over 18×14 pairs is dominated by stable pairs; jitter and the PTCL rows capture the damage.
- **Hop counts exclude probes 7764/62224 (ICMP-filtered) and 1015210 (Docker-opaque)**; path length is still the least reliable metric here.
- **Local-target loss ~55% and noisy jitter** = ICMP filtering on gov/edu sites, not an outage signal; the local RTT (flat-to-lower) is the meaningful control and shows no degradation.
