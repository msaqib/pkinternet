# Reply: incremental RTT and the 40 ms rule

No, the rule would not relabel any of them. The 40 ms test is on each hop's **own absolute
RTT** from the probe, not on the increment over the previous hop. The classifier never
computes an increment; I added that column to `foreign_hops.csv` only because it was
asked for.

A hop is classified foreign only if all of the following hold: it replied, it is not a
private address, its registration resolves to a real non-`PK` country, its ASN is not on
the Shaw/Cogent artifact list, and its own RTT is between 40 and 500 ms. A trace is
tromboned if at least one hop clears all five, and only the first such hop per trace
produces the verdict.

## One trace makes the point

Probe E1 (Orbit, Faisalabad) to `ztbl.com.pk`, whose server is in Pakistan at
`203.101.184.80`:

```
hop  ip                     rtt   increment  country
 1   192.168.100.1          0.8              home router, private
 2   10.14.14.10            3.4       +2.6   ISP access, private
 3   * * *                                   no reply
 4   172.29.244.9           5.2       +1.8   ISP core, private
 5   149.40.227.42          4.4       -0.8   US on paper; 4.4 ms says Karachi
 6   110.93.254.126        21.1      +16.6   PK
 7   110.93.252.136        21.3       +0.2   PK
 8   27.111.228.157       100.5      +79.2   SG   <- leaves the country here
 9   2.21.120.112          96.9       -3.6   NL   <- still abroad
10   72.52.21.194         375.9     +279.0   US   <- still abroad
11   192.168.51.90        376.7       +0.8   private
12   192.168.201.6        378.6       +2.8   private
13   172.16.54.3          303.4      -72.5   private
14   175.107.33.22        302.3      -73.6   PK   <- back in Pakistan
15   203.101.184.80       301.9       -0.3   PK   <- the server, in Pakistan
```

Read hop 9. Its increment is **minus 3.6 ms**. Taken alone that looks like the packet went
nowhere, or even came closer. But its total RTT is **96.9 ms**. The packet was in Singapore
at hop 8 and is still overseas at hop 9. Nothing about it is nearby.

That is the whole answer: a small increment means the packet was already far away and moved
a little further, not that the hop is close.

Two other clauses are visible in the same trace. Hop 5 is a Cogent address registered in
the US answering in 4.4 ms, so it is a Cogent router physically in Karachi; that is what
the artifact list is for. Hops 11 to 13 are private addresses inside the destination's
network at 300 to 380 ms, and the private-address clause skips them.

## The pattern holds across the whole panel

3,660 foreign hops add less than 20 ms over the hop before them. Their own total RTTs have
a median of **104.6 ms**, a 10th percentile of 83.0 ms, and a minimum of **40.1 ms**. Not
one of them falls below the threshold.

What preceded them:

| | |
|---|--:|
| previous hop already over 40 ms | **3,653** |
| of those, previous hop itself classified foreign | 3,627 |
| previous hop under 40 ms | **7** |

So in 3,653 of 3,660 cases the packet had already left the country one hop earlier. The
small increment is movement between two foreign routers, not a border crossing.

## Why an incremental rule would be worse

The crossing appears once per trace as a single large jump, 21 ms to 100 ms at hop 8.
Every foreign hop after it adds only a few milliseconds. Testing the increment would catch
hop 8 and then wrongly release hops 9 and 10.

It would also import noise that absolute RTT does not carry. Across all 10,571 increments,
**23% are negative**: the next hop answers faster than the one before it. That is
impossible as a distance and arises because each router generates its ICMP reply on its own
schedule and return paths differ per hop.

## Two counts

`foreign_hops.csv` holds **76** distinct IPs, not 77; the file has 76 data rows plus a
header. Distinct ASNs are **10 or 11** depending on how you count: `27.111.228.157`, the
Equinix Singapore peering-LAN address, is unannounced in BGP, so Team Cymru returns no ASN
and only RDAP identifies it.
