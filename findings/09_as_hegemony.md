# Finding 09 — The PTCL/Transworld duopoly, quantified from global BGP (AS Hegemony)

**Experiment:** `experiments/09_as_hegemony/` · **Data:** IIJ Internet Health Report (AS Hegemony,
Fontugne et al.), pull of 2026-07-17 · **Independent of our probes entirely.**

## Headline

> **Of the 291 Pakistani-registered ASes visible in global BGP, 89.7% depend on PTCL (AS17557) or
> Transworld (AS38193) for the majority of their AS paths** (hegemony ≥ 0.5); 92.1% show material
> dependency (≥ 0.1). Median hegemony across PK origins: **Transworld 0.50, PTCL 0.17**.

The duopoly our traceroutes observe from 16 vantage points is a measured property of the world's
routing tables — not an artifact of where our probes sit. Notably, *Transworld*, not PTCL, is the
majority dependency for more networks (consistent with Exp 4.1, where TWA ≈ PTCL in hand-offs
abroad).

## Cross-validation against our probes (control plane vs data plane)

| ISP (probe) | Hegemony (global BGP) | Our traceroute finding |
|---|---|---|
| **Orbit** | **TWA = 1.00** — every path via Transworld | worst domestic performer (latency ratio 11.9×) |
| Nayatel | PTCL 0.68, TWA 0.32, **Cogent 0.17** | most independent; uses the in-PK Cogent PoP |
| NTC | PTCL 0.69, TWA 0.31, Omantel 0.21 | state operator, dual-homed |
| Fasttel | PTCL 0.71, TWA 0.29 | fully dependent |
| PTCL / TWA | only small foreign upstreams | top of the hierarchy |

Two independent measurement systems — our probes' data plane and the world's BGP control plane —
give the same per-ISP ranking.

## Method in one line

AS Hegemony = the (viewpoint-trimmed) fraction of BGP AS-paths toward an origin that traverse a
given transit AS (1.0 = total dependency); computed continuously by IHR from RouteViews + RIPE
RIS; queried per origin over all 455 PK-registered ASNs (164 announce nothing and are excluded,
stated).

## Caveats

Paths, not traffic volume; IPv4 only; unannounced private links (e.g. Transworld's internal
backbone) are invisible to BGP, so the scores are a **lower bound** on dependency. API
reproducibility quirk: the IHR endpoint requires both `timebin__gte` and `timebin__lte` (< 7-day
range) and rejects a `format` param.

## Outputs

`experiments/09_as_hegemony/results/pk_hegemony_rollup.csv` (per-AS scores),
`probe_isp_deps.csv` (per-ISP dependency tables). Paper use: replaces the qualitative duopoly
claim in the introduction with one citable number.
