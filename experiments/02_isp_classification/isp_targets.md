# Experiment 02 - Sets, Hosts & Probe Plan

**Author:** Rayan Atif

The definitive plan: the three sets (from the PTA IXP slides + Experiment 01), the
**Pakistan-hosted servers we can use as destinations** (kept separate from probes),
and the **final probe allocation** (existing + volunteers + new). Companion to
`notes.md`.

---

## 1. The three sets (IXP slides 7 & 9, corroborated by Experiment 01)

- **Set 3** - present at PKIX AND exchanging traffic (PTA slide-9 latency test).
- **Set 2** - present at PKIX but not shown to exchange.
- **Set 1** - not at any PKIX node (FLL licensees absent from slide 7).

**Exp 01 corroborates this:** Nayatel reached domestic content at ~3 ms on
independent peering (Set-3 behaviour), while Transworld was the transit chokepoint
everyone routed through and never peered locally (Set-2 behaviour). So our own
data-plane results line up with PTA's classification.

| Set | ISPs |
|---|---|
| **Set 3** (8) | Cybernet/StormFiber, Multinet, Nayatel, PTCL, PERN, Telenor, Wi-Tribe, Wateen *(weak: 15-31 ms)* |
| **Set 2** (~26) | Transworld, Z-Com, Jazz, NTC, COMSATS, Worldcall, Gerry's, Ufone, Zong, Qubee, Virtury, Brain Net, Nexlinx, KK, Connectel, Sigin, Smartline, WellNet, Ylinx, Connect, CubeX, Faria, Fiberbeam, GCS, Redtone, SATCOMM |
| **Set 1** (~59) | FLL licensees not on slide 7 (full list = `data/pk_isp_fll_list.csv` minus slide 7); notable: TPCPL/Nova, Optix, Fiberlink, LinkDotNet, Telecard, Wise, Vision, Smart Telecom, Hazara, Multan Cable, ... |

---

## 2. Hosts in Pakistan, by set (from Exp 01) - these are DESTINATIONS, not probes

PK-hosted servers found in Experiment 01, with their probable city, grouped by set.
A host lets us test reachability *to* an ISP without a probe (for classification); a
probe is still needed to measure that ISP's own customers (RQ1). These are separate
from the probe plan in section 3.

| Set | ISP | Host site | Probable city |
|---|---|---|---|
| 3 | Cybernet / StormFiber | stormfiber.com | Karachi |
| 3 | Multinet | pseb.org.pk, dunyanews.tv | Karachi, Islamabad |
| 3 | Nayatel | nayatel.com | Islamabad |
| 3 | PTCL | ptcl.com.pk, lums.edu.pk | Islamabad, Lahore |
| 3 | PERN / HEC | hec.gov.pk, pu.edu.pk | Lahore |
| 2 | NTC | pta.gov.pk, pbs.gov.pk | Rawalpindi, Islamabad |
| 2 | COMSATS | pid.gov.pk | Islamabad |
| 2 | Nexlinx | nexlinx.net.pk | Lahore |
| 2 | PITB (IXP operator) | punjab.gov.pk | Lahore |
| 1 | LinkDotNet | pucit.edu.pk | Islamabad |
| 1 | Telecard | goto.com.pk | Karachi |

Other in-country hosts on their own ASN (not ISPs): FBR fbr.gov.pk (Islamabad),
UBL ubldigital.com (Karachi), PITC pitc.com.pk (Lahore). Avoid Cybernet's
pakistan/moitt/railways.gov.pk - they hairpin via US Prolexic; use stormfiber.com.

---

## 3. Probe plan

### 3a. Existing probes (5)
| ISP | Set | City |
|---|---|---|
| Nayatel | 3 | Islamabad |
| PTCL | 3 | Lahore *(offline)* |
| Transworld | 2 | Lahore |
| Z-Com | 2 | Lahore |
| TPCPL / Nova | 1 | Lahore |

### 3b. Volunteers signed up (10)

Six in Karachi (below), plus four newly added in Lahore, Islamabad, Burewala, and
Haripur - **Burewala and Haripur put us in non-IXP cities for free**. Names/ISPs for
the four new ones are _TBD_ (fill in).

| Volunteer | ISP | Set | City |
|---|---|---|---|
| Farhan Khan | StormFiber (Cybernet) | 3 | Karachi |
| Narmeen Bawany (home) | StormFiber (Cybernet) | 3 | Karachi |
| Murtaza Lightwala (home) | PTCL | 3 | Karachi |
| Murtaza Lightwala (office) | Transworld + Multinet + Wateen | 2 / 3 / weak | Karachi |
| Narmeen Bawany (office) | Jazz | 2 | Karachi |
| _TBD_ | _TBD_ | ? | Lahore |
| _TBD_ | _TBD_ | ? | Islamabad |
| _TBD_ | _TBD_ | ? | Burewala |
| _TBD_ | _TBD_ | ? | Haripur |

### 3c. New probes to send (12)

Per the instructor, the new probes spread **beyond the three IXP cities** to non-IXP
cities (Multan, Faisalabad, Sialkot, Peshawar, Quetta) - the real "no local IXP node,
must hairpin to an IXP city" test. **No new Lahore probes** (existing + volunteers
cover it); **Islamabad** stays the main anchor (5, trimmed from 8 candidates).

| # | City | ISP | Set | Host? |
|---|---|---|---|---|
| 1-5 | Islamabad / Rawalpindi | **5 of:** Telenor (3), Wi-Tribe (3), Worldcall (2), Wise (1), Vision (1), Smart Telecom (1), Wah (1), Helium (1) | mixed | no |
| 6 | Karachi | Optix | 1 | no |
| 7 | Karachi | Telecard | 1 | yes (goto.com.pk) |
| 8 | Multan | _TBD_ | ? | candidates: Multan Cable (1), StormFiber (3), Worldcall (2) |
| 9 | Faisalabad | _TBD_ | ? | candidates: local WISP (1), Nayatel (3), StormFiber (3) |
| 10 | Sialkot | _TBD_ | ? | candidates: local cable (1), StormFiber (3), PTCL (3) |
| 11 | Peshawar | _TBD_ | ? | candidates: local KPK ISP (1), Nayatel (3), StormFiber (3) |
| 12 | Quetta | _TBD_ | ? | candidates: PTCL (3), Worldcall (2), local WISP (1) |

**Two open picks (yours):** (a) which **5 of the 8** Islamabad candidates to keep, and
(b) the **ISP per remote city** from the candidate lists above. City is a target; the
ISP follows whatever host/volunteer we can recruit there.

*(Telecard has a host at goto.com.pk but is Set 1 - the host only gives a destination;
we still want a probe on it to measure its own customers for RQ1.)*

### 3d. Full probe geography (existing + volunteers + new)
| City | Existing | Volunteers | New | Total |
|---|---|---|---|---|
| Karachi | 0 | 6 | 2 | **8** |
| Lahore | 4 | 1 | 0 | **5** |
| Islamabad / Rawalpindi | 1 | 1 | 5 | **7** |
| Multan | 0 | 0 | 1 | **1** |
| Burewala | 0 | 1 | 0 | **1** |
| Faisalabad | 0 | 0 | 1 | **1** |
| Sialkot | 0 | 0 | 1 | **1** |
| Peshawar | 0 | 0 | 1 | **1** |
| Quetta | 0 | 0 | 1 | **1** |
| Haripur | 0 | 1 | 0 | **1** |
| **Total** | **5** | **10** | **12** | **27** |

Per the instructor's note, the plan now spreads **beyond the three IXP cities**: new
probes go to non-IXP cities (Multan, Faisalabad, Sialkot, Peshawar, Quetta) and
volunteers add Burewala and Haripur. **27 probes total** - the three IXP cities still
anchor it (Karachi 8, Lahore 5, Islamabad 7 = **20**), with **7 in non-IXP cities** to
capture the "no local IXP node, must hairpin to an IXP city" worst case. No new Lahore
probes (existing + volunteers already cover it).

---

## 4. All ISPs that already have a host (consolidated, with city)

| ISP | Set | Host site | City |
|---|---|---|---|
| Cybernet / StormFiber | 3 | stormfiber.com | Karachi |
| Multinet | 3 | pseb.org.pk, dunyanews.tv | Karachi, Islamabad |
| Nayatel | 3 | nayatel.com | Islamabad |
| PTCL | 3 | ptcl.com.pk, lums.edu.pk | Islamabad, Lahore |
| PERN / HEC | 3 | hec.gov.pk, pu.edu.pk | Lahore |
| NTC | 2 | pta.gov.pk, pbs.gov.pk | Rawalpindi, Islamabad |
| COMSATS | 2 | pid.gov.pk | Islamabad |
| Nexlinx | 2 | nexlinx.net.pk | Lahore |
| PITB | 2 | punjab.gov.pk | Lahore |
| LinkDotNet | 1 | pucit.edu.pk | Islamabad |
| Telecard | 1 | goto.com.pk | Karachi |

**11 ISPs** have a usable in-country host. A host lets us reach that ISP *as a
destination* - enough to **classify** it - but (per the instructor) it is **not a
substitute for a probe on that ISP's own customers**. Two reasons:

- **Same site, different ISP:** we want to compare, e.g., a **PTCL customer vs a
  non-PTCL customer reaching lums.edu.pk**. The host alone can't show that gap -
  only end-user probes on each ISP can.
- **The rest of the web:** even if PTCL users reach LUMS instantly, their experience
  reaching *every other* site is what RQ1 is about, and only an end-user probe on
  PTCL reveals it.

We already have end-user probes/volunteers on several of these host ISPs - **PTCL**
(existing + Karachi volunteer), **StormFiber**, **Multinet**, **Nayatel**, **Telecard**
(new probe). The host-only ISPs with **no end-user probe yet** - PERN, NTC, COMSATS,
Nexlinx, PITB, LinkDotNet - remain **probe candidates**, not "already covered."
