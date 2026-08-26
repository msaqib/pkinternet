# Why a 10 ms incremental RTT does not mean the hop is nearby

Short answer: our rule never looks at incremental RTT. It looks at each hop's **own total
RTT** from the probe. I added the incremental column to `foreign_hops.csv` only because it
was asked for; the classifier does not use it and never has.

A small increment does not mean "this hop is close". It means "the packet was already far
away, and this hop is only a little further than the last one".

---

## One real trace makes it obvious

Probe E1 (Orbit, Faisalabad) to `ztbl.com.pk`, whose server is in Pakistan at
`203.101.184.80`:

```
hop  ip                     rtt   increment  country
 1   192.168.100.1          0.8              home router
 2   10.14.14.10            3.4       +2.6   ISP access
 4   172.29.244.9           5.2       +1.8   ISP core
 5   149.40.227.42          4.4       -0.8   US on paper, 4.4 ms says Karachi
 6   110.93.254.126        21.1      +16.6   PK
 7   110.93.252.136        21.3       +0.2   PK
 8   27.111.228.157       100.5      +79.2   SG   <- leaves the country here
 9   2.21.120.112          96.9       -3.6   NL   <- still abroad
10   72.52.21.194         375.9     +279.0   US   <- still abroad
11   192.168.51.90        376.7       +0.8
14   175.107.33.22        302.3      -73.6   PK   <- back in Pakistan
15   203.101.184.80       301.9       -0.3   PK   <- the server, in Pakistan
```

Read hop 9. Its increment is **minus 3.6 ms**. Taken alone that looks like the packet went
nowhere, or even came closer. But its total RTT is **96.9 ms**. The packet was in Singapore
at hop 8 and is still overseas at hop 9. Nothing about it is nearby.

This is why we test the total, not the step. Hop 9 is 96.9 ms from Faisalabad. No Pakistani
router is 96.9 ms from Faisalabad.

Note also hop 5, `149.40.227.42`: registered to Cogent in the US but answering in 4.4 ms.
That is a Cogent router physically inside Pakistan, and it is on our artifact list for
exactly this reason. The registration is wrong, and the latency is what reveals it.

---

## The same pattern across the whole panel

Of the foreign hops we classify, 3,660 add less than 20 ms over the hop before them. Their
own total RTTs:

| | |
|---|--:|
| median total RTT | **104.6 ms** |
| 10th percentile | 83.0 ms |
| minimum | **40.1 ms** |
| how many are below the 40 ms threshold | **zero** |

And what came immediately before them:

| | |
|---|--:|
| previous hop was already over 40 ms | **3,653** |
| of those, previous hop was itself classified foreign | **3,627** |
| previous hop was under 40 ms | **7** |

So in 3,653 of 3,660 cases the packet had already left the country at the previous hop.
The small increment is movement *between two foreign routers*, not a border crossing.

---

## Why an incremental rule would be worse, not better

The border crossing appears once per trace, as one large jump: 21 ms to 100 ms at hop 8.
After that every further foreign hop adds only a few milliseconds.

* Testing **total RTT** catches the crossing at hop 8 and correctly keeps hops 9 and 10
  foreign as well.
* Testing **increment** would catch hop 8, then classify hops 9 and 10 as domestic because
  they add -3.6 ms and, on many traces, single digits.

It would also fail in the other direction. Across all 10,571 increments we measured,
**23% are negative**: the next hop answers faster than the one before it. That is
impossible as a distance, and it happens because each router generates its ICMP reply on
its own schedule and the return path differs per hop. Incremental RTT carries that noise;
total RTT does not.

---

## Which hops actually decide anything

Only the **first** foreign hop in a trace produces a verdict. That is the 4,170 count. The
other 6,400-odd foreign hop observations are second, third and fourth foreign hops in
traces that were already classified, and they change nothing.

So the low-increment hops are not borderline cases at risk of being relabelled. They are
hops deep inside an already-confirmed detour.

---

## Two small counts

* **76** distinct IPs, not 77. The CSV has 76 data rows plus a header.
* **10 or 11** ASNs depending on how you count: one address, the Equinix Singapore peering
  LAN IP `27.111.228.157`, is unannounced in BGP, so Team Cymru returns no ASN for it and
  only RDAP identifies it. It is 10 if you exclude the blank, 11 if you count it.
