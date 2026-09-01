# Exp 14 — CDN edge-server location via HTTP headers (locedge)

## Question

Can we generalize the Cloudflare `colo=` ground-truth check (Exp 07,
`analysis/cloudflare_colo_confirmed.md`) to CDNs other than Cloudflare, and
get cache HIT/MISS per resource, not just the top-level document?

## What this is

[locedge](https://github.com/itsrun/locedge) (Huang, ACM SIGCOMM'22 demo,
"Locating CDN Edge Servers with HTTP Responses") matches response headers
across an entire page load against a rules database (`rules/geo.rules.js`,
`rules/cache.rules.js`, `rules/feature.rules.js`) covering many CDN
providers, not just Cloudflare. Input is a HAR (HTTP Archive) capture of a
full page load; output is, per resource, `provider` / `pop` / `location` /
`cacheStatus`.

**How this differs from the `cdn-cgi/trace` method already used in Exp 07:**

| | `cdn-cgi/trace` | locedge |
|---|---|---|
| Coverage | Cloudflare only | any CDN with a rule (Akamai, Fastly, CloudFront, Cloudflare, ...) |
| Source of truth | Cloudflare states its own colo | inferred from response headers via pattern-matching |
| Granularity | one answer for the whole site | per-resource (every asset on the page) |
| Extra signal | none | cache HIT/MISS/EXPIRED per resource |
| Method | one `curl` | full headless page load (Puppeteer) + HAR capture |

Same limitation as the trace method: the answer is relative to whichever
ISP the capture runs from (anycast/GeoDNS), so a single-vantage run only
tells you the PoP for that one ISP. That's the reason for the batch runner
below, so this can be repeated across the raslas Pis.

## Files

- `capture-har.mjs <url> <out.har>` — loads a URL in headless Chromium via
  Puppeteer, saves the full HAR.
- `locate-cdn.mjs <har>` — runs locedge's `parse(har)` and prints
  provider/pop/location/cacheStatus per resource.
- `run-batch.mjs` — reuses one browser instance to capture + locate every
  hostname in `../../data/pk_cdn_targets.csv`, writes one HAR per site into
  `results/har/` and a summary CSV into `results/`.
- `index.js`, `src/`, `rules/` — the locedge library itself, cloned from
  upstream (not our code).

`capture-har.mjs` / `locate-cdn.mjs` weren't the actual files linked in Dr.
Ilyas's post — those links didn't survive being pasted into the task
description. These are a from-scratch rewrite against locedge's documented
`parse(har)` API; worth a quick diff against his originals if he shares them.

## First result (sanity check against Exp 07 ground truth)

Ran from this machine's own vantage: Cybernet, Lahore (AS9541), one of the
raslas ISPs. `auroracloset.pk` → every Cloudflare-fronted resource on the
page (the domain itself, plus `cdn.shopify.com` assets) came back
`pop: khi`, `location: karachi`, matching the `colo=KHI` result already
confirmed for Cybernet in `analysis/cloudflare_colo_confirmed.md`. The page
document itself showed `cacheStatus: DYNAMIC`; static JS/CSS assets showed
`HIT`. A `fonts.googleapis.com` request was correctly flagged
`provider: google` with no location, a different CDN with no geo rule here.

`results/example_auroracloset.har` is that run, kept as a worked example.

Smoke-tested `run-batch.mjs` against 2 sites (`cloudflare.com`,
`github.com`) before leaving this for a full run: `cloudflare.com`'s own
site resolved to `pop: sin` (Singapore) from this Lahore vantage;
`github.com`'s top-level document didn't carry a header locedge has a rule
for (not a bug — not every CDN annotates the HTML document itself, only
certain sub-resources). Full 22-site run against `data/pk_cdn_targets.csv`
not yet done.

## Next steps

1. Run `run-batch.mjs` from here (Cybernet/Lahore) as one data point.
2. Test that `npm i puppeteer puppeteer-har` actually installs and launches
   on one Raspberry Pi (ARM) before assuming it scales to all of them —
   Chromium is a much heavier dependency than the curl/dig-based scripts in
   `08_CDN`/`10_local_cdn_reach`.
3. If it runs cleanly on one Pi, repeat the batch across however many raslas
   Pis are online, keyed by ISP, and diff `pop`/`location` per site per ISP
   — same shape as `cloudflare_colo_confirmed.md`'s table, generalized past
   Cloudflare.
4. Answer Dr. Ilyas's actual question: whether the CDN a given ISP is
   routed to (and whether it's a local cache hit) varies by ISP, the way
   `ajk.gov.pk` already did for Cloudflare (KHI/SIN split by ISP; PTCL alone
   routed to MCT).

## Setup

```
npm i
node capture-har.mjs <url> <out.har>
node locate-cdn.mjs <out.har>
# or, for the full target list:
node run-batch.mjs
```
