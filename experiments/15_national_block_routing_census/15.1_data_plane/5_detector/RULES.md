# Per-vantage rules

**A rule here is a statement, not a threshold.** It is written as a claim that could be false,
tested against that probe's own data, and only then applied to that probe. A rule proven for
Z-Com says nothing about PTCL until it is tested there too.

**No constant in this file was chosen by hand.** Every number is derived from the speed of light
in fibre, Pakistan's geography, or the structure of the probe's own traces. Where a judgement
remains, it is named as a judgement.

---

## The two constants everything rests on

| | value | source |
|---|---|---|
| speed of light in fibre | **204,000 km/s** | Bozkurt §5.1, measured |
| fibre path vs great circle | **× 2.1** | Bozkurt, the standard conversion |

From Pakistan's own extent, Gilgit to Gwadar = **1,659 km**:

| | derived |
|---|---|
| absolute domestic RTT floor | **16.3 ms** |
| **expected maximum domestic RTT** | **34.2 ms** |

4.1 used `LOCAL_CEIL = 45 ms`, picked by hand. The derived figure is **34.2 ms**.

Minimum RTT from Karachi, if a packet genuinely travelled there:

| destination | km | floor | expected |
|---|---|---|---|
| Muscat | 865 | **8.5 ms** | 17.8 ms |
| Dubai | 1,183 | **11.6 ms** | 24.4 ms |
| Singapore | 4,736 | **46.4 ms** | 97.5 ms |
| Jinan, CN | 4,895 | **48.0 ms** | 100.8 ms |
| Frankfurt | 5,681 | 55.7 ms | 117.0 ms |
| Vancouver | 11,710 | 114.8 ms | 241.1 ms |

**The ambiguous band is 12 to 34 ms**, where a Gulf hop and a long domestic path are
indistinguishable by RTT. That band is a permanent limit of the method, not a tuning problem.

---

## R1 — "Probe v's access path is the chain C(v)"

**Statement.** Every trace from v begins with the same routers, until routes diverge.

**Test.** The longest common prefix of v's traces, tolerating a hop that is silent in some traces.
Parameter-free: the divergence point is measured, not chosen.

**Proven, all seven probes:**

| probe | chain | B_access |
|---|---|---|
| zcom.lhe | `157.20.147.17` | **0.4 ms** |
| cybernet.hrp | `192.168.1.1` → `203.101.189.254` | 2.0 ms |
| nova.lhe | `192.168.100.1` → `70.70.71.137` → `110.93.212.161` | 2.5 ms |
| nayatel.isb | `192.168.18.1` → `100.89.0.1` | 3.0 ms |
| cybernet.khi | `192.168.18.1` → `202.163.100.245` | 3.1 ms |
| orbit.fsd | `192.168.100.1` → `10.14.14.10` | 3.8 ms |
| **ptcl.khi** | `192.168.10.1` → `39.39.0.1` | **25.5 ms** |

**What it establishes.** PTCL pays **25.5 ms before it has measured anything**, on the first hop
out of the CPE. Every other probe pays under 4 ms. This is the whole reason a single global
threshold mislabels PTCL, and it is now derived rather than asserted.

## R2 — "Address X is not in the country its registry claims"

**Statement.** X is registered in country C. If X were in C, no probe could observe it faster than
`2 × d(probe, C) / 204,000`.

**Test.** Falsified when the observed median RTT from **any** probe is below that floor. Physics.
The only judgement is requiring enough samples for a median, which is stated per case.

**Why a median and not a minimum.** A single anomalous packet falsifies nothing. C-root sits at a
143 ms median with one 3.4 ms sample; a minimum-based test wrongly rejects it.

**Proven:**

| address | claims | observed | floor | verdict |
|---|---|---|---|---|
| `182.45.51.22` | Jinan, CN | 41.7 ms from **PTCL** | 48.0 ms | **falsified** |
| `70.70.71.137` | Vancouver, CA | 1.8 ms from Nova | 114.8 ms | **falsified** |
| `149.40.227.0/24` | Ashburn, US | 1.1 ms from Z-Com | 117.7 ms | **falsified** |
| `27.111.230.170` | Singapore | 90.0 ms from Cybernet | 46.4 ms | not falsified |
| `192.33.4.12` | C-root anycast | 111.3 ms | 55.7 ms | not falsified |

The CHINANET case is falsified **using PTCL's own slow observation**, with no cross-vantage
comparison needed. That is the property the earlier frequency-based rule lacked.

**Grouped by prefix, not address.** `149.40.227.0/24` has **15 addresses** in domestic use across
6 probes. Per-address tests saw fragments at 7-8% and missed them.

## R3 — "Probe v can observe paths at all"

**Statement.** v's traces contain public addresses.

**Test.** Proportion of traces with at least one public hop.

| probe | protocol | traces with no public hop | status |
|---|---|---|---|
| nayatel.isb | TCP | **100%** | **rejected** |
| 62224 PERN | ICMP, UDP | **100%** | **rejected** |
| nayatel.isb | ICMP | 11% | proven |
| 62224 PERN | TCP | 3% | proven |

**A probe is not universally usable or unusable. It is usable under a protocol.** Rules R1, R2 and
R4 must be re-proven per protocol.

## R4 — "Probe v's domestic baseline is B(v)"

**Statement.** v's RTT to destinations that are certainly inside Pakistan.

**Test.** Median RTT to targets some *other* probe observes below the derived domestic ceiling
(34.2 ms). Non-circular: the reference set is defined by other probes, and the ceiling by geography.

**Validity gate.** A median tolerates contamination only below 50%. If v's own detour rate exceeds
that, B(v) is the detour and the rule is **rejected for that probe**, not silently applied.

## R5 — "Probe v detoured to destination d"

**Only evaluated after R1 to R4 are proven for that probe under that protocol.** Anything explained
by C(v), B(v), or a falsified geolocation is subtracted first. A detour is what survives.

---

## What is still a judgement, named honestly

- **The 2.1 routing factor** is an average over US and European research networks. Pakistan's
  factor is unmeasured and probably higher, which makes the domestic ceiling conservative.
- **Sample size** for a stable median is not derived. Currently 3, which is a floor not a
  justification.
- **The 12-34 ms ambiguous band** cannot be resolved by RTT. Gulf detours will be under-counted
  and no threshold fixes it.
- **Return-path asymmetry and MPLS** are invisible to traceroute. Not solvable here.
