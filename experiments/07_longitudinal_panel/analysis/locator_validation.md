# Validating the RTT-physics locator against ground truth



## What "our approach" actually does, in two steps

1. **Step 1 — disprove geo-IP.** If a measured ping is faster than light could
   physically travel to the site's registered geo-IP location and back, that
   registered location is provably wrong. 
2. **Step 2 — guess the real location.** Having disproven the registered
   location, the script guesses a new one: whichever probe got the fastest
   reply is assumed to be "near" the true server, and if that best RTT is
   under the local threshold, the site is called `LOCAL`.

Step 1 had never been checked against independent ground truth. Step 2 hadn't
either 

## Ground truth used

Cloudflare exposes `https://<site>/cdn-cgi/trace` on every domain it fronts.
It returns (among other fields) `colo=`, the IATA code of the specific
Cloudflare data center that answered *this* request — an authoritative,
independent signal RIPE Atlas probes can't produce themselves (they can't do
HTTP). This is the same source already named as the gold standard in
`CLAUDE.md`'s reliability ranking ("colo ... the HTTP truth").

## What was run

Input: `experiments/07_longitudinal_panel/analysis/relocate.csv` (already
existed — the Step 1+2 output for all 78 sites checked so far).

```python
import csv, requests

def colo(host):
    r = requests.get(f"https://{host}/cdn-cgi/trace", timeout=8)
    d = dict(line.split("=", 1) for line in r.text.splitlines() if "=" in line)
    return d.get("colo", "n/a")

rows = list(csv.DictReader(open("relocate.csv")))
cdn_sites = [r for r in rows if r["cls"] == "CDN"]
# for each site: colo(r["target"]) and compare to r["latency_verdict"]
```

Full commands and output are reproducible; results saved to
`experiments/07_longitudinal_panel/analysis/colo_groundtruth.csv`.

## Results

Scope: the 34 CDN-class sites where Step 1 already disproved the registered
geo-IP (all were falsely registered to Toronto/Ottawa, Canada).

| | Ground truth: local (`colo=KHI`, Karachi) | Ground truth: abroad (`colo=SIN`/`HKG`) |
|---|---:|---:|
| **Predicted `LOCAL`** (Step 2) | 12 | 19 |
| **Predicted `FAR`** (Step 2)   | 0  | 1 |

(31 of 34 resolved a `colo`; 3 timed out or aren't Cloudflare-fronted.)

- **Step 1 (disprove geo-IP): 34/34 = 100% correct.** Every one of these
  sites really is not in Toronto/Ottawa.
- **Step 2 (guess the true location): 12/31 = 39% correct.** Most of the
  time, "answers a fast ping" meant "nearby anycast edge," not "actually in
  Pakistan" — 19 of the 31 are really served from Singapore or Hong Kong.

## Interpretation

The locator's two jobs have very different reliability. Debunking a false
geo-IP claim is a hard physical proof and holds 100% of the time here.
Naming the *correct* replacement location from RTT alone is a much weaker
inference for anycast/CDN sites specifically, because a fast reply only
proves a nearby edge answered the network-layer probe — not that the HTTP
content is served from that edge (the same ICMP-path-≠-HTTP-serving-location
caveat already noted for `shaukatkhanum.org.pk`, now quantified at scale).

This does not weaken the paper's core tromboning results, which are about
whether traffic *reaches* a destination without leaving the country
(a network-layer question the locator handles well) — it specifically
bounds how much weight the "locally reached ⇒ locally served" claim can carry
for CDN sites.

## Limitation

This ground-truth check only works for Cloudflare-fronted sites, since
`/cdn-cgi/trace` is Cloudflare-specific. Cloudflare is the dominant CDN in
the candidate pool (927 of 1,781 sites), but other CDNs (Akamai, Fastly,
Incapsula, CloudFront) don't expose an equivalent authoritative field, so
this validation doesn't extend to them. Recommended framing: state this
explicitly as a scope limitation in the paper rather than attempting a
per-CDN workaround for a small number of sites.
