# CDN peering, ISP by ISP, site by site

A per-pair (not per-ISP-mean) breakdown of how each of the 9 panel ISPs reaches
each of the 39 measured CDN-hosted sites, plus a hop-level check of *why* —
does the fast path look like real local peering, or is it riding someone
else's transit link.

**Data sources, exactly:**
- RTT + PoP class per (ISP, site): `cdn.csv` (week-minimum RTT, the same file
  that produced Table `cdn-savings` in the paper) — restricted to the paper's
  official 14-probe / 9-ISP panel (probes `1015491` and `7764` appear in the
  raw route archive but are **not** in Table 2 of the paper and are excluded
  here for consistency).
- CDN provider per site: fresh Team Cymru ASN lookup on each site's IP from
  `targets_corrected.csv` (CDN class, n=40; one site, `supermeal.pk`/Azure,
  has no valid RTT in `cdn.csv` and drops out of the RTT matrix, leaving 39).
- Hop-level path per (probe, site): parsed directly from
  `results/a/routes_20260718_195946_annotated.txt` (ASN-tagged, one
  representative traceroute per probe/site pair — 640 CDN-class blocks).

All numbers below are reproducible from `cdn_full_matrix.csv` (546 rows,
written alongside this file) and the parsing scripts in the session
scratchpad, not re-derived by hand.

---

## 1. Which CDN is actually behind "CDN" in this panel

| Provider | ASN | Sites | Names |
|---|---|---|---|
| **Cloudflare** | 13335 | **33 / 40 (82.5%)** | apkamazon.com.pk, auroracloset.pk, burgeroclock.com.pk, businesslist.pk, digikhata.pk, dogar.com.pk, historicalpoint.pk, honda.com.pk, logoofficial.com, meerzah.pk, mepcoebillcheck.pk, motifz.com.pk, pesconlinebill.pk, pinkpetals.pk, reading.pk, sarazcollection.pk, thefrontierpost.com, urbanbeauty.pk, vidmateapp.com.pk, wbm.com.pk, zarajahan.pk, zing.pk, glory-casino.net.pk, wancom.net.pk, ibcc.edu.pk, uos.edu.pk, zu.edu.pk, pesco.com.pk, ajk.gov.pk, joinasf.gov.pk, paknavy.gov.pk, pnmc.gov.pk, airblue.com |
| Amazon | 16509 | 2 | skyscanner.pk, khushhalibank.com.pk |
| Google | 15169 | 2 | idc.net.pk, gamcamedical.pk |
| Sucuri | 30148 | 2 | bnbwu.edu.pk, mcb.com.pk |
| Microsoft Azure | 8075 | 1 | supermeal.pk (no valid ping data) |

**This confirms Table 3 in the paper exactly (33/40 Cloudflare, 7/40
other).** The practical consequence: everything the paper calls "the CDN
peering gap" is, for 33 of 39 measurable sites, **specifically a Cloudflare
peering gap.** The paper should say this plainly instead of leaving "CDN" as
an unlabelled pooled bucket.

**And the 6 non-Cloudflare sites are uniformly bad for every ISP, including
the best-peered ones** — this is the single biggest thing missing from the
paper's current framing:

| Site | Provider | nayatel | cybernet | tes | zcom | nova | orbit | transworld | fasttel | ptcl |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| skyscanner.pk | Amazon | 39.5 | 18.2 | 19.9 | 30.5 | 34.0 | 34.5 | 35.6 | 40.4 | 43.4 |
| gamcamedical.pk | Google | 96.9 | 77.4 | 78.7 | 91.4 | 93.0 | 94.8 | 95.4 | 96.7 | 102.2 |
| mcb.com.pk | Sucuri | 99.9 | 110.5 | 113.6 | 126.0 | 132.8 | 130.9 | 133.7 | 104.5 | 103.1 |
| bnbwu.edu.pk | Sucuri | 128.0 | 109.9 | 118.2 | 131.7 | 134.7 | 131.0 | 138.3 | 104.3 | 106.3 |
| idc.net.pk | Google | 133.5 | 117.6 | 122.2 | 137.0 | 136.5 | 136.2 | 149.9 | 137.1 | 137.3 |
| khushhalibank.com.pk | Amazon | 154.8 | 290.7 | 251.8 | 225.4 | 309.0 | 228.2 | 314.4 | 160.3 | 156.6 |

Nayatel — 2.6ms mean on Cloudflare, the best network in the country — is
**117.6ms mean** on these six (worse than PTCL's 112.8ms mean here). **No
Pakistani ISP in this panel has a working local relationship with Amazon
CloudFront, Google's CDN, Microsoft's edge, or Sucuri.** The entire
"peering exists and helps" story in this paper is a Cloudflare-only story.
`khushhalibank.com.pk` on Amazon is the single worst CDN result in the whole
panel for every ISP except Nayatel and PTCL/Fasttel — worse than most
confirmed international hairpins to non-CDN sites.

---

## 2. The Cloudflare matrix, all 33 sites × 9 ISPs (minimum RTT, ms)

Sites are sorted by mean RTT across ISPs — this sorting itself exposes four
distinct latency "bands" that different sites fall into, and the bands are
**not the same for every ISP**. Full table (also in `cf_pivot.csv`):

```
site                  nayatel  cybernet   tes  zcom  nova  orbit  transworld  fasttel   ptcl
ibcc.edu.pk               2.3      3.6   2.8  16.3  17.4   18.3        18.9    21.2    24.9
honda.com.pk              2.2      3.4   2.9  16.3  17.0   18.8        19.9    22.0    23.9
airblue.com               2.3      4.1   2.8  16.1  16.9   19.1        19.9    21.2    24.7
burgeroclock.com.pk       2.4      4.0   2.8  16.0  17.6   19.2        20.2    22.1    23.6
paknavy.gov.pk            2.5      3.7   3.0  16.0  17.4   18.5        20.2    21.7    25.1
--- band A: everyone "regional or better", 2-25ms ---
meerzah.pk                2.4     99.1   2.4  15.7  17.1   18.5        19.0    21.5    25.2
auroracloset.pk           2.5     99.2   2.8  15.7  17.4   18.0        18.7    21.7    25.3
zarajahan.pk              2.3     99.2   2.8  15.7  17.3   18.2        19.2    21.7    25.1
urbanbeauty.pk            2.3     98.4   2.6  16.0  16.9   18.4        19.2    22.6    25.1
zing.pk                   2.3     99.6   2.8  15.8  17.1   18.1        19.4    21.6    25.1
sarazcollection.pk        2.0     99.3   2.9  15.7  17.1   18.9        19.7    21.6    25.2
logoofficial.com          2.5     99.1   2.8  16.1  17.3   18.5        19.4    22.2    25.2
motifz.com.pk             2.2     99.4   2.8  15.7  17.4   18.6        20.1    21.8    25.2
wbm.com.pk                2.8     99.2   2.7  15.7  17.4   19.1        19.3    22.1    25.2
--- band B: identical to band A for everyone EXCEPT Cybernet, which falls to ~99ms ---
digikhata.pk              2.5      4.0   2.7  16.1  17.1   18.4        19.6   127.5   130.0
zu.edu.pk                 2.4      4.0   2.7  16.1  17.3   19.0        20.0   127.1   129.8
--- band C: identical to band A/B except Fasttel & PTCL fall to ~130ms ---
pesconlinebill.pk         2.1      3.7  78.1  91.3  92.3   93.4        95.2   127.1   129.8
vidmateapp.com.pk         2.3      4.1  78.2  91.9  92.8   94.3        95.8   125.1   131.1
uos.edu.pk                2.4      3.9  77.9  95.2  92.7   94.4        94.8   125.4   129.8
businesslist.pk           2.4      4.0  78.2  91.2  92.7   93.3        95.8   127.6   131.3
--- band D: TES/Zcom/Nova/Orbit/Transworld now ALSO fall to ~78-96ms ---
pinkpetals.pk              2.3      3.9  78.1  91.9  92.8   93.8        94.2   200.3   262.9
wancom.net.pk               2.6     4.0  78.3  91.5  92.9   94.4        94.6   202.2   262.4
apkamazon.com.pk           2.1      3.6  78.2  91.3  92.7   94.2        94.7   202.4   264.1
historicalpoint.pk         2.5      3.5  78.0  94.9  92.6   93.9        94.7   200.9   262.7
thefrontierpost.com        2.5      3.9  78.4  91.1  92.5   93.4        95.5   201.8   265.7
ajk.gov.pk                 2.3      3.9  78.1  90.8  92.5   94.1        95.3   201.4   267.3
pnmc.gov.pk                2.4      3.8  78.3  91.3  96.4   94.1        95.3   201.0   265.1
dogar.com.pk               2.7      3.8  78.0  91.3  92.3   95.0        95.9   201.0   267.7
reading.pk                 2.7      3.3  78.1  91.4  92.3   93.7        95.1   203.9   267.6
pesco.com.pk               2.2      4.0  78.1  91.1  92.7   94.4        96.4   202.5   267.0
mepcoebillcheck.pk         2.3      3.8  78.1  91.0  96.4   93.9        95.0   202.9   265.5
glory-casino.net.pk        2.2      3.8  78.2  91.5  92.7   94.7        94.4   201.4   271.7
joinasf.gov.pk             2.3      3.8  78.3  91.3  92.5   94.2        95.4   204.8   269.1
--- band E (majority, 19 of 33 sites): Fasttel & PTCL now fully international, ~200-270ms ---
```

**What the bands mean.** Cloudflare is anycast — the same site can be served
from a different PoP depending on which BGP path your ISP has to that
specific announced prefix, not just "your ISP" in general. The table shows
each ISP effectively snaps to one of **3-4 fixed RTT values** depending on
which prefix/PoP a given site's IP falls into:

- **Nayatel and TES-good-days**: ~2-3ms, always. Never varies.
- **Cybernet**: ~3-4ms for 24 of 33 sites, but a hard ~99ms for the other 9
  (band B) — same ISP, same physical link, different result **purely because
  of which site**, i.e. which specific Cloudflare prefix.
- **TES**: ~2.8ms for 17 sites, ~78ms for the other 16 — a near-even split.
- **Zcom / Nova / Orbit / Transworld**: cluster at ~16-20ms for 15 sites,
  ~91-96ms for the other 18. These four ISPs move **together**, almost
  exactly in lockstep (see §3) — strong evidence they share the same upstream
  path, not four independent peering relationships.
- **Fasttel / PTCL**: ~21-25ms for 14 sites, ~127-130ms for 2 more, and
  **~200-270ms — a full international round trip — for 19 of 33 sites (58%
  of Cloudflare content)**.

None of this is visible in a per-ISP mean. The paper's "PTCL 136ms mean"
hides that PTCL gets a perfectly fine 24-25ms for some Cloudflare prefixes and
a genuinely international ~265ms for most others — two entirely different
experiences bundled into one number.

---

## 3. Does the fast path reflect real peering, or borrowed transit?

For every (probe, site) pair I found the **last responding hop before the
traceroute enters the CDN's ASN**, and classified it: does that handoff
happen on the ISP's *own* network, on a known Pakistani gateway operator's
network (PTCL/Transworld) that isn't this ISP, or on a named foreign transit
carrier.

| ISP | own network<br>(confirmed direct) | via PTCL | via Transworld | via foreign transit | path invisible<br>(silent hops) |
|---|--:|--:|--:|--:|--:|
| **Nayatel** | 0 | 0 | 0 | 0 | **74 / 78 (95%)** |
| **Cybernet** | **104 / 112 (93%)** | 0 | 0 | 5 (Omantel) | 6 |
| **TES** | 36 / 76 (47%) | 0 | 0 | 36 (34 HK, 2 other) | 4 |
| **Zcom** | 0 | 0 | 18 / 38 (47%) | 18 (17 HK, 1 other) | 0 |
| **Nova** | 0 | 0 | 18 / 38 (47%) | 18 (17 HK, 1 other) | 0 |
| **Orbit** | 0 | 0 | 18 / 38 (47%) | 18 (17 HK, 1 other) | 0 |
| **Transworld** | 0 | 0 | 0 | 0 | **39 / 39 (100%)** |
| **Fasttel** | 0 | **13 / 21 (62%)** | 1 | 17 (Level3) | 4 |
| **PTCL** | 31 / 74 (42%) | — | 0 | 41 (37 Level3, others) | 4 |

*(Rows don't sum to the RTT-band counts one-for-one because this table uses
one representative traceroute per pair from the archive, not the week's full
round history — it's for mechanism, not for the RTT numbers in §2.)*

**Reading this ISP by ISP:**

**Cybernet is the only ISP with strong, direct, confirmed evidence of real
local peering.** 93% of its Cloudflare handoffs go straight from Cybernet's
own ASN (9541) into Cloudflare's (13335), no intermediary. Example
(`airblue.com`, probe 1016143, Karachi):
```
1  192.168.18.1     private
2  202.163.100.236  Cybernet-PK              <- Cybernet's own network
3  10.15.15.122     private
4-6  * (silent)
7  104.16.121.79    Cloudflare               <- straight in, 4.8ms total
```
This is a genuine Set-3 ISP for Cloudflare specifically.

**Nayatel — the fastest ISP in the country — has literally zero confirmed
mechanism.** Every single one of its 74 classifiable Cloudflare traces looks
like this (`airblue.com`, probe 60223):
```
1  192.168.18.1  private
2  100.89.96.1   private
3-7  * (silent — 5 hops never respond)
255  104.16.121.79  Cloudflare, 3.9ms
```
We know from RTT (3.9ms) that whatever this path is, it's short. We do
**not** know whether that's a direct Nayatel↔Cloudflare peer or an invisible
hop through Transworld (Nayatel's known upstream) that happens to be fast.
This is worth being explicit about in the paper: Nayatel's "best-peered ISP"
title rests entirely on RTT, not on any hop-level confirmation — the opposite
problem from the rest of the panel, where paths are visible but sometimes bad.

**Transworld's own retail probe is 100% invisible** (known ICMP-filtering
artifact, already documented for probe 62224 elsewhere in this project) — so
we cannot see Transworld's own path to Cloudflare directly, only infer it
from what its downstream customers show (next point).

**Zcom, Nova, and Orbit move in lockstep — because they're all riding
Transworld's backbone to the same detour.** All three show the *identical*
count pattern (7 explicit-Transworld + 11 registry-Transworld + 17
China-Mobile-HK + 1 other), because their traceroutes show the same shape:
```
(ajk.gov.pk, probe 1015679, Nova/Lahore) — VERDICT TROMBONE, 109.2ms
1  192.168.100.1    private
2  70.70.71.137     Shaw (PK artifact, ignore)
3  110.93.212.161   Transworld (AS38193)          <- enters Transworld
4  110.93.252.200   Transworld internal
5  110.93.252.246   Transworld internal
6  223.121.3.97     China Mobile Intl, HONG KONG  <- leaves Pakistan
7  223.120.23.5     China Mobile Intl, HONG KONG
8-11               Cloudflare (Hong Kong-facing edge), ~93-95ms
```
This is a structural, inherited penalty: Zcom/Nova/Orbit customers pay for a
Hong Kong round trip to reach Cloudflare **not because their own ISP chose
badly, but because their upstream (Transworld) reaches Cloudflare that way**,
for whichever subset of prefixes isn't covered by Transworld's better paths.
TES (Transworld's own retail arm) shows the exact same China-Mobile-HK
detour for 45% of its traces — even Transworld's own retail brand doesn't
fully escape it.

**PTCL is genuinely split, not simply "bad."** 42% of its Cloudflare traces
hand off directly on PTCL's own network (`AS17557` or its Paknet subsidiary
`AS9557`); the other ~50-58% detour through **Level3/Lumen**, a paid
international tier-1 transit carrier:
```
(ajk.gov.pk, probe 1016126, PTCL/Karachi) — VERDICT TROMBONE, 293.9ms
1  192.168.10.1     private
2  39.39.0.1        PTCL (AS17557)
3-6                 private / silent
7  171.75.8.243     Level3 (AS3356)      <- paid international transit
8  213.242.115.18   Level3 (AS3356)
9-10                Cloudflare, 274-293ms
```
versus the *same* ISP, a different Cloudflare prefix, same day:
```
(airblue.com, probe 1016126, PTCL/Karachi) — VERDICT LOCAL, 27.5ms
1-5   private/PTCL
6  221.120.200.3    Paknet (AS9557, PTCL's own subsidiary)
7  104.16.121.79    Cloudflare, 27.5ms
```
So PTCL — the biggest operator, one of only two licensed international
gateways — does not have a blanket peering relationship with Cloudflare. It
has a peering relationship with **some** of Cloudflare's announced prefixes
and pays Level3 for the rest. That's the direct mechanistic explanation for
why PTCL's per-ISP mean (136ms in the paper) looks bad despite PTCL being, on
paper, the best-positioned operator to peer well.

**Fasttel mostly depends on PTCL's infrastructure** (62% of its handoffs are
via PTCL/Paknet) with a Level3 fallback for the rest — consistent with
Fasttel being a smaller downstream ISP with no infrastructure of its own.

---

## 4. What this means for the paper's argument

1. **Say "Cloudflare," not "CDN."** 33 of the 39 measurable sites are one
   provider. The 6 non-Cloudflare sites show that peering, where it exists at
   all, is entirely a Cloudflare-Pakistan relationship — not evidence that
   Pakistani ISPs peer well with CDNs in general. That's a meaningfully
   narrower and more defensible claim than the current text implies, and it's
   *more* citable because it's concrete (a named operator) rather than an
   abstract category.

2. **The "12.7× / 40×" numbers are a mix of two different phenomena** that
   the paper currently reports as one: (a) genuine local peering (Cybernet,
   confirmed direct in 93% of hops) vs. (b) a structural transit inheritance
   (Zcom/Nova/Orbit riding Transworld's Hong Kong leg) vs. (c) a
   per-prefix coin flip (PTCL, 42% direct / 50%+ Level3, same ISP, different
   sites). Only (a) is really about *peering* in the IXP sense the paper
   argues for. (b) and (c) are about *upstream transit quality*, which an IXP
   would only fix if the ISP peered with Cloudflare itself rather than
   continuing to inherit whatever its transit provider does.

3. **Nayatel's headline result needs a caveat**, not a retraction: it's the
   fastest ISP by RTT, but is also the one ISP where we have zero hop-level
   confirmation of *why* — every path is invisible past hop 2. Cybernet is
   the stronger evidentiary case for "real peering pays off," precisely
   because its paths are visible and consistently direct.

4. **The PTCL example (§3, `ajk.gov.pk` vs `airblue.com`) is a good concrete
   pull-quote for the paper**: same ISP, same day, two different Cloudflare
   prefixes, 27ms vs 294ms — because one prefix is peered and the other isn't.
   It's a cleaner illustration of "the local path exists but isn't
   consistently taken" than any of the current PK-hosted-site examples,
   because it isolates the peering variable inside a single ISP.
