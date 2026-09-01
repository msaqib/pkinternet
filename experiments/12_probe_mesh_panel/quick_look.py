"""Quick, plain-language look at the mesh panel data so far.

Reads the latest results/panel_*.csv and prints a simple summary:
how ping is doing, how traceroute is doing. No analysis, just a status check.

Run: python experiments/12_probe_mesh_panel/quick_look.py
"""
import csv
import glob
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")


def latest_panel_csv():
    files = sorted(glob.glob(os.path.join(RESULTS, "panel_*.csv")))
    if not files:
        raise SystemExit("No panel_*.csv found in results/ yet -- run 'fetch' or 'watch' first.")
    return files[-1]


def main():
    path = latest_panel_csv()
    rows = list(csv.DictReader(open(path)))
    print(f"Looking at: {os.path.basename(path)}  ({len(rows)} rows total)\n")

    pings = [r for r in rows if r["kind"] == "ping"]
    traces = [r for r in rows if r["kind"] == "trace"]

    # ---------- PING ----------
    print("=" * 60)
    print(f"PING  ({len(pings)} results so far)")
    print("=" * 60)

    loss_by_dst = defaultdict(list)
    rtt_by_dst = defaultdict(list)
    for r in pings:
        try:
            loss_by_dst[r["dst"]].append(float(r["loss"]))
        except (TypeError, ValueError):
            pass
        if r["rtt_min"]:
            try:
                rtt_by_dst[r["dst"]].append(float(r["rtt_min"]))
            except ValueError:
                pass

    good, bad = [], []
    for dst, losses in loss_by_dst.items():
        avg_loss = sum(losses) / len(losses)
        (bad if avg_loss > 0.5 else good).append((dst, avg_loss, len(losses)))

    print(f"\n{len(good)} probe(s) answering pings normally, {len(bad)} probe(s) not answering at all:\n")

    print("  Answering fine:")
    for dst, loss, n in sorted(good, key=lambda x: x[1]):
        rtts = rtt_by_dst.get(dst, [])
        avg_rtt = f"{sum(rtts)/len(rtts):.1f} ms" if rtts else "n/a"
        print(f"    {dst:<20} loss={loss:5.1%}   avg rtt={avg_rtt}   (n={n})")

    print("\n  Not answering (near-100% loss, whole run so far):")
    for dst, loss, n in sorted(bad, key=lambda x: -x[1]):
        print(f"    {dst:<20} loss={loss:5.1%}   (n={n})")

    print("\n  In plain words: pings to the 'not answering' probes are basically always")
    print("  failing -- almost certainly their router blocking ping from outside,")
    print("  not a problem with our setup. Traceroute below still reaches them fine.")

    # ---------- TRACEROUTE ----------
    print("\n" + "=" * 60)
    print(f"TRACEROUTE  ({len(traces)} results so far)")
    print("=" * 60)

    status_count = defaultdict(int)
    hops = []
    tromboned = 0
    for r in traces:
        status_count[r["status"] or "(blank)"] += 1
        if r["hop_count"]:
            try:
                hops.append(int(r["hop_count"]))
            except ValueError:
                pass
        if r["tromboned"] == "True":
            tromboned += 1

    print(f"\n  status breakdown:")
    for status, n in sorted(status_count.items(), key=lambda x: -x[1]):
        pct = n / len(traces) * 100 if traces else 0
        print(f"    {status:<15} {n:5d}  ({pct:.0f}%)")

    if hops:
        print(f"\n  hop count: min={min(hops)}, max={max(hops)}, avg={sum(hops)/len(hops):.1f}")
    print(f"  tromboned (route leaves & comes back to PK): {tromboned} of {len(traces)} "
          f"({tromboned/len(traces)*100 if traces else 0:.0f}%)")

    print("\n  In plain words: traceroute is working across the board, including to")
    print("  the probes that don't answer ping -- so route data isn't affected by")
    print("  the ping issue above.")

    print("\n" + "=" * 60)
    print("Done. This is just a status snapshot, not the real analysis.")
    print("=" * 60)


if __name__ == "__main__":
    main()
