# Style checklist: de-AI-ing the draft

Patterns to hunt for on a reread. Each one came up as an actual fix in this draft.

## 1. Tricolons + punchline
A list of exactly three things, then a short flat sentence landing the point. Very
recognizable AI cadence.

- Before: "The exchange is built, connected, and capable. It is simply not being used
  for most of the traffic that could benefit from it."
- After: "PKIX's own published figures show inter-ISP latency dropping from
  100--144 ms internationally to 1--31 ms through the exchange, yet across a week of
  hop-level measurement... not one of 222,944 traceroutes crosses either of its
  peering fabrics. The exchange is there and working; almost none of the traffic
  that would benefit from it is actually routed through it."
- Fix: fold the list into a normal sentence with real subordination (commas, "yet",
  "which"), don't let three parallel adjectives stand alone as their own sentence.

## 2. Choppy short-sentence stacking
Several short declarative sentences in a row, each doing one small job, reads as
generated rather than written. Vary sentence length and combine related clauses.

## 3. Dashes
Avoid em dashes for parenthetical asides in prose you're writing. (Also: single `~`
in LaTeX renders as literal strikethrough in some chat viewers when pasted here,
so wrap LaTeX snippets in a code block if sharing over chat.)

## 4. Vague forward/backward references
- Don't open a paragraph with "this problem" / "this idea" / "as shown above" unless
  the immediately preceding text actually sets it up. If something else (a figure, a
  caption, an aside) sits between the setup and the reference, either move the
  reference next to its setup or name the thing explicitly instead of using a pronoun.
- Don't point forward to a result (e.g. "as RQ3 shows") unless the paper actually
  proves that specific claim there. Check before citing your own later section.

## 5. Overclaiming from a single data point
Don't generalize a mechanism ("these operators don't peer with each other") from one
example or one paper's phrasing. State only what's actually been measured, and if you
found it in exactly one place, describe that one measurement rather than a general law.

## 6. Acronym/terminology precision
Expand acronyms correctly and use them consistently with the source's own definition
(e.g. LDI = "Long Distance and International", not "long distance interconnect";
don't reuse a term for a narrower concept than the regulator/source actually means).

## 7. Citation hygiene
- Cite the document you actually pulled the claim/figure from, not a same-author
  document about something else (check title/date, not just "PACRA" as a brand).
  If the report itself credits other sources, it's fine to name them in the caption
  text, but you still cite the report you read.
- If you redraw someone else's chart rather than reproducing the image, say so
  ("Recreated from X data, recoloured by...") rather than presenting it as a plain
  copy.

## 8. LaTeX mechanics worth a pass
- `\,` (thin space) needs to sit with no space on either side: `46\,ms`, not
  `46 \, ms`.
- Bare `~` is a non-breaking space, not a visible tilde/approx symbol. Use `$\sim$`
  for an actual "≈"-looking mark.
- A stray `~` between every word in a list ties them into one unbreakable chunk and
  can cause an Overfull \hbox (text spilling past the column margin). Only use `~`
  where you specifically need to prevent a bad break (e.g. before `\cite`, between a
  number and its unit).
- Check for accidental hard line breaks left over from copy-pasting mid-sentence.

## 9. Numbers/facts drift
Whenever a count (site count, probe count, operator count) appears more than once in
the draft, grep for it — these tend to get updated in one place and left stale in
another (contributions bullet said 100 sites/15 probes when the methodology section
said 98 sites/14 probes).
