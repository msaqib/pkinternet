# Finding — "Pakistan's address space" is two different sets, and they disagree

**2026-09-09.** Built while assembling the all-Pakistan scan universe. Free lookups only.

---

## The two definitions

There are two ways to ask "which addresses belong to Pakistan", and they are not the same question.

| | source | what it means |
|---|---|---|
| **Registry view** | RIPEstat `country-resource-list?resource=PK` | address space **registered** to Pakistan at the RIR |
| **Routing view** | `announced-prefixes` for each of the 466 PK ASNs | address space **announced** by a Pakistani network |

Registration is a paperwork fact. Announcement is an operational one. **Neither contains the other.**

## What they measure

| | networks | addresses |
|---|---|---|
| Registered to PK | 740 | 5,521,664 |
| Union of registered **or** announced by a PK ASN | 932 | **5,774,336** |
| **Announced from PK but NOT registered to PK** | **192** | **252,672** |
| Registered to PK but announced by nobody | 0 | 0 |

**252,672 addresses — 4.4% of Pakistan's routed space — are registered to some other country but announced by Pakistani networks.** A study that defines its universe by registration misses all of it.

The reverse is empty: every block registered to Pakistan is announced by somebody. So the registry
view is a strict subset of the routing view, not merely a different slice.

## Who is doing it

The largest examples, by size:

| prefix | addresses | announced by |
|---|---|---|
| `154.192.0.0/16` | 65,536 | AS23674 Nayatel |
| `154.80.0.0/17` | 32,768 | AS45669 Mobilink (PMCL) |
| `154.198.64.0/18` | 16,384 | AS45669 Mobilink (PMCL) |
| `149.40.192.0/19` | 8,192 | AS45669 Mobilink (PMCL) |
| `154.81.224.0/19` | 8,192 | AS45669 Mobilink (PMCL) |
| `154.208.32.0/19` | 8,192 | AS150750 |
| `205.164.128.0/19` | 8,192 | AS136384 Optix |
| `206.0.192.0/19` | 8,192 | AS136384 Optix |
| `154.57.208.0/20` | 4,096 | AS135407 TES |
| `156.149.208.0/20` | 4,096 | AS24435 |

> **Naming note.** AS45669 is recorded here as **Mobilink (PMCL)**, which is what the registry
> holder string says today (`Mobilink-AS-PK - PMCL /LDI IP TRANSIT`). Earlier drafts of this file
> called it Wateen. Wateen Telecom is a separate ASN, **AS38264**
> (`WATEEN-IMS-PK-AS-AP`), and appears separately in `ISP_SUMMARY.md`. Anything attributing
> AS45669 to Wateen is out of date.

These are major operators, not obscure ones, and the volumes are large. This is ordinary address
leasing: space is transferred or rented across registries far faster than the registry country
field is updated, and a network announcing leased space is doing nothing improper.

## Why this matters to us specifically

**It is a different phenomenon from address squatting, and the two are easy to confuse.**

Both look like "a Pakistani network using foreign-registered addresses", but:

| | leased space, announced | squatted space, unannounced |
|---|---|---|
| Announced in BGP by the PK network | **yes** | **no** |
| Visible in `announced-prefixes` | yes | no |
| Example | `149.40.192.0/19`, Mobilink | `149.40.227.0/24`, seen inside Transworld |
| Interpretation | normal leasing | internal use of space nobody announces |

The distinction is sharp and checkable. `149.40.0.0/16` is Cogent's. Mobilink legitimately
announces several /19s and /20s inside it. But **`149.40.227.0/24` sits in none of those announcements**, it
appears only as hop addresses inside Pakistani traceroutes, and is announced by nobody in Pakistan.
The same registry holder, the same /16, two completely different situations.

> **RTT figures, both vantages, 2026-09-09.** This section originally said the addresses appear
> "at 1 to 5 ms" without naming where that came from. The source is `5_detector/RULES.md` R2:
> a **1.1 ms median from the Z-Com vantage**, against a 117.7 ms physical floor for Ashburn.
>
> The all-Pakistan route sweep measures the same /24 from different vantages (AS135407 and
> AS45669) and sees something very different. Across **778 hop observations of 22 distinct
> `149.40.227.x` addresses** in `3_routes/selected_annotated.json`:
>
> | | ms |
> |---|--:|
> | minimum | 8.0 |
> | 25th percentile | 43.0 |
> | median | 59.5 |
> | 75th percentile | 90.2 |
>
> **These do not contradict each other, and the pair is more informative than either alone.**
> Squatted space is numbered on infrastructure inside a particular network. From a vantage sitting
> on or near that infrastructure it is one or two hops away, so Z-Com sees 1.1 ms. From vantages
> that reach it across the country it is many hops away, so this sweep sees a 59.5 ms median. An
> address genuinely in Ashburn could not be 1.1 ms from anywhere in Pakistan.
>
> **What this changes in practice.** "1 to 5 ms" is a Z-Com figure, not a property of the prefix,
> and must be quoted with its vantage attached. The falsification still holds from both datasets,
> on different grounds: R2 falsifies on Z-Com's 1.1 ms against the 117.7 ms Ashburn floor, and
> this sweep falsifies independently on **106 of 778 observations (14%) below 34.2 ms**, the
> domestic ceiling, which no trans-Atlantic path can beat. The other 86% are consistent with an
> ordinary foreign path and prove nothing either way, which is why the claim rests on the
> sub-ceiling subset rather than on the median.

## Consequence for the scan universe

`build_pk_universe.py` therefore unions both sources. Using the registry alone would have dropped
252,672 addresses, including large parts of Nayatel, Mobilink, Optix and TES.

The same problem exists in the small-ISP universe already scanned: **113 of its 778 blocks are not
in the PK registry list**, because they are announced from Pakistan and registered elsewhere.

## How to reproduce

```
python 1_universe/build_pk_universe.py
```

Queries the country resource list once and `announced-prefixes` for all 466 PK ASNs (12 threads,
zero errors on the 2026-09-09 run), collapses the union, and writes `pk_universe.json`. The split
is written to `universe_split.json`.

## Limits

- **Registry country is a coarse field.** It records the RIR's view of the holder's country, which
  can lag transfers by years, and is set per allocation rather than per use.
- **`announced-prefixes` reflects what RIS collectors see.** A prefix announced only to a single
  regional peer might not reach a collector and would be missing from the routing view too.
- **This is IPv4 only.**
- The 466 ASN list is itself the registry view of *which ASNs are Pakistani*, so a Pakistani
  operator using a foreign-registered ASN would be missed entirely. Not checked.
