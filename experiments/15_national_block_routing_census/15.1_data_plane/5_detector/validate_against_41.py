#!/usr/bin/env python3
"""
Validate detector.py against the frozen Exp 4.1 census, where the answer is known.

Read-only. Touches nothing in experiment 04.1. No network, no measurement credits.

    python validate_against_41.py

Checks, in order:
  A  the RTT arithmetic reproduces the frozen census max_rtt on all 18,260 rows
  B  DOMESTIC_OBSERVED admits the known squatters and rejects the known non-squatters
  C  the rate-limit guard fires only on same-address adjacent jumps
  D  the effect of both corrections on the headline numbers
"""
import os, re, io, csv, json, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import detector as D

RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "..", "..",
                   "04.1_small_isp_tromboning", "results", "run_20260627_192918")
RUN = os.path.normpath(RUN)
CENSUS = os.path.join(RUN, "census_20260627_192918.csv")
RAW    = os.path.join(RUN, "raw_20260627_192918.json")
ALL    = os.path.join(RUN, "routes_all_20260703_112939.txt")
TROM   = os.path.join(RUN, "routes_tromboning_20260703_124138.txt")
SOURCES = {1016126: "ptcl.khi", 1015679: "nova.lhe", 7613: "zcom.lhe",
           1016036: "cybernet.hrp", 1016154: "cybernet.khi",
           60223: "nayatel.isb", 64535: "orbit.fsd"}
HOP = re.compile(r'^\s*(\d+)\s+([\d.]+)\s+(\d+\.\d+\.\d+\.\d+)')
ok = True


def check(label, cond, detail=""):
    global ok
    ok = ok and cond
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))


print("A. RTT arithmetic reproduces the frozen census")
raw = json.load(io.open(RAW, encoding="utf-8"))
stats = {}
for _, results in raw.items():
    for r in results:
        src, dst = SOURCES.get(r.get("prb_id")), r.get("dst_addr")
        if not src or not dst:
            continue
        mx = mj = 0.0
        prev = None
        for h in r.get("result", []):
            pk = h.get("result", [])
            ip = next((p.get("from") for p in pk if p.get("from")), None)
            v = [p["rtt"] for p in pk if p.get("rtt") is not None]
            rtt = min(v) if v else None
            if not ip:
                continue
            if rtt is not None and rtt <= D.QUEUE_CEIL:
                mx = max(mx, rtt)
                if prev is not None:
                    mj = max(mj, rtt - prev)
                prev = rtt
            elif rtt is not None and prev is None:
                prev = min(rtt, D.QUEUE_CEIL)
        stats[(src, dst)] = (mx, mj)
rows = list(csv.DictReader(io.open(CENSUS, encoding="utf-8")))
match = sum(1 for r in rows if r["max_rtt"] and (r["source"], r["target_ip"]) in stats
            and abs(stats[(r["source"], r["target_ip"])][0] - float(r["max_rtt"])) < 0.15)
check("max_rtt matches frozen census", match == len(rows), f"{match} of {len(rows)}")

print("\nB. DOMESTIC_OBSERVED admits the squatters, rejects the rest")
cur, samples = None, collections.defaultdict(lambda: collections.defaultdict(list))
for ln in io.open(ALL, encoding="utf-8", errors="replace"):
    m = re.search(r'probe\s+\d+\s+-\s+(\S+)', ln)
    if m:
        cur = m.group(1); continue
    h = HOP.match(ln)
    if h:
        samples[h.group(3)][cur].append(float(h.group(2)))
DOM = D.build_domestic_observed(samples)
print(f"       {len(DOM)} public addresses admitted, from {len(samples)} seen")
for ip, want, why in [("182.45.51.22",  True,  "CHINANET inside PTCL, Z-Com median 2.4 ms"),
                      ("70.70.71.137",  True,  "Shaw on Nova CPE, median 1.8 ms"),
                      ("149.40.227.134", True, "Cogent on Transworld, Z-Com median 1.1 ms"),
                      ("192.33.4.12",   False, "C-root, 143 ms median, one 3.4 ms reading"),
                      ("199.7.83.42",   False, "L-root anycast"),
                      ("27.111.230.170", False, "Equinix Singapore, 95.5 ms median")]:
    check(f"{ip:16} {'in' if want else 'out':3}  ({why})", (ip in DOM) == want)

print("\nC. rate-limit guard")
blocks = io.open(TROM, encoding="utf-8", errors="replace").read().split("=" * 80)
fired = same = 0
for b in blocks:
    ev = re.search(r'evidence=(\S+)', b)
    if not ev or not ev.group(1).startswith("rtt"):
        continue          # the guard only ever runs on the RTT branch
    hops = [(float(h.group(2)), h.group(3), "", "") for ln in b.splitlines()
            if (h := HOP.match(ln))]
    if len(hops) < 2:
        continue
    if D.rate_limit_artifact(hops):
        fired += 1
        seq = [(r, ip) for r, ip, *_ in hops]
        if any(seq[i][1] == seq[i-1][1] and seq[i][0]-seq[i-1][0] >= D.JUMP_THRESH
               for i in range(1, len(seq))):
            same += 1
check("every firing is a same-address adjacent jump", fired == same, f"{fired} fired")
check("matches the 71 RTT-evidence traces identified by hand", fired == 71, f"{fired}")

print("\nD. effect on the headline numbers")
exit_ip = {}
for b in blocks:
    s = re.search(r'probe\s+\d+\s+-\s+(\S+)', b)
    t = re.search(r'->\s+(\d+\.\d+\.\d+\.\d+)', b)
    if not (s and t):
        continue
    for ln in b.splitlines():
        if "<<< LEAVES PK" in ln and (h := HOP.match(ln)):
            exit_ip[(s.group(1), t.group(1))] = h.group(3); break
rl = set()
for b in blocks:
    s = re.search(r'probe\s+\d+\s+-\s+(\S+)', b)
    t = re.search(r'->\s+(\d+\.\d+\.\d+\.\d+)', b)
    ev = re.search(r'evidence=(\S+)', b)
    if not (s and t and ev and ev.group(1).startswith("rtt")):
        continue
    hops = [(float(h.group(2)), h.group(3), "", "") for ln in b.splitlines()
            if (h := HOP.match(ln))]
    if D.rate_limit_artifact(hops):
        rl.add((s.group(1), t.group(1)))

def verdict(r):
    if not r["status"].startswith("trombone"):
        return False
    k = (r["source"], r["target_ip"])
    if r["status"] == "trombone_hop":
        ip = exit_ip.get(k)
        if ip and ip in DOM:
            mx, mj = stats[k]
            return mj >= D.JUMP_THRESH or mx >= D.HIGH_RTT
        return True
    return k not in rl

N = len(rows)
before = sum(1 for r in rows if r["status"].startswith("trombone"))
after = sum(1 for r in rows if verdict(r))
squat = sum(1 for r in rows if r["status"] == "trombone_hop" and not verdict(r))
ratel = sum(1 for r in rows if r["status"] == "trombone_rtt" and not verdict(r))
print(f"       detour rate    {before}/{N} = {100*before/N:.1f}%   ->   {after}/{N} = {100*after/N:.1f}%")
print(f"       removed by squatted-address rule : {squat}")
print(f"       removed by rate-limit guard      : {ratel}")
check("both corrections remove verdicts", squat > 0 and ratel > 0)
check("no verdict is created", after <= before)

print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
sys.exit(0 if ok else 1)
