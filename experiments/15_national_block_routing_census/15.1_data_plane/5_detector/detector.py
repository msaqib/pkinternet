#!/usr/bin/env python3
"""
Exp 15.1 detector — the Exp 04 rules plus the two corrections found in the 4.1 archive.

Both corrections came from re-analysing run_20260627_192918; see
`FINDING_address_squatting.md` (working notes, outside this repository) and `../SAMPLING_METHOD.md` §3.4.

  1. DOMESTIC_OBSERVED  an address that is consistently fast from some vantage is
                        physically in Pakistan, whatever it is registered as, so no
                        vantage may score it foreign. Consistency is a per-vantage
                        MEDIAN over >= MIN_SAMPLES, never a minimum: one lucky packet
                        otherwise clears a genuinely foreign address.
  2. rate-limit guard   a router that answers its own probe twice, slowly the second
                        time, produces the same RTT jump as a detour. Nothing moved
                        between the two answers, so it is not one.

Pure logic, no I/O and no network. Callers supply hops already resolved to
(rtt_ms, ip, country, asn). Validated by `validate_against_41.py`.
"""

import ipaddress

FOREIGN_RTT_FLOOR = 40.0    # a hop below this never left the country
JUMP_THRESH       = 60.0    # inter-hop step that implies an international leg
HIGH_RTT          = 70.0    # any hop at or above this means the packet left PK
LOCAL_CEIL        = 45.0    # a path whose max RTT stays under this never left
QUEUE_CEIL        = 500.0   # above this is queuing or ICMP generation, not distance
ARTIFACT_ASN      = {"6327"}  # Shaw: Nova-probe CPE, physically in PK

DOMESTIC_CEIL = 10.0   # a median under this is faster than Karachi<->Islamabad
MIN_SAMPLES   = 3      # readings required from one vantage before its median counts


def _is_public(ip):
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


def build_domestic_observed(samples, ceil=DOMESTIC_CEIL, min_samples=MIN_SAMPLES):
    """samples: {ip: {vantage: [rtt, ...]}} over the WHOLE run, every trace, not
    just the detours. Returns the set of addresses that are physically domestic.

    An address qualifies when SOME vantage has >= min_samples readings of it whose
    MEDIAN is under ceil. Per-vantage, because the squatted address 182.45.51.22 has
    a global median of 41.6 ms (PTCL's 340 slow readings dominate) but a Z-Com median
    of 2.4 ms over 29. A global median misses it; a global minimum wrongly clears
    C-root, which sits at 143 ms with one 3.4 ms reading."""
    out = set()
    for ip, by_vantage in samples.items():
        if not _is_public(ip):
            continue    # a private address can never carry a foreign country code
        for rtts in by_vantage.values():
            if len(rtts) < min_samples:
                continue
            s = sorted(rtts)
            n = len(s)
            median = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
            if median < ceil:
                out.add(ip)
                break
    return out


def rate_limit_artifact(hops, jump=JUMP_THRESH):
    """True when the RTT jump that would trigger a verdict happens between two
    ADJACENT hops carrying the SAME address. The router replied twice and was slow
    the second time; the packet did not move, so the jump is not distance.

    On the 4.1 archive this matches 70 of the 1,191 RTT-evidence detours. Only 11 of
    those reached the destination ISP, so `reached` must not be required, and 33 end
    on an RFC1918 address, which cannot be abroad at all."""
    seq = [(r, ip) for r, ip, *_ in hops if ip and r is not None]
    for i in range(1, len(seq)):
        if seq[i][1] == seq[i - 1][1] and seq[i][0] - seq[i - 1][0] >= jump:
            return True
    return False


def classify(hops, isp_asn, domestic_observed=frozenset()):
    """hops: [(rtt_ms|None, ip|None, country, asn)] in TTL order.
    Returns dict(status, evidence, exit_cc, exit_ip, max_rtt, max_jump, reached).

    status: trombone_hop | trombone_rtt | local | inconclusive
    Mirrors census_sweep.classify() so the two are comparable, with the two
    corrections applied."""
    exit_cc = exit_ip = ""
    max_rtt = 0.0
    max_jump = 0.0
    prev = None
    reached = False

    for rtt, ip, cc, asn in hops:
        if not ip:
            continue
        if asn and asn == isp_asn:
            reached = True
        if rtt is not None and rtt <= QUEUE_CEIL:
            max_rtt = max(max_rtt, rtt)
            if prev is not None:
                max_jump = max(max_jump, rtt - prev)
            prev = rtt
        elif rtt is not None and prev is None:
            prev = min(rtt, QUEUE_CEIL)

        foreign = (cc not in ("PK", "", "?")
                   and asn not in ARTIFACT_ASN
                   and ip not in domestic_observed          # correction 1
                   and rtt is not None
                   and FOREIGN_RTT_FLOOR <= rtt <= QUEUE_CEIL)
        if foreign and not exit_cc:
            exit_cc, exit_ip = cc, ip

    if exit_cc:
        return dict(status="trombone_hop", evidence="foreign_hop", exit_cc=exit_cc,
                    exit_ip=exit_ip, max_rtt=max_rtt, max_jump=max_jump, reached=reached)

    if max_jump >= JUMP_THRESH or max_rtt >= HIGH_RTT:
        if rate_limit_artifact(hops):                       # correction 2
            ev, status = "rate_limited_hop", ("local" if reached or
                                              (max_rtt and max_rtt < LOCAL_CEIL)
                                              else "inconclusive")
            return dict(status=status, evidence=ev, exit_cc="", exit_ip="",
                        max_rtt=max_rtt, max_jump=max_jump, reached=reached)
        return dict(status="trombone_rtt",
                    evidence=f"rtt(jump={max_jump:.0f},max={max_rtt:.0f})",
                    exit_cc="?", exit_ip="", max_rtt=max_rtt, max_jump=max_jump,
                    reached=reached)

    status = "local" if (reached or (max_rtt and max_rtt < LOCAL_CEIL)) else "inconclusive"
    return dict(status=status, evidence="", exit_cc="", exit_ip="",
                max_rtt=max_rtt, max_jump=max_jump, reached=reached)
