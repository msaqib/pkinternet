import pandas as pd
from tranco import Tranco

# 1. Use the exact same cache setup you used before so it doesn't re-download
t = Tranco(cache=True, cache_dir='.tranco')
latest = t.list()

# 2. Define a test list of known Pakistani .com/.org/.tv sites
test_domains = [
    'hbl.com',             # Habib Bank
    'abl.com',             # Allied Bank
    'bankalfalah.com',     # Bank Alfalah
    'dawn.com',            # Dawn News
    'geo.tv',              # Geo News
    'nayatel.com',         # Nayatel ISP
    'ptcl.com.pk',         # PTCL (just to see where a major .pk lands)
    'lhe.com.pk'           # LESCO/Lahore Electric
]

print(f"Checking ranks using Tranco list: {latest.list_id}")
print("-" * 50)

results = []
for domain in test_domains:
    # .rank() is fast; it look up the rank without loading all 1M into a list
    rank = latest.rank(domain)
    if rank != -1:
        print(f"✅ {domain} is found at rank: {rank:,}")
        results.append(rank)
    else:
        print(f"❌ {domain} is NOT FOUND in the top 1M")

print("-" * 50)

# 3. Calculate your slice based on the results
if results:
    highest_rank = max(results)
    print(f"Highest rank found among test targets: {highest_rank:,}")
    
    # Add a 20% safety buffer to capture similar or slightly less popular sites
    recommended_slice = int(highest_rank * 1.2) 
    print(f"➡️ RECOMMENDED ACTION: Run your DNS/ASN pipeline on the top {recommended_slice:,} domains.")
else:
    print("❌ None of the test .com/.org sites were found in the top 1M.")
    print("➡️ CONCLUSION: Tranco doesn't see them. You must use curated lists instead of widening the slice.")