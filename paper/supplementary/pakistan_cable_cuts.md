# Pakistan submarine cable faults, 2021-2026

Compiled to source the paper's introduction claim on frequency of submarine
cable faults (replaces the outdated 2022-only figure from
`opalinski2024quest`). Rows for 2021-Aug 2024 come from one document-based
source (ProPakistani/SubTel Forum); rows for Jan 2025 onward are each
independently verified against news reporting of PTA/PTCL/parliamentary
statements.

| Date | Cable | Location / cause | Impact | Source |
|---|---|---|---|---|
| Feb 2021 | TW-1 | Egypt, land cut | Few hours | subtelforum2024pakistan |
| Dec 2021 | AAE-1 | UAE, land cut | Few hours | subtelforum2024pakistan |
| Feb 2022 | TW-1 | 400 km off Karachi | 3 months | subtelforum2024pakistan |
| Nov 2022 | SEAMEWE-5 | Egypt, land cut | Few hours | subtelforum2024pakistan |
| Apr 2023 | AAE-1 | France, land cut | 250 Gbps loss | subtelforum2024pakistan |
| Feb 2024 | SEAMEWE-5 | Egypt, land cut | Few hours | subtelforum2024pakistan |
| 17 Jun 2024 | SEAMEWE-4 | Offshore near Karachi | 1,500 Gbps loss | subtelforum2024pakistan |
| 31 Jul 2024 | PTCL | System configuration error | Few hours | subtelforum2024pakistan |
| 17 Aug 2024 | AAE-1 | Maintenance-related fault | 250 Gbps loss | subtelforum2024pakistan |
| 2 Jan 2025 | AAE-1 | Near Qatar | Ad hoc bandwidth added | tribune2025aae1 |
| 6 Sep 2025 | SMW4 + IMEWE | Cut near Jeddah, Red Sea | Peak-hour slowdowns nationwide | aljazeera2025redsea |
| 14 Oct 2025 | (unnamed, repeater repair) | Planned maintenance | ~18 hr degradation | arabnews2025maintenance |
| 2 Jul 2026 | SMW5 | (project's own Exp 06 fault) | Rerouted, restored ~2 weeks | pta2026smw5 |

## Rollups

- **Since 2021 (full table): 13 incidents**
- **Since 2024 (used in the paper's intro): 8 incidents**
- **Trailing 2 years (Aug 2024-Aug 2026): 5 incidents**

## Not included

- A claimed "early 2026" fault distinct from the July 2026 SMW5 event could
  not be verified. The lead that suggested it traces back to a search result
  that mislabeled the Jan 2, 2025 AAE-1/Qatar fault as "January 2026." Treated
  as a duplicate, not a real separate incident.

## Sources (add to `references.bib` if not already present)

```bibtex
@misc{subtelforum2024pakistan,
  author       = {{SubTel Forum}},
  title        = {Real Culprit Behind {P}akistan 2024 Internet Disruptions},
  year         = {2024},
  month        = oct,
  howpublished = {\url{https://subtelforum.com/real-culprit-behind-pakistan-2024-internet-disruptions/}}
}

@misc{tribune2025aae1,
  author       = {{The Express Tribune}},
  title        = {{PTA} warns of internet disruptions nationwide due to submarine cable fault},
  year         = {2025},
  month        = jan,
  howpublished = {\url{https://tribune.com.pk/story/2519674/pta-warns-of-internet-disruptions-nationwide-due-to-submarine-cable-fault}}
}

@misc{aljazeera2025redsea,
  author       = {{Al Jazeera}},
  title        = {Internet disruptions in {M}iddle {E}ast and {S}outh {A}sia after {R}ed {S}ea cable cuts},
  year         = {2025},
  month        = sep,
  howpublished = {\url{https://www.aljazeera.com/news/2025/9/7/internet-disruptions-in-middle-east-and-south-asia-after-red-sea-cable-cuts}}
}

@misc{arabnews2025maintenance,
  author       = {{Arab News}},
  title        = {Pakistan's {PTCL} warns of week-long Internet disruptions due to submarine cable repair},
  year         = {2025},
  month        = oct,
  howpublished = {\url{https://www.arabnews.com/node/2643101/pakistan}}
}
```

Note: `pta2026smw5` is already in `references.bib`.
