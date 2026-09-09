#!/usr/bin/env python3
"""
Map every /24-equivalent in the scan universe to the ASN that announces it,
and give every ASN its registered holder name.

WHY  The scan and route sweeps record blocks, not operators. To report anything
     per ISP we need block -> ASN -> name. Nothing downstream should re-query
     RIPEstat, so this caches both maps to disk.

SOURCE  announced-prefixes per PK ASN (routing view) for ownership; as-overview
        for the holder string. Registry-only blocks that nobody announces get
        asn=None and are reported as "unannounced" rather than silently dropped.

NOTE  A /24 can sit inside prefixes announced by more than one ASN (a covering
      aggregate plus a more-specific). The LONGEST matching prefix wins, which is
      what a router would do. Ties are broken by the smaller ASN for determinism.

  python build_block_owners.py        -> block_to_asn.json, asn_holder.json
"""
import json, ssl, io, time, ipaddress, urllib.request, threading, queue, collections

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
def get(u, tries=3):
    for i in range(tries):
        try: return json.load(urllib.request.urlopen(u, timeout=90, context=ctx))["data"]
        except Exception:
            if i == tries-1: return None
            time.sleep(2)

U = json.load(io.open("pk_universe.json", encoding="utf-8"))
asns = U["asns"]
print(f"ASNs to query: {len(asns):,}")

pref = {}      # prefix -> set(asn)
holder = {}
lock = threading.Lock(); q = queue.Queue(); [q.put(a) for a in asns]; n = [0]; errs = []
def w():
    while True:
        try: a = q.get_nowait()
        except queue.Empty: return
        r = get(f"https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{a}")
        o = get(f"https://stat.ripe.net/data/as-overview/data.json?resource=AS{a}")
        with lock:
            n[0] += 1
            if o: holder[a] = (o.get("holder") or f"AS{a}").strip()
            if r is None: errs.append(a)
            else:
                for p in r.get("prefixes", []):
                    px = p["prefix"]
                    if ":" in px: continue
                    pref.setdefault(px, set()).add(a)
            if n[0] % 50 == 0: print(f"   {n[0]}/{len(asns)}", flush=True)
ths = [threading.Thread(target=w) for _ in range(12)]
[t.start() for t in ths]; [t.join() for t in ths]
print(f"prefixes: {len(pref):,} announced ({len(errs)} ASN errors)")

# index announced prefixes by length for longest-match
bylen = collections.defaultdict(dict)
for px, owners in pref.items():
    try:
        net = ipaddress.ip_network(px, strict=False)
        bylen[net.prefixlen][int(net.network_address)] = sorted(owners, key=int)[0]
    except Exception: pass
lens = sorted(bylen, reverse=True)

units = []
for s in U["networks"]:
    net = ipaddress.ip_network(s)
    units.extend([net] if net.prefixlen >= 24 else net.subnets(new_prefix=24))
print(f"units: {len(units):,} /24-equivalents")

out = {}; unowned = 0
for u in units:
    a = int(u.network_address); owner = None
    for L in lens:
        if L > 24: continue                    # a /25+ cannot cover a whole /24
        if (a >> (32-L)) << (32-L) in bylen[L]:
            owner = bylen[L][(a >> (32-L)) << (32-L)]; break
    if owner is None: unowned += 1
    out[str(u)] = owner
print(f"unowned (registry-only, announced by nobody): {unowned:,}")

json.dump(out, io.open("block_to_asn.json", "w", encoding="utf-8"))
json.dump(holder, io.open("asn_holder.json", "w", encoding="utf-8"), indent=1)
print(f"wrote block_to_asn.json ({len(out):,}) and asn_holder.json ({len(holder):,})")
