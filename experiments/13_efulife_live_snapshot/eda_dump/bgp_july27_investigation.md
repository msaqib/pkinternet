# Did Cybernet's claimed July 27, 2026 fix actually change EFU Life's routing?

**Question posed:** check RIS and RouteViews (the two independent historical BGP
archives) to see why EFU Life was being routed the way it was, and what changed
around 2026-07-27, the date Cybernet claims to have fixed it.

**Short answer: no evidence of a real fix. Two independent BGP archives (RIS and
RouteViews) both show the domestic routing story is identical before and after
July 27. The one real change found is unrelated to Pakistani ISPs' reachability.**

## Background

Traceroutes (RIPE Atlas, live 2026-09-01/02, and Globalping, same dates) show
non-Cybernet Pakistani ISPs (PTCL, Fariya Networks, IN CABLE INTERNET, FASTTEL
BROADBAND) reaching EFU Life (AS141008) by exiting Pakistan, transiting Global
Secure Layer/GSL Networks (Singapore) and Zain Omantel (Oman-registered per RDAP),
then re-entering via Cybernet (AS9541), the only network that has ever announced
a route to AS141008 in BGP. Cybernet claims this was fixed on 2026-07-27. The
question: does the actual routing-table history support that.

## Method

**RIS** (RIPE's route collectors), queried via RIPEstat's `bgplay` API for
`103.154.196.0/23` (EFU Life's announced prefix, confirmed via
`announced-prefixes`, stable since at least 2026-01-01, no withdrawals), window
2026-07-01 to 2026-08-15: 4,342 announcement/withdrawal events across the window.

**RouteViews** (University of Oregon's independent collector network, no
relationship to RIPE), queried directly: downloaded full routing-table snapshots
(`RIBS`) from the `route-views2` collector at two points, **2026-07-20 00:00 UTC**
(a week before the claimed fix) and **2026-08-03 00:00 UTC** (a week after),
parsed with `bgpdump`, filtered to the exact prefix.

Two independent archives, two different collector networks, checked the same
question two different ways (RIS: continuous event history; RouteViews: clean
before/after snapshot diff).

## Finding 1 (both sources): Cybernet is the only door, unconditionally, throughout

Every single path in both datasets, from every peer, in every direction, ends
`..., 9541, 141008`. AS141008 has never announced itself through any network but
Cybernet, before or after July 27. This matches what the traceroutes already
showed; it's now confirmed at the control-plane level from two independent
archives.

## Finding 2 (both sources): no Pakistani ISP appears as a new direct peer of Cybernet

If Cybernet had built a genuine new domestic peering arrangement on July 27, the
signature would be a Pakistani ASN (PTCL/17557, Transworld/38193, Nayatel/23674,
etc.) newly appearing immediately upstream of AS9541 in the announced path.

- **RIS:** diffed the full set of ASes seen immediately upstream of 9541 before
  vs. after July 27 (116 distinct ASes before, 79 after, out of the full event
  history). The handful that are new after the cutoff (4455, 13237, 22356,
  31500, 209823, 213151, 401753) match no Pakistani network in this project's
  records.
- **RouteViews:** the clean snapshot diff is unambiguous. **All 17 distinct
  AS-paths seen from route-views2's peers on 2026-08-03 are byte-for-byte
  identical to the 17 seen on 2026-07-20.** Zero new paths, zero dropped paths,
  zero changed paths. Full path list (both dates, identical):

  ```
  37100 9541 141008
  7018 1299 9541 141008
  57866 1299 9541 141008
  2497 8529 9541 141008
  3549 3356 9541 141008
  49788 12552 9541 141008
  2914 1299 9541 141008
  3303 3356 9541 141008
  3130 174 9541 141008
  6939 3356 9541 141008
  20130 6939 3356 9541 141008
  3741 137409 8529 9541 141008
  22652 137409 8529 9541 141008
  3257 137409 8529 9541 141008
  2152 6461 137409 8529 9541 141008
  1403 577 6461 6461 137409 8529 9541 141008
  293 6453 8529 8529 8529 8529 8529 9541 141008
  ```

No Pakistani ASN appears in any of these paths at all, from either date.
RouteViews sees this destination purely through international transit (Cogent
3356, GTT/174, NTT 2914, Telia 1299, HE 6939/6461, GSL 137409, Omantel 8529, and
similar), which makes sense, it's a US-based collector network with mostly
international peers, but it independently corroborates that nothing about the
*shape* of reachability changed.

## Finding 3, the one real change, and why it doesn't explain the "fix" claim

RIS's event history shows AS137409 (GSL Networks) had a **direct** peering
adjacency with Cybernet before July 27 (a path existed with 137409 immediately
next to 9541, no Omantel in between) that is absent from RIS's view after July
27. This looked, initially, like a real change.

Checked against RouteViews, and the picture resolves cleanly: RouteViews never
saw a *direct* 137409-9541 adjacency at either date, only the longer
`137409 -> 8529 -> 9541` chain (GSL reaching Cybernet by transiting Omantel),
present identically on both 2026-07-20 and 2026-08-03. Put together: **GSL
Networks apparently lost one direct peering session with Cybernet around
July 27, while its indirect reachability to Cybernet via Omantel was completely
unaffected.** That's a real, specific infrastructure change, just not a
domestic one, and not one that helps any Pakistani ISP. If anything it's the
opposite of the "fix" narrative: one of Cybernet's two paths to GSL's network
went away, leaving GSL's route to Cybernet more dependent on Omantel, not less.

## Conclusion

Nothing in either archive supports Cybernet's claim of a July 27 fix to the
domestic reachability problem. Both the continuous RIS event history and a
clean RouteViews before/after snapshot diff show the same set of paths, the
same absence of any Pakistani peer, and the same total dependency on Cybernet as
the sole announced upstream, on both sides of the claimed fix date. This matches
what we independently measured five weeks later: PTCL, Fariya Networks, IN CABLE
INTERNET, and FASTTEL BROADBAND are all still hairpinning through the exact same
Singapore-then-Oman chain today. The one real change found (GSL's direct peering
session with Cybernet) is a separate, international-only adjustment unrelated to
the domestic hairpin.

## Caveats

- RouteViews check used one collector (`route-views2`) and two single points in
  time, not a continuous event stream like RIS. A transient flap exactly at
  those two timestamps would be invisible; the RIS event-history check (4,342
  events over 6 weeks) is the stronger source for continuity, RouteViews here
  functions as independent corroboration of the snapshot state, not a full
  replay.
- Neither archive can see *why* GSL's direct session with Cybernet dropped
  (deliberate decommission, an outage, a contract change), only that it did.
- "Cybernet claims to have fixed it" was taken as given for this task; the
  specific source/wording of that claim wasn't independently verified here.

## Reproducing

```
# RIS, via RIPEstat (no auth needed)
curl "https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS141008&starttime=2026-01-01T00:00:00&endtime=2026-09-02T00:00:00"
curl "https://stat.ripe.net/data/bgplay/data.json?resource=103.154.196.0/23&starttime=2026-07-01T00:00:00&endtime=2026-08-15T00:00:00"

# RouteViews, raw MRT RIB dumps
curl -o rib_before.bz2 "http://archive.routeviews.org/route-views2/bgpdata/2026.07/RIBS/rib.20260720.0000.bz2"
curl -o rib_after.bz2  "http://archive.routeviews.org/route-views2/bgpdata/2026.08/RIBS/rib.20260803.0000.bz2"
bunzip2 rib_before.bz2 rib_after.bz2
bgpdump -m rib_before | grep '|103.154.196.0/23|'
bgpdump -m rib_after  | grep '|103.154.196.0/23|'
```

(`bgpdump` installed via `brew install bgpdump` for this task.)
