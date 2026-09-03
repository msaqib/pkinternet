# Finding — Pakistani ISPs use foreign address space internally, and it corrupts our detour numbers

> **Provenance.** Follow-up investigation carried out 2026-09-02/03, after the AINTEC 2026
> submission. Source data: the archived Exp 07 panel and Exp 4.1 census in this repository, plus
> public RIPEstat / RIPE Atlas / PeeringDB queries. Working notes live in the RA workspace under
> `trello/`; this is the copy of record.


**Not a Trello task.** This came out of task 05 and matters more than the task did.
Found 2026-09-02. Data: the existing 4.1 census archive plus free RIPEstat lookups. No new
measurements.

---

## The answer in one line

**Two Pakistani ISPs are using foreign-registered IP addresses inside their own networks. Our
detector reads those as "the packet went abroad", and that produced 347 false detours — 17% of the
entire census.**

---

## How it started

Every Nova traceroute has a hop that geolocates to **Shaw Communications, Canada**. The project has
always excluded it as a known artefact, described in the code as *"physically in PK at ~1.5 ms"*.
Nobody had checked why.

So we checked the ownership certificate, the same way as task 05.

---

## Case 1 — Nova and Shaw (Canada)

**Shaw's paperwork is completely clean.** `70.68.0.0/14` is genuinely Shaw's, genuinely announced by
Shaw, and RPKI-valid. Nobody is announcing space they should not.

**But the packet never goes to Canada:**

| | |
|---|---|
| Times we have seen this hop | **336** |
| Fastest ever recorded | **0.9 ms** |
| Lahore → Vancouver, straight line | 10,862 km |
| Fastest a signal could possibly make that round trip | **109 ms** |
| So the observation is faster than physically possible by | **121×** |

**Nova is using Shaw's address space on its own equipment in Pakistan.**

The evidence it is Nova's own kit: the hop appears at **position 2 in 333 of 333 traces** — the
router right after the probe's gateway — and it appears from **Nova and no other vantage**,
including Z-Com and TES which share Nova's transit and would see it too if it belonged to
Transworld.

---

## Case 2 — PTCL and CHINANET (China), and this one broke our results

`182.45.51.22` is registered to **CHINANET Shandong** (`182.32.0.0/12`, country CN) and genuinely
announced by China Telecom. It sits **inside PTCL's network in Pakistan**.

The proof is the hop immediately before it — PTCL's own internal `10.253.8.39` — seen from two
different vantages:

| Vantage | `10.253.8.39` | `182.45.51.22` | difference |
|---|---|---|---|
| Z-Com Lahore | 19.0 ms | 19.4 ms | **+0.4 ms** |
| PTCL Karachi | 42.7 ms | 42.3 ms | **−0.4 ms** |

**A packet cannot reach China and come back in 0.4 ms.** The address is in Pakistan. Only PTCL's
internal path to it is slow.

### Why the detector was fooled

The rule is: *a hop counts as foreign if it geolocates outside Pakistan **and** the RTT is at least
40 ms.* The RTT gate exists precisely to catch bad geolocation.

From PTCL this hop sits at **42.3 ms — two milliseconds over the threshold.** So it passed the gate
and every PTCL trace through it was scored as a detour to China.

From Z-Com the same address answers in 2.2 ms and would never have been flagged. **The same address,
seen from a different vantage, gets opposite verdicts.**

---

## What it costs us

| Measure | As published | **Corrected** |
|---|---|---|
| Census detour rate | 11.0% | **9.1%** |
| PTCL Karachi detour rate | 38.4% | **16.1%** |
| **PTCL → Brain Telecom** | **97.6%** | **0.0%** |
| Detour verdicts resting on this one address | — | **347 of 2,002 (17.3%)** |

**The PTCL → Brain Telecom figure was the sharpest illustration in the census deck** — the
"97.6% from PTCL, 3.8% from Nova, same blocks" slide. All 328 of those verdicts came from this
single address. **It was entirely an artefact.**

Cybernet Haripur (46.3% → 45.0%) and every other vantage are essentially unchanged.
**Task 04 is unaffected** — its Omantel and Equinix Singapore detours run at 100–200 ms on
genuinely foreign infrastructure.

---

## The full sweep

Scanned every hop ever recorded in the 4.1 census — **131,075 observations, 1,637 distinct
addresses** — for public addresses seen **under 10 ms** (faster than Karachi↔Islamabad, so
necessarily domestic) that are **registered abroad**:

| Registered | Address | Fastest | Holder | Seen from |
|---|---|---|---|---|
| **CN** | `182.45.51.22` | 2.2 ms | CHINANET Shandong | zcom, nova, nayatel, cybernet, **ptcl** |
| **CA** | `70.70.71.137` | 0.7 ms | Shaw | nova |
| **BY** | `178.124.134.225` | 0.6 ms | Belpak, Belarus | nova |
| **AE** | `213.202.7.162` | 1.0 ms | Zain Omantel | nova |
| **AE** | `82.178.159.117` | 5.1 ms | Zain Omantel | orbit, zcom |
| **JP** | `58.138.112.90` | 4.4 ms | IIJ Japan | nayatel |

**Checked and excluded — not squatting:** `193.0.14.129`, `192.33.4.12` and `199.7.83.42` are
**anycast root DNS servers** with legitimate in-country instances. Cogent and Hurricane addresses
are global-backbone interface space and never cross the 40 ms gate anyway.

---

## The fix, and it is free

Raising the RTT threshold would not work — it would only lose real detours.

**The multi-vantage design already contains the answer.** If *any* vantage sees an address under
10 ms, that address is physically in Pakistan, and **no** vantage may then score it as foreign:

```
DOMESTIC_OBSERVED = { every hop IP seen anywhere in the run at < 10 ms }

foreign(hop) :=  country != PK
             AND rtt >= 40 ms
             AND ip not in DOMESTIC_OBSERVED
```

One pre-pass over the hop table, no extra measurement, and it would have caught all 347.

**This is now marked mandatory** in `the RA workspace: research-pipeline/experiment_10/SAMPLING_METHOD.md` §3.4 and
in `research-pipeline/experiment_10/10.1_data_plane/MANUAL.md` before Experiment 10 runs.

---

## Why it matters beyond this project

Two ISPs are doing this independently, which suggests it is common rather than exceptional. It means
**any traceroute study of Pakistan that trusts geolocation — even with an RTT gate — will
over-report detours.**

For a paper whose headline number is a detour rate, that is a threat to validity that belongs in the
methods section, not in a reviewer's report.

It also reframes why the detector's RTT gate is right. The documentation said it corrects
**mis-geolocation**. It does not: the geolocation is *correct*, the address really is Canadian or
Chinese. What the gate actually catches is **address squatting on live routed space** — which no
geolocation database, however accurate, could ever get right.

---

## Open

- **Do other Pakistani ISPs squat other foreign ranges?** The sweep covers only hops that appeared
  in the 4.1 census. A wider target set would likely find more.
- **Is any of it arranged with the registered owner?** Unfalsifiable from outside.
- **Practical consequence, unquantified:** a Nova customer trying to reach the real Shaw host at
  `70.70.71.137` gets Nova's own router instead. Minor, but a genuine reachability break.
