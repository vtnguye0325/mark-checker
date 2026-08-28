# Implementation plan — Mockup D, The Record Plate

This plan rebuilds the Mark Checker interface as the mockup in
`docs/mockups/d-record-plate.html`. The design language is
`docs/DESIGN_PRINCIPLES.md`. The product truth is `PRODUCT.md`.

Scope: the `frontend/` React app only. The plan changes no backend code and no
endpoint contract.

---

## 1. What the mockup asks the app to become

The current app is a form above a stack of cards. The mockup is one record:

| Region | Source of the data | Pipeline stage |
|---|---|---|
| Record bar | client | none |
| Plate — verdict, mark, class, score | `/ml-predict` | 1 |
| Rail — metadata and part index | client + all stages | all |
| Part 01 Spectrum | `prob_distinctive` | 1 |
| Part 02 Basis | `/llm-explain` | 2 |
| Part 03 Authority | `/llm-assess` `sources` | 3 |
| Part 04 Action | `/llm-assess` `analysis` | 3 |
| Part 05 Input | `/ml-predict` `formatted_input` | 1 |

The plate and Parts 01 and 05 land together. Part 02 lands second. Parts 03 and
04 land last.

---

## 2. Defects and mismatches found in the current code

Fix these as part of the work. Each one is a real behavior, not a style problem.

### 2.1 A failed `/llm-explain` silently kills Parts 03 and 04

`useTrademarkPipeline.js` catches the `/llm-explain` failure, logs it to the
console, and leaves `explainResult` as `null`. The `if (explainResult)` guard on
line 68 then skips `/llm-assess` completely. No state records this.

Today the user sees cards that never appear. In the mockup the rail prints a
status for every part, so the rail would print `Queued` forever.

**Fix:** add `explainError` to the hook state. Set it in the catch block. Render
Part 02 as an explicit failed part, and print `Unavailable` in the rail for
Parts 02, 03 and 04.

### 2.2 `deriveCategory` reports "generic" for missing data

`deriveCategory(undefined)` fails every threshold test and returns `'generic'`,
the worst tier on the spectrum. If `/ml-predict` ever omits `prob_distinctive`,
Part 01 marks the mark as generic with full confidence.

**Fix:** return `null` from `deriveCategory` when the input is not a finite
number. Part 01 then marks no tier and prints that the score is unavailable.

### 2.3 `AbercrombieSpectrum` never receives the score

The component takes no props. It renders five identical segments and marks
nothing. `deriveCategory` is exported but no file calls it.

**Fix:** Part 01 calls `deriveCategory(result.prob_distinctive)` and fills the
square on the matching row.

### 2.4 The confidence on the plate comes from stage 3, not stage 1

The mockup prints `Confidence: High` on the plate beside the score. That value
does not exist in `/ml-predict`. `extractVerdict()` scrapes the words "high",
"moderate" or "low" out of the LLM prose, which arrives in stage 3 and may never
arrive at all.

**Decided: late fill.** The plate prints `Pending` in the confidence row until
stage 3 lands, then replaces it with the scraped word. The row reads
`Unavailable` if stage 3 fails or returns 429.

Three consequences follow from this choice:

1. `RecordPlate` takes stage 3 data, not stage 1 data alone. Pass `llmData`,
   `llmLoading` and `llmError` into it.
2. `extractVerdict()` in `lib/parseLegalAnalysis.js` must survive. Phase 7 keeps
   it and deletes only the four other helpers.
3. The confidence row changes after the reader has already read the plate. Print
   the word `Pending` and not an empty cell or a placeholder dash, so the change
   reads as an arrival and not as a correction. Do not animate the swap.

`extractVerdict()` returns `confidence: null` when the prose carries no
confidence word. Treat that as `Unavailable`, the same as a failed stage.

### 2.5 Part 05 shows eight named fields; the API returns one string

`/ml-predict` returns `formatted_input` as a single sentence-joined string. The
mockup draws an eight-row table of named fields. Splitting that string into
named fields is guesswork that breaks when the backend changes its format.

**Fix:** Part 05 splits on `. ` exactly as the current debug panel does, and
prints one ruled line per fragment. The table keeps the mockup's rhythm without
inventing a field structure the API does not promise.

### 2.6 A 429 from `/llm-assess` must stay visible

The hook already sets `llmError` with the wait time. The current UI prints it as
a red banner above the analysis. In the mockup, Parts 03 and 04 must state the
wait in place, so the reader learns which part is missing and why.

---

## 3. Phases

### Phase 1 — Foundation

1. **`frontend/index.html`**
   - Replace the font link. Load `Archivo` (`wdth,wght@75..125,400..700`) and
     `JetBrains Mono` (`wght@400;500`). Drop Cormorant Garamond and Space
     Grotesk. The principles ban a serif family and a second sans family.
   - Set `theme-color` to `#000000`.
2. **`frontend/src/App.css`** — replace the file. Write the token block, the
   type scale, the browser surfaces, the plate, the rail, the parts, the index
   rows, the attribution track, the quote panel, the form and the states,
   ported from `docs/mockups/d-record-plate.html`.

Verify: the app builds and renders unstyled-but-correct content.

### Phase 2 — The pipeline hook

**`frontend/src/hooks/useTrademarkPipeline.js`**

- Add `explainError` state. Set it in the `/llm-explain` catch block. Clear it in
  `submit` and in `reset`.
- Return it from `state`.
- Leave the endpoints, the payloads and the abort logic unchanged.

### Phase 3 — Structure

1. **`frontend/src/components/RecordBar.jsx`** (new) — replaces `AppHeader`.
   Prints the product name, `Distinctiveness record` and `Not legal advice`.
   **No record reference.** Nothing in the app generates one, and a string that
   looks like a filing number is a claim this product cannot make. The bar
   therefore carries two items, not three. Space them apart, so the dropped
   third item does not leave the bar looking unfinished.
2. **`frontend/src/components/RecordPlate.jsx`** (new) — the ink plate. Takes
   `result`, `liveMark`, `llmData`, `llmLoading` and `llmError`. Prints the
   verdict at display scale, the mark, the goods, the class, the score and the
   confidence row described in 2.4.
3. **`frontend/src/components/RecordRail.jsx`** (new) — the metadata rows and
   the part index. Takes a `parts` array of `{ id, name, no, status }`. Renders
   a link when the part is on the page and a plain row when it is not.
   **Drop the `Ref` row** with the reference. The metadata group then holds
   `Filed`, `Class`, `Score`, `Model` and `Sources`. Five rows still fill the
   rail, and they pair evenly in the two-column mobile strip.
4. **`frontend/src/App.jsx`** — compose `RecordBar`, `RecordPlate`, the rail and
   the parts. Set the accent on a wrapper class from `result.label`:
   `record--distinctive` sets blue, `record--not` sets red. Build the `parts`
   array from the four loading and error flags in one place, so the rail and the
   body never disagree.

### Phase 4 — The parts

Create `frontend/src/components/parts/`:

1. **`PartSpectrum.jsx`** — the five ruled tier rows. Calls `deriveCategory`.
   Fills the square on the matching row and sets `aria-current`. Prints the tier
   name and range as words, so the row reads without color and without the
   square.
2. **`PartBasis.jsx`** — replaces `AttributionChart`. Draws the signed track:
   a center axis, a filled bar to the right for a positive attribution and an
   outlined bar to the left for a negative one. Keeps `HIDDEN_FIELDS`. Keeps the
   `maxAbs` scaling. Adds the failed and the empty state.
3. **`PartAuthority.jsx`** — replaces `LegalSources`. The first TMEP chunk sits
   in the ink quote panel. The rest list as index rows. TTAB rows print the
   mark, the class and the outcome as words.
4. **`PartAction.jsx`** — replaces the four `llm-card` components. Renders the
   parsed sections as prose under one heading, not as cards. Keeps
   `parseSections` and `renderInline`. Drops `TIER_COLORS`, the mini spectrum
   bar and the verdict chip, because Part 01 and the plate already state both.
5. **`PartInput.jsx`** — the ruled lines from `formatted_input`, per 2.5.

### Phase 5 — The form

**`frontend/src/components/MarkForm.jsx`** — restyle to the mockup's empty
state.

- The mark field is the large bottom-rule input.
- **Confirmed:** the four remaining fields sit on the form with no disclosure.
  Delete `showAdvanced` and `onToggleAdvanced` from `MarkForm`, and delete the
  `showAdvanced` state from `App.jsx`. The office asks for those fields too, so
  the form states them. Mark `Translation` and `Pseudo mark` as optional in the
  label, because the payload builder in `App.jsx` already omits an empty one.
- Keep the NICE select and `NICE_CLASSES`.
- Label the submit button `Open record`.
- Print the error as a ruled block, not a banner.
- Leave `TurnstileWidget` as is. It is a third-party iframe and it cannot take
  this design language. Give it its own bordered block.

### Phase 6 — Behavior the mockup implies but does not carry

1. **Scroll spy.** An `IntersectionObserver` sets the current part in the rail.
   Observe each rendered part. Use a `rootMargin` that accounts for the sticky
   mobile nav.
2. **`scroll-margin-top`** on every part, so an anchor jump does not put the
   heading under the sticky nav.
3. **`prefers-reduced-motion`** removes the progress rule animation and every
   transition.
4. **Focus rings** on the rail links, the chips, the inputs and the buttons.

### Phase 7 — Removal

Delete after nothing imports them:

- `components/AppHeader.jsx`
- `components/ProbBar.jsx`
- `components/AttributionChart.jsx`
- `components/llm/LLMAnalysis.jsx`
- `components/ResultPanel.jsx`
- `AbercrombieSpectrum.jsx` — move `deriveCategory` to
  `lib/spectrum.js` with the tier table first.

Trim `lib/parseLegalAnalysis.js` to `parseSections` and `extractVerdict`. Delete
`TIER_COLORS`, `TIER_ORDER`, `parseSpectrumTiers` and `splitSignals` once Phase 4
lands, because the color-coded tiers and the verdict chip are gone.

`extractVerdict` stays, per 2.4: the plate's confidence row is its only caller.
Take `confidence` from it and ignore its `isDistinctive` and `verdict` fields.
`result.label` from stage 1 owns the verdict word, and a scraped second opinion
must never contradict it on the same plate.

Keep `components/ui/ProgressBar.jsx` and the `@radix-ui/react-progress`
dependency. Reuse it for the 2px loading rule, so the rule keeps its
`role="progressbar"` semantics.

---

## 4. Verification

There is no test runner and no linter in `frontend/package.json`, so the checks
are a build and a manual pass.

1. `npm run build` succeeds with no unresolved import.
2. Walk the three states in the browser: empty, loading, result.
3. Force each failure path and confirm the page states it:
   - `/ml-predict` fails → the form prints the error, no plate appears.
   - `/llm-explain` fails → Part 02 states the failure, and the rail prints
     `Unavailable` for Parts 02, 03 and 04.
   - `/llm-assess` returns 429 → Parts 03 and 04 print the wait, and the
     plate's confidence row turns from `Pending` to `Unavailable`.
   - `prob_distinctive` missing → Part 01 marks no tier.
   - The analysis prose carries no confidence word → `extractVerdict` returns
     `confidence: null` and the plate reads `Unavailable`, never `Pending`
     forever.
   - The reader stays on the plate while stage 3 lands → the confidence row
     swaps from `Pending` with no layout shift and no animation.
4. Check 320px, 768px and 1440px. Confirm no horizontal scroll.
5. Check the merge list in `DESIGN_PRINCIPLES.md` §10.
6. Run `node ~/.claude/skills/impeccable/scripts/detect.mjs frontend/src`.

---

## 5. Decisions on record

Decided 28 Aug 2026. These are settled. Do not reopen them during the build.

| # | Question | Decision | Lands in |
|---|---|---|---|
| 1 | Confidence on the plate | Print `Pending`, then fill from stage 3 | 2.4, Phase 3.2 |
| 2 | Advanced-field disclosure | Delete it; all five fields on the form | Phase 5 |
| 3 | Record reference | Drop it, for now | Phase 3.1, Phase 3.3 |

Decision 3 is marked "for now". If a reference is wanted later, it must be
generated by the backend and stored with the record. A client-side string that
survives one page load is not a reference to anything.

Decision 1 is the one to watch in the finish review. It is the only place where
the plate changes after the reader has read it.
