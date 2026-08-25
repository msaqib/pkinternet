# Panel probe data-quality notes (supplementary to §Data Cleaning)

Full per-probe accounting for the 17 probes scheduled in the Exp 07 panel. The
main text (§Data Cleaning) covers the three issues that affect the headline
probe counts and row totals; this note adds the three it doesn't have space
for, plus the reasoning behind all six, for anyone auditing the pipeline.
Compiled from `experiments/07_longitudinal_panel/analysis/exp07_analysis.ipynb`
(`EXCLUDE_PROBES`, the `PROBE_LABELS` roster, and the "Probe Quality" note)
cross-checked against the raw per-round timestamps in
`experiments/07_longitudinal_panel/results/{a,b}/panel_*.csv`.

## Full accounting

| Probe | Issue | Analyses affected | In main text (§Data Cleaning)? |
|---|---|---|---|
| `1016431` (NTC, Karachi) | Never returned any data during the run | Absent from both datasets entirely | Implicit only, via the "16 of 17" count |
| `AS13335.1015491` (mislabelled; real ASN is Z-Com, AS152605) | Co-located with another probe already in the panel — same physical site, so contributes no independent vantage | Excluded entirely, both datasets | No |
| `ptcl.7764` (PTCL anchor, LUMS/Lahore) | 90% packet loss throughout the run | Excluded entirely, both datasets | Yes ("a third probe... 90% packet loss... excluded from analysis entirely") |
| `transworld.62224` (Lahore) | Fully ICMP-filtered; no intermediate hop ever responds in any traceroute round | Ping RTT retained; excluded from all hop-count and path-based analyses | Yes ("one probe received no valid traceroute responses") |
| `ptcl.1016393` (Mianwali) | Full rate for the first ~29 hours, then bursty/intermittent for the remaining six days at roughly 5–10% of normal rate | Retained everywhere, with a thinner-window caveat | Yes ("ran correctly for approximately 29 hours... degraded to a bursty, intermittent connection") |
| `nayatel.60223` + `nayatel.65892` (both Islamabad) | Traceroute hits the 255 timeout sentinel across most rounds — destinations frequently did not reply | Ping RTT retained; hop-count results from these two should be read with caution | No |
| `cybernet.1016036` (Haripur) | Placeholder coordinate (30.0, 70.0) on file with the platform, not its true location | Excluded from all distance-based and ratio analyses; retained for tromboning classification, since that verdict is decided by a confirmed foreign hop, not by probe coordinates | No |

## Reconciling the headline numbers

17 scheduled → 1 returns no data (`1016431`) → 16 return data → 2 excluded
outright (`1015491` duplicate, `7764` packet loss) → **14 probes for
traceroute-based analysis** (200,292 rows). Ping-based analysis additionally
retains `transworld.62224`'s RTT (its traceroute is unusable but its ping
isn't), giving **15 probes for ping-based analysis** (305,116 rows).

## `ptcl.1016393` timing, verified against raw timestamps

Checked directly against `results/a/panel_20260718_195946.csv` rather than
trusting the notebook's own note, which claims a hard disconnect on July 17 —
that claim doesn't hold up:

- Full rate (~99–103 traceroute rows/hour) from panel start (2026-07-11
  11:57) through **2026-07-12 ~17:00–18:00** — almost exactly the 29-hour
  mark the main text cites.
- A complete ~12-hour gap (2026-07-12 18:00 → 2026-07-13 06:00).
- Low, bursty rate for the rest of the week (daily totals 136, 221, 245, 243,
  74, 35 traceroute rows vs. ~2,352/day at full rate — roughly 10–11% of
  normal), continuing all the way to **2026-07-18 10:01:46**, the same
  end-of-panel timestamp as every other probe.

So the main text's "29 hours, then bursty at 5–10% for six days" is the
accurate description; the notebook's "disconnected July 17" note is wrong and
should not be trusted if this file is revisited.

## Not included above

Two Cybernet probes (`1016143`, `1016154`, both Karachi) and two Nayatel
probes (`60223`, `65892`, both Islamabad) are duplicate operator/city pairs
that were *kept*, unlike `1015491`. The distinction: those pairs sit at
genuinely different physical locations within the same city and support the
paper's within-operator, cross-location comparisons; `1015491` was excluded
specifically because it was co-located at the *same* site as an existing
probe, not merely the same operator and city.
