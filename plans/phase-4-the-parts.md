# Sub-plan — Phase 4, The parts

## Goal

Move the five part bodies out of `App.jsx` into dedicated components under
`frontend/src/components/parts/`. Each component renders one pipeline stage, its
loading state, its empty state and its failure state, in the ruled document style
of `docs/mockups/d-record-plate.html`.

## Files to create

- `frontend/src/components/parts/PartSpectrum.jsx`
- `frontend/src/components/parts/PartBasis.jsx`
- `frontend/src/components/parts/PartAuthority.jsx`
- `frontend/src/components/parts/PartAction.jsx`
- `frontend/src/components/parts/PartInput.jsx`
- `frontend/src/lib/spectrum.js` — the tier table and `deriveCategory`

## Files to change

- `frontend/src/App.jsx` — replace the five inline `<section className="part">`
  blocks with the new components. Keep the `id` on each section for the rail
  anchors. Keep the `ErrorBlock` helper only if a part still needs it; otherwise
  delete it.

## Files NOT to change in this phase

- `frontend/src/AbercrombieSpectrum.jsx` — Phase 7 deletes it. This phase only
  stops `App.jsx` from importing it.
- `frontend/src/components/AttributionChart.jsx`, `components/llm/LLMAnalysis.jsx`
  — Phase 7 deletes them. This phase stops `App.jsx` from importing them.
- `frontend/src/lib/parseLegalAnalysis.js` — Phase 7 trims it. This phase keeps
  `parseSections` and adds no new export.
- `frontend/src/hooks/useTrademarkPipeline.js` — no change.

## Data shapes (confirmed from the backend)

- `/ml-predict` result: `{ label, prob_distinctive, prob_not_distinctive,
  attributions, formatted_input }` plus `mark`, `nice_class`, `description` added
  by the hook. `label` is `"distinctive"` or `"not_distinctive"`.
- `explainData`: `{ formatted_input, attributions }`.
  `attributions[i] = { field, value, attribution }`. `attribution` is a signed
  number, already sorted by absolute value, descending.
- `llmData`: `{ analysis: string, sources: { tmep, ttab } | null }`.
  - `tmep[i] = { id, text, metadata: { section_number, section_title, ... } }`
  - `ttab[i] = { id, text, metadata: { mark, nice_class, outcome, ... } }`

## Ordered steps

### Step 1 — Create `frontend/src/lib/spectrum.js`

1. Export `SPECTRUM_TIERS`, an ordered array from generic to fanciful. Each item:
   `{ id, label, range: [lo, hi], note }`. Take the `note` text and the ranges
   from the mockup Part 01 table:
   - generic — `[0.00, 0.28]` — "Never registrable"
   - descriptive — `[0.28, 0.50]` — "Needs acquired meaning"
   - suggestive — `[0.50, 0.70]` — "Inherently distinctive"
   - arbitrary — `[0.70, 0.88]` — "Inherently distinctive"
   - fanciful — `[0.88, 1.00]` — "Strongest protection"
2. Export `deriveCategory(probDistinctive)`. Per plan 2.2: return `null` when the
   input is not a finite number (`Number.isFinite` is false). Otherwise return
   the `id` of the matching tier, using the same thresholds as the current
   `AbercrombieSpectrum.jsx`:
   `>= 0.88` fanciful, `>= 0.70` arbitrary, `>= 0.50` suggestive,
   `>= 0.28` descriptive, else generic.
3. Add a one-line file comment: the tier table is the single source for Part 01
   and the plate's score row.

### Step 2 — Create `PartSpectrum.jsx`

Props: `{ score }` — pass `result.prob_distinctive`.

1. `const activeId = deriveCategory(score)`.
2. Render the `part-head`: `Part 01` / `Position on the spectrum`.
3. Render `<div className="index">` with one `<div className="tier">` per tier,
   in table order. Each row carries, in the mockup's column order:
   `tier-glyph` (span, `aria-hidden`), the label at `t-h3`, the `tier-note`, and
   the `tier-range` printed as `lo.toFixed(2)`–`hi.toFixed(2)`.
4. On the row whose `id === activeId`: add the `tier--here` class, set
   `aria-current="true"`, and append ` — this mark` to the label, exactly as the
   mockup does.
5. Failure mode — `score` missing or not finite: `activeId` is `null`, so no row
   gets `tier--here`. Below the table, replace the mockup's explanatory line with
   `The classifier did not return a score, so no tier is marked.` in
   `t-small dim`. When `activeId` is set, print the mockup's line instead:
   `The filled square marks the tier. The score on the plate above falls inside
   the range printed on that row.`
6. The row text names the tier and the range as words, so the row reads without
   color and without the square (plan 4.1).

### Step 3 — Create `PartBasis.jsx`

This replaces `AttributionChart` and the inline Part 02. Props:
`{ loading, data, error }` — pass `explainLoading`, `explainData`,
`explainError`.

1. Render the `part-head`: `Part 02` / `Basis for the finding`.
2. Failure mode — `error` is truthy: render a `t-body` line stating the failure
   (`error` holds the message), then a `t-small dim` line:
   `Parts 03 and 04 depend on this step, so they are unavailable too.` Return.
   Match the plan 2.1 requirement that Part 02 is an explicit failed part.
3. Loading mode — `loading` and no `data`: render the mockup's loading rows —
   `<div className="index">` with two `row row--tall` entries:
   `Measuring each field in turn…` / `Running`, then
   `Retrieving TMEP and TTAB doctrine` / `Queued`. Return.
4. Empty mode — no `data`, not loading, no error: render a `t-body dim` line
   `The basis step has not run yet.` Return. (App only mounts the part once
   `result` exists, so this is a guard, not a common path.)
5. Ready mode — `data` present:
   1. Keep `HIDDEN_FIELDS = new Set(['Mark Length', 'NICE Category',
      'Translation'])`. Filter `data.attributions` by it.
   2. Empty-after-filter guard: if nothing remains, render a `t-small dim` line
      `No field contributions to show.` and return.
   3. `maxAbs = Math.max(...visible.map(a => Math.abs(a.attribution)), 0.001)`.
   4. Intro `t-body`: the mockup's sentence about blanking each field in turn.
   5. `<div className="index">` with one `<div className="attr">` per field, in
      the order `data.attributions` already carries (sorted by the backend):
      - `attr-head`: left span holds the field name at `t-h3` and the value at
        `t-small dim mono` (truncate the value to 38 chars with an ellipsis,
        exactly as `AttributionChart` did); right span holds the mono figure
        `${sign}${abs.toFixed(2)} ${word}` where `word` is `toward` for a
        positive attribution, `against` for a negative one, `neutral` for `0`.
        Use a real minus sign `−` for the negative sign, matching the mockup.
      - `attr-track`: a two-cell grid. For a negative attribution, put
        `<i className="attr-outline" style={{ width: pct }}/>` in `attr-neg`. For
        a positive one, put `<i className="attr-fill" style={{ width: pct }}/>`
        in `attr-pos`. `pct = (Math.abs(attribution) / maxAbs) * 100 + '%'`. For
        exactly `0`, leave both cells empty.
   6. Legend line: port the mockup's `t-small dim` legend that explains fill and
      side carry the sign.
6. Do not use `ProgressBar` here. The mockup's track is a static ruled bar, not
   a `role="progressbar"`. `ProgressBar` stays reserved for the 2px loading rule
   (plan Phase 7).

### Step 4 — Create `PartAuthority.jsx`

Replaces `LegalSources` and the inline Part 03. Props:
`{ loading, data, error, explainError }` — pass `llmLoading`, `llmData`,
`llmError`, `explainError`.

1. Render the `part-head`: `Part 03` / `Authority relied on`.
2. Failure mode — `explainError`: render a `t-body` line
   `The basis step did not complete, so no authority was retrieved.` Return.
3. Failure mode — `error` (the 429 or a failed assess): render a `t-body` line
   with `error` (the hook's wait-time message). Add a `t-small dim` line
   `The analysis names its authority; without it, this part stays empty.`
   Return. This satisfies plan 2.6 — the wait states in place.
4. Loading mode — `loading` and no `data`: `t-body dim` line
   `The retrieval agent is still pulling passages.` Return.
5. Empty mode — no `data`: `t-body dim` line `Queued.` Return.
6. Ready mode — `data` present:
   1. `const tmep = data.sources?.tmep ?? []`,
      `const ttab = data.sources?.ttab ?? []`.
   2. If both are empty: `t-body dim` line
      `The analysis cited no external authority.` Return.
   3. Intro `t-body`: the mockup's sentence about the retrieval agent.
   4. First TMEP chunk (`tmep[0]`), when present: render the ink
      `<blockquote className="quote">` with the chunk text and a
      `<cite className="t-label dim-on-ink">` reading
      `TMEP § {section_number} — {section_title}`.
   5. `Also retrieved, not cited` label at `t-label`, then a
      `<div className="index">`:
      - `tmep.slice(1)` rows: left span holds `§ {section_number}` at
        `mono t-small` and `{section_title}` at `t-h3`; right span `TMEP` at
        `row-val t-small dim`.
      - `ttab` rows: left span holds `{mark}` at `t-h3` and `NC {nice_class}` at
        `mono t-small dim`; right span `TTAB — {outcome}` at `row-val t-small`.
        TTAB rows print the mark, the class and the outcome as words (plan 4.3).
      - Guard each `metadata` read with `?.` and fall back to `—`.
   6. If `tmep.length <= 1` and `ttab.length === 0`, skip the
      `Also retrieved` block entirely (the quote already carried the only
      source).

### Step 5 — Create `PartAction.jsx`

Replaces the four `llm-card` components and the inline Part 04. Props:
`{ loading, data, error, explainError }`.

1. Render the `part-head`: `Part 04` / `Recommended action`.
2. Failure and loading modes: mirror `PartAuthority` steps 2–5 with Part 04
   wording:
   - `explainError`: `The basis step did not complete, so no action was
     written.`
   - `error`: print `error`, then `t-small dim`
     `The recommended action is part of the analysis, which did not arrive.`
   - `loading`: `The analysis is still being written.`
   - no `data`: `Queued. This part fills after the analysis lands.`
3. Ready mode — `data` present:
   1. `const sections = parseSections(data.analysis)` from
      `lib/parseLegalAnalysis.js`.
   2. Add a local `renderInline(text)` helper — copy it verbatim from
      `LLMAnalysis.jsx` (splits on `**bold**`). Do not import it; `LLMAnalysis`
      is deleted in Phase 7.
   3. If `sections` is `null`: render `data.analysis` as a single
      `<p className="t-body">` (no markdown structure to parse).
   4. If `sections` is an array: render each as a titled block under the one
      Part 04 heading, not as a card:
      `<div className="stack">` wrapping, per section,
      `<h3 className="t-h3">{title}</h3>` then
      `<p className="t-body">{renderInline(content)}</p>`. Split `content` on
      blank lines into paragraphs so multi-paragraph sections keep their breaks.
   5. Drop `TIER_COLORS`, the mini spectrum bar and the verdict chip. Part 01
      and the plate already state the tier and the verdict (plan 4.4).
4. Do not render the reset button here. `App.jsx` keeps the reset button below
   the parts.

### Step 6 — Create `PartInput.jsx`

Props: `{ formattedInput }` — pass `result.formatted_input`.

1. Render the `part-head`: `Part 05` / `Classifier input`.
2. Intro `t-body`: a sentence that the string below is the exact text the model
   read. Do not claim "eight fields"; the API returns one string (plan 2.5).
3. `const lines = (formattedInput || '').split('. ').filter(Boolean)`.
4. Empty guard: if `lines` is empty, render a `t-small dim` line
   `The classifier input was not returned.` Return.
5. Render `<div className="index">` with one `<div className="row">` per
   fragment. Each row holds a single `<span className="mono t-small">{line}</span>`.
   One ruled line per fragment, matching the current debug-panel split
   (plan 2.5).

### Step 7 — Rewrite the part section of `App.jsx`

1. Add imports for the five new components.
2. Remove the imports of `AbercrombieSpectrum`, `AttributionChart` and
   `LLMAnalysis`. Do not delete those files.
3. Replace the five inline `<section className="part" id="pN">` blocks with:
   ```jsx
   <section className="part" id="p1">
     <PartSpectrum score={result.prob_distinctive} />
   </section>
   <section className="part" id="p2">
     <PartBasis loading={state.explainLoading} data={state.explainData} error={state.explainError} />
   </section>
   <section className="part" id="p3">
     <PartAuthority loading={state.llmLoading} data={state.llmData} error={state.llmError} explainError={state.explainError} />
   </section>
   <section className="part" id="p4">
     <PartAction loading={state.llmLoading} data={state.llmData} error={state.llmError} explainError={state.explainError} />
   </section>
   <section className="part" id="p5">
     <PartInput formattedInput={result.formatted_input} />
   </section>
   ```
   Keep the outer `id` on the section so the rail anchors and the Phase 6
   scroll-spy still target it. Each component renders its own `part-head`, so the
   section wrapper carries no head.
4. Delete the now-unused `ErrorBlock` helper if no other code in `App.jsx` uses
   it. Grep first.
5. Leave `buildParts`, the rail, the plate and the form untouched.

## Failure modes and fallbacks (summary)

| Condition | Part | Fallback |
|---|---|---|
| `prob_distinctive` missing | 01 | No `tier--here` row; line says no tier is marked |
| `/llm-explain` failed | 02 | Explicit failed part; names Parts 03–04 as blocked |
| attributions all hidden | 02 | "No field contributions to show." |
| `/llm-explain` failed | 03, 04 | "The basis step did not complete…" |
| `/llm-assess` 429 or failed | 03, 04 | Prints the wait-time message in place |
| `sources` null or empty | 03 | "The analysis cited no external authority." |
| `analysis` has no `**headings**` | 04 | Render the raw string as one paragraph |
| `formatted_input` empty | 05 | "The classifier input was not returned." |

## Commands that prove the phase works

1. `cd frontend && npm run build` — succeeds, no unresolved import, no reference
   to a deleted export.
2. `cd frontend && npx eslint src` if eslint resolves; otherwise skip (plan
   notes no linter is configured).
3. `node ~/.claude/skills/impeccable/scripts/detect.mjs frontend/src` — no new
   findings in the five new files.
4. Manual: run the app, submit a mark, watch the plate land, then Part 01 and 05,
   then Part 02, then Parts 03 and 04. Confirm the rail status words match the
   part bodies.
5. Manual failure pass: force a `/llm-explain` 500 and confirm Part 02 states the
   failure and Parts 03–04 read "The basis step did not complete".
