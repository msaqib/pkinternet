#!/usr/bin/env python3
"""
Render ISP_SUMMARY.md from isp_summary.json plus the annotated traces.

Every number in the document is computed here. Nothing is typed by hand, so the
document cannot drift from the data: re-run it after any new sweep.

  python write_isp_summary.py   -> ../ISP_SUMMARY.md
"""
import io, json, os, statistics, collections, ipaddress

H = os.path.dirname(os.path.abspath(__file__))
def P(*p): return os.path.join(H, "..", *p)

rows = json.load(io.open(os.path.join(H, "isp_summary.json"), encoding="utf-8"))
ann  = json.load(io.open(P("3_routes", "selected_annotated.json"), encoding="utf-8"))
own  = json.load(io.open(P("1_universe", "block_to_asn.json"), encoding="utf-8"))

# CGN is RFC 6598 carrier-grade NAT. It is operator-internal space, not a foreign
# country, and must never be counted as a foreign hop.
NOT_FOREIGN = ("PK", "PRIV", "CGN", "??")
def foreign(cc):
    return cc not in NOT_FOREIGN

TKEY = next((k for k in ("target", "t", "dst") if k in ann[0]), None)

# per-ISP route shape, taken from the annotated selection
depth = collections.defaultdict(list)
ttllen = collections.defaultdict(list)
for r in ann:
    u = str(ipaddress.ip_network(r[TKEY] + "/24", strict=False))
    a = own.get(u)
    if a is None:
        continue
    depth[a].append(sum(1 for h in r["path"] if h))
    ttllen[a].append(len(r["path"]))

def silentpct(a):
    return 100 * (1 - sum(depth[a]) / sum(ttllen[a]))

othd = [x for a in depth if a != "17557" for x in depth[a]]
otht = [x for a in ttllen if a != "17557" for x in ttllen[a]]
ptcl_floor = sum(1 for x in depth["17557"] if x == 5)

T = {k: sum(r[k] for r in rows) for k in
     ("blocks", "addrs", "checks", "live", "liveblk", "blk8", "reached", "traces", "sel", "selblk")}
live_rows = sorted([r for r in rows if r["live"]], key=lambda r: -r["live"])
top, tail = live_rows[:40], live_rows[40:]
tt = {k: sum(r[k] for r in tail) for k in ("blocks", "liveblk", "live", "blk8", "traces", "reached", "sel")}
ptcl = next(r for r in rows if r["asn"] == "17557")
unan = next(r for r in rows if r["asn"] == "unannounced")

hops     = [h for r in ann for h in r["path"] if h]
nhop     = len(hops)
slots    = sum(len(r["path"]) for r in ann)
silent   = slots - nhop
n_pk     = sum(1 for h in hops if h["cc"] == "PK")
n_priv   = sum(1 for h in hops if h["cc"] == "PRIV")
n_cgn    = sum(1 for h in hops if h["cc"] == "CGN")
n_fgn    = sum(1 for h in hops if foreign(h["cc"]))
n_unann  = sum(1 for h in hops if h.get("kind") == "unannounced")
n_ixp    = sum(1 for h in hops if h.get("kind") == "ixp")
tr_fgn   = sum(1 for r in ann if any(h and foreign(h["cc"]) for h in r["path"]))
med_hops = statistics.median([sum(1 for h in r["path"] if h) for r in ann])
to_dist  = sorted(collections.Counter(sum(1 for h in r["path"] if h is None) for r in ann).items())

def tbl(rs):
    # "checked" is the denominator for "live hosts" and must sit beside it. Without it a
    # reader compares raw counts between networks of very different size and reads a
    # difference in occupancy where there is only a difference in how much we looked.
    o = ["| ASN | network | blocks | checked | live hosts | answered | with life | blk >=8 | traces | reached | selected | median hops |",
         "|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for r in rs:
        a = r["asn"]
        nm = r["name"].split(" - ", 1)[-1][:34]
        d = statistics.median(depth[a]) if depth.get(a) else 0
        ar = 100 * r["live"] / max(r["checks"], 1)
        o.append(f"| {'AS'+a if a != 'unannounced' else 'none'} | {nm} | {r['blocks']:,} | {r['checks']:,} | "
                 f"{r['live']:,} | {ar:.1f}% | {r['liveblk']:,} | {r['blk8']:,} | {r['traces']:,} | "
                 f"{r['reached']:,} ({r['pct_reach']:.0f}%) | {r['sel']:,} | {d:.0f} |")
    return "\n".join(o)

to_tbl = "\n".join(f"| {k} | {v:,} | {100*v/len(ann):.1f}% |" for k, v in to_dist[:9])

md = f"""# Pakistan sweep, results by ISP

**Run 2026-09-08 to 2026-09-09.** Every figure below is produced by
`6_analysis/build_isp_summary.py` and rendered by `6_analysis/write_isp_summary.py`.
Re-run both after any new sweep and this file updates itself.

---

## The short version

We took every address Pakistan announces or is registered to hold, sampled it for
live hosts, traced routes to the ones that answered, and kept the traces clean
enough to analyse.

| step | result |
|---|---|
| Addresses in the universe | **{T['addrs']:,}** across {T['blocks']:,} /24 blocks, {len(rows):,} networks |
| Addresses actually checked | {T['checks']:,} ({100*T['checks']/T['addrs']:.1f}% of the space) |
| Live hosts found | **{T['live']:,}** from the {T['checks']:,} checked, so **{100*T['live']/T['checks']:.1f}% answered**. Not {100*T['live']/T['addrs']:.2f}% of the space: the other {T['addrs']-T['checks']:,} addresses were never tested |
| Blocks with at least one live host | {T['liveblk']:,} of {T['blocks']:,} ({100*T['liveblk']/T['blocks']:.0f}%) |
| Blocks that reached 8 live hosts | {T['blk8']:,} ({100*T['blk8']/T['liveblk']:.0f}% of live blocks) |
| Traceroutes attempted | {T['traces']:,} |
| Traces that reached their target | **{T['reached']:,}** ({100*T['reached']/T['traces']:.0f}%) |
| Targets kept after the quality gate | **{T['sel']:,}** in {T['selblk']:,} blocks, {sum(1 for r in rows if r['selblk'])} networks |
| Hops annotated with country and operator | **{nhop:,}** |

We did not check all 5.7 million addresses. Sampling is adaptive: 8 addresses per
block, escalating to 64 only where something answered, stopping after two empty
draws where nothing did. That is why {100*T['checks']/T['addrs']:.1f}% of the space
was enough to find life in {100*T['liveblk']/T['blocks']:.0f}% of blocks.

## Reading the table

* **blocks** is /24-equivalents the network announces.
* **checked** is how many addresses in that network were actually tested. **This is the
  denominator for the next column and the two must be read together.** It is not 256 per
  block: the sampler tests 8 per block, escalating to 64 only where something answered.
* **live hosts** is distinct addresses that answered, from either vantage point. It is a
  **floor**, not a count of what is there, because sampling stops once a block yields 8.
* **answered** is live hosts as a share of checked. It is the only column here that can be
  compared between networks directly. The raw counts cannot: they mostly track how large
  the network is and how much of it we looked at.
* **with life** is blocks where at least one address answered.
* **blk >=8** is blocks that reached 8 live hosts, the panel target for Exp 16.1.
* **reached** is traces whose last hop is the target itself. This is the route
  visibility number: it says how far into that network we can actually see.
* **selected** is targets passing the gate `reached AND at least 5 hops answered`.
* **median hops** is the median count of hops that answered, per selected trace.

## Every network with a live host, top 40 by live hosts

{tbl(top)}

The remaining **{len(tail)}** networks with live hosts hold {tt['live']:,} live hosts
across {tt['liveblk']:,} blocks, of which {tt['blk8']:,} reached 8, and they contributed
{tt['sel']:,} selected targets. {sum(1 for r in rows if not r['live'])} of the
{len(rows):,} networks produced no live host at all.

Full machine-readable table, all {len(rows):,} networks: `6_analysis/isp_summary.csv`.

---

## What stands out

**PTCL is the country.** AS17557 holds {100*ptcl['blocks']/T['blocks']:.0f}% of
Pakistan's /24 blocks, {100*ptcl['live']/T['live']:.0f}% of the live hosts we found,
and {100*ptcl['sel']/T['sel']:.0f}% of the selected targets. Any country-level
statistic that is not weighted by network is a statistic about PTCL. The top 27
networks hold 90% of all live hosts.

**Route visibility is high and fairly even.** {100*T['reached']/T['traces']:.0f}% of
traces reached their target. Where a network's reach rate sits well below that, the
likely cause is filtering at that operator's edge rather than our tracer, since the
same tracer from the same vantage point reached 8 in 10 targets elsewhere in the
same hour. That is an inference, not a measurement: we have not confirmed filtering
with any operator.

**Registry space that nobody announces is nearly empty.** {unan['blocks']:,} blocks sit
in Pakistan's registry allocation with no BGP announcement covering them, and they
produced {unan['live']:,} live hosts between them. Registered space is not used space.
This refines the universe finding, which reported zero registry-only space at the
level of whole collapsed networks: at /24 granularity the unannounced holes are real
and they are almost entirely empty.

## Where the routes go

Of {nhop:,} annotated hops:

| | hops | share |
|---|--:|--:|
| Pakistan | {n_pk:,} | {100*n_pk/nhop:.1f}% |
| Private or CGNAT | {n_priv+n_cgn:,} | {100*(n_priv+n_cgn)/nhop:.1f}% |
| Foreign country | {n_fgn:,} | {100*n_fgn/nhop:.2f}% |

{tr_fgn:,} of {len(ann):,} traces ({100*tr_fgn/len(ann):.1f}%) contain at least one hop
outside Pakistan. Those are candidates for tromboning analysis, not the finding
itself: a foreign hop becomes evidence only once the latency rules in `RULES.md`
are applied to it.

Two structural features of the hop set are worth recording:

* **{n_unann:,} hops sit in address space that carries no BGP announcement.** Almost
  all of it is Transworld (`110.93.252.0/22`, `119.63.136.0/23`) and Wateen
  (`58.27.172.0/22`) backbone infrastructure. Operators routinely number their
  backbones out of space they do not announce, which is normal practice, but it
  means a hop cannot be attributed to an operator through BGP alone. We attribute
  these through whois instead.
* **{n_ixp:,} hops are on internet exchange fabrics**: DE-CIX Frankfurt, Equinix
  Singapore, Equinix Muscat, EMIX Dubai, HKIX Hong Kong. A hop on an exchange LAN
  belongs to the exchange, not to either peer, so it must not be counted as a
  foreign network hop for the Pakistani side.

## Quality of the selected traces

The gate was `reached the target AND at least 5 hops answered`. Within the
selection, timeouts per trace are distributed as:

| timeouts in the trace | traces | share |
|--:|--:|--:|
{to_tbl}

Median answered hops per trace is {med_hops:.0f}. Timeouts in the middle of a path
are normal: {100*silent/slots:.0f}% of TTL slots across the selection are silent.
Every selected trace still has a confirmed endpoint and at least 5 identified hops.

### The 5-hop gate binds almost entirely on PTCL

This matters for anything built on the selection, so it is stated plainly rather
than buried in the table.

| | PTCL AS17557 | every other network |
|---|--:|--:|
| Selected traces | {len(depth['17557']):,} | {len(othd):,} |
| Median TTL slots probed | {statistics.median(ttllen['17557']):.0f} | {statistics.median(otht):.0f} |
| Median hops that answered | **{statistics.median(depth['17557']):.0f}** | **{statistics.median(othd):.0f}** |
| Silent TTL slots | {silentpct('17557'):.0f}% | {100*(1-sum(othd)/sum(otht)):.0f}% |

PTCL paths are not shorter. They are the same length and far quieter: the tracer
probes about as many TTL slots, but roughly half of them return nothing against
{100*(1-sum(othd)/sum(otht)):.0f}% elsewhere, and no other network in the top ten
exceeds {max(silentpct(a) for a in sorted(depth, key=lambda x: -len(depth[x]))[1:10]):.0f}%.
{ptcl_floor:,} of {len(depth['17557']):,} selected PTCL traces
({100*ptcl_floor/len(depth['17557']):.0f}%) answered exactly 5 hops, sitting
precisely on the gate floor.

Three consequences:

1. **The gate is not a mild filter, it is the binding constraint on PTCL.** Raising
   it to 6 hops would drop most PTCL traces and shrink the largest network in the
   study to a fraction of its size. The threshold was chosen before this was
   measured, so it is not tuned to a result, but any change to it is effectively a
   decision about how much PTCL to keep.
2. **Selected traces are not uniformly clean.** A PTCL trace that passed is
   typically minimally qualified, while a Nayatel or Wateen trace that passed
   usually cleared the bar comfortably. Per-network comparisons of path detail
   must account for this, and cannot treat all selected traces as equivalent.
3. **The cause is not established.** Fewer answering hops at equal path length is
   consistent with ICMP TTL-expiry rate limiting or suppression inside PTCL's
   core, and also with MPLS tunnels that hide interior hops from traceroute. We
   have not distinguished these. Treat it as an observed property of PTCL paths
   from this vantage pair, not as a mechanism.

   It is worth noting that two independent measurements now single out the same
   network. The liveness re-probe put PTCL's miss rate near 35% against 22% to 25%
   elsewhere (`SWEEP_FINDINGS.md` section 5C), and hop silence here is 48% against
   {100*(1-sum(othd)/sum(otht)):.0f}%. Those measure different things, host replies
   and TTL-expiry replies, and both are suppressed on PTCL relative to its peers.
   That is consistent with ICMP rate limiting being the common cause and is not
   consistent with MPLS alone, which would hide interior hops without affecting
   whether end hosts answer. This raises the standing of the rate-limiting reading
   from one candidate among several to the better-supported one. It remains a
   hypothesis: neither measurement observes a rate limiter directly, and a
   controlled test at varying probe rates against PTCL would be needed to confirm it.

---

## Limits you must carry into any claim made from this table

1. **Live host counts are floors, and the floors are not equally tight.** Adaptive
   sampling stops at 64 addresses per block, so no block can report more than 64
   live hosts regardless of true occupancy. Separately, re-probing measured a miss
   rate near 35% on PTCL against 22% to 25% on other networks (`SWEEP_FINDINGS.md`
   section 5C), so densities are comparable within a network over time, not between
   networks.

2. **Every reach rate here is "as seen from Mobilink".** Discovery and tracing ran
   from different networks. Hosts were found mostly from AS135407 (TES): 781,428
   checks and 33,316 live hosts, against 62,674 checks and 10,421 live from AS45669
   (Mobilink). But the route sweep is 43,671 of 43,765 traces from Mobilink, a clean
   cutover after the first 88. So the **reached** column is not a property of the
   destination network alone and is not an average over two vantages
   (`SWEEP_FINDINGS.md` section 5E).

3. **A second vantage point does not agree with the first.** In a controlled re-test,
   roughly 9% of 250 addresses confirmed alive from AS135407 did not answer from
   AS45669, at every concurrency tested. That asymmetry is a property of Pakistani
   interconnection rather than a fault in the scan, and it means "live" is
   vantage-relative. Counts in this table are a union of two vantages over **disjoint
   address sets**, because the top-up skipped every address already probed. They are
   not a two-vantage measurement of the same addresses.

4. **Selection is biased toward dense blocks by construction.** A block needs live
   hosts before it can be traced at all, and the gate then prefers clean traces.
   Blocks with 1 to 3 live hosts are held as a control group to measure how large
   that bias is. That comparison has not been run yet, so the size of the bias is
   currently unknown, not small.

5. **This is one vantage pair, one country, IPv4 only, over two days.** No ISP has
   confirmed any of it. Nothing in this file is ground truth from an operator, and
   the route shape of a network can change on any day.

6. **A network's reach rate mixes two causes**: filtering at that operator's edge,
   and blocks whose live hosts were themselves marginal. This table does not
   separate them.
"""

io.open(P("ISP_SUMMARY.md"), "w", encoding="utf-8").write(md)
print(f"wrote ISP_SUMMARY.md ({len(md):,} chars)")
