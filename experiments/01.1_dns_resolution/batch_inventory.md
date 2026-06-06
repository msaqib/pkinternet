# Batch Inventory - Experiment 1.1 (DNS Resolution)

**Author:** Rayan Atif

Per-ISP DNS resolution for every site: which batch, the probe (ISP) that asked,
the IP(s) it resolved, and whether ISPs disagreed (GeoDNS). PTCL and TPCPL were
offline during this run, so only 3 probes responded.


## batch1

| Website | Category | Probe (ISP) | Resolved IP(s) | IP ASN | Per-ISP agreement |
|---|---|---|---|---|---|
| balochistan.gov.pk | government | Nayatel | 129.121.85.241 | AS31898 | same |
|  |  | Transworld | 129.121.85.241 | AS31898 |  |
|  |  | Z-Com | 129.121.85.241 | AS31898 |  |
| fbr.gov.pk | government | Nayatel | 103.125.60.60 | AS138424 | same |
|  |  | Transworld | 103.125.60.60 | AS138424 |  |
|  |  | Z-Com | 103.125.60.60 | AS138424 |  |
| hec.gov.pk | government | Nayatel | 111.68.100.163 | AS45773 | same |
|  |  | Transworld | 111.68.100.163 | AS45773 |  |
|  |  | Z-Com | 111.68.100.163 | AS45773 |  |
| kp.gov.pk | government | Nayatel | 175.107.63.150 | AS23888 | same |
|  |  | Transworld | 175.107.63.150 | AS23888 |  |
|  |  | Z-Com | 175.107.63.150 | AS23888 |  |
| nadra.gov.pk | government | Nayatel | 23.206.197.50;23.206.197.72 | AS20940 | DIFFERS (GeoDNS) |
|  |  | Transworld | 2.19.193.138;2.19.193.169 | AS20940 |  |
|  |  | Z-Com | 2.23.84.10;2.23.84.46;23.48.214.75;23.48.214.80 | AS20940 |  |
| pakistan.gov.pk | government | Nayatel | 203.101.184.84 | AS9541 | same |
|  |  | Transworld | 203.101.184.84 | AS9541 |  |
|  |  | Z-Com | 203.101.184.84 | AS9541 |  |
| pta.gov.pk | government | Nayatel | 175.107.60.231 | AS23888 | same |
|  |  | Transworld | 175.107.60.231 | AS23888 |  |
|  |  | Z-Com | 175.107.60.231 | AS23888 |  |
| punjab.gov.pk | government | Nayatel | 103.226.216.120 | AS59323 | same |
|  |  | Transworld | 103.226.216.120 | AS59323 |  |
|  |  | Z-Com | 103.226.216.120 | AS59323 |  |
| secp.gov.pk | government | Nayatel | 104.20.33.223;172.66.157.118 | AS13335 | same |
|  |  | Transworld | 104.20.33.223;172.66.157.118 | AS13335 |  |
|  |  | Z-Com | 104.20.33.223;172.66.157.118 | AS13335 |  |
| sindh.gov.pk | government | Nayatel | 175.107.33.163 | AS23888 | same |
|  |  | Transworld | 175.107.33.163 | AS23888 |  |
|  |  | Z-Com | 175.107.33.163 | AS23888 |  |

## batch2

| Website | Category | Probe (ISP) | Resolved IP(s) | IP ASN | Per-ISP agreement |
|---|---|---|---|---|---|
| bisp.gov.pk | government | Nayatel | 104.21.43.243;172.67.190.163 | AS13335 | DIFFERS (GeoDNS) |
|  |  | Transworld | 104.21.43.243;172.67.190.163;188.114.96.6;188.114.97.6 | AS13335 |  |
|  |  | Z-Com | 188.114.96.6;188.114.96.7;188.114.97.6;188.114.97.7 | AS13335 |  |
| moitt.gov.pk | government | Nayatel | 203.101.184.86 | AS9541 | same |
|  |  | Transworld | 203.101.184.86 | AS9541 |  |
|  |  | Z-Com | 203.101.184.86 | AS9541 |  |
| nlc.com.pk | government | Nayatel | 104.26.6.113;104.26.7.113;172.67.71.233 | AS13335 | same |
|  |  | Transworld | 104.26.6.113;104.26.7.113;172.67.71.233 | AS13335 |  |
|  |  | Z-Com | 104.26.6.113;104.26.7.113;172.67.71.233 | AS13335 |  |
| nltpk.gov.pk | government | Nayatel | (none) | - | same |
|  |  | Transworld | (none) | - |  |
|  |  | Z-Com | (none) | - |  |
| pbs.gov.pk | government | Nayatel | 113.197.54.86 | AS23888 | same |
|  |  | Transworld | 113.197.54.86 | AS23888 |  |
|  |  | Z-Com | 113.197.54.86 | AS23888 |  |
| pid.gov.pk | government | Nayatel | 203.124.45.87 | AS7590 | same |
|  |  | Transworld | 203.124.45.87 | AS7590 |  |
|  |  | Z-Com | 203.124.45.87 | AS7590 |  |
| pitc.com.pk | government | Nayatel | 163.61.25.12 | AS153561 | same |
|  |  | Transworld | 163.61.25.12 | AS153561 |  |
|  |  | Z-Com | 163.61.25.12 | AS153561 |  |
| pseb.org.pk | government | Nayatel | 125.209.103.90 | AS9260 | same |
|  |  | Transworld | 125.209.103.90 | AS9260 |  |
|  |  | Z-Com | 125.209.103.90 | AS9260 |  |
| railways.gov.pk | government | Nayatel | 203.101.184.86 | AS9541 | same |
|  |  | Transworld | 203.101.184.86 | AS9541 |  |
|  |  | Z-Com | 203.101.184.86 | AS9541 |  |
| sbp.org.pk | government | Nayatel | (none) | - | same |
|  |  | Transworld | (none) | - |  |
|  |  | Z-Com | (none) | - |  |

## batch3

| Website | Category | Probe (ISP) | Resolved IP(s) | IP ASN | Per-ISP agreement |
|---|---|---|---|---|---|
| arynews.tv | news | Nayatel | 104.26.6.13;104.26.7.13;172.67.72.246 | AS13335 | same |
|  |  | Transworld | 104.26.6.13;104.26.7.13;172.67.72.246 | AS13335 |  |
|  |  | Z-Com | 104.26.6.13;104.26.7.13;172.67.72.246 | AS13335 |  |
| bolnews.com | news | Nayatel | 104.26.10.66;104.26.11.66;172.67.68.39 | AS13335 | same |
|  |  | Transworld | 104.26.10.66;104.26.11.66;172.67.68.39 | AS13335 |  |
|  |  | Z-Com | 104.26.10.66;104.26.11.66;172.67.68.39 | AS13335 |  |
| dawn.com | news | Nayatel | 104.26.2.124;104.26.3.124;172.67.72.98 | AS13335 | same |
|  |  | Transworld | 104.26.2.124;104.26.3.124;172.67.72.98 | AS13335 |  |
|  |  | Z-Com | 104.26.2.124;104.26.3.124;172.67.72.98 | AS13335 |  |
| dunyanews.tv | news | Nayatel | 202.142.167.148 | AS9260 | same |
|  |  | Transworld | 202.142.167.148 | AS9260 |  |
|  |  | Z-Com | 202.142.167.148 | AS9260 |  |
| express.com.pk | news | Nayatel | 104.21.72.31;172.67.174.102 | AS13335 | same |
|  |  | Transworld | 104.21.72.31;172.67.174.102 | AS13335 |  |
|  |  | Z-Com | 104.21.72.31;172.67.174.102 | AS13335 |  |
| geo.tv | news | Nayatel | 104.16.218.243;104.16.219.243 | AS13335 | same |
|  |  | Transworld | 104.16.218.243;104.16.219.243 | AS13335 |  |
|  |  | Z-Com | 104.16.218.243;104.16.219.243 | AS13335 |  |
| hamariweb.com | news | Nayatel | 104.20.40.53;172.66.171.219 | AS13335 | same |
|  |  | Transworld | 104.20.40.53;172.66.171.219 | AS13335 |  |
|  |  | Z-Com | 104.20.40.53;172.66.171.219 | AS13335 |  |
| jang.com.pk | news | Nayatel | 104.17.16.38;104.18.86.101 | AS13335 | same |
|  |  | Transworld | 104.17.16.38;104.18.86.101 | AS13335 |  |
|  |  | Z-Com | 104.17.16.38;104.18.86.101 | AS13335 |  |
| samaadigital.com | news | Nayatel | (none) | - | same |
|  |  | Transworld | (none) | - |  |
|  |  | Z-Com | (none) | - |  |
| thenews.com.pk | news | Nayatel | 104.17.71.37;104.18.83.16 | AS13335 | same |
|  |  | Transworld | 104.17.71.37;104.18.83.16 | AS13335 |  |
|  |  | Z-Com | 104.17.71.37;104.18.83.16 | AS13335 |  |

## batch4

| Website | Category | Probe (ISP) | Resolved IP(s) | IP ASN | Per-ISP agreement |
|---|---|---|---|---|---|
| 24newshd.tv | news | Nayatel | 65.21.69.178 | AS24940 | same |
|  |  | Transworld | 65.21.69.178 | AS24940 |  |
|  |  | Z-Com | 65.21.69.178 | AS24940 |  |
| businessrecorder.com | news | Nayatel | (none) | - | same |
|  |  | Transworld | (none) | - |  |
|  |  | Z-Com | (none) | - |  |
| dailypakistan.com.pk | news | Nayatel | 65.109.77.254 | AS24940 | same |
|  |  | Transworld | 65.109.77.254 | AS24940 |  |
|  |  | Z-Com | 65.109.77.254 | AS24940 |  |
| hbl.com | banking | Nayatel | 45.60.109.176;45.60.73.176 | AS19551 | same |
|  |  | Transworld | 45.60.109.176;45.60.73.176 | AS19551 |  |
|  |  | Z-Com | 45.60.109.176;45.60.73.176 | AS19551 |  |
| mcb.com.pk | banking | Nayatel | 192.124.249.159 | AS30148 | same |
|  |  | Transworld | 192.124.249.159 | AS30148 |  |
|  |  | Z-Com | 192.124.249.159 | AS30148 |  |
| nawaiwaqt.com.pk | news | Nayatel | 65.109.88.147 | AS24940 | same |
|  |  | Transworld | 65.109.88.147 | AS24940 |  |
|  |  | Z-Com | 65.109.88.147 | AS24940 |  |
| propakistani.pk | news | Nayatel | 104.26.12.229;104.26.13.229;172.67.71.114 | AS13335 | same |
|  |  | Transworld | 104.26.12.229;104.26.13.229;172.67.71.114 | AS13335 |  |
|  |  | Z-Com | 104.26.12.229;104.26.13.229;172.67.71.114 | AS13335 |  |
| such.tv | news | Nayatel | 13.248.169.48;76.223.54.146 | AS16509 | same |
|  |  | Transworld | 13.248.169.48;76.223.54.146 | AS16509 |  |
|  |  | Z-Com | 13.248.169.48;76.223.54.146 | AS16509 |  |
| tribune.com.pk | news | Nayatel | 104.18.193.13;104.18.194.13 | AS13335 | same |
|  |  | Transworld | 104.18.193.13;104.18.194.13 | AS13335 |  |
|  |  | Z-Com | 104.18.193.13;104.18.194.13 | AS13335 |  |
| urdupoint.com | news | Nayatel | 104.26.6.27;104.26.7.27;172.67.68.78 | AS13335 | same |
|  |  | Transworld | 104.26.6.27;104.26.7.27;172.67.68.78 | AS13335 |  |
|  |  | Z-Com | 104.26.6.27;104.26.7.27;172.67.68.78 | AS13335 |  |

## batch5

| Website | Category | Probe (ISP) | Resolved IP(s) | IP ASN | Per-ISP agreement |
|---|---|---|---|---|---|
| 1bill.com.pk | banking | Nayatel | (none) | - | same |
|  |  | Transworld | (none) | - |  |
|  |  | Z-Com | (none) | - |  |
| askaribank.com.pk | banking | Nayatel | 104.18.2.57;104.18.3.57 | AS13335 | same |
|  |  | Transworld | 104.18.2.57;104.18.3.57 | AS13335 |  |
|  |  | Z-Com | 104.18.2.57;104.18.3.57 | AS13335 |  |
| bankalfalah.com | banking | Nayatel | 40.120.122.192 | AS8075 | same |
|  |  | Transworld | 40.120.122.192 | AS8075 |  |
|  |  | Z-Com | 40.120.122.192 | AS8075 |  |
| bankislami.com.pk | banking | Nayatel | 104.18.28.162;104.18.29.162 | AS13335 | same |
|  |  | Transworld | 104.18.28.162;104.18.29.162 | AS13335 |  |
|  |  | Z-Com | 104.18.28.162;104.18.29.162 | AS13335 |  |
| easypaisa.com.pk | banking | Nayatel | 18.142.75.3 | AS16509 | same |
|  |  | Transworld | 18.142.75.3 | AS16509 |  |
|  |  | Z-Com | 18.142.75.3 | AS16509 |  |
| jazzcash.com.pk | banking | Nayatel | 104.26.0.79;104.26.1.79;172.67.70.2 | AS13335 | same |
|  |  | Transworld | 104.26.0.79;104.26.1.79;172.67.70.2 | AS13335 |  |
|  |  | Z-Com | 104.26.0.79;104.26.1.79;172.67.70.2 | AS13335 |  |
| meezanbank.com | banking | Nayatel | 104.18.0.183;104.18.1.183 | AS13335 | same |
|  |  | Transworld | 104.18.0.183;104.18.1.183 | AS13335 |  |
|  |  | Z-Com | 104.18.0.183;104.18.1.183 | AS13335 |  |
| nayapay.com | banking | Nayatel | 104.20.21.218;172.66.158.161 | AS13335 | same |
|  |  | Transworld | 104.20.21.218;172.66.158.161 | AS13335 |  |
|  |  | Z-Com | 104.20.21.218;172.66.158.161 | AS13335 |  |
| sadapay.com | banking | Nayatel | 198.202.211.1 | AS209242 | same |
|  |  | Transworld | 198.202.211.1 | AS209242 |  |
|  |  | Z-Com | 198.202.211.1 | AS209242 |  |
| ubldigital.com | banking | Nayatel | 103.8.14.50 | AS56126 | same |
|  |  | Transworld | 103.8.14.50 | AS56126 |  |
|  |  | Z-Com | 103.8.14.50 | AS56126 |  |

## batch6

| Website | Category | Probe (ISP) | Resolved IP(s) | IP ASN | Per-ISP agreement |
|---|---|---|---|---|---|
| daraz.pk | ecommerce | Nayatel | 47.246.167.152;47.246.167.168;47.246.174.148;47.246.174.23 | AS45102 | same |
|  |  | Transworld | 47.246.167.152;47.246.167.168;47.246.174.148;47.246.174.23 | AS45102 |  |
|  |  | Z-Com | 47.246.167.152;47.246.167.168;47.246.174.148;47.246.174.23 | AS45102 |  |
| faysal.com | banking | Nayatel | 205.178.189.131 | AS19871 | same |
|  |  | Transworld | 205.178.189.131 | AS19871 |  |
|  |  | Z-Com | 205.178.189.131 | AS19871 |  |
| goto.com.pk | ecommerce | Nayatel | 116.0.44.219 | AS55340 | same |
|  |  | Transworld | 116.0.44.219 | AS55340 |  |
|  |  | Z-Com | 116.0.44.219 | AS55340 |  |
| habibmetro.com | banking | Nayatel | 52.128.23.26 | AS19324 | same |
|  |  | Transworld | 52.128.23.26 | AS19324 |  |
|  |  | Z-Com | 52.128.23.26 | AS19324 |  |
| olx.com.pk | ecommerce | Nayatel | 108.139.86.12;108.139.86.16;108.139.86.61;108.139.86.68 | AS16509 | DIFFERS (GeoDNS) |
|  |  | Transworld | 13.35.202.103;13.35.202.114;13.35.202.12;13.35.202.89 | AS16509 |  |
|  |  | Z-Com | 13.224.163.14;13.224.163.34;13.224.163.55;13.224.163.97;13.35.202.103;13.35.202.114;13.35.202.12;13.35.202.89 | AS16509 |  |
| pakwheels.com | ecommerce | Nayatel | 104.26.6.233;104.26.7.233;172.67.72.209 | AS13335 | same |
|  |  | Transworld | 104.26.6.233;104.26.7.233;172.67.72.209 | AS13335 |  |
|  |  | Z-Com | 104.26.6.233;104.26.7.233;172.67.72.209 | AS13335 |  |
| priceoye.pk | ecommerce | Nayatel | 104.20.35.152;172.66.148.155 | AS13335 | same |
|  |  | Transworld | 104.20.35.152;172.66.148.155 | AS13335 |  |
|  |  | Z-Com | 104.20.35.152;172.66.148.155 | AS13335 |  |
| shophive.com | ecommerce | Nayatel | 104.26.10.152;104.26.11.152;172.67.73.72 | AS13335 | same |
|  |  | Transworld | 104.26.10.152;104.26.11.152;172.67.73.72 | AS13335 |  |
|  |  | Z-Com | 104.26.10.152;104.26.11.152;172.67.73.72 | AS13335 |  |
| symbios.pk | ecommerce | Nayatel | 69.167.171.64 | AS32244 | same |
|  |  | Transworld | 69.167.171.64 | AS32244 |  |
|  |  | Z-Com | 69.167.171.64 | AS32244 |  |
| telemart.pk | ecommerce | Nayatel | 104.21.65.247;172.67.195.207 | AS13335 | same |
|  |  | Transworld | 104.21.65.247;172.67.195.207 | AS13335 |  |
|  |  | Z-Com | 104.21.65.247;172.67.195.207 | AS13335 |  |

## batch7

| Website | Category | Probe (ISP) | Resolved IP(s) | IP ASN | Per-ISP agreement |
|---|---|---|---|---|---|
| alfatah.com.pk | ecommerce | Nayatel | 46.202.136.217 | AS47583 | same |
|  |  | Transworld | 46.202.136.217 | AS47583 |  |
|  |  | Z-Com | 46.202.136.217 | AS47583 |  |
| gulahmedshop.com | ecommerce | Nayatel | 23.227.38.65 | AS13335 | same |
|  |  | Transworld | 23.227.38.65 | AS13335 |  |
|  |  | Z-Com | 23.227.38.65 | AS13335 |  |
| ishopping.pk | ecommerce | Nayatel | 104.20.47.188;172.66.149.222 | AS13335 | DIFFERS (GeoDNS) |
|  |  | Transworld | 104.20.47.188;172.66.149.222;188.114.96.6;188.114.97.6 | AS13335 |  |
|  |  | Z-Com | 188.114.96.6;188.114.96.7;188.114.97.6;188.114.97.7 | AS13335 |  |
| jazz.com.pk | telecom | Nayatel | 104.20.42.250;172.66.168.19 | AS13335 | same |
|  |  | Transworld | 104.20.42.250;172.66.168.19 | AS13335 |  |
|  |  | Z-Com | 104.20.42.250;172.66.168.19 | AS13335 |  |
| khaadi.com | ecommerce | Nayatel | 3.160.77.120;3.160.77.15;3.160.77.47;3.160.77.54 | AS16509 | DIFFERS (GeoDNS) |
|  |  | Transworld | 3.160.77.120;3.160.77.15;3.160.77.47;3.160.77.54 | AS16509 |  |
|  |  | Z-Com | 18.66.78.124;18.66.78.46;18.66.78.8;18.66.78.83;65.9.168.3;65.9.168.34;65.9.168.42;65.9.168.98 | AS16509 |  |
| outfitters.com.pk | ecommerce | Nayatel | 23.227.38.32 | AS13335 | same |
|  |  | Transworld | 23.227.38.32 | AS13335 |  |
|  |  | Z-Com | 23.227.38.32 | AS13335 |  |
| ptcl.com.pk | telecom | Nayatel | 221.120.226.61 | AS17557 | same |
|  |  | Transworld | 221.120.226.61 | AS17557 |  |
|  |  | Z-Com | 221.120.226.61 | AS17557 |  |
| sapphireonline.pk | ecommerce | Nayatel | 64.68.202.16 | AS16686 | same |
|  |  | Transworld | 64.68.202.16 | AS16686 |  |
|  |  | Z-Com | 64.68.202.16 | AS16686 |  |
| sargodha.com | ecommerce | Nayatel | 13.248.169.48;76.223.54.146 | AS16509 | same |
|  |  | Transworld | 13.248.169.48;76.223.54.146 | AS16509 |  |
|  |  | Z-Com | 13.248.169.48;76.223.54.146 | AS16509 |  |
| telenor.com.pk | telecom | Nayatel | 104.18.12.112;104.18.13.112 | AS13335 | same |
|  |  | Transworld | 104.18.12.112;104.18.13.112 | AS13335 |  |
|  |  | Z-Com | 104.18.12.112;104.18.13.112 | AS13335 |  |

## batch8

| Website | Category | Probe (ISP) | Resolved IP(s) | IP ASN | Per-ISP agreement |
|---|---|---|---|---|---|
| brain.net.pk | telecom | Nayatel | 5.161.30.49 | AS213230 | same |
|  |  | Transworld | 5.161.30.49 | AS213230 |  |
|  |  | Z-Com | 5.161.30.49 | AS213230 |  |
| lums.edu.pk | education | Nayatel | 110.93.234.24;111.68.103.174;203.135.62.24 | AS38193 | DIFFERS (GeoDNS) |
|  |  | Transworld | 10.99.0.24 | - |  |
|  |  | Z-Com | 110.93.234.24;111.68.103.174;203.135.62.24 | AS38193 |  |
| nayatel.com | telecom | Nayatel | 124.109.50.84 | AS23674 | DIFFERS (GeoDNS) |
|  |  | Transworld | 203.82.48.231 | AS23674 |  |
|  |  | Z-Com | 188.166.22.60;203.82.48.231 | AS14061 |  |
| nexlinx.net.pk | telecom | Nayatel | 202.59.80.26 | AS17563 | same |
|  |  | Transworld | 202.59.80.26 | AS17563 |  |
|  |  | Z-Com | 202.59.80.26 | AS17563 |  |
| nust.edu.pk | education | Nayatel | 104.26.2.7;104.26.3.7;172.67.68.211 | AS13335 | same |
|  |  | Transworld | 104.26.2.7;104.26.3.7;172.67.68.211 | AS13335 |  |
|  |  | Z-Com | 104.26.2.7;104.26.3.7;172.67.68.211 | AS13335 |  |
| pu.edu.pk | education | Nayatel | 111.68.103.27 | AS45773 | same |
|  |  | Transworld | 111.68.103.27 | AS45773 |  |
|  |  | Z-Com | 111.68.103.27 | AS45773 |  |
| stormfiber.com | telecom | Nayatel | 203.101.172.139 | AS9541 | same |
|  |  | Transworld | 203.101.172.139 | AS9541 |  |
|  |  | Z-Com | 203.101.172.139 | AS9541 |  |
| supernet.com.pk | telecom | Nayatel | (none) | - | same |
|  |  | Transworld | (none) | - |  |
|  |  | Z-Com | (none) | - |  |
| wateen.com | telecom | Nayatel | 91.108.117.126 | AS47583 | same |
|  |  | Transworld | 91.108.117.126 | AS47583 |  |
|  |  | Z-Com | 91.108.117.126 | AS47583 |  |
| zong.com.pk | telecom | Nayatel | 148.72.244.140 | AS26496 | same |
|  |  | Transworld | 148.72.244.140 | AS26496 |  |
|  |  | Z-Com | 148.72.244.140 | AS26496 |  |

## batch9

| Website | Category | Probe (ISP) | Resolved IP(s) | IP ASN | Per-ISP agreement |
|---|---|---|---|---|---|
| aku.edu | education | Nayatel | 52.156.198.57 | AS8075 | same |
|  |  | Transworld | 52.156.198.57 | AS8075 |  |
|  |  | Z-Com | 52.156.198.57 | AS8075 |  |
| comsats.edu.pk | education | Nayatel | 104.20.28.132;172.66.158.132 | AS13335 | same |
|  |  | Transworld | 104.20.28.132;172.66.158.132 | AS13335 |  |
|  |  | Z-Com | 104.20.28.132;172.66.158.132 | AS13335 |  |
| iba.edu.pk | education | Nayatel | 192.124.249.134 | AS30148 | same |
|  |  | Transworld | 192.124.249.134 | AS30148 |  |
|  |  | Z-Com | 192.124.249.134 | AS30148 |  |
| ilmkidunya.com | education | Nayatel | 54.39.132.143 | AS16276 | same |
|  |  | Transworld | 54.39.132.143 | AS16276 |  |
|  |  | Z-Com | 54.39.132.143 | AS16276 |  |
| pucit.edu.pk | education | Nayatel | 202.147.169.205 | AS23966 | same |
|  |  | Transworld | 202.147.169.205 | AS23966 |  |
|  |  | Z-Com | 202.147.169.205 | AS23966 |  |
| rozee.pk | education | Nayatel | 104.26.14.193;104.26.15.193;172.67.69.213 | AS13335 | same |
|  |  | Transworld | 104.26.14.193;104.26.15.193;172.67.69.213 | AS13335 |  |
|  |  | Z-Com | 104.26.14.193;104.26.15.193;172.67.69.213 | AS13335 |  |
| taleem360.com | education | Nayatel | 104.21.94.27;172.67.218.139 | AS13335 | same |
|  |  | Transworld | 104.21.94.27;172.67.218.139 | AS13335 |  |
|  |  | Z-Com | 104.21.94.27;172.67.218.139 | AS13335 |  |
| taleemabad.com | education | Nayatel | 47.129.37.78 | AS16509 | same |
|  |  | Transworld | 47.129.37.78 | AS16509 |  |
|  |  | Z-Com | 47.129.37.78 | AS16509 |  |
| uet.edu.pk | education | Nayatel | 104.21.79.62;172.67.142.140 | AS13335 | same |
|  |  | Transworld | 104.21.79.62;172.67.142.140 | AS13335 |  |
|  |  | Z-Com | 104.21.79.62;172.67.142.140 | AS13335 |  |
| zameen.com | real_estate | Nayatel | 108.131.240.252;108.133.16.203;54.154.192.49 | AS16509 | same |
|  |  | Transworld | 108.131.240.252;108.133.16.203;54.154.192.49 | AS16509 |  |
|  |  | Z-Com | 108.131.240.252;108.133.16.203;54.154.192.49 | AS16509 |  |

## batch10

| Website | Category | Probe (ISP) | Resolved IP(s) | IP ASN | Per-ISP agreement |
|---|---|---|---|---|---|
| bykea.com | food | Nayatel | 104.21.59.53;172.67.214.144 | AS13335 | DIFFERS (GeoDNS) |
|  |  | Transworld | 104.21.59.53;172.67.214.144 | AS13335 |  |
|  |  | Z-Com | 188.114.96.6;188.114.96.7;188.114.97.6;188.114.97.7 | AS13335 |  |
| cheetay.pk | food | Nayatel | (none) | - | same |
|  |  | Transworld | (none) | - |  |
|  |  | Z-Com | (none) | - |  |
| dawaaidawa.com | health | Nayatel | (none) | - | same |
|  |  | Transworld | (none) | - |  |
|  |  | Z-Com | (none) | - |  |
| foodpanda.pk | food | Nayatel | 104.18.33.30;172.64.154.226 | AS13335 | same |
|  |  | Transworld | 104.18.33.30;172.64.154.226 | AS13335 |  |
|  |  | Z-Com | 104.18.33.30;172.64.154.226 | AS13335 |  |
| gharbaar.com | real_estate | Nayatel | 15.206.219.50;43.204.181.126 | AS16509 | same |
|  |  | Transworld | 15.206.219.50;43.204.181.126 | AS16509 |  |
|  |  | Z-Com | 15.206.219.50;43.204.181.126 | AS16509 |  |
| hum.tv | entertainment | Nayatel | 20.74.192.6 | AS8075 | same |
|  |  | Transworld | 20.74.192.6 | AS8075 |  |
|  |  | Z-Com | 20.74.192.6 | AS8075 |  |
| lamudi.pk | real_estate | Nayatel | (none) | - | same |
|  |  | Transworld | (none) | - |  |
|  |  | Z-Com | (none) | - |  |
| oladoc.com | health | Nayatel | 104.26.12.63;104.26.13.63;172.67.68.42 | AS13335 | same |
|  |  | Transworld | 104.26.12.63;104.26.13.63;172.67.68.42 | AS13335 |  |
|  |  | Z-Com | 104.26.12.63;104.26.13.63;172.67.68.42 | AS13335 |  |
| sehat.com.pk | health | Nayatel | 104.21.57.219;172.67.192.115 | AS13335 | same |
|  |  | Transworld | 104.21.57.219;172.67.192.115 | AS13335 |  |
|  |  | Z-Com | 104.21.57.219;172.67.192.115 | AS13335 |  |
| shifa.com.pk | health | Nayatel | 104.26.14.111;104.26.15.111;172.67.68.27 | AS13335 | same |
|  |  | Transworld | 104.26.14.111;104.26.15.111;172.67.68.27 | AS13335 |  |
|  |  | Z-Com | 104.26.14.111;104.26.15.111;172.67.68.27 | AS13335 |  |

## batch11

| Website | Category | Probe (ISP) | Resolved IP(s) | IP ASN | Per-ISP agreement |
|---|---|---|---|---|---|
| aplus.tv | entertainment | Nayatel | (none) | - | same |
|  |  | Transworld | (none) | - |  |
|  |  | Z-Com | (none) | - |  |
| dramas.online | entertainment | Nayatel | 15.197.204.56;3.33.243.145 | AS16509 | same |
|  |  | Transworld | 15.197.204.56;3.33.243.145 | AS16509 |  |
|  |  | Z-Com | 15.197.204.56;3.33.243.145 | AS16509 |  |
| paktv.tv | entertainment | Nayatel | 185.151.30.207 | AS48254 | same |
|  |  | Transworld | 185.151.30.207 | AS48254 |  |
|  |  | Z-Com | 185.151.30.207 | AS48254 |  |