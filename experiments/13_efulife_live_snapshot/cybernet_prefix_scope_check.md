# Is EFU Life's missing domestic peering unique to EFU Life, or a Cybernet-wide pattern?

**Question:** were other Cybernet-hosted prefixes affected the same way as EFU Life's, or
is the "reachable only via GSL Singapore + Zain Omantel, no domestic peer" pattern
specific to EFU Life's own customer block?

**Note on scope first:** EFU Life is not technically "a Cybernet prefix." It has its own
ASN (141008) and announces its own block (`103.154.196.0/23`), with Cybernet (9541) only
listed as its transit provider. The 957 prefixes Cybernet announces directly (origin
AS9541, `announced-prefixes` for AS9541) are a different category, addresses for
regular customers who don't have their own ASN. Checking those is the right test for
"is this Cybernet-wide."

## Method

Picked 5 of Cybernet's 957 announced prefixes (not exhaustive, a spot check): its own
core infrastructure block (`124.29.240.0/24`, which contains `124.29.240.218`, the exact
router IP every single traceroute in this investigation passes through immediately
before reaching a Cybernet-hosted destination), plus four other customer-looking blocks
(`175.107.204.0/24`, `153.117.0.0/16`, `202.163.120.0/24`, `61.5.128.0/24`). For each,
pulled every AS-path currently visible via RIPEstat's `looking-glass` (RIS-backed) and
checked which AS sits immediately upstream of 9541.

## Result: split, not uniform

| Prefix | Peer-paths seen | Paths via a Pakistani ISP directly |
|---|--:|--:|
| `124.29.240.0/24` (Cybernet's own core block) | 295 | **0** |
| `175.107.204.0/24` | 289 | **0** |
| `153.117.0.0/16` | 252 | **0** |
| `202.163.120.0/24` | 295 | **74**, all via PTCL |
| `61.5.128.0/24` | 232 | **158**, all via PTCL (68% of paths) |

## Interpretation

Cybernet and PTCL have a real, substantial domestic BGP peering session, this isn't in
doubt, it dominates the routing for at least two of the five blocks checked. But that
session evidently doesn't carry Cybernet's entire address space. EFU Life's block shows
the identical pattern to three of Cybernet's own blocks (including Cybernet's own core
infrastructure prefix): zero domestic peers, 100% international transit via the same
Singapore/GSL + Oman/Omantel chain documented elsewhere in this investigation.

So this is not an EFU-Life-specific problem, and it's not a total absence of domestic
peering either. It looks like a **selective one**: some subset of Cybernet's announced
space rides the PTCL peering session, some subset doesn't, and EFU Life's customer block
falls on the "doesn't" side, along with Cybernet's own core block. Candidate reasons
(not verifiable from routing data alone, would need Cybernet's actual configuration or a
direct answer from them):

- A deliberate prefix-list filter on the Cybernet-PTCL session, only specific blocks
  allowed through, rather than a full routing-table exchange.
- A commercial/tier distinction, e.g. hosted or enterprise customer blocks (EFU Life's
  category) handled under a different arrangement than regular broadband address space.
- Organic/historical inconsistency, blocks added to the domestic peering's allow-list at
  different times by different engineers, with no one going back to reconcile the rest.

## Caveats

- 5 of 957 prefixes is a spot check, not a census. The 3:2 split found here shouldn't be
  read as "60% of Cybernet's space lacks domestic peering", a larger, randomly-sampled
  check would be needed to put a real number on that.
- This only tests the AS9541-PTCL(17557) pair specifically, since that's the only
  Pakistani ASN that showed up at all across the sample. It doesn't rule out Cybernet
  having a similarly narrow/selective arrangement with some other Pakistani ISP not
  captured in this small sample.
- As elsewhere in this investigation, an AS-path in BGP is the *announced* route; it
  doesn't prove what fraction of actual customer traffic uses it vs. some other
  mechanism.
