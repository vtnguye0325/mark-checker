Findings

---

[Severity 4] Main form fields have no <label> elements

- Principle: Accessibility (H13)
- Location: MarkForm.jsx:18, 32, 43
- Issue: The three primary inputs — trademark name, goods/services description, and NICE class — have id attributes but no associated <label> elements. The mark input uses only a placeholder. The
  textarea and select use only placeholders/option text. Advanced fields (Translation, Pseudo Mark) do have labels. The inconsistency makes it worse.
- User impact: Screen readers announce these fields as "edit text, edit text, combobox" with zero context. A blind user cannot tell what any of the three main fields are asking for. This renders the
  primary interface completely unusable for assistive technology.
- Fix: Add visually present labels (or visually hidden ones if you want clean aesthetics). Recommend visible labels above inputs — they also help sighted users who don't read placeholders carefully.

---

[Severity 3] Sub-readable font sizes on content users must read

- Principle: Aesthetic and Minimalist Design (H8), Perceptibility (H14)
- Location: App.css — .abcr-seg-name (7.5px), .abcr-desc-item (7.5px), .nice-badge (8px), .ls-nc (8px), .ls-outcome (8px), .legal-sources-count (8px), .prob-label (9px), .field-label (9px),
  .advanced-toggle (9px), .attr-field (9px), .divider-label (9px), .explain-status (9px)
- Issue: 7.5px text is physically unreadable on most displays. Even 9px is at or below most users' minimum comfortable reading size. These are not decorative elements — prob-label says "Distinctiveness",
  field-label says "Translation", .abcr-seg-name says "Arbitrary" etc. Users need to read these.
- User impact: Users will squint, misread, or skip over information they need to interpret the result. On mobile or non-retina displays this becomes genuinely illegible.
- Fix: Minimum 11px for anything a user must read. 10px absolute floor for purely decorative chrome. Labels that carry semantic meaning (prob-label, field-label, spectrum names) should be 11-12px.

---

[Severity 3] --text-dim fails WCAG AA contrast

- Principle: Accessibility (H13)
- Location: App.css:19 — --text-dim: #6b6760 on --bg: #0f0f0e
- Issue: Contrast ratio is approximately 3.85:1. WCAG AA requires 4.5:1 for normal text, 3:1 for large text (18px+ or 14px+ bold). The majority of --text-dim usage is on 8-11px text — far below "large
  text" threshold. Used in: .brand-sub, .header-tagline, .field-hint, .select-arrow, .advanced-toggle, .divider-label, .result-mark--dim, .tier-dash, .debug-toggle, .abcr-desc-item, .ls-expand, .ls-nc,
  .attr-legend.
- User impact: Users with low vision, older users, or anyone on a dim display will struggle to read this text. Legal analysis tools attract professionals who may be in bright offices with glare on
  screens.
- Fix: Darken --bg or lighten --text-dim. Since --bg is already very dark, raise --text-dim to at minimum #7e7a73 (≈4.6:1 ratio).

---

[Severity 3] Abercrombie spectrum is disconnected from the result

- Principle: Perceptibility (H14), Recognition over Recall (H6)
- Location: AbercrombieSpectrum.jsx — no props, purely static
- Issue: The spectrum renders 5 colored segments (Generic → Fanciful) with no indication of where the analyzed mark sits. The deriveCategory() function exists and correctly maps prob_distinctive to a
  category — but it's never used to highlight the active segment. The user must mentally cross-reference the verdict badge text against the spectrum legend to understand positioning.
- User impact: The spectrum looks like a legend explaining concepts rather than a result visualization. Users who understand trademark law expect to see "your mark is here." Users who don't know
  trademark law get no help from an unhighlighted color bar.
- Fix: Pass prob_distinctive as a prop, call deriveCategory(), and visually mark the active segment — brighter strip, highlighted name, or an indicator arrow above it. The infrastructure already exists
  in the same file.

---

[Severity 3] Content elements still use muted/dim color

- Principle: Perceptibility (H14)
- Location: App.css — .prob-label (line 556, --text-muted), .prob-value (line 585, --text-muted), .attr-subtitle (line 654, --text-muted), .attr-field (line 672, --text-muted), .attr-value (line 678,
  --text-dim), .loading-text (line 463, --text-muted), .ls-text--preview (line 973, --text-muted)
- Issue: The distinctiveness percentage (.prob-value), the probability label ("Distinctiveness"), the attribution field names and values, and the loading status text are all the primary content of their
  respective sections. They're not decorative metadata — they're what the user came to read.
- User impact: "72%" in --text-muted beside an important probability bar is harder to read than it needs to be. The attr field names and values inside the Feature Attribution chart are data, not labels.
- Fix: --text for prob-label, prob-value, attr-subtitle, attr-field, attr-value, loading-text. Keep --text-muted only for .ls-text--preview (genuinely secondary — it's a collapsed preview).

---

[Severity 2] No cancel during the 3-step loading pipeline

- Principle: User Control and Freedom (H3)
- Location: useTrademarkPipeline.js:14 — AbortController exists but only for the first fetch; ResultPanel.jsx — no cancel button in loading state
- Issue: The pipeline runs three sequential network calls: /predict → /explain → /analyze. Total wall time can be 10-30 seconds. There's an AbortController for /predict but /explain and /analyze don't
  use it. The UI offers no way to cancel once analysis starts.
- User impact: If a user types the wrong mark name and submits, they must wait for all three requests to complete before they can reset and try again. Frustrating on slow connections.
- Fix: Expose a cancel() function from the hook. Wire AbortControllers to all three fetches. Show a "Cancel" button in the loading state.

---

[Severity 2] NICE class is jargon with no explanation

- Principle: Match Between System and Real World (H2), Help and Documentation (H10)
- Location: MarkForm.jsx:43 — <option value="">Class…</option> with no tooltip or hint
- Issue: "NICE class" is an international trademark classification system. Most users filing their first trademark application won't know what class to choose. The select has no hint text, no link to a
  reference, and no inline explanation.
- User impact: Users either guess a class (potentially invalidating their analysis) or abandon the tool and open a Google search.
- Fix: Add a .field-hint below the select: "International classification of goods/services — pick the category that matches your product." Or add a tooltip on the label.

---

[Severity 2] Disabled analyze button at 0.28 opacity looks broken

- Principle: Affordances and Signifiers (H11), Visibility of System Status (H1)
- Location: App.css:368 — .btn-analyze:disabled { opacity: 0.28 }
- Issue: 28% opacity on a small button on a dark background makes it nearly invisible. First-time users may think the button doesn't exist or the interface is broken, rather than understanding they need
  to fill in the form.
- User impact: Users may stall on the empty form wondering what to do next, not realizing the button is there and waiting for input.
- Fix: Raise to opacity: 0.45 minimum. Consider adding a cursor: not-allowed tooltip or showing a brief inline prompt like "Fill in all fields to analyze" when the button is clicked while disabled.

---

[Severity 2] No pipeline progress — users don't know more is coming

- Principle: Visibility of System Status (H1)
- Location: ResultPanel.jsx, LLMAnalysis.jsx — each section loads independently with no overall progress frame
- Issue: After /predict returns, the result appears. Then the attribution chart loads. Then the legal analysis loads. But there's no framing that says "3 of 3 complete" or "more analysis in progress."
  The LLM loading spinner appears at the very bottom of a long page — users who don't scroll won't see it.
- User impact: Users think they're done after the first result, then are surprised by more content appearing below. Or they miss the LLM analysis entirely because they didn't scroll down to see it was
  loading.
- Fix: Add a compact status strip below the result hero that shows the pipeline stages: "Model ✓ · Attribution ✓ · Legal Analysis…" — clears itself when all three complete.

---

[Severity 2] Abercrombie spectrum has no explanation for non-lawyers

- Principle: Help and Documentation (H10), Match Between System and Real World (H2)
- Location: AbercrombieSpectrum.jsx:48 — section label "Abercrombie Spectrum" with no tooltip
- Issue: The Abercrombie doctrine is a 1976 court case. Non-lawyers won't know what the spectrum means, why there are 5 categories, or how it relates to their mark's registrability.
- User impact: The visualization is meaningless to most users. They see colored boxes, shrug, and scroll past.
- Fix: Add a one-line explanation below the header: "A legal framework for trademark strength — marks higher on the spectrum are easier to register."

---

[Severity 1] Advanced toggle uses ▶ (right-arrow) for "closed"

- Principle: Consistency and Standards (H4)
- Location: MarkForm.jsx:60
- Issue: ▶ conventionally means "play" or "navigate right." For expand/collapse, the pattern is ▼/▲ (pointing where content will appear) or +/−. A right-pointing triangle is ambiguous.
- Fix: Change to ▼ for closed, ▲ for open.

---

[Severity 1] Reset discards form state with no undo

- Principle: Tolerance and Forgiveness (H15)
- Location: App.jsx:28-31
- Issue: Reset clears mark, description, nice_class, translation, pseudo_mark — all at once, immediately, no confirmation.
- Fix: Minor for short inputs. Consider pre-filling with previous values, or a brief "Undo reset" toast.

---

[Severity 1] No Cmd+Enter keyboard shortcut for submit

- Principle: Flexibility and Efficiency (H7)
- Location: MarkForm.jsx — no onKeyDown handler
- Fix: Add onKeyDown to the textarea to submit on Cmd+Enter or Ctrl+Enter.

---

[Severity 1] Error state has no retry button

- Principle: Error Recovery (H9)
- Location: ResultPanel.jsx:30 — no retry in error path; error is shown in MarkForm but button is still "Analyze"
- Issue: When the API fails, the error banner appears but disappears on the next submission. Not truly broken — Analyze button remains — but a "Try again" button directly in the error banner would be
  clearer.
- Fix: Minor. The existing UX (error banner + Analyze button) is acceptable.

---

Strengths

1. prefers-reduced-motion respected — all animations disabled cleanly with a single media query block. The right approach.
2. Accessible progress bars via @radix-ui/react-progress — role="progressbar", aria-valuemin/max/now, getValueLabel — properly implemented.
3. AbortController on submit — previous in-flight requests are cancelled when a new submission happens. Prevents race conditions and stale results.
4. Custom easing curves — cubic-bezier values instead of browser defaults. Animations have real craft behind them.
5. Result hierarchy — mark name at display scale → verdict badge → probability → spectrum → attribution → LLM cards. The information architecture of the result is logical and well-ordered.

- Fix: Minor. The existing UX (error banner + Analyze button) is acceptable.

---

Strengths

1. prefers-reduced-motion respected — all animations disabled cleanly with a single media query block. The right approach.
2. Accessible progress bars via @radix-ui/react-progress — role="progressbar", aria-valuemin/max/now, getValueLabel — properly implemented.
3. AbortController on submit — previous in-flight requests are cancelled when a new submission happens. Prevents race conditions and stale results.
4. Custom easing curves — cubic-bezier values instead of browser defaults. Animations have real craft behind them.
5. Result hierarchy — mark name at display scale → verdict badge → probability → spectrum → attribution → LLM cards. The information architecture of the result is logical and well-ordered.
6. Focus styles — inputs have a real focus ring (border + box-shadow), not just outline: none with nothing replacing it.

---

All 14 findings will be fixed by default. Anything you'd like to skip or deprioritize before I start?
