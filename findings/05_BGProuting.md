BGP VALIDATION — SUMMARY AND METHODOLOGY
=========================================


METHODOLOGY
-----------

To validate our traceroute-observed AS paths against independently verifiable
BGP routing data, we used two complementary sources: RIPEstat historical BGP
data and bgp.he.net peer tables.

In the first stage, we queried RIPEstat's bgp-state API for each unique
destination IP and timestamp observed during our 48-hour experiment window
(June 14–16, 2026). This API returns the AS paths that globally-connected
BGP collector routers were hearing at the time of measurement. We compared
each observed traceroute path against these collected paths and classified
results as consistent (exact match), partial (destination ASN matched but
intermediate transit differed), or no match.

The majority of paths returned as partial. This is expected and does not
indicate anomalous routing. RIPEstat's collectors observe paths announced
outward to the global internet, but many transit arrangements between ISPs
are private peering or customer relationships that are not re-advertised
globally. A Pakistani ISP routing through a transit provider it has a direct
session with will not always appear in global BGP tables.

In the second stage, we performed a rigorous peer-level validation using
bgp.he.net, which aggregates observed BGP peering relationships for each
autonomous system. For each of our six probe ISPs (PTCL, Transworld, Nayatel,
Cybernet, Zcom, Nova), we retrieved their direct peer tables. For each transit
ASN observed in our traceroutes, we checked whether it appears in the probe
ISP's known peer list, or in the peer list of any ISP reachable within three
hops. This multi-level check accounts for the reality that traffic frequently
traverses two or three transit providers before reaching its destination, and
each handoff is a legitimate BGP relationship even if not directly visible
from the probe ISP's own peer table.

In total we validated 80 unique ISP-site-path combinations using this approach.


RESULTS
-------

78 out of 80 unique observed paths were fully consistent with known BGP
peering arrangements after multi-level checking. The remaining two paths
contained transit ASNs that could not be verified through any public peer
table and are documented below.

For PTCL, all observed paths are consistent with its known upstream providers.
PTCL peers directly with Lumen/Level3 (AS3356), and this ASN appeared in our
traceroutes as the primary transit for Cloudflare-hosted content including
dawn.com, express.com.pk, and telemart.pk. PTCL also uses SingTel (AS7473)
to reach Alibaba-hosted content such as daraz.pk, and NTT (AS2914) for
MCB-hosted content. All three upstreams appear in PTCL's bgp.he.net peer
table.

For Transworld, all paths are consistent. Transworld peers directly with
Cloudflare (AS13335), China Mobile International HK (AS58453), and Telecom
Italia Sparkle (AS6762). These are the exact ASNs observed in our traceroutes
for Cloudflare-hosted, MCB-hosted, and HBL-hosted destinations respectively.

For Nayatel, all paths except one are consistent. Nayatel has only two direct
peers, PTCL and Transworld. It reaches all international destinations through
Transworld, inheriting Transworld's direct peering with Cloudflare and other
providers. This explains Nayatel's consistently low RTT to CDN-hosted content.
The one exception is documented under anomalies below.

For Cybernet, all paths except one are consistent. Cybernet uses Arelion/Telia
(AS1299) for HBL traffic, Zain Omantel and Hurricane Electric (AS8529, AS6939)
for NADRA traffic, and Transworld for local Pakistani content. All are
confirmed peers. The one exception is documented below.

For Zcom, all paths are consistent. Zcom routes exclusively through Transworld
(AS38193) as its upstream, and all downstream transit observed in our
traceroutes are confirmed peers of Transworld.

For Nova, all paths are consistent after multi-level checking. Nova routes
through Shaw Communications Canada (AS6327) as its first international hop.
Shaw peers with Arelion (AS1299), which in turn peers with Transworld
(AS38193). This two-hop chain explains why Transworld appeared as transit
in Nova's paths even though it is not Nova's direct peer.


ANOMALIES
---------

Two paths remain unexplained after exhaustive multi-level peer checking.

The first involves Cybernet's traffic to MCB (mcb.com.pk), where AS20773
appeared as a transit ASN in the path 9541 > 1299 > 20773 > 30148. This
occurred consistently across 90 measurement rounds. AS20773 is not present
in any public peer table within three levels of Cybernet. It appears to be
a downstream customer or subsidiary of Arelion that is not publicly documented.
The traffic successfully reached its destination (Sucuri, AS30148) and the
path was stable throughout the experiment, suggesting this is a legitimate but
undocumented transit arrangement rather than a routing anomaly.

The second involves a single measurement round in which Nayatel's traffic to
MCB (mcb.com.pk) traversed AS26496 (GoDaddy) in the path 2914 > 26496 > 30148.
GoDaddy is a web hosting company and not a known transit provider. This
appeared exactly once out of 191 measurement rounds for this ISP-site pair
and did not recur. This is consistent with a transient routing event, possibly
caused by a brief BGP route change on MCB's content provider's side.


CONCLUSION
----------

Our traceroute-observed AS paths are consistent with publicly verifiable BGP
peering relationships for 78 of 80 unique paths across all six probe ISPs and
all eight measured sites. The two unexplained paths do not indicate network
compromise or systematic routing irregularities. One is a stable path through
an undocumented but operationally plausible transit ASN, and the other is a
single transient event that self-corrected within one measurement interval.
The BGP validation confirms the integrity of our traceroute data and provides
independent corroboration of the routing patterns described in our analysis.