> **RETIRED 2026-09-08.** The control plane holds no observation to compare against for
> this question: 0 of 364 collector paths to a Pakistani block contain any Pakistani vantage
> AS, and 1 of 3,352 collector sessions worldwide is Pakistani. See `RETIRED.md`. The text
> below is kept as the original design record only.

# 15.3 — Comparison: does BGP predict what the packets do?

**Asks:** where do the control plane (15.2) and the data plane (15.1) agree, and what does each kind
of disagreement mean?
**Method:** a join, a confusion matrix, and case analysis of the off-diagonal.
**Status:** designed, unrun.

---

## 1. Why this is the interesting sub-experiment

15.1 and 15.2 answer the same question with different instruments. Agreement is reassuring but
uninformative. **The off-diagonal cells are where the findings are**, because each implies a
specific mechanism neither experiment could identify alone.

## 2. The join

Key: **(vantage AS, block)**. 15.1 produces a verdict per target address; collapse to a per-block
verdict as **all-local / split / all-detour** — three-way, never binary, because 20% of blocks are
internally split (`../SAMPLING_METHOD.md` §5.5).

| | **15.2 predicts domestic** | **15.2 predicts foreign** | **no observed path exists** |
|---|---|---|---|
| **15.1 observes local** | ✅ agree — routing works as advertised | **Cell B** | **Cell S** |
| **15.1 observes detour** | **Cell A** | ✅ agree — the detour was predictable from BGP | **Cell S** |

**Cell S is mandatory, not optional.** It is not that 15.2 produces nothing — 15.2 *models* a path
from CAIDA relationships, so it will usually emit something. It is that **no collector anywhere
observed a path from this vantage AS to this block**, so the prediction rests entirely on inferred
relationships with no observation behind them. 15.2 must therefore carry a
`path_observed: true|false` flag alongside every prediction, and 15.3 must report the two
populations separately. Folding unobserved predictions into the agreement rate credits the model for
cases nothing ever checked.

## 3. What each disagreement means

**Cell A — BGP says domestic, packets leave.** A domestic path was available and not taken, or the
"domestic" path is domestic only in AS terms. Candidate mechanisms:

- intra-AS traffic engineering, or an MPLS tunnel that exits and re-enters
- a transit provider hauling traffic to a foreign exchange despite holding a domestic customer route
- CAIDA mis-inferring a relationship that does not actually carry this traffic

This is the **policy-failure** cell: the capability existed and went unused. It is the strongest
evidence a national-IXP argument can have.

**Cell S — no observed path.** The vantage AS appears in no collector path to the block. 15.2's
Gao–Rexford model will still emit a verdict, but nothing observed supports it, and the CAIDA
relationships it runs on are weakest exactly here — small PK ASes with few observed paths.
**This is expected to be the common case for Pakistan-to-Pakistan routes, not an edge case.** Of 3,352 collector sessions worldwide (RIS 1,434 + RouteViews 1,918)
exactly one is Pakistani — PTCL at rrc26 — and it feeds only its own cone. Domestic Pakistani
routing is therefore largely absent from the public control plane.

*Worked case:* EFU Life (`04_efu_life_routing_change.md` (working notes, outside this repository)). Every Pakistani vantage
AS appears in **0 of 364** collector paths to `103.154.196.0/23`, while traceroute showed a
6,000 km detour through Equinix Singapore and later its removal — a 4–7× latency change with no
control-plane trace before or after.

**Report Cell S separately and never fold it into agreement.** The headline number it produces is
its own result: *what fraction of domestic Pakistani routing is public BGP simply unable to
describe?*

**Cell B — BGP says foreign, packets stay home.** There is an interconnect the public control plane
cannot see — almost always a **private interconnect (PNI)** or unannounced local peering. This is
the **hidden-domestic-infrastructure** cell, and it is exactly the mechanism
the `IXP_simulation/` working directory (outside this repository) §8 concluded is operating for Cloudflare and Tencent in Pakistan: real
in-country presence, privately arranged, invisible from outside.

## 4. Metrics to report

- **Agreement rate**, overall and per vantage AS — computed over Cell S-excluded pairs only, with
  the excluded count stated alongside.
- **Cohen's κ** rather than raw agreement — the classes are heavily imbalanced (~85% local), so raw
  agreement flatters any predictor that guesses "local".
- **Cell S rate** — the share of (vantage, block) pairs with **no observed** collector path. Report
  before any agreement statistic, since it bounds what the comparison can actually cover. Report
  agreement within Cell S too, but always labelled as model-vs-data with no observation behind the
  model.
- **Cell A and Cell B rates per destination ISP** — which operators are policy failures, and which
  have invisible private paths.
- **Predictive value:** if you only had BGP, how wrong would your national detour estimate be? That
  number is the argument for why active measurement is necessary at all — and it is a publishable
  result whichever way it comes out.

## 5. Hazards

- **Time alignment.** RIB dumps, CAIDA snapshot and the traceroute run must cover the same window.
  Comparing a June RIB to a September traceroute measures elapsed time, not mechanism.
- **Granularity mismatch.** 15.2 predicts per (vantage AS, block); 15.1 observes per target address.
  The three-way collapse is where information is lost — record how many blocks were split before
  collapsing, and never score a split block as clean agreement.
- **`unknown` is not `domestic`.** Blocks 15.2 could not resolve are excluded from the matrix and
  counted separately.

## 6. Outputs

```
results/
├─ joined.csv          (vantage AS, block) → predicted, observed, agreement class
├─ confusion.csv       the 2×2 plus unknown/split columns, overall and per vantage
├─ cell_a_cases.md     walked-through traceroutes for the policy-failure cell
└─ cell_b_cases.md     walked-through traceroutes for the hidden-interconnect cell
```

## 7. Exit criteria

- Every (vantage AS, block) pair classified, or explicitly excluded with a reason.
- At least five worked cases each for Cell A and Cell B, with the raw traces quoted in full.
- A one-line answer to: *could this study have been done with BGP alone?*
