#!/usr/bin/env python3
"""
Retry domains that failed with LifetimeTimeout in resolve_dns.py's
first pass. That error means "no answer arrived in time", not "this
domain doesn't exist" — unlike NXDOMAIN/NoAnswer/NoNameservers, which
stay treated as final, confirmed results.

Up to 2 attempts per domain, alternating resolver, longer per-query
timeout than the first pass (a live spot-check showed some of these,
e.g. tumblr.com, resolve fine on a second try).

Updates outputs/resolved_cache.json in place: recovers any domain that
succeeds this time, leaves the timeout error on ones that still fail,
does not touch domains that already have a confirmed non-timeout result.

Checkpointed/resumable the same way as resolve_dns.py.

Run from site_collection/pipeline/:
    python3 retry_timeouts.py
"""
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import dns.resolver

CACHE_FILE = "outputs/resolved_cache.json"
RESOLVERS = ["8.8.8.8", "1.1.1.1"]
CHECKPOINT_EVERY = 200
WORKERS = 25
TIMEOUT = 6
RETRIES = 2


def resolve_one(domain):
    err = None
    resolver_ip = RESOLVERS[0]
    for attempt in range(RETRIES):
        resolver_ip = RESOLVERS[attempt % len(RESOLVERS)]
        r = dns.resolver.Resolver(configure=False)
        r.nameservers = [resolver_ip]
        r.timeout = TIMEOUT
        r.lifetime = TIMEOUT
        try:
            ans = r.resolve(domain, "A")
            return ans[0].to_text(), None, resolver_ip
        except Exception as e:
            err = type(e).__name__
    return None, err, resolver_ip


def main():
    with open(CACHE_FILE) as f:
        cache = json.load(f)

    todo = [d for d, v in cache.items() if v.get("error") == "LifetimeTimeout"]
    print(f"{len(todo)} timed-out domains to retry")

    recovered = 0
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(resolve_one, d): d for d in todo}
        for fut in as_completed(futures):
            domain = futures[fut]
            ip, err, resolver_ip = fut.result()
            if ip:
                cache[domain] = {"ip": ip, "error": None, "resolver": resolver_ip}
                recovered += 1
            else:
                cache[domain] = {"ip": None, "error": err, "resolver": resolver_ip}
            done += 1
            if done % CHECKPOINT_EVERY == 0:
                with open(CACHE_FILE, "w") as f:
                    json.dump(cache, f)
                print(f"  [checkpoint] {done}/{len(todo)} retried, {recovered} recovered so far")

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

    print(f"Done: {recovered}/{len(todo)} recovered")


if __name__ == "__main__":
    main()
