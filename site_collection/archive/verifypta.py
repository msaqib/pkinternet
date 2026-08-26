#!/usr/bin/env python3
"""
Verify ISP domains from PTA list via DNS resolution.
Run from pkinternet root:
    python3 other/verify_pta_isps.py
"""

import socket
import csv

# paste the ISP list here — domain column only
ISP_DOMAINS = [
    "star-telecom74.ru",
    "aa-networks.net",
    "www.airlinkcommunication.com",
    "airmax.com.pk",
    "www.alpinesinternet.com.pk",
    "www.urdupoint.com",
    "ascontel.net",
    "acn.net.pk",
    "aitqta.net.pk",
    "badarnetworks.online",
    "balitelecom.net",
    "bigdata.net.pk",
    "bignetbroadband.net",
    "blazeoptics.pk",
    "brain.net.pk",
    "broadbandvision.net",
    "en.dailypakistan.com.pk",
    "cactuspk.com",
    "call2phone.com",
    "celmoretech.com",
    "developingtelecoms.com",
    "cits.net.pk",
    "zong.com.pk",
    "connect.net.pk",
    "crystal-lite.net",
    "cubexsweatherly.com",
    "cyber.net.pk",
    "darlink.pk",
    "deltatelecom.net.pk",
    "dreamnet.com.pk",
    "ebonenet.com",
    "earthlinkbroadband.com",
    "www.ebone.net.pk",
    "stitch.withgoogle.com",
    "enigmafiber.com",
    "www.fcnkasur.com",
    "fariya.com",
    "fastlinefiber.com.pk",
    "fastweb.com.pk",
    "fasttel.com.pk",
    "fiber2home.pk",
    "fiber-beam.net",
    "fc.com.pk",
    "fiberish.net.pk",
    "fibnex.com",
    "future-telecom.com",
    "galaxy.net.pk",
    "ges.net.pk",
    "gerrys.net",
    "globalconnectsynergy.com",
    "gnss.com.pk",
    "gulfcablenetwork.com",
    "hccnp.net.pk",
    "helium.com.pk",
    "iweb.net.pk",
    "incableinternet.com",
    "insta.com.pk",
    "jk-networks.com",
    "khantelecom.net",
    "kknetworks.com.pk",
    "lahoreinternetsolutions.com",
    "link2netsolutions.com",
    "jazz.com.pk",
    "logi-tech.net",
    "lbi.net.pk",
    "loomnet.com.pk",
    "mzy.net.pk",
    "mtcl.com.pk",
    "mastercomm.net.pk",
    "mcsol.com.pk",
    "mispl.pk",
    "multicityinternet.com",
    "multinet.com.pk",
    "muxbroadband.com",
    "nasstecairnet.net.pk",
    "nayatel.com",
    "www.techjuice.pk",
    "netelastic.com.pk",
    "netflow.com.pk",
    "netzetel.com",
    "nexcom.net.pk",
    "nuinternet.com.pk",
    "optimaxnetworks.com",
    "optix.pk",
    "orbitnetworks.net.pk",
    "originnet.com.pk",
    "pace-tel.com",
    "pakdatacom.com.pk",
    "gmai.com",
    "pbb.net.pk",
    "primebroadband.net.pk",
    "pie.com.pk",
    "rds.net.pk",
    "reliance-broadband.net",
    "satcomm.pk",
    "shahramteleco.pk",
    "sharptel.pk",
    "signin.com.pk",
    "skylight-internet.com",
    "smarttel.com.pk",
    "smart-net.org",
    "sparklinks.pk",
    "ses.net.pk",
    "superfast.net.pk",
    "scpl.pk",
    "supernetglobal.com",
    "tech3speed.com.pk",
    "telecard.com.pk",
    "teleco-solutions.com",
    "nexlinx.net.pk",
    "tw1.com",
    "teznet.com.pk",
    "nova.net.pk",
    "wateen.com",
    "topcity-1.com",
    "worldcall.net.pk",
    "uconnect.net.pk",
    "upnet.com.pk",
    "visiontelecom.com.pk",
    "wancom.net.pk",
    "wavecomm.com.pk",
    "waylink.com.pk",
    "wcpl.com.pk",
    "winet.com.pk",
    "wideband.com.pk",
    "wisecomm.net.pk",
    "worldcall.pk",
    "xfiber.pk",
    "xtreamfiber.net.pk",
    "ylinx.pk",
]

def check(domain):
    d = domain.replace('www.', '')
    try:
        ip = socket.gethostbyname(d)
    except:
        return None, 'FAILED'
    
    # also try HTTP
    import requests
    for scheme in ['https', 'http']:
        try:
            r = requests.get(f"{scheme}://{d}", timeout=5, 
                           allow_redirects=True,
                           headers={'User-Agent': 'Mozilla/5.0'})
            return ip, f'EXISTS (HTTP {r.status_code})'
        except:
            continue
    return ip, 'EXISTS (DNS only, HTTP failed)'

print(f"Checking {len(ISP_DOMAINS)} domains...\n")
print(f"{'Domain':<45} {'IP':<20} {'Status'}")
print("-" * 75)

results = []
exists = 0
failed = 0

for domain in ISP_DOMAINS:
    ip, status = check(domain)
    if status == 'EXISTS':
        exists += 1
    else:
        failed += 1
    print(f"{domain:<45} {ip or '':<20} {status}")
    results.append({'domain': domain, 'ip': ip or '', 'status': status})

print(f"\nTotal: {len(ISP_DOMAINS)}  Exists: {exists}  Failed: {failed}")

# save CSV
with open('other/pta_isp_verified.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['domain','ip','status'])
    writer.writeheader()
    writer.writerows(results)
print("Saved to other/pta_isp_verified.csv")