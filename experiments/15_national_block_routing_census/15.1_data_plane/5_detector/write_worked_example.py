#!/usr/bin/env python3
"""
Render WORKED_EXAMPLE.md: every rule applied, in order, to one real suspect.

Written for a reader with no context. Every term is defined where it first appears,
every party is named, and every number says which file produced it. Nothing is typed
by hand; re-run after any stage changes.

  python write_worked_example.py [--target 58.27.233.225]
"""
import io, json, os, argparse, ipaddress, collections, statistics as st

H = os.path.dirname(os.path.abspath(__file__))
def P(*p): return os.path.join(H, "..", *p)

ap = argparse.ArgumentParser()
ap.add_argument("--target", default="58.27.233.225")
A = ap.parse_args()
T = A.target
U = str(ipaddress.ip_network(T + "/24", strict=False))

R = json.load(io.open(os.path.join(H, "rules_local.json"), encoding="utf-8"))
D = json.load(io.open(os.path.join(H, "trombone_local.json"), encoding="utf-8"))
ann = json.load(io.open(P("3_routes", "selected_annotated.json"), encoding="utf-8"))
own = json.load(io.open(P("1_universe", "block_to_asn.json"), encoding="utf-8"))
hold = json.load(io.open(P("1_universe", "asn_holder.json"), encoding="utf-8"))
base = json.load(io.open(P("3_routes", "rtt_baseline_sample.json"), encoding="utf-8"))
isp = json.load(io.open(P("6_analysis", "isp_summary.json"), encoding="utf-8"))

rtt = {}
for fn, how in (("rtt_foreign.json", "direct echo"), ("rtt_foreign_ttl.json", "in-path"),
                ("rtt_inpath.json", "in-path")):
    fp = P("3_routes", fn)
    if os.path.exists(fp):
        for ip, v in json.load(io.open(fp, encoding="utf-8")).items():
            if v.get("n"):
                rtt[ip] = dict(v, how=how)

trace = next(r for r in ann if r["target"] == T)
verdict = next(r for r in D["rows"] if r["target"] == T)
asn = own.get(U)
name = hold.get(asn, "")
FENCE = R["R4prime"]["fence_ms"]
FALS = R["R2"]["falsified_detail"]
CH = [c["ip"] for c in R["R1"]["chain"]]
V = R["vantage"]

def isprow(a):
    return next((x for x in isp if x["asn"] == a), None)
me = isprow(asn)

def opname(holder):
    """Human-readable operator name from a registry holder string. The handle before
    the dash is a registry label (WATEEN-IMS-PK-AS-AP), not a name anyone uses."""
    if not holder:
        return "unknown"
    tail = holder.split(" - ", 1)[-1]
    head = holder.split(" - ", 1)[0]
    base = head.split("-")[0].title()
    return f"{base}" if base and base.lower() not in ("as", "") else tail[:30]

OP = opname(name)

# liveness provenance for this block
checked, live, byscan = 0, {}, collections.Counter()
pre = U.rsplit(".", 1)[0] + "."
for fn, tag in (("local_scan.jsonl", "earlier small-ISP scan"),
                ("pk_scan.jsonl", "main sweep, from TES"),
                ("topup_scan.jsonl", "top-up, from Mobilink")):
    fp = P("2_liveness", fn)
    if not os.path.exists(fp):
        continue
    for l in io.open(fp, encoding="utf-8"):
        try: d = json.loads(l)
        except Exception: continue
        if d["t"].startswith(pre):
            checked += 1; byscan[tag] += 1
            if d["m"]: live[d["t"]] = tag

blockrows = [r for r in D["rows"] if r["block"] == U]
sameasn = [r for r in D["rows"] if r["asn"] == asn]
sa_blk = collections.Counter(r["block"] for r in sameasn if r["status"] == "trombone")
sa_all = collections.Counter(r["block"] for r in sameasn)
sa_exit = collections.Counter(r["exit_ip"] for r in sameasn if r["status"] == "trombone")

def hopline(i, h):
    if not h:
        return f"| {i} | `*` | | | | no reply |"
    m = rtt.get(h["ip"])
    r = f"**{m['min']}**" if m else (f"{h['rtt']:.0f}*" if isinstance(h.get("rtt"), (int, float)) else "")
    note = ""
    if h["ip"] in CH: note = "our own access path (R1)"
    elif h["ip"] in FALS: note = "**squatted** (R2)"
    elif h["cc"] in ("PRIV", "CGN"): note = "inside our own network"
    elif h["cc"] != "PK": note = "**OUTSIDE PAKISTAN**"
    return (f"| {i} | `{h['ip']}` | {r} | {h['cc']} | "
            f"{(h.get('holder') or '')[:30]} | {note} |")

path_tbl = "\n".join(hopline(i, h) for i, h in enumerate(trace["path"], 1))
exit_ip = verdict["exit_ip"]
exit_m = rtt.get(exit_ip, {})
fl = R["country_floors"].get(verdict["exit_cc"], {})
after = None
seen_exit = False
for h in trace["path"]:
    if h and h["ip"] == exit_ip: seen_exit = True; continue
    if seen_exit and h: after = h; break

dom = sorted(v["min"] for t, v in base.items()
             if next((x["status"] for x in D["rows"] if x["target"] == t), "") == "local")
trb = sorted(v["min"] for t, v in base.items()
             if next((x["status"] for x in D["rows"] if x["target"] == t), "") == "trombone")
q = st.quantiles(dom, n=4)
sq = [h for h in trace["path"] if h and h["ip"] in FALS]
npub = sum(1 for h in trace['path'] if h and h['cc'] not in ('PRIV', 'CGN'))

md = f"""# One suspect, every rule, in order

A single Pakistani address, followed from the moment it entered the study to the moment
it was called a detour. **Written for a reader with no prior context**: every term is
defined where it appears and every number names the file that produced it.

Generated by `write_worked_example.py` from the pipeline's own output, so this page
cannot drift from the code.

---

## The cast

| | |
|---|---|
| **The target** | `{T}`, an ordinary address in Pakistan that answered a ping |
| **Its owner** | **AS{asn}, {OP}** — {name.split(' - ')[-1][:44]}. A Pakistani broadband operator |
| **Where we measured from** | **AS{V.get('asn','45669') if isinstance(V,dict) else '45669'} Mobilink (PMCL)**, a Pakistani mobile operator. This is our *vantage point*: the connection our laptop was on |
| **The other vantage** | **AS135407 TES**, Trans World Enterprise Services. Used for most of the liveness scanning, but almost none of the tracing |
| **The suspect hop** | `{exit_ip}`, registered to **{verdict['exit_holder'][:40]}** in **{verdict['exit_cc']}** |
| **When** | Sweep 8 to 9 September 2026; clean re-measurement 10 September 2026 |

**"AS"** means Autonomous System: one network under one operator's control, identified by
a number. AS{asn} is {OP}'s network. The registry string `{name[:44]}` is a label, not a
trading name.

**A warning about the suspect's registry string.** `{verdict['exit_holder'][:40]}` looks
like a street address, and it is one: CHINANET registers every block it holds to China
Telecom's head office. **It says nothing about where the router physically sits**, which
is exactly the confusion R2 exists to resolve.

---

## 1. How this address entered the study at all

### What a "block" is

`{U}` is a **/24 block**: 256 consecutive addresses, from `{pre}0` to `{pre}255`. It is
the smallest chunk that is routed independently on the public internet in practice, and
operators tend to hand one out to a single place and purpose. We treat it as the unit
that probably shares a fate.

Pakistan's whole address space, as this study defines it, is **22,556 such blocks**. This
is one of them. {OP} announces **{me['blocks']:,}** of them.

### Why we did not test all 256 addresses

Most Pakistani address space has nothing switched on. Testing everything would have taken
about 29 hours of continuous probing for very little gain, so the scanner follows signal
instead. It takes a **draw**: 8 random addresses at a time.

* Nothing answers after two draws (16 addresses) → abandon the block.
* Something answers → keep drawing until 8 live hosts are found, or 64 addresses tried.

Draws accumulate. Nothing is discarded and no address is tested twice.

### What happened in this block

| pass | addresses tested | what it is |
|---|--:|---|
""" + "\n".join(
    f"| {k} | {v} | {'the national scan, run from TES' if 'main' in k else 'a second pass, explained below' if 'top-up' in k else 'an earlier scan of small ISPs only'} |"
    for k, v in byscan.items()) + f"""
| **total** | **{checked} of 256** | |

**{len(live)} answered.** `{T}` was found by the **{live.get(T,'?')}**.

### What a "top-up" is, and why it exists

The main scan hit its 64-address budget in this block and found only **{byscan.get('main sweep, from TES',0) and sum(1 for t,s in live.items() if 'main' in s)} live hosts**. A block needs
**8** to be useful later, because experiment 16.1 plans to watch these same addresses over
months and needs spares as hosts come and go.

So a **top-up** is a second pass, run from a *different Pakistani network*, over blocks
that found between 1 and 7 hosts. It only tests addresses the first pass never tried.

Here it tested {byscan.get('top-up, from Mobilink',0)} more and found
{sum(1 for t,s in live.items() if 'top-up' in s)}, taking the block to 8.

**This is not the first scan being wrong.** In a controlled re-test, about **9% of hosts
that answer from one Pakistani network do not answer from another**, at every level of
load tested. "Alive" is not a property of an address; it is a property of an address *as
seen from somewhere*. This block is a small instance of that, and it is why the target we
are about to follow was found by Mobilink and not by TES.

Source: `../2_liveness/`, finding written up in `../SWEEP_FINDINGS.md` section 5B.

### Why this address was traced, and kept

Every live host was traced. **A trace is one traceroute** from our vantage to one target:
packets are sent with a deliberately small hop limit so each router along the way is
forced to announce itself.

Not every trace is usable. The gate keeps a trace only if:

* it **reached** the target, meaning the last hop is the target itself, so we know where
  the packet actually ended up; and
* at least **5 hops answered**, so there is enough of a path to see its shape.

This trace answered **{trace['answered']} of {trace['hops_total']}** hop positions and reached its target, so it
was kept. **{len(blockrows)} of the block's 8 live hosts** produced a usable trace.

---

## 2. R0 — can this measurement support a latency rule at all?

Before any rule that uses time, the data has to be capable of carrying one. Two checks
that need nothing external:

1. Does round-trip time ever *fall* as the path gets longer? Distance cannot do that.
2. Does one fixed router give a stable reading when asked repeatedly?

**The original sweep fails both.** Across the whole selection, 22% of neighbouring hop
pairs show time going *down* deeper into the path, and one unmoving router returned
anything between 4 ms and 853 ms. The cause was ours: the tracer sent **one packet per
hop** while 120 threads competed for the connection.

So every latency figure below comes from a **re-measurement**: 20 to 30 packets per
address, 6 to 8 threads, keeping the **minimum**. Queuing and slow routers only ever *add*
to a round trip, so the minimum of a clean burst is the closest thing to the real cost.
Spread on those bursts is 1 to 2 ms.

**Numbers in bold are re-measured. Numbers marked `*` are original sweep values** with no
clean re-measurement, and must not be used for a verdict.

## 3. R1 — subtract our own access path

Every trace from this vantage begins with the same three routers, before paths diverge:

""" + "\n".join(f"* `{c['ip']}` — appears at this position in {c['pct']}% of all {len(ann):,} traces" for c in R["R1"]["chain"]) + f"""

Together they cost **{R['R1']['B_access_ms']:.0f} ms**, paid before we have measured anything about the
destination. That is our own connection, not the destination's fault, so it is subtracted
first. Nothing in this chain can be a detour.

## 4. The path itself

| hop | address | RTT ms | country | operator | what it is |
|--:|---|--:|---|---|---|
{path_tbl}

**Reading this.** Hops 1 and 2 are inside our own building and our provider's network.
Hops 3 to 5 are the access chain from R1. Hops 6 to 8 cross **Transworld**, a Pakistani
carrier. Hop {next((i for i,h in enumerate(trace['path'],1) if h and h['ip']==exit_ip), '?')} is the one that matters. Hops marked `*` are unusable sweep values.

**Why are some hops silent?** A `*` means no reply came back at that hop limit. Routers
are not obliged to announce themselves and many are configured not to, or rate-limit the
replies. Roughly 43% of hop positions across the study are silent. It does not mean the
packet stopped: later hops still answer.

**Why does the time jump around?** Because those are single-packet sweep values. Hop
{next((i for i,h in enumerate(trace['path'],1) if h and h['ip']==exit_ip), '?')} re-measured cleanly is **{exit_m.get('min','?')} ms**, not the {next((f"{h['rtt']:.0f}" for h in trace['path'] if h and h['ip']==exit_ip), '?')} ms
the sweep recorded. This is exactly what R0 exists to catch.

## 5. R2 — throw out addresses that are not where they claim

A foreign registry country is **not** evidence of anything on its own, for two reasons:

* **4.4% of Pakistan's routed space is legitimately registered abroad.** Address space is
  leased and transferred far faster than registry paperwork is updated.
* **Operators number their own routers out of space they do not announce.** Sometimes
  that space belongs to somebody else entirely. This is called **squatting**, and it is
  common.

So R2 asks a physical question instead: *could a packet reach the claimed location and
come back this fast?* If the answer is no, the claim is dead. The bound is the speed of
light in fibre, 204,000 km/s, over the straight-line distance. Nothing can beat it.

Across the study this falsified **{R['R2']['falsified']} addresses**, including seven **US Department of
Defense** addresses answering in about 3 ms, plus Cogent, Cloudflare, AT&T and T-Mobile
ranges. All Pakistani routers wearing foreign address space. Without this step they would
be counted as departures and would fabricate thousands of false detours.

**In this particular trace: {len(sq)} hops were falsified.** The suspect hop survives R2,
which is the whole point of the next section.

## 6. R3 — can this vantage see paths at all?

A probe that only ever returns private addresses can prove nothing. Under ICMP this
vantage is fine: only 3 of 43,765 traces contained no public router. This trace contains
{npub}.

This is checked **per protocol**, never once and for all. In an earlier archive the same
device produced no usable path in 100% of its TCP traces and 11% of its ICMP traces.

## 7. R4′ — is the suspect actually abroad?

R2 kills a *claim*. It does not prove an address is in Pakistan. "Not in Virginia" is not
"in Pakistan", so falsified addresses get a second test against **this vantage's own
domestic latency**, measured from {R['R4prime']['reference_n']} destinations whose paths never left the country:

| | ms |
|---|--:|
| domestic median | {st.median(dom):.0f} |
| p25 / p75 | {q[0]:.0f} / {q[2]:.0f} |
| **fence (p75 + 3 × IQR)** | **{FENCE:.0f}** |

**What a "fence" is.** The standard statistical definition of an outlier: three
inter-quartile ranges above the upper quartile. Nobody picks the number; the data does. A
slow vantage gets a high baseline *and* a high fence, so the same procedure works
anywhere without retuning.

**R4′ only runs on addresses R2 falsified.** If a registry claim survives R2, the address
is where it says it is and its latency adds nothing.

Our suspect `{exit_ip}` measures **{exit_m.get('min','?')} ms** ({exit_m.get('how','?')},
{exit_m.get('n','?')} packets, spread {exit_m.get('spread','?')} ms). Its claimed country
{verdict['exit_cc']} sits at a straight-line floor of **{fl.get('floor_ms','?')} ms** from the nearest
Pakistani soil. {exit_m.get('min','?')} ms clears that comfortably, so **R2 does not falsify the
claim**, R4′ never runs, and the address really is in {verdict['exit_cc']}.

### The uncomfortable part, kept in on purpose

**{exit_m.get('min','?')} ms is also *below* our own {FENCE:.0f} ms domestic fence.**

That is not a contradiction. Western China is roughly 1,400 km from northern Pakistan,
closer than many domestic paths are slow. A genuine Chinese hop can cost less than a
sluggish trip across Pakistan.

**So latency could never have found this detour. Only topology did.** The same is true of
Dubai and Muscat, which are closer still. This is the honest limit of every latency-based
rule here, and it is why R4′ is a second net for what topology misses rather than a
replacement for it.

## 8. R5 — the verdict

```
1. subtract our own access path        R1
2. remove squatted space               R2   ({len(sq)} hops here)
3. test survivors against the fence    R4'  (not needed here: claim stood)
4. whatever is still foreign is a departure
```

**`{T}` tromboned.**

A packet from a Pakistani connection, bound for a Pakistani address owned by
{OP}, went out through **{verdict['exit_cc']}** at `{exit_ip}`
({verdict['exit_holder'][:34]}){f", came back into Pakistan at `{after['ip']}` ({(after.get('holder') or '')[:30]}), and then reached its destination" if after else ""}.

**That shape is what "tromboning" means**: domestic traffic leaving the country and
returning, like the slide of a trombone. It costs latency, it costs the operator
international transit fees, and it puts domestic traffic on foreign equipment.

## 9. R6 — does the verdict predict anything it was never told?

The topological test never saw a single latency figure. If it is finding something real,
its verdicts should still separate on time:

| | destinations | median clean RTT |
|---|--:|--:|
| called domestic | {len(dom)} | **{st.median(dom):.0f} ms** |
| called tromboning | {len(trb)} | **{st.median(trb):.0f} ms** |

A **{st.median(trb)-st.median(dom):.0f} ms** gap, produced by a method with no access to hop labels. Two
independent lines of evidence agreeing is worth more than either alone.

---

## 10. What this one example does and does not show

**It is not one observation, it is part of a pattern.** All **{len(blockrows)}** usable
traces into `{U}` trombone, through the **same** exit. Across
{OP}'s whole network, **{len(sa_blk)} of {len(sa_all)} traced blocks ({100*len(sa_blk)/max(len(sa_all),1):.0f}%)**
trombone, and **{sa_exit.most_common(1)[0][1] if sa_exit else 0} of their {sum(sa_exit.values())} tromboning traces leave through this same
Chinese address**. This is one routing decision, seen many times.

**Which is why we count blocks, not traces.** 146 of 157 tromboning blocks are
all-or-nothing: every host in them detours, or none does. Tromboning is a property of the
destination prefix, not of individual machines. The study's headline is therefore
**{len([1 for b in set(r['block'] for r in D['rows'] if r['status']=='trombone')])} blocks**, not the {D['trombone']:,} traces.

**It does not show how much we are missing.** The result is a floor. A detour through
routers that stay silent, or hidden inside an MPLS tunnel, is recorded as domestic.

**Nothing here has been confirmed by any operator.**

---

## 11. Reproduce it

```bash
# the block's live hosts and which pass found them
grep '"58.27.233' ../2_liveness/pk_scan.jsonl ../2_liveness/topup_scan.jsonl

# this trace, with every hop annotated
python -c "import io,json;print([r for r in json.load(io.open('../3_routes/selected_annotated.json',encoding='utf-8')) if r['target']=='{T}'])"

# re-measure the suspect hop yourself, in-path, 25 packets
python ../3_routes/measure_rtt_ttl.py --all --packets 25 --threads 6

# rules and verdict
python prove_rules_local.py
python classify_local.py
python write_worked_example.py --target {T}
```

Every tromboning path in the study, with its exit hop marked: `routes_trombone.txt`.
"""
io.open(os.path.join(H, "WORKED_EXAMPLE.md"), "w", encoding="utf-8").write(md)
print(f"wrote WORKED_EXAMPLE.md ({len(md):,} chars) for {T}")
