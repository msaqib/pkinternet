from tranco import Tranco

t = Tranco(cache=True, cache_dir='.tranco')
latest = t.list()

all_domains = latest.top(1000000)
pk_domains = [d for d in all_domains if d.endswith('.pk')]

print(f"Total .pk domains: {len(pk_domains)}")
with open('tranco_pk_domains.txt', 'w') as f:
    for d in pk_domains:
        f.write(d + '\n')
print("Saved to tranco_pk_domains.txt")