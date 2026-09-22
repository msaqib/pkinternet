# Traceroutes to the 26 selected PK sites, from two probes

Probes: Nayatel (probe 60223) and Z COM Networks (probe 7613). Delays are in ms. `*` means no reply. Country is the registry country of the hop address. `dest` is the destination's own reply.

Protocol: TCP port 443 for 52 of 52 traces. Where the destination did not answer TCP but did answer ICMP, the ICMP trace is added (6 traces).

| # | Site | Tranco rank | Sector | Nayatel | Z COM |
|---|---|---|---|---|---|
| 1 | vu.edu.pk | 10,918 | Education | reached, 9 ms | reached, 2 ms |
| 2 | aiou.edu.pk | 13,428 | Education | reached, 4 ms | reached, 37 ms |
| 3 | punjab.gov.pk | 15,755 | Government Services & Facilities | reached, 16 ms | reached, 1 ms |
| 4 | weboc.gov.pk | 22,523 | Government Services & Facilities | reached, 56 ms | reached, 93 ms |
| 5 | cyber.net.pk | 27,376 | Communications | TCP not reached; ICMP reached, 24 ms | TCP not reached; ICMP reached, 96 ms |
| 6 | ntc.net.pk | 29,528 | Communications | reached, 4 ms | reached, 200 ms |
| 7 | pu.edu.pk | 34,716 | Education | TCP not reached; ICMP reached, 24 ms | TCP not reached; ICMP reached, 20 ms |
| 8 | zong.com.pk | 36,984 | Communications | reached, 4 ms | reached, 37 ms |
| 9 | connect.net.pk | 41,417 | Communications | reached, 27 ms | reached, 19 ms |
| 10 | hec.gov.pk | 42,527 | Education | reached, 4 ms | reached, 37 ms |
| 11 | gerrys.net | 44,989 | Communications | reached, 23 ms | reached, 23 ms |
| 12 | ppsc.gop.pk | 45,910 | Government Services & Facilities | reached, 16 ms | reached, 2 ms |
| 13 | mora.gov.pk | 46,140 | Government Services & Facilities | reached, 4 ms | reached, 36 ms |
| 14 | fbr.gov.pk | 46,414 | Government Services & Facilities | reached, 4 ms | reached, 36 ms |
| 15 | lums.edu.pk | 55,995 | Education | not reached | reached, 3 ms |
| 16 | tamashaweb.com | 58,607 | Commercial Facilities | reached, 39 ms | reached, 1 ms |
| 17 | lesco.gov.pk | 80,932 | Energy | reached, 18 ms | reached, 3 ms |
| 18 | kpese.gov.pk | 84,512 | Education | TCP not reached; ICMP reached, 6 ms | TCP not reached; ICMP reached, 43 ms |
| 19 | ep.gov.pk | 86,688 | Transportation Systems | reached, 5 ms | reached, 38 ms |
| 20 | cinepax.com | 90,901 | Commercial Facilities | reached, 41 ms | reached, 3 ms |
| 21 | cll.com.pk | 92,344 | Healthcare & Public Health | reached, 17 ms | reached, 2 ms |
| 22 | pmdc.pk | 102,122 | Healthcare & Public Health | reached, 4 ms | reached, 37 ms |
| 23 | pshealthpunjab.gov.pk | 102,355 | Healthcare & Public Health | reached, 27 ms | reached, 3 ms |
| 24 | gepco.com.pk | 105,072 | Energy | not reached | not reached |
| 25 | cuecinemas.com | 109,213 | Commercial Facilities | reached, 16 ms | reached, 2 ms |
| 26 | universalcinemas.com | 109,816 | Commercial Facilities | reached, 44 ms | reached, 22 ms |

## 1. vu.edu.pk

Tranco rank 10,918, Education, WATEEN-IMS-PK-AS-AP, destination 58.27.231.136

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 8.8 ms
      1  192.168.18.1         1.5 ms  private address
      2  100.89.160.1         3.6 ms  shared address space (ISP internal)
    3-7  *
   dest  58.27.231.136        8.8 ms  PK  WATEEN-IMS-PK-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 1.8 ms
      1  157.20.147.17        0.3 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       4.2 ms  PK  TWA-AS-AP
      3  110.93.197.49        1.5 ms  PK  TWA-AS-AP
    4-5  *
      6  111.68.103.53        1.7 ms  PK  HECPERN-AS-PK
      7  58.27.231.136        1.8 ms  PK  WATEEN-IMS-PK-AS-AP   <- destination
```

## 2. aiou.edu.pk

Tranco rank 13,428, Education, HECPERN-AS-PK, destination 45.64.25.46

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 3.9 ms
      1  192.168.18.1         2.1 ms  private address
      2  100.89.160.1         3.5 ms  shared address space (ISP internal)
    3-7  *
   dest  45.64.25.46          3.9 ms  PK  HECPERN-AS-PK   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 36.9 ms
      1  157.20.147.17        0.4 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.9 ms  PK  TWA-AS-AP
      3  110.93.252.50       16.2 ms  PK  TWA
      4  110.93.255.187      36.5 ms  PK  TWA
      5  117.20.23.234       37.4 ms  PK  TWA-AS-AP
    6-7  *
      8  45.64.25.46         36.9 ms  PK  HECPERN-AS-PK   <- destination
```

## 3. punjab.gov.pk

Tranco rank 15,755, Government Services & Facilities, PITB-PUNJAB-PK, destination 103.226.216.120

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 16.0 ms
      1  192.168.18.1         1.6 ms  private address
      2  100.89.160.1        10.0 ms  shared address space (ISP internal)
    3-7  *
   dest  103.226.216.120     16.0 ms  PK  PITB-PUNJAB-PK   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 1.5 ms
      1  157.20.147.17        1.0 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.8 ms  PK  TWA-AS-AP
      3  110.93.252.191       1.0 ms  PK  TWA
      4  110.93.202.170       1.3 ms  PK  TWA
    5-7  *
      8  103.226.216.120      1.5 ms  PK  PITB-PUNJAB-PK   <- destination
```

## 4. weboc.gov.pk

Tranco rank 22,523, Government Services & Facilities, CYBERNET-APII, destination 175.107.219.203

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 55.6 ms
      1  192.168.18.1         1.5 ms  private address
      2  100.89.160.1         3.2 ms  shared address space (ISP internal)
    3-7  *
   dest  175.107.219.203     55.6 ms  PK  CYBERNET-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 92.8 ms
      1  157.20.147.17        1.0 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       1.0 ms  PK  TWA-AS-AP
      3  110.93.252.200      16.5 ms  PK  TWA
      4  157.20.147.17        0.0 ms  PK  ZCOMNETWORKS-AS-AP
    5-7  *
      8  175.107.219.203     92.8 ms  PK  CYBERNET-AP   <- destination
```

## 5. cyber.net.pk

Tranco rank 27,376, Communications, CYBERNET-AP, destination 203.101.172.72

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination did not reply
      1  192.168.18.1         1.3 ms  private address
      2  100.89.160.1         3.3 ms  shared address space (ISP internal)
  3-255  *
```

Same probe, ICMP (the destination answered this one):

```
destination replied, 23.8 ms
      1  192.168.18.1         1.5 ms  private address
      2  100.89.160.1         3.0 ms  shared address space (ISP internal)
      3  172.27.0.29          3.0 ms  private address
      4  172.27.0.22          2.2 ms  private address
      5  172.31.5.170         2.7 ms  private address
      6  110.93.202.134       2.9 ms  PK  TWA
      7  110.93.253.110      21.9 ms  PK  TWA
      8  119.63.137.61       23.8 ms  PK  TWA
   9-11  *
     12  203.101.172.72      23.8 ms  PK  CYBERNET-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination did not reply
      1  157.20.147.17        0.4 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       1.0 ms  PK  TWA-AS-AP
      3  110.93.254.66       16.3 ms  PK  TWA
  4-255  *
```

Same probe, ICMP (the destination answered this one):

```
destination replied, 96.0 ms
      1  157.20.147.17        0.5 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.9 ms  PK  TWA-AS-AP
      3  110.93.254.66       19.9 ms  PK  TWA
      4  *
      5  192.168.76.193     100.7 ms  private address
      6  192.168.4.9         96.1 ms  private address
      7  10.15.1.2           97.1 ms  private address
      8  203.101.172.72      96.0 ms  PK  CYBERNET-AP   <- destination
```

## 6. ntc.net.pk

Tranco rank 29,528, Communications, CYBERNET-AP, destination 203.101.184.82

**Detour from Z COM:** the path leaves Pakistan through SG, NL, US and reaches the site in 200 ms. From Nayatel it takes 4 ms.

DDOS Scrubbing effect

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 3.9 ms
      1  192.168.18.1         1.8 ms  private address
      2  100.89.160.1        17.3 ms  shared address space (ISP internal)
    3-7  *
   dest  203.101.184.82       3.9 ms  PK  CYBERNET-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 199.7 ms
      1  157.20.147.17        1.3 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       1.0 ms  PK  TWA-AS-AP
      3  110.93.252.102      16.4 ms  PK  TWA
      4  110.93.252.246      16.6 ms  PK  TWA
      5  27.111.228.157      91.6 ms  SG  EQUINIX-AP
      6  2.21.120.169        91.8 ms  NL  PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NETWORK
      7  72.52.21.194       275.9 ms  US  PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NETWORK
   8-10  *
     11  175.107.33.22      199.5 ms  PK  NTC-AS-AP
     12  203.101.184.82     199.7 ms  PK  CYBERNET-AP   <- destination
```

**Nayatel (probe 60223, AS23674), ICMP and UDP**

The TCP/443 trace from Nayatel showed nothing at hops 3 to 7. Two more traces to the same destination were run from the same probe to expose them. One used ICMP (measurement 213596339) and one used UDP (measurement 213596343). Both gave the same path. Delays here are the median of three replies.

```
ICMP, destination did not reply
      1  192.168.18.1         0.8 ms  private address
      2  100.89.160.1         2.9 ms  shared address space (ISP internal)
      3  172.27.0.29          3.1 ms  private address
      4  172.27.0.22          2.7 ms  private address
      5  172.31.5.170         3.1 ms  private address
      6  103.213.108.67       4.2 ms  PK  HTISPL-PK
      7  202.163.94.89        9.7 ms  PK  CYBERNET-AP
   8-12  *
    255  *
```

```
UDP, destination did not reply
      1  192.168.18.1         1.0 ms  private address
      2  100.89.160.1         2.9 ms  shared address space (ISP internal)
      3  172.27.0.29          2.7 ms  private address
      4  172.27.0.22          2.6 ms  private address
      5  172.31.5.170         2.8 ms  private address
      6  103.213.108.67       3.6 ms  PK  HTISPL-PK
      7  202.163.94.89        3.4 ms  PK  CYBERNET-AP
   8-12  *
    255  *
```

Hops 1 to 5 are inside Nayatel. Hop 6 is registered to Cyber Internet Services Pakistan (Cybernet) and hop 7 is in Cybernet's AS9541. Nayatel therefore hands the traffic to Cybernet at hop 6, within about 4 ms. No hop leaves Pakistan and none belongs to Prolexic.

Hops 8 to 12 and the destination did not reply to ICMP or UDP, so the last part of the path is not observed. The destination did answer TCP/443 in 3.9 ms, which is too fast for a detour abroad. RIPE RIS shows all 363 paths to 203.101.184.0/24 passing through AS32787 (Prolexic). Nayatel does not use that route.

## 7. pu.edu.pk

Tranco rank 34,716, Education, HECPERN-AS-PK, destination 111.68.103.27

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination did not reply
      1  192.168.18.1         1.0 ms  private address
      2  100.89.160.1         3.3 ms  shared address space (ISP internal)
  3-255  *
```

Same probe, ICMP (the destination answered this one):

```
destination replied, 23.5 ms
      1  192.168.18.1         1.5 ms  private address
      2  100.89.160.1         2.9 ms  shared address space (ISP internal)
      3  172.27.0.29          3.6 ms  private address
      4  172.27.0.22          2.7 ms  private address
      5  172.31.5.170         3.1 ms  private address
      6  103.213.108.66       4.0 ms  PK  HTISPL-PK
    7-9  *
     10  111.68.103.27       23.5 ms  PK  HECPERN-AS-PK   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination did not reply
      1  157.20.147.17        0.4 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       1.0 ms  PK  TWA-AS-AP
      3  110.93.252.54       16.3 ms  PK  TWA
      4  110.93.255.169      17.0 ms  PK  TWA
      5  110.93.253.193      17.2 ms  PK  TWA
      6  117.20.16.70        24.3 ms  PK  TWA-AS-AP
  7-255  *
```

Same probe, ICMP (the destination answered this one):

```
destination replied, 20.4 ms
      1  157.20.147.17       12.6 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.8 ms  PK  TWA-AS-AP
      3  110.93.252.48       16.1 ms  PK  TWA
      4  110.93.255.169      16.7 ms  PK  TWA
      5  110.93.253.193      17.3 ms  PK  TWA
      6  117.20.16.70        18.2 ms  PK  TWA-AS-AP
   7-11  *
   dest  111.68.103.27       20.4 ms  PK  HECPERN-AS-PK   <- destination
```

## 8. zong.com.pk

Tranco rank 36,984, Communications, CMPAKLIMITED-AS-AP, destination 209.150.154.189

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 3.9 ms
      1  192.168.18.1         1.5 ms  private address
      2  100.89.160.1         3.3 ms  shared address space (ISP internal)
    3-7  *
   dest  209.150.154.189      3.9 ms  PK  CMPAKLIMITED-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 36.9 ms
      1  157.20.147.17        0.5 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.9 ms  PK  TWA-AS-AP
      3  110.93.254.66       16.3 ms  PK  TWA
      4  110.93.254.87       36.2 ms  PK  TWA
      5  149.40.227.35       37.0 ms  US  COGENT-174
   6-10  *
   dest  209.150.154.189     36.9 ms  PK  CMPAKLIMITED-AS-AP   <- destination
```

## 9. connect.net.pk

Tranco rank 41,417, Communications, CONNECT-AS-AP, destination 115.42.65.248

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 27.5 ms
      1  192.168.18.1         1.0 ms  private address
      2  100.89.160.1         3.7 ms  shared address space (ISP internal)
    3-7  *
   dest  115.42.65.248       27.5 ms  PK  CONNECT-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 18.7 ms
      1  157.20.147.17        0.7 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.9 ms  PK  TWA-AS-AP
      3  110.93.252.200      16.5 ms  PK  TWA
      4  110.93.254.161      17.3 ms  PK  TWA
      5  221.132.113.201     17.6 ms  PK  TWA-AS-AP
      6  *
      7  221.120.249.117     17.3 ms  PK  PKTELECOM-AS-PK
      8  115.42.65.248       18.7 ms  PK  CONNECT-AS-AP   <- destination
```

## 10. hec.gov.pk

Tranco rank 42,527, Education, HECPERN-AS-PK, destination 111.68.100.163

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 4.1 ms
      1  192.168.18.1         1.8 ms  private address
      2  100.89.160.1         3.3 ms  shared address space (ISP internal)
    3-7  *
   dest  111.68.100.163       4.1 ms  PK  HECPERN-AS-PK   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 36.6 ms
      1  157.20.147.17        1.3 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.9 ms  PK  TWA-AS-AP
      3  110.93.252.102      16.4 ms  PK  TWA
      4  110.93.254.99       36.7 ms  PK  TWA
      5  117.20.23.234       37.5 ms  PK  TWA-AS-AP
      6  *
      7  111.68.97.83        36.6 ms  PK  HECPERN-AS-PK
      8  111.68.100.163      36.6 ms  PK  HECPERN-AS-PK   <- destination
```

## 11. gerrys.net

Tranco rank 44,989, Communications, GERRYS-AS-AP, destination 202.69.33.8

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 23.2 ms
      1  192.168.18.1         1.5 ms  private address
      2  100.89.160.1         2.9 ms  shared address space (ISP internal)
    3-7  *
   dest  202.69.33.8         23.2 ms  PK  GERRYS-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 23.1 ms
      1  157.20.147.17        0.3 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.9 ms  PK  TWA-AS-AP
      3  110.93.252.50       19.3 ms  PK  TWA
      4  110.93.255.169      19.8 ms  PK  TWA
      5  119.63.129.98       29.2 ms  PK  TWA-AS-AP
      6  202.69.33.8         23.1 ms  PK  GERRYS-AS-AP   <- destination
```

## 12. ppsc.gop.pk

Tranco rank 45,910, Government Services & Facilities, PITB-PUNJAB-PK, destination 103.111.161.187

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 16.4 ms
      1  192.168.18.1         1.1 ms  private address
      2  100.89.160.1         5.2 ms  shared address space (ISP internal)
    3-7  *
   dest  103.111.161.187     16.4 ms  PK  PITB-PUNJAB-PK   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 2.2 ms
      1  157.20.147.17        0.3 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       6.6 ms  PK  TWA-AS-AP
      3  110.93.252.191       2.5 ms  PK  TWA
      4  110.93.202.170       1.3 ms  PK  TWA
    5-7  *
      8  103.111.161.187      2.2 ms  PK  PITB-PUNJAB-PK   <- destination
```

## 13. mora.gov.pk

Tranco rank 46,140, Government Services & Facilities, NTC-AS-AP, destination 43.250.84.202

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 3.6 ms
      1  192.168.18.1         1.0 ms  private address
      2  100.89.160.1         3.4 ms  shared address space (ISP internal)
    3-7  *
   dest  43.250.84.202        3.6 ms  PK  NTC-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 36.2 ms
      1  157.20.147.17        0.3 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.9 ms  PK  TWA-AS-AP
      3  110.93.254.38       16.3 ms  PK  TWA
      4  110.93.253.209      35.9 ms  PK  TWA
      5  119.63.136.223      36.1 ms  PK  TWA
      6  202.83.160.210      37.0 ms  PK  NTC-AS-AP
      7  175.107.33.22       36.1 ms  PK  NTC-AS-AP
      8  43.250.84.202       36.2 ms  PK  NTC-AS-AP   <- destination
```

## 14. fbr.gov.pk

Tranco rank 46,414, Government Services & Facilities, FBR-AS-AP, destination 103.125.60.60

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 4.1 ms
      1  192.168.18.1         1.1 ms  private address
      2  100.89.160.1         3.4 ms  shared address space (ISP internal)
    3-7  *
   dest  103.125.60.60        4.1 ms  PK  FBR-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 36.5 ms
      1  157.20.147.17        3.0 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.8 ms  PK  TWA-AS-AP
      3  110.93.252.50       16.3 ms  PK  TWA
      4  110.93.252.107      36.1 ms  PK  TWA
      5  119.63.134.206      37.3 ms  PK  TWA-AS-AP
      6  *
      7  103.125.60.60       36.5 ms  PK  FBR-AS-AP   <- destination
```

## 15. lums.edu.pk

Tranco rank 55,995, Education, TWA-AS-AP, destination 110.93.234.24

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination did not reply
      1  192.168.18.1         1.6 ms  private address
      2  100.89.160.1         3.2 ms  shared address space (ISP internal)
  3-255  *
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 2.9 ms
      1  157.20.147.17        7.9 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184      13.3 ms  PK  TWA-AS-AP
      3  110.93.252.191       1.2 ms  PK  TWA
      4  119.63.135.106       1.3 ms  PK  TWA-AS-AP
      5  110.93.234.24        2.9 ms  PK  TWA-AS-AP   <- destination
      6  *
      7  110.93.234.24     1000.7 ms  PK  TWA-AS-AP   <- destination
```

## 16. tamashaweb.com

Tranco rank 58,607, Commercial Facilities, Mobilink-AS-PK, destination 119.160.12.44

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 39.0 ms
      1  192.168.18.1         1.3 ms  private address
      2  100.89.160.1         3.1 ms  shared address space (ISP internal)
    3-7  *
   dest  119.160.12.44       39.0 ms  PK  Mobilink-AS-PK   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 1.0 ms
      1  157.20.147.17        0.4 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       1.0 ms  PK  TWA-AS-AP
      3  110.93.252.139       1.0 ms  PK  TWA
      4  110.93.255.94        1.1 ms  PK  TWA
      5  110.93.249.185       9.3 ms  PK  TWA-AS-AP
      6  119.30.106.58        1.5 ms  PK  LDN-AS-PK
      7  *
      8  119.160.12.44        1.0 ms  PK  Mobilink-AS-PK   <- destination
```

## 17. lesco.gov.pk

Tranco rank 80,932, Energy, NEXLINX-AS-AP, destination 116.58.54.125

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 18.0 ms
      1  192.168.18.1         1.5 ms  private address
      2  100.89.160.1         3.5 ms  shared address space (ISP internal)
      3  192.168.18.1         0.0 ms  private address
    4-7  *
   dest  116.58.54.125       18.0 ms  PK  NEXLINX-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 3.3 ms
      1  157.20.147.17        0.3 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       2.3 ms  PK  TWA-AS-AP
      3  110.93.252.139       1.0 ms  PK  TWA
      4  110.93.255.94        1.0 ms  PK  TWA
      5  110.93.202.170       1.4 ms  PK  TWA
    6-7  *
      8  202.59.80.68         2.2 ms  PK  NEXLINX-AS-AP
      9  *
     10  116.58.54.125        3.3 ms  PK  NEXLINX-AS-AP   <- destination
```

## 18. kpese.gov.pk

Tranco rank 84,512, Education, NTC-AS-AP, destination 175.107.63.111

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination did not reply
      1  192.168.18.1         0.8 ms  private address
      2  100.89.160.1         3.7 ms  shared address space (ISP internal)
  3-255  *
```

Same probe, ICMP (the destination answered this one):

```
destination replied, 5.8 ms
      1  192.168.18.1         1.5 ms  private address
      2  100.89.160.1         2.7 ms  shared address space (ISP internal)
      3  172.27.0.29          2.7 ms  private address
      4  172.27.0.22          2.1 ms  private address
      5  172.31.5.170         2.7 ms  private address
      6  110.93.202.134       2.5 ms  PK  TWA
      7  110.93.254.7         2.9 ms  PK  TWA
      8  110.93.204.153       5.9 ms  PK  TWA-AS-AP
      9  175.107.63.3         5.7 ms  PK  NTC-AS-AP
     10  175.107.63.3        11.6 ms  PK  NTC-AS-AP
     11  175.107.63.111       5.8 ms  PK  NTC-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination did not reply
      1  157.20.147.17        0.7 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.9 ms  PK  TWA-AS-AP
      3  110.93.252.200      16.4 ms  PK  TWA
      4  110.93.254.23       36.6 ms  PK  TWA
      5  110.93.204.153      39.3 ms  PK  TWA-AS-AP
      6  175.107.63.3        42.8 ms  PK  NTC-AS-AP
  7-255  *
```

Same probe, ICMP (the destination answered this one):

```
destination replied, 42.6 ms
      1  157.20.147.17        0.6 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.6 ms  PK  TWA-AS-AP
      3  110.93.252.48       19.8 ms  PK  TWA
      4  110.93.254.111      39.2 ms  PK  TWA
      5  110.93.204.153      42.3 ms  PK  TWA-AS-AP
      6  175.107.63.3        42.3 ms  PK  NTC-AS-AP
      7  175.107.63.3        42.7 ms  PK  NTC-AS-AP
      8  175.107.63.111      42.6 ms  PK  NTC-AS-AP   <- destination
```

## 19. ep.gov.pk

Tranco rank 86,688, Transportation Systems, NAYATEL-PK, destination 124.109.52.82

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 5.3 ms
      1  192.168.18.1         1.0 ms  private address
      2  100.89.160.1         3.4 ms  shared address space (ISP internal)
    3-4  *
      5  172.31.5.205         4.1 ms  private address
      6  172.16.90.246        3.9 ms  private address
      7  *
      8  124.109.36.76        5.6 ms  PK  NAYATEL-PK
      9  124.109.52.82        5.3 ms  PK  NAYATEL-PK   <- destination
     10  124.109.52.82        5.0 ms  PK  NAYATEL-PK   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 38.1 ms
      1  157.20.147.17        0.6 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       7.7 ms  PK  TWA-AS-AP
      3  110.93.252.48       16.3 ms  PK  TWA
      4  110.93.252.107      36.0 ms  PK  TWA
      5  110.93.202.135      36.3 ms  PK  TWA
    6-9  *
     10  124.109.36.76       38.1 ms  PK  NAYATEL-PK
     11  124.109.52.82       38.1 ms  PK  NAYATEL-PK   <- destination
     12  124.109.52.82       37.8 ms  PK  NAYATEL-PK   <- destination
```

## 20. cinepax.com

Tranco rank 90,901, Commercial Facilities, ASN-NCKHI-AP, destination 103.249.155.209

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 40.6 ms
      1  192.168.18.1         1.6 ms  private address
      2  100.89.160.1         3.2 ms  shared address space (ISP internal)
    3-4  *
      5  192.168.18.1         0.0 ms  private address
    6-7  *
   dest  103.249.155.209     40.6 ms  PK  ASN-NCKHI-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 2.7 ms
      1  157.20.147.17       19.5 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       1.1 ms  PK  TWA-AS-AP
      3  119.63.130.53        1.5 ms  PK  TWA-AS-AP
      4  195.129.143.2        1.7 ms  NL  UUNET
      5  195.129.100.134      1.8 ms  NL  UUNET
      6  195.129.100.2        2.0 ms  NL  UUNET
      7  *
      8  103.249.155.209      2.7 ms  PK  ASN-NCKHI-AP   <- destination
      9  103.249.155.209      3.5 ms  PK  ASN-NCKHI-AP   <- destination
```

## 21. cll.com.pk

Tranco rank 92,344, Healthcare & Public Health, MULTINET-AS-AP, destination 125.209.70.164

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 17.2 ms
      1  192.168.18.1         1.7 ms  private address
      2  100.89.160.1         7.8 ms  shared address space (ISP internal)
    3-7  *
   dest  125.209.70.164      17.2 ms  PK  MULTINET-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 1.7 ms
      1  157.20.147.17        2.0 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       9.3 ms  PK  TWA-AS-AP
      3  110.93.197.229       2.1 ms  PK  TWA-AS-AP
      4  202.142.160.201      1.4 ms  PK  MULTINET-AS-AP
      5  125.209.70.164       1.7 ms  PK  MULTINET-AS-AP   <- destination
      6  125.209.70.164       3.5 ms  PK  MULTINET-AS-AP   <- destination
```

## 22. pmdc.pk

Tranco rank 102,122, Healthcare & Public Health, NTC-AS-AP, destination 175.107.60.117

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 3.6 ms
      1  192.168.18.1         1.1 ms  private address
      2  100.89.160.1         3.2 ms  shared address space (ISP internal)
    3-7  *
   dest  175.107.60.117       3.6 ms  PK  NTC-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 36.7 ms
      1  157.20.147.17        1.6 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       8.6 ms  PK  TWA-AS-AP
      3  110.93.254.38       16.3 ms  PK  TWA
      4  110.93.252.107      36.1 ms  PK  TWA
      5  119.63.136.223      36.0 ms  PK  TWA
      6  202.83.160.210      37.3 ms  PK  NTC-AS-AP
      7  175.107.33.22       36.1 ms  PK  NTC-AS-AP
      8  175.107.60.117      36.7 ms  PK  NTC-AS-AP   <- destination
```

## 23. pshealthpunjab.gov.pk

Tranco rank 102,355, Healthcare & Public Health, NEXLINX-AS-AP, destination 116.58.20.78

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 27.2 ms
      1  192.168.18.1         1.4 ms  private address
      2  100.89.160.1         3.6 ms  shared address space (ISP internal)
    3-7  *
   dest  116.58.20.78        27.2 ms  PK  NEXLINX-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 3.0 ms
      1  157.20.147.17        0.6 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       2.1 ms  PK  TWA-AS-AP
    3-4  *
      5  202.125.140.26       1.7 ms  PK  PKTELECOM-AS-PK
    6-7  *
      8  202.59.80.56         1.7 ms  PK  NEXLINX-AS-AP
   9-10  *
     11  116.58.20.75         2.9 ms  PK  NEXLINX-AS-AP
     12  116.58.20.78         3.0 ms  PK  NEXLINX-AS-AP   <- destination
```

## 24. gepco.com.pk

Tranco rank 105,072, Energy, PITC1-AS-AP, destination 163.61.25.23

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination did not reply
      1  192.168.18.1         1.0 ms  private address
      2  100.89.160.1         3.4 ms  shared address space (ISP internal)
  3-255  *
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination did not reply
      1  157.20.147.17        0.7 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184      12.0 ms  PK  TWA-AS-AP
      3  149.40.227.93        1.5 ms  US  COGENT-174
      4  *
      5  157.20.147.17        0.0 ms  PK  ZCOMNETWORKS-AS-AP
  6-255  *
```

## 25. cuecinemas.com

Tranco rank 109,213, Commercial Facilities, MULTINET-AS-AP, destination 202.141.242.194

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 16.0 ms
      1  192.168.18.1         1.5 ms  private address
      2  100.89.160.1         3.2 ms  shared address space (ISP internal)
    3-7  *
   dest  202.141.242.194     16.0 ms  PK  MULTINET-AS-AP   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 1.5 ms
      1  157.20.147.17        0.8 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       0.9 ms  PK  TWA-AS-AP
      3  110.93.197.229       1.6 ms  PK  TWA-AS-AP
      4  202.142.160.201      1.4 ms  PK  MULTINET-AS-AP
      5  202.141.242.194      1.5 ms  PK  MULTINET-AS-AP   <- destination
```

## 26. universalcinemas.com

Tranco rank 109,816, Commercial Facilities, LDN-AS-PK, destination 103.69.111.99

**Nayatel (probe 60223, AS23674)**, TCP/443

```
destination replied, 43.8 ms
      1  192.168.18.1         1.5 ms  private address
      2  100.89.160.1         3.2 ms  shared address space (ISP internal)
    3-7  *
   dest  103.69.111.99       43.8 ms  PK  LDN-AS-PK   <- destination
```

**Z COM (probe 7613, AS152605)**, TCP/443

```
destination replied, 21.9 ms
      1  157.20.147.17        0.6 ms  PK  ZCOMNETWORKS-AS-AP
      2  110.93.205.184       1.1 ms  PK  TWA-AS-AP
      3  110.93.252.54       16.3 ms  PK  TWA
      4  110.93.255.169      17.0 ms  PK  TWA
      5  110.93.202.21       19.8 ms  PK  TWA
    6-7  *
      8  119.30.106.42       39.1 ms  PK  LDN-AS-PK
      9  119.30.105.222      35.8 ms  PK  Mobilink-Peering-AS-PK
  10-11  *
     12  202.147.168.70      20.8 ms  PK  LDN-AS-PK
  13-14  *
     15  103.69.111.99       21.9 ms  PK  LDN-AS-PK   <- destination
```
