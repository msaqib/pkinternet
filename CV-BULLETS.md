# Candidate Research CV Bullets

*Traceable to empirical data in `EVIDENCE.tsv` and `FINDINGS.md` (APNIC Foundation funded research).*

---

### Candidate Bullet 1 (Measurement Scale & National Census)
- **Engineered a nationwide active measurement platform** across 16 RIPE Atlas probes, collecting **222,944 Paris traceroutes**, **445k+ pings**, and an 18,260-trace census across **747 prefix blocks in 48 ISPs** to conduct Pakistan's first empirical inter-domain routing study.
  - *Backing Evidence:* `EVIDENCE.tsv` rows: Exp 07 Longitudinal Panel Total Traceroutes (`findings/07_longitudinal_panel.md`), Exp 4.1 Small-ISP Census Total Traceroutes (`experiments/04.1_small_isp_tromboning/results/run_20260627_192918/census_20260627_192918.csv`).

### Candidate Bullet 2 (Transit Duopoly & Hegemony Quantification)
- **Quantified national transit dependency using global BGP AS-hegemony data** and APNIC population models, proving **89.7% of 291 Pakistani ASes** and **99.63% of ~42.3M users** depend on a PTCL/Transworld duopoly, with 87.4% of Transworld domestic infrastructure unannounced in BGP.
  - *Backing Evidence:* `EVIDENCE.tsv` rows: Exp 09 ASNs Dependent on PTCL or TWA Majority (`findings/09_as_hegemony.md`), Exp 6.1.1 APNIC User Population on Duopoly-Majority ASNs (`findings/smw5_fault_complete_story.md`), Exp 07 Unannounced Transworld Domestic Routers (`findings/07_longitudinal_panel.md`).

### Candidate Bullet 3 (Submarine Cable Outage Resilience)
- **Observed the July 2026 SEA-ME-WE 5 submarine cable fault** in real time across data and control planes, discovering a **78-sigma latency spike** on international paths while domestic routes remained 100% insulated, and demonstrating rapid recovery was driven by upstream BGP re-carriering (+7.1% to +9.1% onto Hurricane Electric) rather than physical cable repair.
  - *Backing Evidence:* `EVIDENCE.tsv` rows: Exp 6.1.1 RIPE Anchor Peak Latency Sigma Spike (`findings/smw5_fault_complete_story.md`), Exp 6.1 Hurricane Electric Upstream Surge (`findings/06.1_submarine_hegemony.md`), Exp 06 SMW5 Outage Monitor (`findings/06_submarine_outage.md`).

### Candidate Bullet 4 (IXP Bypassing & Domestic Path Tromboning)
- **Discovered 0 of 222k+ panel traceroutes crossed national IXP fabrics (PKIX/PIE)** due to private bilateral bypasses, causing **5.52%–15.1% of domestic traffic** and **58.3%–85.6% of banking traffic** to hairpin through foreign exchanges (Singapore/US) at up to **75× the physical latency floor**.
  - *Backing Evidence:* `EVIDENCE.tsv` rows: Exp 07 Longitudinal Panel Traces Crossing PKIX/PIE (`findings/07_longitudinal_panel.md`), Exp 07 Domestic Target Trombone Rate (`experiments/07_longitudinal_panel/analysis/evidence_sweep_findings.md`), Exp 07 Financial Services Trombone Rate (`paper/running_draft_detector_rules_final.md`), Exp 07 Pakistan Class Latency Ratio Maximum Tail Peak (`experiments/07_longitudinal_panel/analysis/ratio_corrected.csv`).
