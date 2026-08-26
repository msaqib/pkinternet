"""Run from site_collection/, not from pipeline/: python3 pipeline/get_tranco.py"""
from tranco import Tranco

t = Tranco(cache=True, cache_dir='.tranco')
latest = t.list()

# Pull only the top 350,000 domains based on our test analysis
SLICE_SIZE = 350000
print(f"Fetching top {SLICE_SIZE:,} domains from Tranco list {latest.list_id}...")
sliced_domains = latest.top(SLICE_SIZE)

print(f"Total domains retrieved: {len(sliced_domains)}")

# Save them to a file to feed into your DNS/ASN pipeline
output_file = 'outputs/tranco_350k_slice.txt'
with open(output_file, 'w') as f:
    for d in sliced_domains:
        f.write(d + '\n')


print(f"Saved to {output_file}. Ready for your DNS/ASN pipeline!")