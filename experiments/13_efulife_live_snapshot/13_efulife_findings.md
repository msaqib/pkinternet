# EFU Life Investigation — Key Findings

Quick-reference summary. Full detail and methodology in the other files in this
folder (`bgp_july27_investigation.md`, `cybernet_prefix_scope_check.md`,
`nine_probe_snapshot_summary.md`) and in `edits/` for corrections made to prior
project files.

## The core finding

- Every ISP that can reach EFU Life, domestic or not, passes through the
  identical router (`124.29.240.218`, Cybernet). No second domestic door exists.
- Domestic ISPs (Cybernet, PERN, Nayatel, TES, Nova, Z-Com): 24-101ms, stay
  inside Pakistan.
- PTCL: 203ms, leaves Pakistan entirely (GSL Networks &rarr; a Zain Omantel
  block &rarr; back into Cybernet).

## Globalping cross-check (7 more ISPs, non-RIPE)

- Sharp Telecom, Karachi: 4.6ms, all-domestic, fastest vantage of the whole
  investigation.
- 4 of 7 ISPs (PTCL, Fariya Networks, IN CABLE INTERNET, FASTTEL BROADBAND)
  hairpin through the exact same three hops. Not a PTCL-only problem.
- Nayatel showed an unexplained slow-but-still-domestic reading (113ms) the
  same day RIPE's Nayatel probes read 24-26ms. Unresolved.

## Geolocation corrections (the "Muscat/LA" story)

- Two of three disputed international hops didn't hold up on direct
  verification: "Equinix Muscat" and "Los Angeles" were both retracted to
  "abroad, unconfirmed."
- Singapore hop held up, confirmed on its own hostname twice, 6 weeks apart.
- "UAE" corrected to "Oman", RIPE's own registration record says so directly,
  though the exact city (Muscat) is still unconfirmed.
- Corrections made to the source project files, not just this write-up
  (logged in `edits/`).

## Did Cybernet's claimed July 27 fix happen?

- Checked two independent BGP archives (RIS and RouteViews). **No evidence of
  any change.** All paths identical before and after.
- PTCL is actually *slower* now (203ms) than the archived measurement from
  before the claimed fix (119ms).
- One real change did happen: GSL Networks lost a *direct* peering session
  with Cybernet. International-only, unrelated to Pakistan, not "the fix."

## Is this EFU-specific, or Cybernet-wide?

- Checked Cybernet's own 957 announced address blocks (not EFU's, which
  Cybernet only provides transit for).
- PTCL genuinely peers domestically with Cybernet for **291 of 952** blocks
  checked (30.6%), not zero.
- But EFU Life's block, and Cybernet's own core infrastructure block, both
  fall outside that peering. Selective, not absent.
- Caveat that matters: BGP tools structurally can't see small domestic-only
  ISP links (they only hear from internationally-connected networks), so "0"
  from BGP means "invisible," not "doesn't exist." Traceroute is what actually
  proved domestic reachability where it exists.

## Follow-on: EFU Life isn't a one-off

- Cybernet's full neighbor list (192 connections RIS has ever recorded) has
  only 2 real domestic ISPs in it: PTCL and Transworld. Everything else
  Pakistani-registered is either Cybernet's own second ASN or a customer.
- 10 other Pakistani companies follow the exact same pattern as EFU Life: own
  ASN, single-homed to Cybernet only (DataCheck, Samba Bank, MCB Arif Habib,
  Intermarket, Shirazi, MTPPL, HBL Bank, K-Electric, NayaPay, Khadim Ali Shah
  Bukhari Securities).
- Checked each one's own announced block in BGP: **7 of 10 show no domestic
  peer visible** (same pattern as EFU Life: DataCheck, MCB Arif Habib,
  Intermarket, Shirazi, MTPPL, NayaPay, Khadim Ali Shah Bukhari Securities).
  **3 of 10 show a real domestic peer** (Samba Bank via Transworld; HBL Bank
  and K-Electric via both PTCL and Transworld).
- Planned next step (not yet run): live traceroute from RIPE Atlas + Globalping
  probes to 1-2 companies from the "no domestic peer" group (DataCheck or
  NayaPay) plus one from the "has domestic peer" group (HBL Bank) as a
  contrast, to check whether traceroute confirms or contradicts the BGP split,
  the same way it did for Cybernet's own core block.

