# Foreign-classified hops: incremental RTT and IXP peering-LAN membership

Both questions answered. Attached: `foreign_hops.csv` (full per-IP table),
`foreign_hops.txt` (readable summary), `foreign_hop_audit.py` (the script, re-runnable).

Scope: Exp 07 panel, traces to Pakistani-hosted sites only, 14 probes, the same filter
that produces the 5.52% headline.

---

## Q1. The foreign-classified IPs and their incremental RTT

**76 distinct IP addresses** were ever classified foreign, across **10,583** qualifying
hop observations. Of those, **4,170 were the first foreign hop in their trace**, which is
the set that actually produces a tromboning verdict.

Incremental RTT, defined as this hop's RTT minus the RTT of the nearest preceding
responding non-private hop in the same trace:

| | |
|---|--:|
| samples | 10,571 |
| median | **+75.7 ms** |
| p10 | -1.6 ms |
| p90 | +182.6 ms |
| negative | **23.0%** |

Per-IP columns in the CSV: `ip, asn, registered_cc, org, geoip_city, times_qualified,
times_first_foreign_hop, n_probes, rtt_median_ms, rtt_min_ms, rtt_max_ms,
incr_rtt_median_ms, incr_rtt_p10_ms, incr_rtt_p90_ms, incr_negative_pct, incr_samples,
no_preceding_hop, ixp_peering_lan, ixp_prefix`.

### The 76 IPs split into two clearly different populations

| IP | org | incr median | negative |
|---|---|--:|--:|
| `27.111.228.157` | Equinix Singapore | **+78.2 ms** | 0.3% |
| `72.52.25.142` | Akamai Prolexic | **+175.5 ms** | 0.2% |
| `116.51.17.201` | NTT | **+106.2 ms** | 1.5% |
| `206.148.27.235` | Global Secure Layer | +85.4 ms | 1.0% |
| ... | | | |
| `2.21.120.112` | Akamai Prolexic | **-4.0 ms** | 95.8% |
| `134.0.219.250` | Omantel | -2.0 ms | 92.5% |
| `223.121.3.98` | China Mobile HK | -95.6 ms | 73.3% |
| `160.202.164.163` | GSL Networks | -58.4 ms | 99.0% |

The first group adds large, consistent delay. The second answers *faster* than the hop
before it in most observations, which is impossible as a distance and means the increment
there is measuring ICMP-generation behaviour, not propagation.

**The 23.0% negative rate is the noise floor of incremental RTT as a measure.** We report
it rather than smoothing it, because it bounds what the quantity can be used for: it
cannot separate queueing from distance for the second group.

---

## Q2. Which of them are on a foreign IXP peering LAN

Checked against 14 published peering-LAN prefixes: Equinix Singapore, Ashburn, Chicago
and Palo Alto, SGIX, HKIX, BBIX, DE-CIX Frankfurt, AMS-IX, LINX, Megaport Singapore,
UAE-IX Dubai, NAPAfrica, and the Euro-IX `185.1.0.0/16` allocation.

**Three IPs match, all on Equinix Singapore `27.111.228.0/22`:**

| IP | Observations | First-foreign-hop (exits) |
|---|--:|--:|
| `27.111.228.157` | 2,390 | 2,388 |
| `27.111.230.181` | 985 | 984 |
| `27.111.230.138` | 168 | 168 |
| **total** | **3,543** | **3,540** |

Three IPs out of 76. But **3,540 of the 4,170 verdicts, 84.9%**.

So the overwhelming majority of tromboning we report is Pakistani-hosted content being
reached across the Equinix Singapore exchange fabric. No other exchange matched.

---

## Why this bears on the threshold objection

The concern was that a 40 ms hop could be domestic queueing, and that we assumed a
speed-of-light-in-fibre figure without estimating the slowdown factor for Pakistani fibre.
Both points are fair, and the second is not something our data can settle.

**The IXP result does not depend on either.** An address inside `27.111.228.0/22` is a
port on the Equinix Singapore peering fabric because of who allocated and announces that
prefix, not because of any latency we measured. It stays in Singapore whatever $v_f$ turns
out to be, and no amount of domestic queueing puts a Pakistani router on a Singapore
exchange LAN.

That gives an independent confirmation of ~85% of the tromboning claim that uses no RTT
threshold and no speed-of-light assumption at all. The remaining ~15%, spread over 73
other IPs, still rests on the latency argument.

Two further points from the same data:

* These three IPs have among the **lowest** negative-increment rates in the whole set
  (0.3%, 0.2%, 0.0%) and a tight positive median around +78 to +95 ms. Whatever the noise
  in incremental RTT generally, it is not what is driving these verdicts.
* Their absolute RTT medians are 97 to 99 ms. Karachi to Singapore is 4,736 km, a
  round-trip floor of about 46 ms at $c/1.468$. Even a fibre slowdown factor considerably
  worse than assumed leaves these consistent with Singapore and inconsistent with any
  domestic path.

---

## Reproducing

```
python experiments/07_longitudinal_panel/analysis/foreign_hop_audit.py
```

Reads `raw_a_20260718_201113.json.gz` plus the hop annotation, Cymru and RDAP caches
already in `analysis/`. Writes both output files. Takes about a minute.
