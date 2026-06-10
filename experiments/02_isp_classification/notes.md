# Experiment 02 - ISP Classification (PKIX Set 1 / 2 / 3)

**Author:** Rayan Atif

Single source of truth for Experiment 02. Covers the goal, the PKIX roster, the
set classification, current probe + volunteer coverage, the probe budget, and the
recruitment plan.

---

## 1. Objective

Classify Pakistani ISPs by their relationship to PKIX, then test whether it affects
user experience.

- **Set 1** - not present at any PKIX node (ignored the PTA mandate).
- **Set 2** - physically present at PKIX but NOT exchanging routes/traffic.
- **Set 3** - present AND actively exchanging traffic.

**Research questions:**
- **RQ1** - is the user experience (RTT, hop count, hairpinning) of Set-3 ISP
  customers better than Set-1/2?
- **RQ2** - do customers of the *same* ISP receive similar service?

---

## 2. Source: PTA "Pakistan Peering Roadshow" deck (12 May 2026)

By Ahmed Bakht Baloch, Director Cybersecurity PTA.

- **Nodes (slide 5/8):** Islamabad (HEC, 2017), Karachi (HEC, 2019), Lahore
  (PITB, 2023), Karachi PTCL/DE-CIX datacenter (2024), Multan (pipeline).
- **Slide 7 (complete physical-presence roster):** Islamabad 22 ISPs, Karachi 14,
  Lahore 18 - the **Set-1 boundary**. (Slide 6 is an older, shorter version.)
- **Slide 9 (latency test = Set-3 evidence):** PTA measured RTT to locally hosted
  sites internationally vs through the IXP, for 8 ISPs: **Cybernet, Multinet,
  Nayatel, PERN, PTCL, Telenor, Wateen, Wi-Tribe.** International 102-144 ms;
  through-IXP 1-31 ms. These 8 demonstrably exchange = **Set 3**. **Wateen is the
  laggard (15-31 ms vs 1-6 ms)** - present and exchanging, but poorly.
- **Slide 10:** fees (join Rs 100k/200k for 1G/10G; monthly Rs 60k/125k; none
  charged since 2016). **Slide 17:** way forward includes CDN deployment and
  connecting to PeeringDB.

---

## 3. How we verify the sets (method)

PTA's Set-2/Set-3 split is a *claim*; we verify it on the **data plane**:
- For a pair of ISPs A, B: traceroute from a probe on A toward a host/probe on B.
  A hop in the **PKIX peering-LAN prefix** (or a low-RTT local path) = they exchange
  at the IXP (**Set 3**). Transit through PTCL/Transworld, or a foreign hairpin, =
  **not** exchanging (**Set 2**).
- **RTT alone is not enough** (two ISPs both buying PTCL transit can reach each other
  fairly fast without using the IXP). The decisive signal is the **IXP-LAN hop** in
  the path - so obtaining PKIX's peering-LAN prefixes per node is a key input.

Design principles for probe placement:
- **Put probes in the IXP cities** (Islamabad, Karachi, Lahore) - local exchange is
  only testable where a node exists.
- **Probes on members unlock probe-to-probe** two-way tests and a full peering
  matrix; cluster within a city where possible.

---

## 4. Set classification + probe coverage

Definitiveness: **Set 3** is definitive (PTA's slide-9 measurement). **Set 2** is
definitive *membership* (slide 7) but the "not exchanging" label is our hypothesis
to verify. **Set 1** = FLL licensees (`data/pk_isp_fll_list.csv`) not on slide 7
(~59; best-effort name matching).

| Set | Members | Probed | Unprobed |
|---|---|---|---|
| **Set 3** (exchanging) | 8 | **5** | 3 |
| **Set 2** (present, unverified) | ~26 | **3** | ~23 |
| **Set 1** (not at PKIX) | ~59 | 1 | ~58 |

### Set 3 - confirmed exchanging (slide 9)
| ISP | PKIX nodes | Probe? | Probe city |
|---|---|---|---|
| Cybernet / StormFiber | ISB, KHI, LHE | ✅ volunteer ×2 | Karachi |
| Multinet | ISB, KHI, LHE | ✅ volunteer | Karachi |
| Nayatel | ISB, LHE | ✅ existing | Islamabad |
| PTCL | ISB | ✅ existing (offline) + volunteer | Lahore + Karachi |
| Wateen *(weak)* | ISB, KHI, LHE | ✅ volunteer | Karachi |
| PERN / HEC | ISB, KHI, LHE | ❌ | — |
| Telenor | ISB, KHI | ❌ | — |
| Wi-Tribe | ISB | ❌ | — |

### Set 2 - present, exchange not demonstrated (slide 7, not in slide 9)
| ISP | PKIX nodes | Probe? | Probe city |
|---|---|---|---|
| Transworld (TWA/TES) | ISB, KHI, LHE | ✅ existing + volunteer | Lahore + Karachi |
| Z-Com (ZCom) | LHE | ✅ existing | Lahore |
| Jazz (VEON) | ISB, LHE | ✅ volunteer | Karachi |
| COMSATS, NTC, Worldcall, Gerry's, Ufone, Zong, Qubee, Virtury | ISB | ❌ | — |
| Brain Net, Nexlinx, KK, Connectel, Sigin, Smartline, WellNet, Ylinx | LHE | ❌ | — |
| Connect, CubeX, Faria, Fiberbeam, GCS, Redtone, SATCOMM | KHI | ❌ | — |

**Notable:** Transworld is present at all nodes but absent from the latency test -
a strong Set-2 candidate, consistent with Exp 01 (it is the transit chokepoint).

### Set 1 - not at any PKIX node (~59 FLL licensees)
Mostly small regional cable / broadband operators. Notable:
- **TPCPL / Nova** (AS136174) = **our probe 1015679 → we already have a Set-1
  control** (Lahore).
- **Optix** (AS136384) and **Fiberlink** (AS55714) - reportedly host Netflix caches
  but are *not* PKIX members (hosting a cache ≠ peering at the IXP).

---

## 5. Volunteers signed up (all Karachi)

| Volunteer | Where | ISP | Set |
|---|---|---|---|
| Farhan Khan | Home | StormFiber (Cybernet) | Set 3 |
| Narmeen Bawany | Home | StormFiber (Cybernet) | Set 3 (2nd customer → RQ2) |
| Murtaza Lightwala | Home | PTCL DSL | Set 3 |
| Murtaza Lightwala | Office | Transworld + Multinet + Wateen | Set 2 / 3 / weak |
| Narmeen Bawany | Office | Jazz (VEON) | Set 2 |

Wins: Set 3 well covered; Wateen (the laggard) covered; two Cybernet home customers
(RQ2 starter); a **multi-homed office** (3 ISPs at one site) = clean controlled test.
Note: a RIPE probe attaches to one link, so the multi-homed office needs 3 probes or
multi-WAN - confirm with Murtaza.

---

## 6. Probe budget and allocation (~21 new + 5 existing)

~21 new probes on top of the 5 existing - far short of ~88 members, so prioritise.

- **5 existing** (Lahore ×4, ISB ×1): Nayatel (S3), PTCL (S3, offline),
  Transworld (S2), Z-Com (S2), TPCPL/Nova (S1 control).
- **~6 to current Karachi volunteers** (above).
- **~15 left to allocate:**

| Use | Probes | Targets |
|---|---|---|
| **Set 3** | 2 | Telenor (ISB), Wi-Tribe (ISB) |
| **Set 2** (lean - several have hosts) | 2 | Brain Net (LHE), Worldcall (ISB) |
| **Set 1** baseline (**biggest share**) | 11 | distinct ISPs across the 3 IXP cities (mostly ISB + LHE, since volunteers fill Karachi) |

**Set 1 (11) >> Set 2 (2):** Set 1 is the non-IXP baseline and the largest population
(~59 ISPs), the clean contrast against Set 3, so it gets the bulk - as **distinct
ISPs spread across the three IXP cities** (same-city controls vs the Set-3 there).
Set 2 stays minimal because NTC/COMSATS/Nexlinx/PERN/LinkDotNet are already
classifiable via their Exp-01 hosts. **Geography: all probes in the IXP cities**
(volunteers fill Karachi, so new probes weight to Islamabad + Lahore). The full
allocation table is in `isp_targets.md` (section 3).

Recruiting: ask each volunteer their **ISP + city**, match to the tables above, and
prefer **multiple volunteers on the same ISP in different cities** (unlocks RQ2).

**Use Experiment 01 hosts to classify - but a host does not replace a probe.** The
classification test is "probe-on-A to host-on-B". Exp 01 already found **PK-hosted servers** we can use as the host on B:
NTC (`pta.gov.pk`, `sindh/kp/pbs.gov.pk`), PERN (`hec.gov.pk`, `pu.edu.pk`),
Multinet (`pseb.org.pk`, `dunyanews.tv`), Cybernet (`stormfiber.com`),
COMSATS (`pid.gov.pk`), PTCL (`ptcl.com.pk`, `lums.edu.pk`), Nayatel (`nayatel.com`),
PITB (`punjab.gov.pk`) and Nexlinx (`nexlinx.net.pk`) - so those ISPs can be
**classified as destinations without a probe on them**. (Avoid Cybernet's
`pakistan/moitt/railways.gov.pk` - they hairpin via US Prolexic; use `stormfiber.com`.)

A *host* lets us reach an ISP *as a destination* - enough to **classify** it - but
(per the instructor) it is **not a substitute for a probe on that ISP's customers**.
Even where a host exists (e.g. PTCL hosts `lums.edu.pk`), we still want an end-user
probe: to compare a **PTCL customer vs a non-PTCL customer reaching LUMS**, and because
that ISP's customers' experience reaching *every other* site is exactly what RQ1
measures. So the host-only ISPs (PERN, NTC, COMSATS, Nexlinx, PITB, LinkDotNet) stay
**probe candidates, not "already covered."** New probes still go *first* to ISPs with
**neither a probe nor a host** (plus a couple of Set-3 ISPs for the RQ1 baseline), but
having a host does not retire the need for one. The full per-ISP coverage and the
new-probe shortlist are in **`isp_targets.md`**.

Exp 1.1 also helps: DNS resolves consistently across ISPs for ~92% of sites, so
cross-ISP comparisons to a common target are valid; avoid the 8 GeoDNS sites as
targets.

---

## 7. Caveats & open items

- Set 2 vs Set 3 is **PTA's** claim; our measurements must confirm it independently.
- Set 1 is fuzzy name-matching of the FLL list vs slide 7; a few (e.g. "Sign In",
  "Web Concepts") are ambiguous.
- Slide 7 is dated to node years (2016/2019/2022-23); membership may have changed.
- [ ] Obtain PKIX peering-LAN prefixes per node (lets a traceroute *prove* Set 3).
- [ ] Register volunteer probes; build the inter-ISP measurement matrix.
- [ ] Confirm the multi-homed office probe count.
- [ ] Decide whether to spend end-user probes on the host-only ISPs (PERN, NTC,
  COMSATS, Nexlinx, PITB, LinkDotNet) - a host classifies them but doesn't capture
  their customers' experience (RQ1).
