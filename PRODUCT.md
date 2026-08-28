# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The primary user is a small business owner or founder who is naming a product and has no legal
training. They want a fast, plain-English read on whether the name can be registered, before they
pay a trademark attorney for an opinion.

A second audience is a trademark attorney or paralegal who runs a first-pass screen on a client
mark. The owner leads the design; the attorney's depth stays available but subordinate.

A third, non-operating audience reads the repository as a portfolio piece. This audience must not
change what the interface says, only how well it shows the pipeline it runs.

## Product Purpose

Mark Checker grades a proposed brand name on the Abercrombie spectrum, which runs from *generic*
(never protectable) through *descriptive* and *suggestive* to *arbitrary* and *fanciful*. The grade
decides whether the trademark office will register the name.

That grade is a judgment call that costs hundreds of dollars and takes days to get from a lawyer,
and two lawyers can disagree. The product gives an instant first read, so the applicant knows where
they stand before they pay for advice. Success is a user who understands the verdict, believes it,
and knows what to change about the name.

## Positioning

The verdict comes from a ModernBERT classifier fine-tuned on trademark records, not from a prompt to
a general LLM. The app then shows its work in two ways a prompt cannot: leave-one-out attribution
that measures how much each input field moved the score, and a retrieval agent that pulls the actual
TMEP sections and TTAB decisions the explanation is allowed to cite.

The product is an evidence document, not an oracle. A neighboring product that wraps a chat model
cannot truthfully claim either the measured attribution or the grounded citation.

## Operating Context

The user runs one check at a time, in a browser, at a desk, at the moment they are choosing a name.
The session is short and the result is read once, carefully, then acted on. The user may run several
candidate names in a row to compare them.

The vocabulary of the domain is fixed and legal: mark, goods and services, NICE class, distinctive,
descriptive, TMEP, TTAB, pseudo mark. The interface uses those words because the user will meet them
again on the trademark office's own forms.

## Capabilities and Constraints

Input:

- `mark` — the proposed trademark text (required).
- `description` — the goods or services the mark will be used for (required).
- `nice_class` — the international classification, chosen from a list (required).
- `translation` — the English meaning of a foreign-language mark (optional, currently behind a
  disclosure).
- `pseudo_mark` — the constituent words of a compound mark (optional, currently behind a disclosure).

The check runs as three chained requests, each slower than the last, and the interface fills in as
each returns:

1. `POST /ml-predict` — returns `label` (`distinctive` / `not_distinctive`), `prob_distinctive` (a
   float from 0 to 1), and `formatted_input`, the 8-field string the classifier actually read.
2. `POST /llm-explain` — returns `attributions`, one record per input field with the field name, its
   value, and a signed attribution that can push toward or against distinctiveness. Three fields
   (Mark Length, NICE Category, Translation) are currently hidden from the chart.
3. `POST /llm-assess` — returns `analysis`, a markdown document in four named sections, plus
   `sources` (retrieved `tmep` and `ttab` chunks with their metadata) and `prompt` (the exact system
   and user messages sent to the model).

The four analysis sections are, in order: what the model found (carries the verdict and a high /
moderate / low confidence), where this mark sits on the spectrum, what the model leaned on, and what
to do next.

Constraints:

- `/llm-assess` is rate limited and returns 429 with a `Retry-After` header. The interface must show
  the wait, not a generic failure.
- A Cloudflare Turnstile challenge gates submission when a site key is configured.
- The classifier returns a probability, never a certainty. The interface must not present the verdict
  as legal advice.
- The three stages resolve at different speeds, so partial results are the normal state, not an edge
  case.

Undecided: whether the interface keeps the current single page, the current disclosure for the
optional fields, or the model-input debug panel. The user has declared all of this open.

## Brand Commitments

The product name is **Mark Checker**.

The user has made `docs/DESIGN_PRINCIPLES.md` binding. It commits the interface to a Bauhaus and
Swiss typographic language: monochrome base with the three primaries as signal only, one grotesk
family, 0px corner radius, no shadows, an 8px spacing scale, asymmetric composition, and extreme
contrast of type scale. The document also fixes the accent meanings — red for conflict and high
risk, blue for link and primary action, yellow for caution and pending.

The document's own reference is the "Bauhaus Legacy" concept by Eugene Shuklin.

## Evidence on Hand

- A working three-stage pipeline with real endpoints, described above.
- Real domain content: the TMEP is a public manual with numbered sections, and TTAB decisions are
  public and carry a mark, a NICE class, and an outcome.
- The NICE classification is a real, fixed list of 45 classes (`frontend/src/constants/niceClasses.js`).
- No customers, no testimonials, no pricing, no benchmark numbers, and no accuracy figure have been
  established. Future work must not invent any of them.
- No screenshot assets exist yet; `docs/assets/result.png` is a TODO in the README.

## Product Principles

1. **The verdict is a first read, never advice.** State the confidence and the reasoning, and never
   let the interface imply a registration outcome is settled.
2. **Show the work.** The attribution and the retrieved doctrine are the product's claim to
   trustworthiness. They are not an appendix.
3. **Speak the office's vocabulary.** Use the legal terms the user will meet again on the real form,
   and define them in place rather than replacing them with friendly substitutes.
4. **Partial is normal.** The interface is designed around three results arriving at three different
   times, not around a single loaded state.
5. **The owner reads first, the attorney reads deeper.** Depth is available on the same page; it
   never blocks the plain answer.

## Accessibility & Inclusion

The binding design document requires WCAG AA contrast (4.5:1 body, 3:1 large text), a visible focus
ring on every interactive element, a layout that holds at 320px, 768px, and 1440px, obedience to
`prefers-reduced-motion`, and that every state carry a word and not only a color.
