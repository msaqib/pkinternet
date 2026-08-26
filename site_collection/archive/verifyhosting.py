import json
import socket

with open('other/isps_res.json') as f:
    data = json.load(f)

suspicious_domains = [
    'vu.edu.pk', 'pitc.com.pk', 'myanimelist.net', 'buienradar.nl',
    'cntv.cn', 'totogaming.am', 'tse.jus.br', 'punjabpolice.gov.pk',
    'buienradar.be', 'hypic.com', 'youth.cn', 'punjab.gov.pk',
    'toptop.net', 'flashget.com'
]

# Step 1: fresh DNS resolution for each domain
fresh_ips = {}
for domain in suspicious_domains:
    try:
        fresh_ips[domain] = socket.gethostbyname(domain)
    except socket.gaierror:
        fresh_ips[domain] = None

# Step 2: bulk ASN/country lookup on the fresh IPs via Team Cymru
def bulk_cymru_lookup(ip_list):
    query = "begin\nverbose\n" + "\n".join(ip_list) + "\nend\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect(('whois.cymru.com', 43))
    sock.sendall(query.encode())
    response = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    sock.close()
    return response.decode(errors='replace')

valid_ips = [ip for ip in fresh_ips.values() if ip]
raw = bulk_cymru_lookup(valid_ips)

asn_info = {}
for line in raw.strip().split('\n')[1:]:
    parts = [p.strip() for p in line.split('|')]
    if len(parts) >= 7:
        asn, ip, prefix, cc, registry, allocated, as_name = parts[:7]
        asn_info[ip] = {'asn': asn, 'country': cc, 'as_name': as_name}

# Step 3: print full comparison
print(f"{'domain':<22} {'json_country':<14} {'fresh_ip':<18} {'fresh_country':<15} {'fresh_as_name'}")
print('-' * 100)
for domain in suspicious_domains:
    json_country = data.get(domain, {}).get('country', 'N/A')
    fresh_ip = fresh_ips[domain] or 'FAILED'
    info = asn_info.get(fresh_ip, {})
    fresh_country = info.get('country', 'N/A')
    fresh_as_name = info.get('as_name', 'N/A')
    print(f"{domain:<22} {json_country:<14} {fresh_ip:<18} {fresh_country:<15} {fresh_as_name}")