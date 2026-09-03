# Task 05 — Were other Cybernet prefixes affected?

> **Provenance.** Follow-up investigation carried out 2026-09-02/03, after the AINTEC 2026
> submission. Source data: the archived Exp 07 panel and Exp 4.1 census in this repository, plus
> public RIPEstat / RIPE Atlas / PeeringDB queries. Working notes live in the RA workspace under
> `trello/`; this is the copy of record.


## As sent

> Were cybernet prefixes other than the EFU Life IP address affected?

**Status: answered.** 2026-09-02. All data public and free — no measurement credits used.

---

## The answer in one line

**Yes — 36 blocks broke. But it was a different problem, on a different day, for a different
reason, and EFU Life was not one of them.**

---

## Two ideas you need first

### A "deed" (RPKI)

Every block of IP addresses has an owner, and that owner can publish a **signed certificate saying
which network is allowed to announce it**. Networks worldwide check that certificate before
accepting a route. If the announcement does not match the certificate, they throw the route away.

Think of it as a land registry for the internet.

### An "observer"

RIPE asked about **330 networks worldwide** to share their routing tables — the list of *"for these
addresses, send traffic this way."* Each of those networks is an **observer**.

Ask all 330 *"do you know how to reach this block?"*:

| Answer | Meaning |
|---|---|
| **326 say yes** | basically the whole internet can reach it |
| **17 say yes** | almost nobody can |

An observer is a **network, not a person**, and it measures **can reach**, not **does visit**.
They are volunteers, skewed toward large European and US networks — so the count drifts a little on
its own, and anything under about ±4 is noise.

---

## What happened

Cybernet announces **957 blocks**. Most are Pakistani. But **39 are American** — ranges like
`206.135.x`, `66.167.x`, `68.166.x`, `209.101.x`.

**The deed on those American blocks names GTT, an American carrier. It does not name Cybernet.**

For years this did not matter, because checking the deed was optional. Then:

> **31 July 2026, 16:00 UTC — 36 of those blocks fell from ~330 observers to under 20, all in the
> same fifteen minutes.**

The *shape* of the fall is what proves the cause. A withdrawn route drops to zero instantly. These
fell off a cliff and then kept sliding for days — which is what it looks like when more and more
networks independently switch on deed-checking and each decides to reject the route.

---

## Where it stands today

**Cybernet never stopped announcing.** All 39 American blocks are still in its announcement list.
What changed is how many networks believe it.

**And the addresses are not unreachable — they now belong to someone else in practice:**

| Who announces | What | Believed by |
|---|---|---|
| **GTT** | `206.135.0.0/16` | **332 observers** |
| **GTT** | `206.135.160.0/20` — new on **1 Sept 2026** | **326 observers** |
| **Cybernet** | `206.135.160.0/24` | **20 observers** |

Normally a smaller, more specific block wins. But a router that **rejects** Cybernet's /24 simply
falls back to GTT's /16 instead.

**So the internet is now split:** roughly **95% of networks send that traffic to GTT in the US**,
and about **5% send it to Cybernet in Karachi**. Every surviving path to Cybernet runs through
**PTCL** — for example `49544 17557 9541`.

Anything Cybernet actually hosts there is unreachable from most of the internet, **not because the
route vanished, but because the traffic is being handed to somebody else.** That is worse than an
outage: it is silent and one-directional.

GTT adding a `/20` on 1 September — more specific, competing directly with Cybernet's /24s —
suggests **someone at GTT is actively asserting the space. This is live, not history.**

---

## Why this is not the EFU Life story

| | EFU Life (task 04) | These 36 blocks |
|---|---|---|
| Symptom | slow — traffic detoured abroad | traffic delivered to the wrong company |
| When | somewhere in 18 Jul – 1 Sep | **31 July, 16:00, exactly** |
| Cause | no domestic link between two ISPs | **ownership certificate names someone else** |
| Visible in BGP? | **no** | **yes, glaringly** |
| Same event? | — | **no** |

EFU Life's own deed is correct and names EFU Life. So do the deeds on Cybernet's Pakistani blocks.
**Only the borrowed American space broke.** The two events looked connected purely because they
involved the same company in the same fortnight.

---

## How we checked

| Question | Source | Method |
|---|---|---|
| Which blocks, and when were they visible? | `stat.ripe.net/data/routing-history` | Queried AS9541, 15 Jul – 10 Aug → **943 prefix timelines**, each with observer counts per time window |
| Which ones broke? | same data | Kept blocks above **200** observers on 30 Jul and below **100** on 5 Aug → exactly **36**, all with the same drop timestamp |
| Was it real, or a measurement artefact? | same query on **PTCL** and **Nayatel** | See below — this was the step that mattered |
| Why did they break? | `stat.ripe.net/data/rpki-validation` | Validated each block **against its true origin AS** → all 36 `invalid_asn`, deed naming AS3257 |
| Are they still announced? | `stat.ripe.net/data/announced-prefixes` | Yes — 39 still listed today |
| Who gets the traffic now? | `stat.ripe.net/data/looking-glass` | GTT's covering block carried by 332 peers, Cybernet's /24 by 20 |

### The control that changed the answer

The first pass showed Cybernet's blocks gaining **+2 observers** on average, which reads like an
improvement. Two unrelated ISPs, measured the same way:

| ISP | median change |
|---|---|
| PTCL | +2.0 |
| Nayatel | +2.0 |
| Cybernet | +2.0 |

**Everyone gained the same** — RIPE simply added observation points that fortnight. Nothing about
any network changed. Without the control we would have reported an improvement that did not exist,
and it also killed a separate theory about EFU Life gaining "+4 around 24 July".

---

## Open

- **Did GTT publish the deed on 31 July, or did a large network switch on checking that day?**
  Both look identical in our data. Needs the certificate's history from the RPKI archive.
- **Is Cybernet's use of the space legitimate?** A stale deed on properly leased space and an
  unauthorised announcement look the same from outside. A question for Cybernet, not for measurement.
- **Is anything actually hosted there?** We probed 25 addresses and got no reply — but that may be
  circular, since traffic now goes to GTT. Empty and misdirected look identical from here.

---

## Related

This investigation also turned up a **separate and more consequential finding** about Pakistani ISPs
using foreign address space internally, which corrects published census numbers:
**`address_squatting_detector_correction.md`**.
