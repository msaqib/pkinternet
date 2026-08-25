#!/usr/bin/env python3
"""
What tromboned traffic would save if it stayed domestic.

Two estimates, both same-site so neither repeats the pooled comparison that mixes
different populations of sites:

  like-for-like  each tromboning probe-site pair against the pairs that reach the SAME
                 site domestically. This is the achievable target, since it is what other
                 operators actually get to that server today.

  frontier       each tromboning pair against the single best RTT any probe in the panel
                 achieves to that site. An upper bound, not an estimate: for one site the
                 best observed RTT is 0.4 ms from a probe essentially beside the server.

Only sites reachable both ways and answering ICMP can be measured, which excludes
ztbl.com.pk and fgeha.gov.pk. Those two carry 57% of all tromboning, so the coverage
caveat belongs in any sentence quoting these numbers.

    python experiments/07_longitudinal_panel/analysis/trombone_savings.py
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
EXCLUDE = {1015491, 7764}


def main():
    f = pd.read_csv(os.path.join(HERE, "final_classified_rounds.csv"))
    d = pd.read_csv(os.path.join(EXP, "results", "b", "panel_20260718_200355.csv"))
    d = d[~d.probe_id.isin(EXCLUDE)].dropna(subset=["rtt_min"])

    rate = 100 * f.trombone.mean()
    print("tromboning rate: %.2f%%  (%d of %d rounds)"
          % (rate, f.trombone.sum(), len(f)))

    pair = f.groupby(["target", "probe_id"]).trombone.mean().reset_index(name="frac")
    rtt = d.groupby(["target", "probe_id"]).rtt_min.median().reset_index(name="rtt")
    j = pair.merge(rtt, on=["target", "probe_id"])
    j["state"] = j.frac.map(lambda x: "tromboned" if x > 0.5 else "local")

    rows = []
    for site, g in j.groupby("target"):
        t, l = g[g.state == "tromboned"], g[g.state == "local"]
        if len(t) and len(l):
            rows.append(dict(site=site, n_trom=len(t), n_local=len(l),
                             trom_rtt=t.rtt.median(), local_rtt=l.rtt.median(),
                             frontier=g.rtt.min()))
    r = pd.DataFrame(rows)
    if r.empty:
        print("no site is reachable both ways with ping data")
        return
    r["save_like"] = r.trom_rtt - r.local_rtt
    r["pct_like"] = 100 * r.save_like / r.trom_rtt
    r["save_front"] = r.trom_rtt - r.frontier
    r["pct_front"] = 100 * r.save_front / r.trom_rtt

    print("\nsites reachable both ways, with ping data on both sides")
    print("%-24s %5s %6s %9s %10s %9s %7s"
          % ("site", "trom", "local", "trom RTT", "local RTT", "saving", "pct"))
    for _, x in r.sort_values("save_like", ascending=False).iterrows():
        print("%-24s %5d %6d %8.1f %10.1f %8.1f %6.0f%%"
              % (x.site, x.n_trom, x.n_local, x.trom_rtt, x.local_rtt,
                 x.save_like, x.pct_like))

    w = r.n_trom
    print("\nLIKE-FOR-LIKE, the achievable target")
    print("  pair-weighted saving   %.1f ms   (%.0f%%)"
          % ((r.save_like * w).sum() / w.sum(), (r.pct_like * w).sum() / w.sum()))
    print("  median saving          %.1f ms   (%.0f%%)"
          % (r.save_like.median(), r.pct_like.median()))
    print("\nFRONTIER, an upper bound")
    print("  pair-weighted saving   %.1f ms   (%.0f%%)"
          % ((r.save_front * w).sum() / w.sum(), (r.pct_front * w).sum() / w.sum()))
    print("\ncoverage: %d tromboning pairs across %d sites; ztbl.com.pk and fgeha.gov.pk"
          % (int(w.sum()), len(r)))
    print("block ICMP entirely and cannot be measured this way.")


if __name__ == "__main__":
    main()
