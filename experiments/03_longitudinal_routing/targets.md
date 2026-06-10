# Experiment 03 — the 5 longitudinal targets

Picked from the Exp 01 results so that the set spans the behaviours most likely to
**change over time**, plus one stable control. Edit the `TARGETS` list in
`trace_monitor.py` to match this table.

| # | Hostname | Label | Category | Exp 01 behaviour | Why watch it over time |
|---|----------|-------|----------|------------------|------------------------|
| 1 | `pseb.org.pk` | PSEB | government | Real PK server on **Multinet (AS9260)**, genuinely local (~40 ms) | **Stable control.** A real in-country unicast server should show a flat path/RTT. If *this* moves, something systemic changed. |
| 2 | `sehat.com.pk` | Sehat | health | **Cloudflare anycast**; observed serving from **Karachi** on some ISPs but **Hong Kong (~195 ms)** on Z-Com | Prime PoP-flip candidate — watch whether the handoff metro swings between PK and HK/SG across the day. |
| 3 | `bykea.com` | Bykea | food | **Cloudflare anycast**; seen at **Islamabad ~6 ms** (Nayatel) vs **Hong Kong ~194 ms** (Z-Com) | Second anycast watcher; from the Nayatel probe it should be local — does it ever get pushed abroad at peak? |
| 4 | `moitt.gov.pk` | MoITT | government | PK ASN (Cybernet) but **hairpins through Akamai Prolexic (AS32787) in the US**, 120–210 ms, often no reply | High-latency hairpin + scrubbing — watch RTT swing and reachability (loss) over time. |
| 5 | `dailypakistan.com.pk` | Daily Pakistan | news | **Foreign real server — Hetzner, Helsinki (FI)** | Stable *foreign* unicast baseline: path should be steady but long; contrasts with target 1 (stable + local) and isolates pure diurnal RTT change on a fixed foreign path. |

**Probe:** 60223 — Nayatel (AS23674), Islamabad. Chosen for full hop visibility
(see `notes.md` → Chosen methodology).

These 5 are **not** in Exp 1.1's GeoDNS list, so resolving once at schedule time is
valid. If you swap any target, re-check it against
`experiments/01.1_dns_resolution/` first.
