#!/usr/bin/env python3
"""
R5 for the local sweep: which traces left Pakistan and came back.

RUN prove_rules_local.py FIRST. This consumes rules_local.json and will refuse to
run without it, because R5 is only meaningful after R1 to R4 are settled.

WHAT THIS DECIDES, and what it deliberately does not
  Detection here is TOPOLOGICAL. A trace tromboned if it reached a Pakistani target
  and passed through a hop that is genuinely outside Pakistan. Every target is
  Pakistani by construction: the universe is Pakistan's announced and registered
  space, so a foreign hop on the way to one is a departure and a return.

  The RTT arm of the Exp 04 detector is NOT used. prove_rules_local.py measured why:
  local_trace.py sends one packet per TTL and ran at 120 threads, so 22% of adjacent
  hop pairs show RTT falling more than 20 ms deeper into the path, which distance
  cannot do. Applying `max_rtt >= 70` to this data labels 75.9% of traces, which
  measures concurrency, not geography.

  So this reports a FLOOR on tromboning, not a rate. A detour that stays inside a
  foreign network which never answers, or one hidden by an MPLS tunnel, is invisible
  here and is counted as local.

WHAT COUNTS AS ABROAD
  * A hop annotated to a foreign country, EXCLUDING the addresses R2 falsified. Those
    are Pakistani infrastructure numbered out of foreign space, and counting them
    would manufacture detours out of address squatting. This is the single most
    important correction: without it the Cogent 149.40.226/227 hops alone would
    fabricate thousands.
  * A hop on a FOREIGN internet exchange fabric. The hop belongs to the exchange
    rather than to either peer, but the packet is still physically in Frankfurt or
    Singapore, so for departure it counts.

  python classify_local.py     -> trombone_local.json, TROMBONE_FINDINGS.md, routes_trombone.txt
"""
import io, json, os, collections, statistics as st

H = os.path.dirname(os.path.abspath(__file__))
def P(*p): return os.path.join(H, "..", *p)

RULES = os.path.join(H, "rules_local.json")
if not os.path.exists(RULES):
    raise SystemExit("rules_local.json missing. Run prove_rules_local.py first.")
R = json.load(io.open(RULES, encoding="utf-8"))
FLOORS = R["country_floors"]
HOME = ("PK", "PRIV", "CGN", "??")

# R2 falsifies a CLAIM: "this address is not where its registry says". That is not the
# same as "this address is in Pakistan". An address can be provably not in Virginia and
# still be abroad. So R4-prime decides the second question, using this vantage's own
# measured domestic distribution rather than any assumption.
FENCE = (R.get("R4prime") or {}).get("fence_ms")
_rtt = {}
for fn in ("rtt_inpath.json", "rtt_foreign_ttl.json", "rtt_foreign.json"):
    fp = P("3_routes", fn)
    if os.path.exists(fp):
        for ip, v in json.load(io.open(fp, encoding="utf-8")).items():
            if v.get("n") and ip not in _rtt:
                _rtt[ip] = v["min"]

FALSIFIED, FALSIFIED_BUT_FOREIGN = set(), set()
for ip, rec in R["R2"]["falsified_detail"].items():
    r = _rtt.get(ip, rec.get("rtt"))
    if FENCE is not None and r is not None and r > FENCE:
        FALSIFIED_BUT_FOREIGN.add(ip)   # not where it claims, but not domestic either
    else:
        FALSIFIED.add(ip)               # behaves domestically: squatted Pakistani space

ann = json.load(io.open(P("3_routes", "selected_annotated.json"), encoding="utf-8"))
own = json.load(io.open(P("1_universe", "block_to_asn.json"), encoding="utf-8"))
holder = json.load(io.open(P("1_universe", "asn_holder.json"), encoding="utf-8"))
import ipaddress


def abroad(h):
    """True when this hop is physically outside Pakistan, as far as we can tell."""
    if not h or h["cc"] in HOME:
        return False
    if h["ip"] in FALSIFIED:          # squatted space: Pakistani box, foreign registry
        return False
    # FALSIFIED_BUT_FOREIGN falls through: R2 killed its registry claim, R4-prime says
    # its latency is outside this vantage's domestic range, so it is abroad regardless.
    return True


rows = []
for r in ann:
    exits = [h for h in r["path"] if abroad(h)]
    first = exits[0] if exits else None
    unit = str(ipaddress.ip_network(r["target"] + "/24", strict=False))
    rows.append(dict(
        target=r["target"], block=r["block"], asn=own.get(unit),
        status="trombone" if first else "local",
        exit_cc=first["cc"] if first else "", exit_ip=first["ip"] if first else "",
        exit_holder=(first.get("holder") or "")[:40] if first else "",
        exit_is_ixp=bool(first and first.get("kind") == "ixp"),
        n_foreign=len(exits), answered=r["answered"], gaps=r["gaps"]))

T = sum(1 for x in rows if x["status"] == "trombone")
N = len(rows)
by_cc = collections.Counter(x["exit_cc"] for x in rows if x["status"] == "trombone")
by_ixp = collections.Counter(x["exit_holder"] for x in rows if x["exit_is_ixp"])

# per network, and only where the sample can carry a number
per = collections.defaultdict(lambda: [0, 0])
for x in rows:
    if x["asn"]:
        per[x["asn"]][0] += 1
        if x["status"] == "trombone":
            per[x["asn"]][1] += 1
ranked = sorted(((a, n, t) for a, (n, t) in per.items() if n >= 100),
                key=lambda z: -z[2]/z[1])

json.dump(dict(traces=N, trombone=T, rate=round(100*T/N, 2),
               by_country=by_cc.most_common(), by_exchange=by_ixp.most_common(),
               falsified_excluded=len(FALSIFIED), rows=rows),
          io.open(os.path.join(H, "trombone_local.json"), "w", encoding="utf-8"))

# readable routes for the tromboning traces, per the standing rule that no verdict
# ships without the paths to check it against
idx = {r["target"]: r for r in ann}
with io.open(os.path.join(H, "routes_trombone.txt"), "w", encoding="utf-8") as fh:
    fh.write(f"Traces that left Pakistan and returned. {T:,} of {N:,}.\n"
             f"Detection is topological. Addresses R2 falsified are NOT counted as foreign;\n"
             f"they are Pakistani infrastructure numbered out of foreign space.\n\n")
    for x in rows:
        if x["status"] != "trombone":
            continue
        t = idx[x["target"]]
        fh.write("=" * 74 + f"\n {x['target']}  block {x['block']}  exit via {x['exit_cc']} "
                 f"{x['exit_holder']}\n")
        for i, h in enumerate(t["path"], 1):
            if not h:
                fh.write(f"   {i:>2}  *\n"); continue
            mark = "<== LEFT PK" if abroad(h) and h["ip"] == x["exit_ip"] else (
                   "abroad" if abroad(h) else
                   "squatted" if h["ip"] in FALSIFIED else "")
            rtt = f"{h['rtt']:.0f} ms" if isinstance(h.get("rtt"), (int, float)) else ""
            fh.write(f"   {i:>2}  {h['ip']:<17}{rtt:>8}  {h['cc']:<5}"
                     f"{(h.get('holder') or '')[:30]:<32}{mark}\n")
        fh.write("\n")

print(f"traces classified      {N:,}")
print(f"left Pakistan          {T:,}  ({100*T/N:.2f}%)   <-- a FLOOR, not a rate")
print(f"stayed domestic        {N-T:,}")
print(f"R2 falsified {len(FALSIFIED)+len(FALSIFIED_BUT_FOREIGN)} addresses; R4-prime fence "
      f"{FENCE} ms splits them:")
print(f"   {len(FALSIFIED):>4} behave domestically -> squatted PK space, not a departure")
print(f"   {len(FALSIFIED_BUT_FOREIGN):>4} exceed the fence     -> abroad, though not where they claim")
print(f"\nexit country:")
for cc, n in by_cc.most_common(10):
    f = FLOORS.get(cc, {})
    print(f"   {cc:<4}{n:>6,}   floor {f.get('floor_ms','?')} ms via {f.get('hub','?')}")
if by_ixp:
    print(f"\nexits crossing a foreign internet exchange:")
    for k, n in by_ixp.most_common():
        print(f"   {k[:34]:<36}{n:>6,}")
print(f"\nhighest tromboning rate, networks with >=100 traces:")
print(f"   {'ASN':<9}{'network':<34}{'traces':>8}{'trombone':>10}{'rate':>8}")
for a, n, t in ranked[:12]:
    nm = holder.get(a, f"AS{a}").split(" - ", 1)[-1][:32]
    print(f"   AS{a:<7}{nm:<34}{n:>8,}{t:>10,}{100*t/n:>7.1f}%")
print(f"\nwrote trombone_local.json and routes_trombone.txt")
