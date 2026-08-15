# Why some inconclusive rows are probably real hairpins

This file walks through one concrete example, the website fgeha.gov.pk (Federal
Government Employees Housing Authority), to show why a stricter detection rule
sometimes calls a real hairpin inconclusive, and how we can tell the difference
between a real hairpin with missing evidence and a genuinely unknown case.

## The two rules, quickly

Every traceroute round gets checked for two things: did any hop actually show a
foreign IP address, and did the total time to reach the site look too slow. The
current rule counts either one as a hairpin. A stricter rule only counts it if
a foreign IP was actually seen. If the foreign hop happens not to reply that
round, the strict rule calls the result inconclusive, even if the timing still
looks exactly like a hairpin.

## Being Cybernet hosted is not the same as staying in Pakistan

fgeha.gov.pk is registered on Cybernet's network, but that only tells us where
the origin server lives, not what the traffic passes through to get there.
This site sits behind Akamai's DDoS protection service, which runs out of
scrubbing centers abroad. Every visitor, on every ISP, has to bounce out to
Akamai first and then get forwarded back to the real Cybernet server. This is
the same pattern already documented in this project for moitt.gov.pk and
railways.gov.pk, both Cybernet hosted, both hairpinning through the same
Akamai service in the US. Hosting tells you where the server sits. It does not
tell you whether the path to reach it stays inside the country.

The physical route looks like this:

```
Pakistan probe
    |
Transworld backbone (Pakistan)
    |
Equinix, Singapore                <-- first foreign hop
    |
Akamai Prolexic, Netherlands      <-- still foreign
    |
Akamai Prolexic, United States    <-- still foreign
    |
back into Pakistan (NTC)
    |
Cybernet
    |
fgeha.gov.pk (the actual website)
```

That whole round trip, out to Singapore, over to Europe, across to the US, and
back, takes around 200 milliseconds. This matters because 200ms becomes the
fingerprint of this specific hairpin. Any round that ends around 200ms for this
same site is very likely the same trip, whether or not we got to see the
middle of it.

## How we know this is really Akamai's DDoS service, not just a name in a table

This is worth checking directly rather than trusting the hop name alone.

The ASN that shows up in the middle of the path, 32787, is registered in the
RIPE database as PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NETWORK, Akamai
Technologies, Inc. That is the network's own stated business purpose, not
something guessed from a hostname.

To make sure this was not just an artifact of the measurement window back in
July, a fresh traceroute to fgeha.gov.pk's address was run again just now,
months later, from a different vantage point entirely. It hit the exact same
addresses the panel data showed originally, the same Singapore hop, the same
Netherlands hop, the same US hop, at similarly high response times. So this is
a stable pattern that is still happening today, not a one time fluke.

One honest limit: the page itself does not carry any header that says Akamai
or Prolexic outright. Checking the live response shows only the origin
server's own headers, Microsoft IIS, WordPress, Plesk, nothing branded. That
is expected rather than suspicious, since Prolexic works as a network level
scrubbing tunnel rather than a reverse proxy, so it does not stamp the page the
way something like Cloudflare would. So what we have is strong circuit level
evidence, the network's own registered purpose plus a reproduced path, not a
first party statement from Akamai or FGEHA that scrubbing is active. Getting
that would mean asking FGEHA's own IT team directly.

## Same website, four probes that saw the whole path, three that did not

| Probe (ISP) | Middle of the path | Countries actually seen | Time to reach the site | Strict rule says | What the evidence supports |
|---|---|---|---|---|---|
| Nova | fully visible | Singapore, Netherlands, US | 207 ms | trombone | trombone |
| PTCL, Karachi | fully visible | Singapore, Netherlands, US | 201 ms | trombone | trombone |
| Z-Com | fully visible | Singapore, Netherlands, US | 194 ms | trombone | trombone |
| Orbit | fully visible | Singapore, Netherlands, US | 201 ms | trombone | trombone |
| Nayatel | went quiet for 5 hops, then the site answered | none | 212 ms | inconclusive | trombone |
| Cybernet, vantage 1 | went quiet for 5 hops, then the site answered | none | 212 ms | inconclusive | trombone |
| Cybernet, vantage 2 | went quiet for 6 hops, then the site answered | none | 220 ms | inconclusive | trombone |

The bottom three rows never show a foreign IP, so the strict rule marks them
inconclusive. But the time they took to get an answer, 212 to 220 milliseconds,
lands right on top of the confirmed rounds above them, 194 to 207 milliseconds.
A purely domestic Cybernet destination normally answers in under 45
milliseconds in this dataset. There is no domestic explanation for a 212
millisecond round trip to a Cybernet site. The simplest explanation is that
these three rows took the exact same international trip as the four rows
above them, and the routers in the middle just did not reply that particular
round, which is a common and unremarkable thing for routers to do.

## Checking whether Nayatel simply has a slow path to Cybernet in general

This is worth checking directly instead of assuming. There is a third
Cybernet hosted site in this dataset, cxtreme.pk, which has zero foreign hop
evidence anywhere across the entire week, on any probe. It is the cleanest
possible domestic Cybernet destination available for comparison.

| Site | Nayatel's typical time to reach it | Any foreign evidence anywhere for this site |
|---|---|---|
| cxtreme.pk | 25 ms | none, confirmed genuinely domestic |
| ztbl.com.pk | 213 ms | yes, confirmed foreign hop seen on other probes |
| fgeha.gov.pk | 214 ms | yes, confirmed foreign hop seen on other probes |

Nayatel reaches Cybernet in 25 milliseconds when the destination really is
domestic. It only jumps to over 200 milliseconds for the two sites that other
probes already prove go through Akamai abroad. So this is not a general
Nayatel to Cybernet slowness. It is specific to these two sites, which matches
the Akamai explanation above rather than a peering gap between the two ISPs.

## The strategy, in one sentence

For any inconclusive row, check whether some other probe, on some other round,
already proved this same website is a hairpin, and if so, check whether this
row's response time is close to that proven hairpin's response time. If both
are true, treat it as the same hairpin with missing middle evidence, not as an
unknown case.

## On Cybernet specifically

Cybernet's own path does show up clearly elsewhere. For a different site,
kknetworks.com.pk, a Cybernet probe shows the entire path, including the same
Singapore hop, in full:

```
Cybernet access
    |
Cybernet backbone (two domestic hops)
    |
Equinix, Singapore
    |
Transworld backbone
    |
Cogent, registered in the US but physically inside Pakistan
    |
kknetworks.com.pk
```

So Cybernet is fully capable of showing its foreign hops when the routers
along the way choose to answer. Its blank middle hops on fgeha.gov.pk are best
read as that specific round going quiet, not as Cybernet somehow hiding its
path in general.

## What this means for the numbers, roughly

This is one site out of many, so treat these as illustrative, not final.

- Strict rule alone: 5.1 percent of Pakistani site traces count as hairpins.
- Adding back rows like the three above, where the timing matches a proven
  hairpin for that same site: roughly 7.8 percent.
- The current rule, which also counts slow timing with no matching proof
  anywhere: 15.2 percent.

## Caveats, stated plainly

- This file shows one site in detail. The 7.8 percent figure comes from
  applying the same check across every site, not just this one.
- The check compares a row's time against the median time of confirmed
  hairpins for that same site. It is a reasonable heuristic, not a proven
  method, and has not been reviewed or adopted yet.
- Some inconclusive rows have no confirmed hairpin for that site anywhere in
  the data, cxtreme.pk is one example we checked in full. Those stay
  genuinely unknown, and this method correctly leaves them alone.
