#!/usr/bin/env python3
"""
Second pass over blocks that build_block_owners.py left unowned.

WHY  Ownership there was derived from announced-prefixes for the 466 ASNs the
     registry calls Pakistani. A block announced by an ASN registered elsewhere
     is invisible to that pass (103.125.144.0/24 / AS137409 is a real example),
     and so is a block announced only as more-specifics.

     This asks network-info directly, per block, which reports whatever ASN
     actually announces it today regardless of that ASN's registry country.
     Blocks that still come back empty are genuinely unannounced.

  python resolve_unowned.py   -> updates block_to_asn.json, asn_holder.json,
                                 writes unannounced_blocks.json
"""
import json, ssl, io, time, urllib.request, threading, queue

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
def get(u, tries=3):
    for i in range(tries):
        try: return json.load(urllib.request.urlopen(u, timeout=60, context=ctx))["data"]
        except Exception:
            if i == tries-1: return None
            time.sleep(1.5)

blocks = json.load(io.open("block_to_asn.json", encoding="utf-8"))
holder = json.load(io.open("asn_holder.json", encoding="utf-8"))
todo = [k for k, v in blocks.items() if v is None]
print(f"unowned blocks to resolve: {len(todo):,}")

lock = threading.Lock(); q = queue.Queue(); [q.put(t) for t in todo]
n = [0]; found = [0]; new_asn = set()
def w():
    while True:
        try: b = q.get_nowait()
        except queue.Empty: return
        ip = b.split("/")[0].rsplit(".", 1)[0] + ".1"
        d = get(f"https://stat.ripe.net/data/network-info/data.json?resource={ip}")
        a = (d.get("asns") or [None])[0] if d else None
        with lock:
            n[0] += 1
            if a:
                blocks[b] = str(a); found[0] += 1
                if str(a) not in holder: new_asn.add(str(a))
            if n[0] % 200 == 0: print(f"   {n[0]}/{len(todo)}  {found[0]} resolved", flush=True)
ths = [threading.Thread(target=w) for _ in range(12)]
[t.start() for t in ths]; [t.join() for t in ths]
print(f"resolved {found[0]:,}; {len(todo)-found[0]:,} genuinely unannounced; {len(new_asn)} new ASNs")

for a in sorted(new_asn):
    o = get(f"https://stat.ripe.net/data/as-overview/data.json?resource=AS{a}")
    holder[a] = (o.get("holder") if o else None) or f"AS{a}"

json.dump(blocks, io.open("block_to_asn.json", "w", encoding="utf-8"))
json.dump(holder, io.open("asn_holder.json", "w", encoding="utf-8"), indent=1)
json.dump(sorted(k for k, v in blocks.items() if v is None),
          io.open("unannounced_blocks.json", "w", encoding="utf-8"), indent=1)
print(f"wrote block_to_asn.json, asn_holder.json ({len(holder)}), unannounced_blocks.json")
