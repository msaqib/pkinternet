# papers — 15.1 — data plane

PDFs held here are copies; the canonical set is the `literature/` working directory, outside this repository (see its `README.md` for the full
filename → paper index).

## Held in this folder

- **`DissectingLatency.pdf`** — Bozkurt et al. 2018 — how far real fibre latency sits above the great-circle floor. Why the RTT thresholds sit above the theoretical minimum, not at it.
- **`1505.03449v1.pdf`** — Singla et al., *Towards a Speed of Light Internet* — the latency floor argument in its cleanest form.
- **`2606.24027v2.pdf`** — Klein et al., *Overconfident Coordinates: Quantifying Confidence in Traceroute Geolocation* — directly the reason a hop's country code is never sufficient on its own and must be gated by RTT.

## Also relevant, in the `literature/` working directory (outside this repository)

- **`2043164.2018452.pdf`** — Sundaresan et al., SIGCOMM 2011 — active measurement from the network edge; vantage-placement practice.

## Cited but not held locally — fetch before writing

- **Gharaibeh et al., IMC 2017**, *A look at router geolocation in public and commercial databases* — cited in `SAMPLING_METHOD.md` §3.2 as the basis for distrusting geolocation alone.
- **Gueye et al. 2006**, *Constraint-based geolocation of Internet hosts* — RTT as a hard upper bound on distance, the principle the RTT gate implements.
