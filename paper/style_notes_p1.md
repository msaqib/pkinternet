# Writing-style notes — how "p1" is written (for our paper)

**Paper:** Sanchez, Bustamante, Krishnamurthy, Willinger, Smaragdakis, Erman —
*"Inter-Domain Traffic Estimation for the Outsider"*, **ACM IMC 2014**.
(15 pages, ~11,800 words, 84 references.) One of our Exp 03 source papers.

Notes on *how it is written* — structure, voice, wording, evidence, references — so we
can match the register when we write ours.

## 1. Overall structure (IMC measurement-paper template)
`Title → Abstract → 1 Introduction → 2 Related Work → 3–4 Methodology (the named
approach) → 5 Data → 6 Validation → 7 Evaluation/Results → 8 Discussion → 9 Conclusions
& Future Work → References`.
- **Method and evaluation are separate sections** (build the technique first, then
  prove it). Data gets its own short section (what, how much, provenance).
- **Validation before Evaluation:** they first show the method agrees with ground
  truth, *then* apply it. We should do the same — establish the detector is right
  (our RTT-physics validation) before quoting rates.

## 2. Abstract anatomy (copy this 5-move shape)
1. **Why it matters** (broad): *"Characterizing the flow of Internet traffic is
   important in a wide range of contexts, from network engineering … to … business
   relationships."*
2. **The impediment/gap:** *"the nearly impossible task of collecting large-scale …
   data has severely constrained …"*
3. **"In this paper, we introduce …"** — one-sentence statement of the contribution.
4. **The key insight, plainly:** *"the popularity of a route … can serve as an
   informative proxy for the volume of traffic it carries."*
5. **Name it + validate it with a number:** they brand it **"Network Syntax"** and
   close with hard evidence: *"strong correlation (r² up to 0.9) …"*.
→ For us: matter → (PK traffic-data / vantage gap) → "we measure tromboning/hosting
across PK from RIPE Atlas" → the insight (RTT physics beats geo-IP; route popularity /
hairpin detection) → a headline number (e.g. "X% of small-ISP prefixes hairpin abroad").

## 3. Introduction pattern
- Opens with the **research area and its history**, prior work **bracket-cited in
  clusters** (`[10, 17, 48]`), then pivots on *"There is, however, a growing consensus
  on the need to shift focus …"* — i.e. *established field → the missing piece → our
  angle*.
- Names the **central obstacle** ("The major impediment … has been the scarcity of
  publicly available traffic data") and frames the paper as removing it.
- Contributions are stated as what they *do*, not adjectives.

## 4. Voice, tense, register
- **First-person plural throughout:** "We introduce…", "We apply…", "We demonstrated…".
- **Present tense** for the method/claims ("Network Syntax applies structural
  analysis…"); **past tense** for the experiments done ("We evaluated four … datasets").
- **Formal but plain** — short declarative sentences, minimal adverbs, no hype words.
  Precision over flourish.
- **Analogy as a teaching device:** they anchor an abstract method in a familiar
  domain (*urban-planning "Space Syntax" → city grids and traffic*). A single, carried-
  through analogy makes a method memorable — worth one good analogy in ours.

## 5. Evidence & honesty
- **Quantitative everywhere** — correlations (r²), percentages, "two months of data
  collected two years apart", "a Tier-1 ISP and a large IXP".
- **Ground-truth validation is the backbone** — the claim is only as strong as the
  agreement with real data; they lead with it.
- **Explicit hedging, stated as a judgement call:** *"we acknowledge that order of
  magnitude is a coarse approximation, [but] we argue this is a valuable …"* — name the
  limitation, then justify why the result still matters. (This matches how we write our
  caveats — do it in the paper too, don't hide them.)

## 6. Figures / tables
- Figures carry the argument (distributions, correlation plots, percentage bars);
  prose refers to them by number ("as we show in Section 7.1 …"). Every quantitative
  claim is backed by a figure/table, not asserted.

## 7. References (ACM numbered style)
- **Numbered `[n]`**, dense (84 refs), cited in clusters.
- Entry format: `Author, A., and Author, B. Title. In Proc. of VENUE (Year).`
  e.g. *"Ager, B., Chatzis, N., … Anatomy of a large european IXP. In Proc. of ACM
  SIGCOMM (2012)."*
- **Datasets/tools cited as references with URLs** (RouteViews, RIPE RIS, PeeringDB,
  PCH). → We should cite RIPE Atlas, RIPEstat, Team Cymru, CAIDA pfx2as, ip-api, and the
  TASS paper this way.

## 8. Actionable checklist for our paper
- [ ] Abstract = the 5 moves above, ending on a headline number.
- [ ] Separate **Method** and **Evaluation**; put **Validation** (detector correctness:
      RTT gate vs geo-IP, the Shaw/Cogent false-positive fixes) *before* the rates.
- [ ] First-person "we"; present for method, past for measurements.
- [ ] One carried-through framing (tromboning / hairpinning / "the local path exists but
      is not used").
- [ ] Every number → a figure/table; state caveats openly and justify relevance.
- [ ] Cite tools & datasets as numbered references with URLs; cluster related cites.
- [ ] Aim IMC-length (~12–15 pp) with the standard section order.
