**Figure 1 — RTT Heatmap**

a grid where each row is a probe (ISP) and each column is a destination site. the color in each cell shows the median ping RTT in milliseconds — yellow is fast, dark red is slow. it gives a complete picture of which ISPs are fast or slow to which sites at a glance. this is the most paper-ready figure.

---

**Figure 2 — Per-ISP KPI CDFs**

one panel per ISP showing three curves — one for PK-hosted sites, one for CDN sites, one for internationally-hosted sites. the x axis is RTT and the y axis is the cumulative fraction of measurements. if the PK curve is far left (low RTT) and the Abroad curve is far right (high RTT) that confirms the tromboning penalty is real. directly answers RQ1.

---

**Figure 3 — Trombone Rate Heatmap**

same grid as figure 1 but instead of RTT the color shows what percentage of traceroute rounds were classified as tromboning for that probe-site pair. a dark cell means that ISP almost always hairpins when reaching that site. shows exactly which ISPs are the worst offenders and for which destinations.

---

**Figure 4 — Trombone Flipping**

looks only at PK-hosted sites. for each probe-site pair it calculates what fraction of rounds tromboned. shows a histogram of those fractions. pairs near 0% always stay local, pairs near 100% always trombone, pairs in the middle sometimes do one and sometimes the other. the middle ones are the most important — they prove a local path physically exists but is not consistently chosen. directly answers RQ3.

---

**Figure 5 — Diurnal Pattern**

plots median RTT by hour of day, separately for PK-hosted, CDN, and internationally-hosted sites. if the lines are flat across 24 hours the penalty is structural and not caused by evening congestion. if there are peaks at certain hours it suggests load or congestion effects. directly answers RQ2.

---

**Figure 6 — Anomaly Detection**

automatically finds the 4 probe-site pairs with the highest RTT variance over the week and plots their RTT as a time series. no manual selection needed — the script finds the most interesting cases itself. useful for spotting routing changes, outages, and events like cable faults.

---

**Figure 7 — Route Stability**

same grid structure as figures 1 and 3 but each cell shows how many distinct transit paths were observed for that probe-site pair over the full week. a value of 1 means perfectly stable routing throughout. higher values mean the path changed. mostly 1s confirm that the routing inefficiency is a stable structural choice not random variation.

---

**Statistics Table**

a CSV file with median RTT, mean RTT, packet loss percentage, and median hop count per ISP per hosting class. used to populate the numeric tables in the paper. anyone can open it in Excel or read it directly.