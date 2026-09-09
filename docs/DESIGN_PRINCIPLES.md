# Brutalist Design Principles

This document defines the design language for the Mark Checker interface. The language is
raw web-brutalism: the page shows its structure, uses the default materials of the browser,
and hides nothing behind decoration.

Reference: the approved mockups in `docs/mockups/brutalism/`. `a-specimen.html` is the
landing state. `a-result.html` is the record state. When this document and a mockup
disagree, the mockup wins, and you must update this document.

This document replaces the Bauhaus language. The two share one rule: form follows function.
They differ in tone. Bauhaus was ordered and quiet. Brutalism is loud and direct.

---

## 1. The core rule

**Show the structure. Hide nothing.**

A screen is a document with a ledger of fields and a set of findings. Every rule, border,
and block must show the user where a thing starts and where it ends. Do not soften an edge,
do not fade a state, and do not hide a boundary.

Three tests for any element:

1. What does this element tell the user?
2. What happens if I delete it?
3. Can a thicker rule or a black block do the same job?

If the answer to (2) is "nothing", delete the element.

---

## 2. The six principles

### 2.1 Raw materials

The browser gives you text, rules, and rectangles. Use them as they are. Do not add a
shadow, a gradient, a blur, or a rounded corner. Separate two areas with a rule or with an
inverted block (black fill, paper text).

### 2.2 The ledger

The product collects facts and reports facts. Lay out both as a ledger: one row per fact,
a label on the left, a value on the right, a rule between rows. The form is a ledger. The
record metadata is a ledger. The model inputs are a ledger.

### 2.3 Extreme scale

Set the headline as large as the viewport permits. Set the body at 16px. Do not use the
middle sizes. The landing headline runs to 224px. The verdict word runs to 148px. The mark
input runs to 64px. The distance between the headline and the body makes the hierarchy.

### 2.4 The inverted block

Use a full-bleed black block for the item that carries the most weight on the page. The
landing page inverts the mark row. The record page inverts the plate, the spectrum band,
and the cited passage. Do not invert more than three blocks on one page.

### 2.5 One accent per state

Yellow marks a pending or cautionary state. Red marks a load, a refusal, or an error. Blue
marks a link or a primary action. A page carries one accent rule, and each accent always
sits next to a word.

### 2.6 Motion states a fact

The landing page carries one moving element: the spectrum marquee. It moves because the
verdict is undecided. The record page carries the same band, stopped, and reads the score
as a position on it. Nothing else on either page moves.

---

## 3. Typography

### 3.1 Typefaces

Use two families from one source. Both are grotesks and both are OFL.

| Token | Family | Weights | Use |
|---|---|---|---|
| `--sans` | Archivo | 400, 500, 600, 800 | Body, inputs, values, footer |
| `--cond` | Archivo Narrow | 600, 700 | Headlines, labels, buttons, the mark, the verdict |

Fallback stack: `Helvetica, Arial, sans-serif`.

Load them from Google Fonts with `display=swap`. Do not add a third family. Do not add a
monospace family for figures. Set figures with `font-variant-numeric: tabular-nums
lining-nums` in `--sans`.

### 3.2 Type scale

| Token | Family | Size | Weight | Tracking | Line height | Use |
|---|---|---|---|---|---|---|
| `headline` | cond | `clamp(52px, 15.5vw, 224px)` | 700 | -0.02em | 0.82 | The landing question, uppercase |
| `headline-outline` | cond | `clamp(34px, 9.6vw, 138px)` | 700 | -0.01em | 0.9 | The second line of the headline, paper fill, 2px ink stroke |
| `verdict` | cond | `clamp(54px, 10vw, 148px)` | 700 | -0.02em | 0.85 | The finding on the plate |
| `mark-input` | cond | `clamp(34px, 6vw, 64px)` | 700 | 0.02em | 1.05 | The mark field, uppercase |
| `mark` | cond | `clamp(30px, 3.4vw, 44px)` | 700 | 0.01em | 1.05 | The mark on the plate, uppercase |
| `button` | cond | `clamp(20px, 3.2vw, 30px)` | 700 | 0.1em | 1 | Primary action, uppercase |
| `marquee` | cond | `clamp(20px, 2.4vw, 30px)` | 700 | 0.04em | 1 | The spectrum band, uppercase |
| `h2` | cond | 32px | 700 | -0.01em | 1.1 | Part title, uppercase |
| `row-title` | cond | 18px to 22px | 700 | 0 | 1.2 | Tier name, source title, a large value, uppercase |
| `quote` | sans | `clamp(18px, 2vw, 23px)` | 400 | 0 | 1.4 | The cited passage |
| `input` | sans | 19px | 400 | 0 | 1.3 | Text field, select |
| `body` | sans | 16px | 400 | 0 | 1.5 | Paragraphs, values |
| `small` | sans | 13px to 14px | 400 | 0 | 1.5 | Hints, footer, secondary values |
| `label` | cond | 12px | 700 | 0.16em | 1.3 | Uppercase eyebrow, row label, cite |
| `brand` | cond | 15px | 700 | 0.2em | 1 | The product name in the header |
| `status` | cond | 11px | 700 | 0.14em | 1 | Rail status word, uppercase |

Rules:

- Set every `--cond` element in uppercase. Set every `--sans` element in sentence case.
- Set the headline with `overflow-wrap: anywhere` so that it cannot push the viewport wide.
- Hold body text between 45 and 75 characters per line. Use `max-width: 66ch` on a
  paragraph.
- Never set body text below 13px.
- Align text left. Do not justify, and do not center a paragraph.

### 3.3 Type as image

The headline is the hero. On the landing page it fills the top of the screen in two lines:
a solid line and an outlined line. On the record page the verdict word does the same job.
Neither page carries an illustration, an icon set, or a photograph.

---

## 4. Color

### 4.1 The base

The base is warm paper and near-black ink. Do not use pure white or pure black.

| Token | Value | Use |
|---|---|---|
| `--paper` | `#F1EFE8` | Page background, text on ink |
| `--ink` | `#0A0A0A` | Text on paper, inverted block fill, rules, buttons |
| `--rule` | `#0A0A0A` | Hairline rules (alias of `--ink`) |
| `--gray` | `#6B6A65` | Secondary text on paper, hairlines on ink |
| `--dim-ink` | `#9A9790` | Secondary text on ink |
| `--faint` | `#D8D5CC` | Skeleton bars, disabled fills |

### 4.2 The accents

| Token | Value | Meaning |
|---|---|---|
| `--yellow` | `#F2C200` | Pending, caution, the active tier, the score pin |
| `--red` | `#D62015` | Loading, refusal, error, the focus ring, the caret |
| `--blue` | `#0B3FD9` | Link, primary button hover, the accent rule on a distinctive finding |

Rules:

- Pair every accent with a word. Never show a state through color alone.
- Yellow fills a block (the notice, the stamp, the active tier row). Red and blue never fill
  a block larger than a button.
- Set the record accent rule to `--blue` when the finding is distinctive and to `--red`
  when it is not distinctive.
- The marquee colors "Generic" red and "Fanciful" yellow, and nothing else.

### 4.3 Contrast

Meet WCAG AA at minimum. `--ink` on `--paper` gives 17:1. `--gray` on `--paper` gives
4.7:1. `--dim-ink` on `--ink` gives 6.8:1. `--yellow` on `--ink` gives 12:1. `--ink` on
`--yellow` gives 12:1. `--red` on `--ink` gives 3.8:1 and passes only as large text. Do not put `--gray` text on `--ink`, and do not put `--red` text on
`--ink` below 24px.

### 4.4 Browser chrome

Theme the browser itself.

- `::selection` is `--ink` on `--paper`. Inside an inverted block it is `--paper` on `--ink`.
- `caret-color` is `--red`.
- The scrollbar is `--ink` on `--paper`, thin, with a 1px `--ink` rule on the track.
- `color-scheme: light`. The product ships one theme.

---

## 5. Layout

### 5.1 Margins

Use one margin token, `--m`. Set it to 20px below 900px and to 48px at 900px and above. Every
full-bleed block pads its content by `--m`. Do not set a page maximum width; the rules run
edge to edge.

### 5.2 The spacing scale

Use these values: 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 28, 32, 40, 44, 48. Vertical
padding inside a section is 40px to 48px. Padding inside a row is 8px to 22px.

### 5.3 Rules and edges

| Weight | Use |
|---|---|
| 1px `--rule` | A row inside a ledger, a table row, a source row |
| 1px `--gray` | A row inside an inverted block |
| 2px `--ink` | The header, a section boundary, the form boundary, a bordered box, a button outline |
| 5px accent | The accent rule under the record bar, the active tier on the frozen scale |

Do not use a dotted or dashed border. Do not use a border on a card, because there are no
cards. Every boundary is a rule between two blocks.

### 5.4 Composition patterns

1. **The header strip.** The brand on the left, the nav on the right, each nav item cut by
   a 2px left rule, a 2px rule below. Hover inverts an item.
2. **The ledger.** A stack of rows. Each row is a two-column grid: a 190px label column with
   a 1px right rule, then the value. Below 760px the row stacks.
3. **The inverted block.** A full-bleed `--ink` block with `--paper` text. The mark row,
   the plate, the spectrum band, and the cited passage use it.
4. **The band.** A full-bleed inverted strip that carries one line of large condensed type.
   The marquee is the moving band. The frozen scale is the measured band.
5. **The action row.** A two-column grid: the hint on the left, the button on the right,
   above a 2px rule. Below 760px the row stacks.
6. **The document.** A 250px sticky rail on the left, the parts on the right. Below 1000px
   the rail stacks on top.
7. **The stamp.** A yellow box with a 2px border and a label, rotated -2deg. Use it once,
   on the landing page, for the "not legal advice" mark.

### 5.5 Breakpoints

| Width | Change |
|---|---|
| 640px | Input lines go to two columns |
| 760px | Ledger rows, the action row, and the close row go to two columns |
| 900px | `--m` grows to 48px, the deck and the plate go to two columns |
| 1000px | The rail sticks to the left of the parts |

Test at 390px, 768px, and 1440px.

---

## 6. Components

### 6.1 Buttons

A button is an `--ink` rectangle with `--paper` text, 0 radius, no border.

- **Primary:** `button` type, padding 22px 40px, full width of its cell, the label on the
  left and an arrow on the right.
- **Hover:** `--blue` fill. **Active:** `--red` fill.
- **Disabled:** `--paper` fill, `--gray` text, a 2px inset `--gray` ring, `cursor:
  not-allowed`.
- **On ink** (the record bar): transparent fill, `--paper` text, a 1px `--paper` bottom
  rule. Hover inverts to `--paper` fill and `--ink` text.
- **Focus:** the global ring (see 6.7).

Label a button with a verb: "Open record", "Check another name". Do not label it "Submit".

### 6.2 Inputs

An input has no box. It has a 2px `--ink` bottom rule, transparent fill, 0 radius, and
19px `--sans` text. Hover tints the fill 5% ink. Focus shows the global ring at 3px offset.
The placeholder is `--gray`.

The mark input sits in the inverted row. It is `--cond`, uppercase, `mark-input` size,
`--paper` text on `--ink`, with a 2px `--paper` bottom rule. Hover tints the fill 8% paper.

A select carries the same rule and a two-triangle arrow drawn with `background-image`.
Do not use the native arrow.

Place the label in the row's left column, in the `label` token. Mark an optional field with
"Optional" in `--sans` 12px `--gray` under the label.

### 6.3 The notice

A full-bleed `--yellow` strip with a 1px top rule. It holds a bordered label ("Read this")
and one paragraph at 14px. Use it for a fact the user must read before they act, such as
the free-tier limit.

### 6.4 The marquee

A full-bleed inverted band. The track holds the five tier names twice and moves left by 50%
over 30 seconds, linear, infinite. "Generic" is `--red` and "Fanciful" is `--yellow`. The
band carries an `aria-label`. The track is `aria-hidden`. Under `prefers-reduced-motion:
reduce` the animation stops and the first five names stand still.

### 6.5 The frozen scale

The record page shows the same band, stopped. The track is a five-column grid with the
columns sized to the tier ranges: 28fr, 22fr, 20fr, 18fr, 12fr. Each cell shows the tier
name and the range. The tier that holds the score has a 5px `--yellow` top rule, a
`--yellow` name, and a `#1c1c1c` fill. A 2px `--yellow` pin sits under the track at the
score position with the words "This mark".

### 6.6 The tier table

One row per tier: a 12px glyph, the name, the range, then the note. The glyph is a 12px
square with a 2px `--ink` border. The row that holds the score fills `--yellow`, extends
10px past the text edge on both sides, and fills the glyph solid. Its label reads
"Fanciful — this mark".

### 6.7 Focus

`:focus-visible` is a 3px `--red` outline with a 2px offset. Inside an inverted block it is
`--yellow`. Never remove the ring.

### 6.8 The attribution bar

A split axis. The track is a two-column grid, 14px tall, with a 1px `--ink` border and a
2px `--ink` center rule. A positive value fills `--ink` to the right. A negative value draws
a 1px outlined box to the left. The sign reads from the fill and from the side, so a user
who cannot see color reads it.

### 6.9 The cited passage

An inverted block at `quote` size, padded 34px 40px, with the source in the `label` token
in `--dim-ink` below it. The rows that were retrieved but not cited follow as a ledger.

### 6.10 The pending block

A box with a 2px `--ink` border. A `--yellow` label sits at the top with the status and the
wait ("Writing — about 20 seconds"). One paragraph explains what will arrive. Skeleton
bars in `--faint` show the shape of the missing text. Do not use a spinner.

### 6.11 The rail

A 250px sticky column with a 2px right rule. It holds two ledgers: the record metadata
and the parts. Each part link shows a status word in the `status` token: Ready, Queued,
Loading, or Unavailable. The current part carries a 6px `--red` square in the left gutter.
Loading is `--red`. Hover inverts the link.

### 6.12 The record bar

A full-bleed `--ink` strip at 11px vertical padding. It holds the brand, "Not legal advice",
the account email in `--dim-ink`, and the account buttons. A 5px accent rule sits under
it.

---

## 7. Motion

- The marquee is the only continuous animation. 30 seconds, linear, infinite.
- Hover and focus change color with no transition. The change is instant.
- `scroll-behavior: smooth` on the record page, for the rail links.
- Obey `prefers-reduced-motion: reduce`. Stop the marquee. Set `scroll-behavior: auto`.
- Do not fade an element in, do not slide a panel, and do not stagger a list.

---

## 8. Anti-patterns

| Anti-pattern | Reason |
|---|---|
| Any corner radius | It softens the edge. |
| Any box shadow | It fakes depth. |
| Pure white or pure black | It reads as a default. The paper is warm. |
| A gradient, a blur, or translucency | It hides the structure. |
| A card with a border | There are no cards. Use rules between blocks. |
| A third font family | It splits the voice. |
| A spinner or a progress ring | A skeleton and a word say more. |
| A transition on hover | Brutalism does not ease. |
| A color-only status | A color-blind user cannot read it. |
| A middle type size (24px to 48px) for a heading | It flattens the hierarchy. |
| A decorative icon or emoji | It carries no information. |
| A second moving element | The marquee is the one. |

---

## 9. Application to Mark Checker

The product answers one question and then shows its work. The two states share one world.

- **The landing state.** The header strip. The headline "IS YOUR NAME / REGISTRABLE?" with
  the second line outlined. The deck with the stamp and one paragraph. The marquee. The
  ledger form: mark (inverted), goods, NICE class, translation (optional), pseudo mark
  (optional). The yellow notice about the free tier. The action row with the hint and
  "Open record →". The "How it works" section: a 32px title, one line of deck, three stage
  columns divided by 1px rules, one line for each stage, and the "Read the method" button.
  The footer.
- **The method state.** The long explainer behind the "Read the method" button. A 96px title,
  a deck, and one part for each stage, in the part rhythm of the record. A "What it does not
  do" part holds the limits. The close row returns the reader to the form. The footer.
- **The record state.** The record bar and the accent rule. The plate: the finding on the
  left, the subject ledger on the right, with Confidence "Pending" in `--yellow` until stage
  three returns. The frozen scale with the pin at the score. The document: the rail on the
  left, the five parts on the right. Part 01 the tier table. Part 02 the attribution bars.
  Part 03 the cited passage and the retrieved rows. Part 04 the pending block while the
  assessment writes. Part 05 the input ledger. The close row with "Check another name →".
  The footer.
- **Partial is normal.** Stage one returns first. The plate, the scale, and Parts 01, 02,
  and 05 render at once. Parts 03 and 04 show their status in the rail and a pending block
  in place until they return. An unavailable part keeps its slot and says "Unavailable".
- **The error state.** A refusal (a 429, a billing error, a model error) is a fact. Show it
  in the pending block's slot with a `--red` label and the words the user needs. Do not
  hide the part.

---

## 10. Checklist before merge

Check every UI change against this list:

- [ ] Every corner radius is 0.
- [ ] No element has a box shadow, a gradient, or a blur.
- [ ] The page uses `--paper` and `--ink`, not white and black.
- [ ] Only Archivo and Archivo Narrow load.
- [ ] Every `--cond` element is uppercase.
- [ ] The page has one hero: the headline or the verdict.
- [ ] Every state has a word next to its color.
- [ ] The rules are 1px, 2px, or 5px, and the 5px rule is an accent.
- [ ] Body text contrast is 4.5:1 or better.
- [ ] Every interactive element shows the 3px focus ring.
- [ ] The marquee is the only continuous animation, and it stops under reduced motion.
- [ ] The layout holds at 390px, 768px, and 1440px, and nothing scrolls sideways.
- [ ] `node ~/.claude/skills/impeccable/scripts/detect.mjs --json <file>` returns no findings other than the marquee.
