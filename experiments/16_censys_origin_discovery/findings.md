# Exp 16 findings — Censys origin discovery

Working doc, updated as more domains get checked. Plain-language summary of
what's actually been confirmed so far, not a final writeup.

## khushhalibank.com.pk

Classified as CDN (AWS CloudFront) in `pk_100_final_v2.csv`. Censys search
turned up 10 real hits presenting the bank's actual wildcard certificate,
across two Pakistani ISPs (PTCL x7, Transworld x3), not the CDN. Full
per-hit detail in `results/manual_censys_log.csv`.

- `119.159.230.218` (PTCL) — real cert, blocked from direct browsing
- `117.20.24.58` (Transworld) — real cert, blocked (WAF, 403)
- `117.20.24.54` (Transworld) — real cert, blocked from direct browsing
- `117.20.24.53` (Transworld) — real cert, **not blocked**, serves the
  actual live Khushhali Internet Banking site directly
- `202.125.155.68` (PTCL) — real cert, **not blocked**, serves the live
  site directly
- `202.125.155.77` (PTCL) — real cert, blocked (WAF, 403)
- `202.125.155.73`, `202.125.155.72` (PTCL) — real cert, blocked. Share
  reverse DNS (`rwp44.pie.net.pk`) with `.68`/`.77` but Censys geolocates
  them to Lahore instead of Rawalpindi, likely a geolocation DB
  inconsistency, not a real second site.
- `221.120.222.161`, `221.120.222.163` (PTCL) — real cert, blocked. Same
  pattern again: share reverse DNS (`lhr63.pie.net.pk`) but Censys splits
  them across Hafizabad/Lahore.

Same Dynatrace + F5 WAF stack shows up on both ISPs, so this reads like one
coordinated, professionally-run production pool split across two
providers, not scattered leftover boxes.

### Note on "the target never replies" (applies to every IP below)

Ping and HTTPS are separate settings. These IPs block ping even when wide
open over HTTPS, so a silent target is not a sign of blocking. We check
the hops leading up to it instead.

Most probes show an unbroken path from source to a hop on the bank's own
network, then the expected silence. A minority have a real gap somewhere
in the middle, an unanswered hop, a genuine blind spot, not evidence
either way.

**Method note**: the first run below used ICMP traceroute (RIPE Atlas's
default), which is why the target itself never replies, it's dropping
ping specifically, even though it accepts real TCP connections on 443 (per
the curl tests). `trace_khushhalibank_candidate.py` now supports
`--protocol TCP --port 443` (TCP is the new default). Retested `.53` with
it, see below, results are mixed rather than a clean win.

### Reachability check — 119.159.230.218 (PTCL, blocked to direct requests)

This is the candidate that returns connection-reset when asked for a page
directly. Only its network path was tested here, not its content, that
was already ruled out by curl.

15 live PK RIPE Atlas probes, ICMP traceroute. 10 of 15 came back clean
(unbroken path to a PTCL hop, no gaps). 5 of 15 had a gap somewhere in the
middle, a silent hop, real blind spot, not evidence of anything either way.

**0 of 15 show a genuine foreign hop.** Two probes (64722, 1015679) show
an ASN that looks foreign (Cogent/US, Shaw/Canada), but this project
already identified and corrected this exact pattern, see
`findings/address_squatting_detector_correction.md`. Two Pakistani ISPs
use foreign-registered IP address space on their own equipment physically
sitting inside Pakistan. The giveaway is RTT: a real Lahore-to-Vancouver
round trip needs ~109ms minimum, these hops answer in 1-3ms, physically
impossible unless the address is actually local. Detail below.

**Clean example — probe 1016126, PTCL network (ptcl.1016126):**
```
hop  ip               asn      operator
1    192.168.10.1     —        private
2    39.39.0.1        AS17557  PTCL (PK)
3-6  10.253.x.x       —        private (internal PTCL routing)
7    221.120.221.46   AS17557  PTCL (PK)
8    10.190.199.57    —        private
9    221.120.222.166  AS17557  PTCL (PK)
10-14 * (no response) — target itself, expected
```
Every hop that answers is either private/internal or PTCL. Nothing else.

**Probe 64722, on Optix Pakistan (AS136384.64722) — Cogent hop is the
known in-Pakistan PoP artifact, not a real US hop:**
```
hop  ip               asn      operator                       rtt
1    192.168.18.1     —        private
2    205.164.150.1    AS136384 Optix Pakistan (PK)
3    202.141.224.73   AS9260   Multinet Pakistan (PK)
4    149.40.227.188   AS174    "Cogent" (labeled US)            2.8ms  <- known artifact, physically in PK per 04.1 notes
5    110.93.255.168   —        Transworld (PK)
6    119.63.137.83    —        Transworld (PK)
7-8  10.253.x.x       —        private (internal PTCL routing)
9    221.120.221.50   AS17557  PTCL (PK)
11   221.120.222.166  AS17557  PTCL (PK)
12-16 * (no response) — target itself, expected
```
2.8ms is roughly 40x too fast for a real US round trip. Every hop on this
path is really in Pakistan.

**Probe 1015679, on network AS136174 (nova.1015679) — Shaw hop is the
documented Nova/TPCPL address-squatting artifact, not a real Canada hop:**
```
hop  ip               asn      operator                       rtt
1    192.168.100.1    —        private
2    70.70.233.222    AS6327   "Shaw Communications" (labeled CA) 1.5ms  <- documented artifact, Nova's own router in PK
3    110.93.212.161   AS38193  Transworld (PK)
4-5  110.93.x.x       —        Transworld (PK)
6-7  10.253.x.x       —        private (internal PTCL routing)
8    221.120.221.46   AS17557  PTCL (PK)
10   221.120.222.166  AS17557  PTCL (PK)
11-15 * (no response) — target itself, expected
```
1.5ms matches the already-documented Shaw artifact signature exactly
(prior investigation found 336 observations of this hop, fastest 0.9ms,
always at hop 2, always from Nova). Every hop on this path is really in
Pakistan too.

**Bottom line for .218**: 15 of 15 probes show either a fully clean
domestic path, or a domestic path with an unexplained silent gap. Zero
probes show any genuine evidence of a foreign hop.

Raw data: `results/khushhalibank_candidate_20260913_091017/`

### Reachability check — 117.20.24.53 (Transworld, wide open)

This is the candidate that loads the real bank site directly in a browser,
no CDN, no login wall, confirmed by curl earlier (HTTP 200, page title
"Khushhali Internet Banking", real logo asset).

**ICMP run**, 18 probes scheduled, 14 completed (4 failed for unrelated
reasons, offline probes, not a target problem): 12 of 14 clean, ending on
Transworld right before the target goes silent. 2 of 14 had a mid-path
gap but still ended on Transworld. 0 of 14 show a genuine foreign hop,
probe 64722 shows the same known in-Pakistan Cogent PoP artifact
documented above, not a real US hop.
Raw data: `results/khb-53-open_20260913_093858/`

**TCP/443 retest**, same 18 probes, `--protocol TCP --port 443` instead of
ICMP, since we know from curl this server actually answers on port 443
even though it ignores ping.

**Probe 62224, on PERN (pern.62224), got a reply from the server:**
```
hop  ip               asn      operator                      rtt
1    10.102.76.1      —        private                       2.3ms
2    172.25.3.14      —        private                       0.8ms
3    * (no response)
4    117.20.24.53     AS38193  Transworld Associates (PK)     1009.4ms  <<< DESTINATION, replied
```
The server answered directly, correctly tagged as Transworld, Pakistan.
The RTT jump (0.8ms at hop 2 to 1009.4ms at hop 4) fails this project's
own standing rule: `experiments/04.1_small_isp_tromboning/notes.md` says
to ignore any RTT over 500ms as a queuing/ICMP-error-generation artifact.

Retested the same probe (62224) against the same target alone, to check
if that RTT was a one-off:
```
hop  ip               asn      operator                      rtt
1    10.102.76.1      —        private                       1.6ms
2    172.25.3.14      —        private                       0.8ms
3    * (no response)
4    117.20.24.53     AS38193  Transworld Associates (PK)     1005.4ms  <<< DESTINATION, replied
```
1005.4ms, within 4ms of the original 1009.4ms. That's not random queuing
jitter, a real fluke would not land within 4ms of itself twice. This is a
consistent, repeatable delay specific to this last hop, not a one-off
artifact. Still can't say what causes it (server-side rate limiting on
the port, a deliberate slow-path for non-CDN TCP connections, or
something in how RIPE Atlas's TCP traceroute closes out the final hop),
but it's a real, reproducible signal, not noise. IP and ASN attribution
(Transworld, Pakistan) hold either way.

The rest of that TCP run had more mid-path gaps than the ICMP run (8 of 15
vs 2 of 14). Most likely explanation: PTCL/Transworld load-balance
traffic across more than one physical path (ECMP), so two separate
traceroute runs to the same target can legitimately take different
routes, this isn't necessarily about TCP vs ICMP. Only ran each once, so
can't fully separate the two explanations.

Raw data: `results/khb-53-tcp443_20260913_100711/`

## nbp.com.pk

CDN-fronted (Cloudflare). 2 real hits, both on `nbp.com.pk`'s own certs.

- `103.28.150.250`, on **NBP's own ASN** (AS58506, literally named after
  their head office address). Real cert, valid to 2026-10-14. Serves real
  content: a redirect to `/remote/login`, NBP's own SSL-VPN gateway for
  staff, not the public bank site.
- `103.76.29.140`, third-party ASN, cert **expired 2025-10-24**, dropped.

Only 2 hits total for this domain, no server found serving the actual
public banking website. Confirms NBP runs real infrastructure inside
Pakistan, but doesn't prove the customer-facing site itself has a
domestic backend, weaker finding than khushhalibank.

## bop.com.pk

CDN-fronted (Incapsula). 2 real hits, both on **Bank of Punjab's own ASN**
(AS137461).

- `103.109.121.2:4443`, VPN gateway, same `/remote/login` pattern as NBP.
  Cert expired 2 days ago (Sep 12), otherwise real and live.
- `103.109.121.165`, Outlook Web Access (email) server, connection times
  out on direct access, blocked, not reset or 403, a silent drop.

Same shape as nbp.com.pk: real domestic infrastructure confirmed, no hit
on the actual public banking site itself.

## bankislami.com.pk

CDN-fronted (Cloudflare). 8 real hits, all on the same Pakistani hosting
provider (MYSOL-PK, AS45446, not the bank's own ASN, but still domestic).

- `ib.bankislami.com.pk` ("Internet Banking") and `mbapp.bankislami.com.pk`
  ("Mobile Banking") are the most important names here, likely back the
  actual customer banking products, both blocked from direct access
  (403/timeout), can't confirm content directly.
- `ememo4u.bankislami.com.pk` fully live, redirects to a real login page,
  internal approval system.
- `secure.bankislami.com.pk` (2 IPs, redundant pair) live VPN gateway.
- The literal wildcard cert itself was hit on a GitLab/DevOps box in
  Rawalpindi (`202.44.91.24`), everything else in this batch is Karachi,
  worth a second look.

All certs verified real (`O=BANK ISLAMI PAKISTAN LIMITED`). More
diverse and stronger than nbp/bop, but still no direct confirmed hit on
the actual public-facing banking website's content.

## abl.com

CDN-fronted (Cloudflare). Strongest batch of the whole session. 15 real
Pakistani hits: 11 on **Allied Bank's own ASN** (AS58515), 4 mail
gateways on a separate real Pakistani ISP (Cyber Internet Services).

- **`www.abl.com` itself**, the actual main public domain, hit directly
  on the bank's own ASN. Real EV cert (`O=Allied Bank Limited`). Blocked
  (403) from direct access, but this is the strongest single ownership
  signal of the whole session, it's not a subdomain, it's the homepage.
- **`login.abl.com`**, live, redirects to
  `https://www.myabl.com/retail/pages/dashboard.html`, the bank's real
  retail internet banking product lives on a separate branded domain
  (`myabl.com`), not `abl.com`. Worth searching `*.myabl.com` next.
- 6 more fully live pages confirmed with real content: merchant portal,
  merchant-portal staging login, IBM WebSEAL/BPM gateway, webmail,
  BeyondTrust remote-support tool, Cisco AnyConnect VPN portal
  (`/+CSCOE+/logon.html`).
- 2 reachable but no root content (API backends, expected).
- 1 blocked (POS staging system).
- 4 real mail gateways (`smtp-gw1/2/5/6.abl.com`) on Cyber Internet
  Services Pakistan, not curl-checkable (SMTP, not HTTPS), confirmed via
  Censys's own cert scan only.
- 3 coincidental name-match hits correctly ruled out and removed from the
  log: `abl.com.bd` (Bangladesh, unrelated company), `abl.com.sg`
  (Singapore, unrelated shared hosting), and a Russian RDP box, none of
  these are Allied Bank Limited Pakistan.

## myabl.com

Follow-up to the `login.abl.com` redirect above. 2 hits, both on
**Allied Bank's own ASN** (AS58515), same as abl.com.

- **`www.myabl.com`** (`103.247.66.147`): real EV cert
  (`O=Allied Bank Limited`). This is the one that closes the loop.
  Traced the full chain by hand: `www.myabl.com` redirects to
  `/pages/home.html`, which redirects through an Oracle Access Manager
  SSO handshake (`agentid=obdx-18-prod`, Oracle Banking Digital
  Experience, production) to `login.abl.com`, which serves the real,
  live **"myABL - Login"** page, Allied Bank's actual customer internet
  banking login screen, page title confirmed, ~40KB of real content.
  Same class of finding as khushhalibank's `.53`, a fully confirmed
  public-facing banking product, on domestic infrastructure, end to end.
- `ppdocsrvc.myabl.com` (`103.247.66.142`): real cert
  (`CN=whatsappdocsrvc.myabl.com`), a WhatsApp-banking document service.
  404 at root, expected for an API backend.

So abl.com is now the second domain (after khushhalibank) with a fully
confirmed hit on the actual customer-facing banking product itself, not
just internal tooling.
