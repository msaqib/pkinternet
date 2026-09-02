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
2. ~~Test that `npm i puppeteer puppeteer-har` actually installs and
   launches on one Raspberry Pi (ARM)~~ **done, 2026-09-02, see below —
   partial success, one real blocker found.**
3. If it runs cleanly on one Pi, repeat the batch across however many raslas
   Pis are online, keyed by ISP, and diff `pop`/`location` per site per ISP
   — same shape as `cloudflare_colo_confirmed.md`'s table, generalized past
   Cloudflare.
4. Answer Dr. Ilyas's actual question: whether the CDN a given ISP is
   routed to (and whether it's a local cache hit) varies by ISP, the way
   `ajk.gov.pk` already did for Cloudflare (KHI/SIN split by ISP; PTCL alone
   routed to MCT).

## Raspberry Pi test (raslas-01, 2026-09-02)

Answering the open question from Dr. Ilyas's post directly: **partial
success.** Puppeteer/Chromium is installable and Chromium itself runs on
the Pi's ARM64, but headless navigation to a real HTTPS site currently
hangs. Not yet a green light for the multi-Pi run.

**What works:**
- `raslas-01`/`02`/`04`/`05` all reachable now over the existing Tailscale
  mesh (`msaqib@`), same nodes as `cloudflare_colo_confirmed.md`.
- Puppeteer's own bundled-Chromium download doesn't support Linux/ARM64 at
  all — moot here anyway, because **`/usr/bin/chromium` (v147) is already
  installed** as part of the Pi's OS image. Used `puppeteer-core` (no
  bundled browser) pointed at it via `executablePath`, so nothing needs to
  be downloaded.
- Installed a standalone Node v20.19.2 arm64 build into `~/nodejs` (24MB
  download, 168MB unpacked) rather than Debian's `nodejs`/`npm` apt
  packages, which pull in several hundred tiny `node-*` stub packages —
  a bad fit for an **8GB SD card sitting at 91% full with only ~590MB free
  to begin with.**
- `npm i puppeteer-core puppeteer-har` → 107 packages, 61MB, 46s, once two
  environment problems (below) were worked around.
- Chromium launches and renders fine for a local page
  (`chromium --headless=new ... about:blank` → clean DOM, instant).

**Two distinct problems found and fixed along the way:**
1. **Node's own networking hangs indefinitely** on any HTTPS request
   (`npm install`, plain `https.get`) — traced to Node 20's Happy-Eyeballs
   dual-stack connection logic (`autoSelectFamily`, on by default in Node
   20) stalling against this Pi's network, which has no usable IPv6 route
   (`curl -6` to any external host returns nothing, no fast failure).
   **Fix:** `NODE_OPTIONS="--no-network-family-autoselection --dns-result-order=ipv4first"`.
2. **`puppeteer-core`'s postinstall (`install.mjs`) still attempted a
   browser download** despite not needing one, and briefly ran the SD card
   to **100% full** before getting killed — genuinely risky on a Pi this
   short on space, since it could affect whatever else this Pi runs.
   **Fix:** `PUPPETEER_SKIP_DOWNLOAD=true` before `npm i`. Cleaned up
   afterward (`rm -rf ~/.cache/puppeteer`); disk settled at 274MB free.

**The unresolved blocker:** Chromium itself (invoked directly, no
Puppeteer) hangs indefinitely (20s+, no output) navigating to a real
external HTTPS site (`https://example.com`), even after: `--headless=new`,
`--disable-background-networking`, `--disable-component-update`,
`--disable-sync`, `--dns-over-https-mode=off`, and forcing DNS via
`--host-resolver-rules="MAP example.com <literal IPv4>"` (which bypasses
DNS for the target entirely). One `ss -tnp` snapshot mid-hang caught
Chromium connected to a Google IP unrelated to the target site (likely
some background service call independent of the disable flags tried), but
disabling more of Chromome's background networking didn't fix it, and with
`--host-resolver-rules` added, the process stopped opening **any**
connection at all before the timeout. Root cause not yet isolated — could
be the same IPv6 stack issue as Node's (Chromium has its own independent
network stack, so Node's fix doesn't carry over), or something about how
this Pi's firewall/DPI treats headless Chrome's traffic differently from
`curl`. No stray processes or disk left behind; the Pi was left clean.

**Bottom line for Dr. Ilyas:** the Pi has enough RAM (7.6GB) and CPU
headroom, and does not need Puppeteer's own Chromium download since the OS
image already ships one — but **disk space is a real constraint** (start
around 90%+ full on an 8GB card before installing anything) and **headless
Chromium's actual page navigation is currently broken on this Pi's network
path**, independently of the Node-level networking bug already fixed. This
needs to be resolved before a multi-Pi comparison is worth running; the
Node fix does not carry over to Chromium since they have separate network
stacks. Next: try `chromium --headless=new` in verbose/network-logging mode
(`--enable-logging --v=1` or `--log-net-log=netlog.json`) to see exactly
which host it's stuck contacting.

## Setup

```
npm i
node capture-har.mjs <url> <out.har>
node locate-cdn.mjs <out.har>
# or, for the full target list:
node run-batch.mjs
```
