# Spectrum dial design principles

This document defines the selected design direction for Mark Checker.
The user selected the Spectrum dial concept from the bleibtgleich’26 design study.
The [start mockup](mockups/bleibtgleich26/b-spectrum-dial.html) and [result mockup](mockups/bleibtgleich26/b-spectrum-dial-result.html) show its composition.
The [study](BLEIBTGLEICH26_DESIGN_STUDY.md) explains the reference evidence.

The mockups show fixed sample data. The production interface must use real API responses.
When a mockup conflicts with product truth, keep product truth and update the mockup.

## Core idea

Use a spectrum instrument to explain a model finding.
Give the visitor a clear answer, then show the reason and sources.
Keep the design calm enough for careful legal reading.

The dial has two roles:

- The landing dial teaches the five categories.
- The result dial marks the category that the model score selects.

Keep the result marker fixed when the visitor explores another category.
Do not show a result marker before the model returns a valid score.

## Visual character

Use large, tight sans-serif type, uneven columns, thin rules, and active empty space.
Use an olive scene for the instrument and light paper for long content.
Use near-black for strong type, the main action, and short contrast bands.
Repeat one small, round Mark Checker symbol across the app.

The interface must feel like a precise editorial instrument.
It must not resemble a legal form with decorative machinery attached.
It must not present the dial as a promise about registration.

## Color tokens

| Token | Value | Use |
|---|---|---|
| `--ink` | `#171815` | Main type, rules, active dial node, dark band |
| `--paper` | `#F5F5F1` | Long reading surfaces and inverted type |
| `--olive` | `#C5C9A9` | Landing scene, result instrument, selected row |
| `--olive-light` | `#E0E3CF` | Quiet instrument surfaces and inactive nodes |
| `--line` | `#8F9477` | Rules on olive |
| `--muted` | `#4B503E` | Secondary type on olive |
| `--error` | `#A13622` | Error text and focus ring when contrast permits |

Use the same token names across all main views.
Keep body text at 4.5:1 contrast or better.
Keep large text at 3:1 contrast or better.
Check placeholder text against its actual input surface.
Pair every state color with a word.

Do not use red as a generic accent.
Reserve red for failure, conflict, and focus.
Use olive for the selected spectrum place and for the instrument scene.

## Type

Use one expressive grotesk family for display type and a compatible sans family for body text.
Use a local or licensed font only after the build confirms its load cost and fallback.
Keep body text readable when a font does not load.

| Role | Desktop size | Mobile size | Rules |
|---|---|---|---|
| Display | 80px to 150px | 52px to 86px | Heavy sans, short lines, optical tracking |
| Section heading | 55px to 110px | 42px to 70px | Heavy sans, clear line breaks |
| Result mark | 38px to 90px | 38px to 56px | Heavy sans, wrap long marks |
| Body | 16px to 18px | 16px | Sentence case, 45 to 75 characters per line |
| Supporting text | 13px to 15px | 13px to 15px | Use for explanations and metadata |
| Functional label | At least 12px | At least 12px | Clear words, restrained tracking |
| Number | 13px to 94px | 13px to 58px | Tabular figures where values align |

Keep display tracking near `-0.04em`.
Do not crush letter shapes to fit a narrow column.
Use uppercase only for short labels.
Use roman sans type in the final page.
Do not use an italic serif headline in the final page.

## Grid and space

Use a page gutter of at least 16px on a narrow screen.
Use an open two-column composition for the desktop landing and result scenes.
Use thin rules to separate data, not boxed cards for every section.
Give long text a light paper surface and a bounded line length.
Let the dial and the main heading share the first viewport.

At 850px and below, stack the instrument below the main message.
At 600px and below, use one column for forms and detailed reading.
At 320px, keep all controls inside the viewport.
Let a detailed spectrum list scroll within its own region only when necessary.
Never make the full page scroll sideways.

## The dial

Draw the dial with CSS or SVG geometry.
Use radial marks as measurement ticks, not background texture.
Place five numbered controls around the dial in explore mode.
Give each control a category name in its accessible label.
Show the selected category name and definition in text below the dial.

In result mode, mark the actual category from `SPECTRUM_TIERS`.
Show the numeric model score and the words "model score".
Keep the actual category visually distinct from a category preview.
Keep a five-row text list below the dial for exact ranges and keyboard reading.

If the score is absent or invalid, show "Score unavailable" and remove the marker.
Do not choose a default category for missing data.

## Landing and form

Show the educational dial before the form.
State what the product does in plain words near the dial.
Keep one clear form action.
Collect the mark, goods or services, and NICE class as required fields.
Keep translation and pseudo mark available with explicit optional labels.
Keep the first-read notice near the action.

The form can echo the entered mark in large type.
That echo is a preview of text, not an assessment.
Do not show a score or category before submission.

## Result and evidence

Show the mark, context, finding, score, and actual category together.
Call the score a model score or probability score.
State that the finding is a first read, not a registration decision.

Keep this reading order:

1. Finding and context.
2. Spectrum position.
3. Written reading and next step.
4. Sources.
5. Score breakdown.
6. Submitted model input.

The API fills these sections at different times.
Give each section a named status: Queued, Loading, Ready, or Unavailable.
Keep earlier sections visible when a later request fails.

The score breakdown shows a signed value and a bar for each visible field.
The sources section shows TMEP and TTAB details from the response.
Do not invent a citation when the response has no sources.

## Motion

Use one short dial-marker transition when the selected category changes.
Use a short panel transition only when it helps the visitor track a state change.
Keep content visible before motion starts.
Stop continuous motion under `prefers-reduced-motion: reduce`.
Keep category, score, and status words visible without motion.

Do not add a moving marquee to the final result.
The dial is the main interaction.

## Controls and accessibility

Use a minimum 44px touch target for dial nodes and primary controls.
Show a visible focus ring on every link, button, field, and dial node.
Use native form labels and error text.
Keep keyboard order aligned with visual order.
Keep the dial usable without pointer movement.
Use text for every loading, success, empty, and failure state.

Do not put an interactive button inside an element with `role="img"`.
Use a group name for the dial and separate names for its controls.

## Other views

Apply the same color, type, rules, and control behavior to history, method, and sign-in.
Keep those views quieter than the main dial scene.
Do not repeat the large dial where it would block a task.

## Failure rules

When prediction fails, keep the form values and show a retry path.
When attribution fails, keep the finding and mark the dependent analysis unavailable.
When assessment fails, keep the finding and score breakdown visible.
When a rate limit gives a wait, show the wait in words.
When auth expires, keep the current input or result while the visitor signs in.
When the API is unreachable at build time, render the shell without an API request.

## Review checklist

- [ ] The landing dial teaches categories and shows no predicted result.
- [ ] The result dial reads one shared category mapping.
- [ ] The actual marker stays fixed during category exploration.
- [ ] The result shows a score as a model output, not a legal certainty.
- [ ] The finding stays visible after later request failures.
- [ ] All main views use the same tokens and type rules.
- [ ] The layout fits 320px, 390px, 768px, and 1440px.
- [ ] Body text, placeholders, and focus states meet accessibility requirements.
- [ ] Reduced motion keeps every state readable.
- [ ] No production component uses fixed mockup result data.

The finished frontend will define the final token-bearing `DESIGN.md`.
Update that file and `.impeccable/design.json` after the build, not from a mockup alone.
