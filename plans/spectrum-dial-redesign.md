# Spectrum dial redesign plan

## Decision and scope

The user selected the Spectrum dial direction from the bleibtgleich’26 study.
This plan covers the landing page, form, result, history, method page, account controls, and shared states.
The plan changes the frontend visual system and the content hierarchy.
It does not change the model, API contracts, database schema, or legal meaning of a score.

Use these artifacts as the visual starting point:

- [Design study](../docs/BLEIBTGLEICH26_DESIGN_STUDY.md).
- [Spectrum dial start mockup](../docs/mockups/bleibtgleich26/b-spectrum-dial.html).
- [Spectrum dial result mockup](../docs/mockups/bleibtgleich26/b-spectrum-dial-result.html).
- [Saved result images](../docs/assets/02-the-verdict.jpg) and [score breakdown image](../docs/assets/03-basis-for-the-finding.jpg).

The mockups show composition and tone. They do not define legal claims, API data, or complete error behavior.
The result mockup uses illustrative ZEPHYRLINE data. The production page must use response data.

## Product goal

Help a founder understand one model finding and the evidence behind it.
Keep the first read clear when later requests load or fail.
Let a legal reader inspect the source details without blocking the founder.

The visitor completes this path:

1. Learn what the five categories mean.
2. Enter a mark, goods or services, and a NICE class.
3. Read the model finding and score.
4. See the mark on the five-part spectrum.
5. Read the score breakdown, written analysis, and retrieved sources as they arrive.
6. Check another mark or open a saved record.

## Design direction

The dial is an instrument for reading the spectrum. It is the main visual object.
Large sans-serif type, asymmetric columns, thin rules, and open space come from the design study.
The olive scene gives the spectrum a distinct place. White and near-black carry long reading.
The result uses the same dial, but the model score controls its marker.
The landing dial teaches categories. It never predicts a mark before submission.

Use [the design principles](../docs/DESIGN_PRINCIPLES.md) for tokens and behavior.
Use [the vibe brief](../docs/VIBE.md) for tone and visual judgment.

### Visual hierarchy

| Surface | First focal point | Second focal point | Supporting content |
|---|---|---|---|
| Landing | Spectrum dial | Question and form action | Short product explanation |
| Form | Mark field | Goods and NICE class | Optional fields and notice |
| Result | Mark and finding | Actual dial marker and score | Context and stage status |
| Detail | Spectrum position | Written reading | Sources and score breakdown |
| History | Mark and finding | Date and score | Open-record action |
| Method | Three-stage explanation | Source definitions | Limits and return action |

### Source of truth

- Read the five category names and score ranges from `frontend/src/lib/spectrum.js`.
- Read the mark, goods, and NICE class from the submitted form values.
- Read the label, score, and formatted model input from the prediction response.
- Read score contributions from the explanation response.
- Read the analysis and retrieved sources from the assessment response.
- Keep the sample data only in the standalone mockups.

## Current implementation map

| Area | Current file | Planned work |
|---|---|---|
| Page flow | `frontend/src/App.jsx` | Keep the existing views and three-stage flow. Replace their visual composition. |
| Shared CSS | `frontend/src/App.css` | Replace brutalist tokens and broad selectors with the dial system. |
| Form | `frontend/src/components/MarkForm.jsx` | Recompose fields without changing the payload. |
| Landing band | `frontend/src/components/Marquee.jsx` | Replace the marquee with an educational dial. |
| Result hero | `frontend/src/components/RecordPlate.jsx` | Place the finding, mark, context, and score around the dial. |
| Result scale | `frontend/src/components/RecordScale.jsx` | Replace the frozen band with a measured dial marker. |
| Record index | `frontend/src/components/RecordRail.jsx` | Keep status navigation, but reduce its visual weight. |
| Spectrum detail | `frontend/src/components/parts/PartSpectrum.jsx` | Keep all five categories and the actual category label. |
| Score breakdown | `frontend/src/components/parts/PartBasis.jsx` | Keep signed values and explain bar direction. |
| Written reading | `frontend/src/components/parts/PartAction.jsx` | Keep parsed analysis and its error state. |
| Sources | `frontend/src/components/parts/PartAuthority.jsx` | Keep TMEP and TTAB metadata and empty states. |
| Submitted input | `frontend/src/components/parts/PartInput.jsx` | Keep the exact model input available below the main answer. |
| Progress states | `frontend/src/components/parts/PartPending.jsx`, `PartError.jsx` | Give each request a clear state and next action. |
| Other views | `HistoryPanel.jsx`, `MethodPage.jsx`, `SignInModal.jsx` | Apply the same type, color, rules, and control styles. |
| Data flow | `frontend/src/hooks/useTrademarkPipeline.js` | Preserve request order and abort behavior. Improve exposed retry actions if needed. |
| Spectrum logic | `frontend/src/lib/spectrum.js` | Keep one category mapping for the dial and details. |

## Work sequence

### Phase 0: Record the baseline

1. Save the current landing and result views at 390px, 768px, and 1440px.
2. Record the current form, history, method, sign-in, loading, and error states.
3. Record which result sections arrive after each API response.
4. Mark existing user edits before changing any frontend file.
5. Keep the saved result images as content evidence, not as a pixel target.

Exit when each existing view and request state has a named replacement.

### Phase 1: Build the shared visual system

1. Add paper, olive, ink, line, muted text, and error tokens to the frontend styles.
2. Define the display, heading, body, label, and number type levels.
3. Define the page gutters, section space, rules, focus ring, and button styles.
4. Define reusable layout classes for open columns and ruled rows.
5. Remove old brutalist rules after each owner component uses the new system.
6. Keep readable text when a font fails to load.

Exit when the landing, result, history, and method views share the same tokens.

### Phase 2: Build one reusable spectrum dial

1. Create a `SpectrumDial` component near the other frontend components.
2. Pass an explicit `mode` value: `explore` or `result`.
3. Read category names and score bounds from `SPECTRUM_TIERS`.
4. In explore mode, let each button show one definition and example.
5. In result mode, derive the actual category from the numeric model score.
6. Keep the actual marker fixed when the visitor explores another definition.
7. Give each dial button an accessible name and a visible focus state.
8. Add a text list for narrow screens and for readers who cannot use the radial layout.
9. Keep the category and score readable if CSS motion or JavaScript fails.
10. Use one deliberate transition for the marker. Obey reduced motion.

The dial must not turn a probability into a registration promise.
The dial must not show a category when the response has no finite score.

Exit when the dial works with mouse, keyboard, touch, and reduced motion.

### Phase 3: Redesign the landing and form

1. Give the olive dial scene the first viewport.
2. Put the main question beside the dial with short, plain copy.
3. Keep the Mark Checker name and one clear action.
4. Move the form directly below the scene.
5. Keep the required mark, goods or services, and NICE class fields.
6. Keep translation and pseudo mark available with clear optional labels.
7. Show the mark text in a large preview without implying a model result.
8. Preserve validation, Turnstile, auth, and the submitted payload.
9. Keep a clear notice that the result is a first read.
10. Give the disabled action a reason that the visitor can read.

Exit when a new visitor can identify the product, complete the form, and find the action.

### Phase 4: Redesign the first result

1. Show the mark, goods or services, NICE class, finding, and score at once.
2. Place the actual category on the dial with a word and a marker.
3. Show the probability as a model score, not as registration odds.
4. Place the first-read notice beside the finding.
5. Show the remaining request states below the finding.
6. Keep the first result visible while later requests run.
7. Keep the score range list below the dial for precise reading.

Use the saved result images to check content coverage.
The images show a high score and missing later analysis. The new design must support both facts.

Exit when the visitor can read the answer before the later requests complete.

### Phase 5: Redesign the result details

1. Show the five categories in a ruled list under the dial.
2. Show the actual category with a word, a marker, and its range.
3. Place the written reading before technical evidence in the reading order.
4. Keep TMEP excerpts, TTAB rows, source metadata, and empty source states.
5. Show signed score contributions with text and bar direction.
6. Keep the submitted model input in a disclosure near the end.
7. Keep the section index on desktop and a compact index on mobile.
8. Keep each section anchored and named for keyboard navigation.

Exit when the owner gets a plain answer and a legal reader can inspect the evidence.

### Phase 6: Redesign other views

1. Apply the shared system to history rows and record reopen actions.
2. Apply the system to the method page and its return action.
3. Apply the system to the sign-in modal without weakening focus management.
4. Keep the account controls clear at each viewport.
5. Preserve the app's current view changes and scroll reset behavior.

Exit when no main view retains the old brutalist visual language.

### Phase 7: Add state and failure behavior

Use this table to trace each failure from the request to the visible result.

| Condition | Current stage | Visible result | Caller and system effect |
|---|---|---|---|
| API, DNS, or database is unreachable | Prediction | Keep the form and entered values. Show a retry action. | No record opens. The visitor can retry or edit the form. |
| Prediction returns an invalid score | Prediction | Show the finding only when valid. Show no dial marker. | Later sections must not infer a category from invalid data. |
| Attribution request fails | Explanation | Keep the finding and spectrum. Mark the score breakdown unavailable. | The assessment does not start under the current pipeline. Mark its sections unavailable. |
| Assessment request fails | Assessment | Keep the finding and score breakdown. Mark reading and sources unavailable. | The visitor can still use the earlier result. |
| Assessment returns 429 with `Retry-After` | Assessment | Show the wait in words and offer retry after the wait. | Preserve the result and avoid a rapid request loop. |
| Assessment returns 429 without `Retry-After` | Assessment | Show the server's daily-limit message when present. | Preserve the result and stop pointless retries. |
| Auth expires | Any request | Open sign-in and keep the entered mark or visible record. | Resume only after a valid session returns. |
| Turnstile fails | Submission | Keep the form and show the verification problem. | No request starts until verification succeeds. |
| Sources are empty or null | Assessment | Say that the analysis cited no outside source. | Keep the written reading if it exists. |
| Browser reloads during a check | Any request | Restore only persisted history or form data that the app owns. | Do not present a partial result as complete. |
| Build runs without the API | Build | Render the app shell and landing page. | No build step calls the API or needs the database. |

Trace each catch return through its caller before merging the change.
Check the visible state after each failed request.

### Phase 8: Verify and finish

1. Inspect the landing and result at 320px, 390px, 768px, and 1440px.
2. Inspect the longest mark and goods text that the form accepts.
3. Inspect a score at every category boundary and a missing score.
4. Inspect loading, success, empty, 429, auth expiry, and network failure states.
5. Check keyboard order, focus, button names, and the text version of the dial.
6. Check body and placeholder contrast against WCAG AA.
7. Check reduced motion and the dial's touch behavior.
8. Confirm that the old marquee and duplicate category data are gone.
9. Confirm that no result claim exceeds the API response.
10. Update `DESIGN.md` and `.impeccable/design.json` from the finished build.

Stop when the complete flow matches the selected direction and preserves every API state.

## File ownership and change limits

The frontend work owns `frontend/src/App.jsx`, `App.css`, and the named components.
Keep the API endpoints and database schema outside this redesign.
Do not revert unrelated work in auth, backend, Docker, or start scripts.
The current worktree contains edits in those areas.

Use the standalone mockups as visual references.
Do not copy their fixed sample response into production code.

## Acceptance criteria

- The landing page presents the educational dial and a usable form.
- The result page uses the real score and one shared category mapping.
- The visitor can always distinguish an actual result from a category preview.
- The first result stays visible when the explanation or assessment fails.
- The reading, sources, score breakdown, and submitted input remain accessible.
- The history, method, and sign-in views share the new visual system.
- The layout fits 320px, 390px, 768px, and 1440px without page-wide overflow.
- Every control has a visible focus state and a usable touch target.
- Reduced motion preserves state changes without continuous movement.
- The product calls the result a first read and never promises registration.

## Open decisions for the build

Resolve these choices from the mockups and the working app before implementation:

1. Choose whether the result keeps a separate screen or remains in the current `check` view.
2. Choose whether the desktop section index stays sticky beside the result.
3. Choose whether the optional fields stay open or move into one disclosure.
4. Choose the exact licensed display font after checking its rendered form and load cost.

These choices do not block the plan. Keep the current behavior unless the new layout requires a change.
