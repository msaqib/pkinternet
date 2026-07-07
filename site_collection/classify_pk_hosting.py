"""
classify_pk_hosting.py

Reads tranco_pk_asn.json (domain -> ip, asn, country), does a bulk
Team Cymru WHOIS lookup to get the AS name for each IP, then classifies
each domain's hosting as Local / CDN / Abroad.

Usage:
    python classify_pk_hosting.py

Input:
    tranco_pk_asn.json   (must be in the same directory, or edit INPUT_PATH below)

Output:
    tranco_pk_hosting_classification.csv
"""

import socket
import json
import pandas as pd

INPUT_PATH = 'other/isps_res.json'
OUTPUT_PATH = 'isps_hosting_classification.csv'

CDN_KEYWORDS = [
    'CLOUDFLARE', 'AKAMAI', 'FASTLY', 'INCAPSULA', 'IMPERVA',
    'LIMELIGHT', 'EDGECAST', 'EDGIO', 'CDN77', 'STACKPATH',
    'CLOUDFRONT', 'AZURE-CDN', 'GOOGLE-CLOUD-CDN'
]


def bulk_cymru_lookup(ip_list):
    """Single bulk WHOIS query to Team Cymru for a list of IPs."""
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


def parse_cymru_response(raw_text):
    """Parse pipe-delimited Cymru response into {ip: {asn, country, as_name}}."""
    lines = raw_text.strip().split('\n')[1:]  # skip header row
    asn_info = {}
    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 7:
            asn, ip, prefix, cc, registry, allocated, as_name = parts[:7]
            asn_info[ip] = {'asn': asn, 'country': cc, 'as_name': as_name}
    return asn_info


def classify(row):
    if row['country'] == 'PK':
        return 'Local'
    as_name = str(row['as_name']).upper()
    if any(kw in as_name for kw in CDN_KEYWORDS):
        return 'CDN'
    return 'Abroad'


def main():
    with open(INPUT_PATH) as f:
        data = json.load(f)

    domain_ip_pairs = [(domain, info['ip']) for domain, info in data.items() if info.get('ip')]
    print(f"Loaded {len(domain_ip_pairs)} domains with IPs from {INPUT_PATH}")

    ip_only = [ip for _, ip in domain_ip_pairs]
    raw = bulk_cymru_lookup(ip_only)
    asn_info = parse_cymru_response(raw)
    print(f"Got AS name/country data for {len(asn_info)} IPs from Team Cymru")

    rows = []
    for domain, ip in domain_ip_pairs:
        info = asn_info.get(ip, {})
        rows.append({
            'domain': domain,
            'ip': ip,
            'asn': info.get('asn'),
            'country': info.get('country'),
            'as_name': info.get('as_name'),
        })

    df = pd.DataFrame(rows)
    df['hosting_location'] = df.apply(classify, axis=1)

    print("\nHosting location breakdown:")
    print(df['hosting_location'].value_counts())

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved full results to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()