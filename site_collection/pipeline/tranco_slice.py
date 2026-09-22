#!/usr/bin/env python3
"""
Pull a rank-range slice of the Tranco top-sites list for the PK/CDN
discovery pipeline. Not filtered by TLD, any domain in the range is
kept, the point is to find non-.pk sites that turn out to be
PK-hosted or CDN-hosted.

Run from site_collection/pipeline/:
    python3 tranco_slice.py --start 0 --end 300000
    python3 tranco_slice.py --start 300000 --end 500000
"""
import argparse
from tranco import Tranco


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    t = Tranco(cache=True, cache_dir=".tranco")
    latest = t.list()
    domains = latest.top(args.end)[args.start:args.end]

    out = args.out or f"outputs/tranco_slice_{args.start}_{args.end}.txt"
    with open(out, "w") as f:
        for d in domains:
            f.write(d + "\n")

    print(f"Saved {len(domains)} domains (rank {args.start}-{args.end}) to {out}")


if __name__ == "__main__":
    main()
