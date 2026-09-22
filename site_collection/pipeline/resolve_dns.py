#!/usr/bin/env python3
"""
Step 1 of the PK/CDN discovery pipeline: DNS-resolve a slice of domains.

Uses explicit public resolvers (8.8.8.8 / 1.1.1.1), not the system/ISP
default. The ISP resolver on this network has been observed silently
returning a wrong-but-valid IP for some domains instead of erroring
(landed several unrelated global sites on a PTCL residential broadband
block, AS17557 PTCLBB-PK) — see filter_pk_cdn.py for the second layer
of defense against this on the PK candidates specifically.

Checkpoints to a JSON cache every CHECKPOINT_EVERY domains, so the run
is safely resumable: kill it any time (laptop sleep, network drop,
ctrl-C) and rerun the same command, it skips domains already resolved.

Run from site_collection/pipeline/:
    python3 resolve_dns.py --slice outputs/tranco_slice_0_300000.txt
"""
import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import dns.resolver

RESOLVERS = ["8.8.8.8", "1.1.1.1"]
CHECKPOINT_EVERY = 200
WORKERS = 30


def resolve_one(domain, resolver_ip):
    r = dns.resolver.Resolver(configure=False)
    r.nameservers = [resolver_ip]
    r.timeout = 4
    r.lifetime = 4
    try:
        ans = r.resolve(domain, "A")
        return ans[0].to_text(), None
    except Exception as e:
        return None, type(e).__name__


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slice", required=True)
    ap.add_argument("--cache", default="outputs/resolved_cache.json")
    args = ap.parse_args()

    with open(args.slice) as f:
        domains = [line.strip() for line in f if line.strip()]

    if os.path.exists(args.cache):
        with open(args.cache) as f:
            cache = json.load(f)
        print(f"Resuming: {len(cache)} domains already resolved")
    else:
        cache = {}

    todo = [d for d in domains if d not in cache]
    print(f"{len(todo)} domains left to resolve out of {len(domains)}")

    done_since_checkpoint = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {
            pool.submit(resolve_one, domain, RESOLVERS[i % len(RESOLVERS)]): (domain, RESOLVERS[i % len(RESOLVERS)])
            for i, domain in enumerate(todo)
        }

        for fut in as_completed(futures):
            domain, resolver_ip = futures[fut]
            ip, err = fut.result()
            cache[domain] = {"ip": ip, "error": err, "resolver": resolver_ip}
            done_since_checkpoint += 1

            if done_since_checkpoint >= CHECKPOINT_EVERY:
                with open(args.cache, "w") as f:
                    json.dump(cache, f)
                done_since_checkpoint = 0
                print(f"  [checkpoint] {len(cache)}/{len(domains)} resolved")

    with open(args.cache, "w") as f:
        json.dump(cache, f)

    resolved = sum(1 for v in cache.values() if v.get("ip"))
    print(f"Done: {resolved}/{len(cache)} resolved successfully")


if __name__ == "__main__":
    main()
