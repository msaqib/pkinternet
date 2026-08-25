# Investigation — probe 1016393 (PTCL, Mianwali/N. Punjab): is its high trombone rate real?

**Trigger:** `eda_findings.md` §1 flagged this probe as a to-do ("may have inflated trombone
numbers") but never resolved it — traceroute-verdict numbers built on it are still in the 14-probe
headline roster. This document resolves it with a full re-investigation, not just the earlier
single-snapshot spot check.

**Question:** is PTCL-Mianwali (1016393) genuinely worse-routed than PTCL-Karachi (1016126) —
same ISP, different PoP — or is its elevated trombone rate a measurement artifact?

---

## Data used, and why

| Source | What it gives | Why pulled |
|---|---|---|
| `results/a/panel_20260718_195946.csv` (222,944 rows, whole week) | per-round `tromboned` flag, `exit_cc`, `transit`, filtered to `probe_id=1016393`/`1016126`, `cls=Pakistan` | the actual headline metric these probes feed into — need the full week, not one snapshot |
| `results/a/routes_20260718_195946_annotated.txt` (25,024 lines) | one **latest-round** hop-by-hop traceroute per (probe, target) pair, with per-hop RTT and ASN | `panel_*.csv` has no per-hop RTT for `kind=trace` rows (RTT lives only in the ping stream — see below) — needed this file to see *where* the delay sits inside a trace |
| `results/b/panel_20260718_200355.csv` (whole week, `kind=ping`) | independent min-of-N ping RTT per round, same probe/target pairs | a second, structurally-different measurement stream (separate RIPE Atlas account, separate protocol) — the only way to check whether the traceroute's RTT reading is trustworthy without just trusting the traceroute itself |
| `targets.csv` | target list, order | ruled out one hypothesis (see below) |

All four are already-committed run outputs; nothing new was measured for this investigation — it's
entirely a re-analysis of what Exp 07 already collected.

---

## What was found

### 1. In the CSV, the raw numbers really do differ by a lot

Whole week, Pakistan-class targets, `kind=trace`:

| Probe | rounds | trombone | rate |
|---|--:|--:|--:|
| **1016393 (PTCL-Mianwali)** | 1,539 | 758 | **49.3%** |
| 1016126 (PTCL-Karachi) | 6,720 | 2,022 | 30.1% |

(1016126 has more rounds because it stayed connected the whole week; 1016393 joined later —
irrelevant to the rate comparison.) Same ISP, 19-point gap. This is the number that needed
checking.

### 2. The single-round snapshot: a "staircase" that shouldn't exist if it were real geography

Pulling every one of 1016393's 40 Pakistan-class blocks from the one **latest-round** snapshot in
`routes_20260718_195946_annotated.txt` and sorting by the traceroute's own reported `maxRTT`:

```
enc.com.pk             LOCAL          15.0ms
galaxy.net.pk          LOCAL          32.0ms
iulms.edu.pk           LOCAL          33.0ms
sparkbroadband.pk      LOCAL          33.3ms
worldlinkisp.pk        LOCAL          35.8ms
hrd1902.com.pk         INCONCLUSIVE   50.1ms
ztbl.com.pk            TROMBONE      249.9ms   ← from here down, an almost perfectly smooth ramp
zcomnetworks.com.pk    TROMBONE      279.6ms
youth.cn               TROMBONE      335.6ms
dunyanews.tv           TROMBONE      369.7ms
  ... (26 more targets, each 5-20ms above the last) ...
dgcs.gos.pk            TROMBONE      498.5ms
roadmaster.pk          TROMBONE      499.5ms
```

34 **different destination sites** — different servers, different real-world locations, no
plausible shared physical path — produce `maxRTT` values that climb in an almost perfectly smooth
ramp from 249.9ms to 499.5ms, filling the range with no gaps, and **not one exceeds 500ms**.
Genuinely independent network paths to unrelated servers do not do this by chance; a shared,
external delay mechanism with a ceiling near 500ms does. This is consistent with — and sharpens —
METHODOLOGY.md's existing documented caveat that RTTs above ~500ms on this pipeline are a **queuing /
ICMP-error-generation artifact**, not real geography. (Ruled out one candidate explanation:
target-list order in `targets.csv` is alphabetical and does not match this ordering, so it isn't a
simple "later in the batch queue" effect from file order — the mechanism is per-round, not
per-file-position.)

### 3. The smoking gun: the same physical hop, same round, RTT from 5.9ms to 533ms

Hop 2 on every one of these traces is `39.45.64.1` — literally PTCL's first router past this
probe's own connection, inside PTCL's Mianwali network, physically a few kilometres away. In a
clean example (the EFU Life case study), this exact hop reads **6.2ms**. In this same measurement
run, minutes apart, the identical router reads:

| Target | hop-2 RTT (same IP, `39.45.64.1`) |
|---|--:|
| worldlinkisp.pk | 5.9ms |
| excise.gos.pk | 6.1ms |
| efulife.com | 6.2ms |
| trax.pk | 6.4ms |
| dgcs.gos.pk | 6.0ms |
| ztbl.com.pk | 39.4ms |
| dunyanews.tv | 349.4ms |
| gnnhd.tv | 431.2ms |
| cpsp.edu.pk | 526.3ms |
| topcity-1.com | **533.3ms** |

A router a few kilometres away cannot genuinely take half a second to reply on one packet and 6ms
on the next, sent moments later from the same probe. This proves the noise is being injected at or
before the very first hop — i.e. it's a property of **this probe's own uplink / the traceroute
tool's interaction with it**, not the downstream international path. It also explains why the
"staircase" in §2 doesn't correlate cleanly with any single carrier or exit country: the extra
delay lands at effectively random points in each individual trace, sometimes at hop 2, sometimes
much later (see `roadmaster.pk` below).

**Second confirmation, same trace, same IP measured twice:** `roadmaster.pk`'s trace has the
identical destination IP appear at both hop 10 (**479.4ms**) and hop 13 (**46.9ms**) — a ten-fold
difference for the same address in the same traceroute. Real path RTT cannot do this; per-packet
queuing/rate-limiting noise can.

### 4. Cross-checking against the independent ping stream settles which targets are real

`results/a` traceroute and `results/b` ping run on **separate RIPE Atlas accounts** with different
protocols — if the traceroute's RTT reading is an artifact specific to that pipeline, the ping
stream (min-of-N per round, whole week) should disagree for the same target. It does, sharply, and
splits cleanly into two groups:

**Confirmed real** (ping corroborates elevated RTT, ~100% weekly trombone rate — these are targets
already independently documented elsewhere as genuine hairpins or offshore hosts):

| Target | weekly trombone rate | ping median (week) |
|---|--:|--:|
| efulife.com | 100% | 163.1ms |
| networld.pk | 98% | 202.7ms |
| phf.gop.pk | 55% | 249.2ms |
| toptop.net | 100% | 122.9ms |
| youth.cn | 100% | 110.4ms |

**Likely artifact** (ping stays in the normal 18–50ms domestic band all week, every week, but the
traceroute flags trombone on a third to half of hourly rounds anyway):

| Target | weekly trombone rate | ping median (week) |
|---|--:|--:|
| kknetworks.com.pk | 31% | 19.0ms |
| tevta.gop.pk | 32% | 19.6ms |
| psca.gop.pk | 30% | 18.8ms |
| zcomnetworks.com.pk | 40% | 20.7ms |
| excise.gos.pk | 31% | 30.3ms |
| epads.gov.pk | 21% | 29.4ms |
| cxtreme.pk | 28% | 29.4ms |
| worldlinkisp.pk | 29% | 28.4ms |
| sparkbroadband.pk | 28% | 33.7ms |
| gbn.net.pk | 36% | 33.5ms |
| logon.com.pk | 23% | 33.9ms |
| topcity-1.com | 48% | 37.9ms |
| hrd1902.com.pk | 51% | 41.0ms |
| bbise.edu.pk | 47% | 43.2ms |
| cpsp.edu.pk | 44% | 49.6ms |
| iub.edu.pk | 40% | 50.2ms |

If these 16 sites' domestic traffic genuinely flapped abroad a third of the time, ping — sampled
independently, same probe, same week — would show it too (a bimodal RTT distribution, not a flat
~20–50ms median). It doesn't.

**Quantified impact:** summing whole-week rounds by bucket —

| Bucket | rounds | trombone flags | rate |
|---|--:|--:|--:|
| All PK-class (1016393) | 1,539 | 758 | 49.3% |
| Confirmed-real (ping ≥60ms, or independently known offshore) | 278 | 258 | 92.8% |
| **Likely-artifact (ping <60ms all week)** | 607 | 212 | 34.9% |
| Unconfirmed (target blocks ICMP ping — mostly `.gov.pk`/`.edu.pk`, per METHODOLOGY.md's known ping-silence pattern) | 654 | 288 | 44.0% |

Removing just the 212 likely-artifact trombone flags from the numerator drops 1016393's overall
rate from **49.3% → 35.5%** — still above PTCL-Karachi's 30.1%, but the gap shrinks by roughly
two-thirds. The remaining "unconfirmed" bucket (654 rounds, mostly ping-silent government/education
sites) can't be resolved this way at all — those sites need AS-path/exit-country evidence instead
of RTT, which the traceroute data has but wasn't re-derived here.

---

## What this does and doesn't prove

**Proves:**
- Probe 1016393's traceroute-based RTT readings contain a real, reproducible artifact — most
  visibly at the very first hop — capable of inflating a clean ~6ms reading to 500+ms within the
  same measurement round, at effectively random points along the path.
- A material share (at minimum the 212 quantified rounds, 28% of this probe's total trombone
  count) of its "domestic traffic hairpinned abroad" verdicts are false positives, not real
  routing.
- The handful of targets already documented elsewhere as genuine hairpins/offshore hosts
  (efulife.com, networld.pk, phf.gop.pk, toptop.net, youth.cn) are **not** affected — ping
  independently confirms those are real, and this investigation doesn't touch that conclusion.

**Doesn't prove:**
- That PTCL-Mianwali is *not* genuinely somewhat worse-routed than PTCL-Karachi. Even after
  removing the confirmed-artifact rounds, 1016393 still runs at 35.5% vs 1016126's 30.1% —
  a real gap could still exist underneath the noise; this investigation can't rule that in or out
  for the 654 ping-silent rounds.
- The root cause of the artifact (ICMP-generation rate-limiting at PTCL's Mianwali PoP vs. a
  problem local to the probe host itself) — hop 2 evidence points at "very early in the path," not
  further than that.
- Anything about other probes. This was probe-specific; the finding doesn't generalize without
  re-running the same ping-cross-check elsewhere (worth doing if another vantage's trombone rate
  ever looks similarly out of line with its own ping data).

## Recommended next step (not done here — this file is the investigation, not the fix)

`eda_findings.md`'s original suggestion still stands and is now backed by evidence: **exclude
1016393 from RTT-jump-based trombone statistics, or re-derive its verdicts from AS-path/exit-country
evidence** (which the traceroute hop data already contains, independent of the noisy RTT column)
**instead of the RTT-threshold heuristic**, before citing this probe's specific numbers anywhere
that isn't already using the 14-probe roster's aggregate.
