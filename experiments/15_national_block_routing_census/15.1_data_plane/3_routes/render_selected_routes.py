#!/usr/bin/env python3
"""
Render the selected traces as a readable text file, and fill in any holder names
that the annotation pass left blank.

WHY  No verdict ships without the paths a reader can check it against. This is the
     human-readable companion to selected_annotated.json.

MARKERS in the right-hand column
  private     RFC 1918 or CGNAT space, no operator attribution possible
  IXP         an internet exchange fabric. The hop belongs to the exchange, not to
              either peer, and must not be counted as a foreign hop for the peer.
  unannounced address space carrying no BGP announcement. Almost all of it is
              operator backbone (Transworld, Wateen) numbered out of space the
              operator does not announce. Attribution here comes from whois, not BGP.
  FOREIGN     a hop outside Pakistan. A candidate for tromboning, NOT a finding:
              the latency rules in 5_detector/RULES.md decide that.

  python render_selected_routes.py [--limit 2000]
"""
import io, json, os, argparse

H = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=2000, help="traces to render, 0 for all")
A = ap.parse_args()

ann = json.load(io.open(os.path.join(H, "selected_annotated.json"), encoding="utf-8"))
holder = json.load(io.open(os.path.join(H, "..", "1_universe", "asn_holder.json"), encoding="utf-8"))

filled = 0
for r in ann:
    for h in r["path"]:
        if h and h.get("asn") and not h.get("holder"):
            n = holder.get(str(h["asn"]))
            if n:
                h["holder"] = n
                filled += 1
json.dump(ann, io.open(os.path.join(H, "selected_annotated.json"), "w", encoding="utf-8"))
print(f"filled {filled:,} blank holder names from asn_holder.json")

rows = ann if A.limit == 0 else ann[:A.limit]
out = io.open(os.path.join(H, "selected_routes.txt"), "w", encoding="utf-8")
out.write(f"""Selected traces from the all-Pakistan route sweep.
Gate: the trace reached its target AND at least 5 hops answered.
{len(ann):,} traces selected in total; {len(rows):,} rendered here.

Column 4 is the country the hop's address is registered to. Column 5 is the ASN
announcing it, blank where nothing announces it. FOREIGN marks a hop outside
Pakistan: a candidate for tromboning, not a finding. IXP marks an exchange fabric,
which belongs to the exchange rather than to either peer.

""")
for r in rows:
    out.write("=" * 74 + "\n")
    out.write(f" {r['target']}   block {r['block']}   "
              f"{r['answered']}/{r['hops_total']} hops, {r['gaps']} timeouts\n")
    for i, h in enumerate(r["path"], 1):
        if not h:
            out.write(f"   {i:>2}  *\n")
            continue
        cc, kind = h["cc"], h.get("kind", "announced")
        mark = ("private" if cc in ("PRIV", "CGN") else
                "IXP" if kind == "ixp" else
                "unannounced" if kind == "unannounced" else
                "FOREIGN" if cc not in ("PK", "CGN", "??") else "")
        asn = f"AS{h['asn']}" if h.get("asn") else ""
        rtt = f"{h['rtt']:.0f} ms" if isinstance(h.get("rtt"), (int, float)) else ""
        name = "" if cc in ("PRIV", "CGN") else (h.get("holder") or "")[:34]
        out.write(f"   {i:>2}  {h['ip']:<17}{rtt:>8}  {cc:<5}{asn:<10}{mark:<12}{name}\n")
    out.write("\n")
out.close()
print(f"wrote selected_routes.txt ({len(rows):,} traces)")
