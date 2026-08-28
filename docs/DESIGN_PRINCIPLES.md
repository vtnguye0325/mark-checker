# Bauhaus Design Principles

This document defines the design language for the Mark Checker interface. The language comes
from the Bauhaus school (Weimar and Dessau, 1919-1933) and from the Swiss typographic style
that grew out of it.

Reference: the "Bauhaus Legacy" website concept by Eugene Shuklin on Dribbble
(shot 24035833). The screenshots show the target look: black and white, very large grotesk
type, hard rectangular blocks, and no decoration.

---

## 1. The core rule

**Form follows function.**

Every visual element must do a job. If an element does no job, delete it. Do not add a
gradient, a shadow, a rounded corner, or an icon to make a screen look "finished". A screen
is finished when a user can read it and act on it.

Three tests for any element:

1. What does this element tell the user?
2. What happens if I delete it?
3. Does a simpler shape do the same job?

If the answer to (2) is "nothing", delete the element.

---

## 2. The six principles

### 2.1 Truth to materials

The web is flat. Text is text and a button is a rectangle. Do not imitate paper, glass,
leather, or metal. Do not add drop shadows to fake depth. Use a border or a change of
background color to separate two areas.

### 2.2 Geometry first

Build every component from the three primitive shapes: the rectangle, the circle, and the
triangle. The rectangle carries content. The circle marks a person or a state. The triangle
points.

Use a 0px corner radius by default. Allow a full circle (999px) only for an avatar or a
status dot. Never use a 4px or 8px "soft" radius; it reads as a generic template.

### 2.3 Asymmetric balance

Do not center everything. Balance a large dark block on the left against small text on the
right. Bauhaus layouts hold tension between unequal parts. A centered layout is static and
safe, and it removes the hierarchy.

The reference shot shows this: a tall black quote panel takes the left third, a thin list of
names takes the middle, and stacked photographs take the right.

### 2.4 Extreme contrast of scale

Set a headline 8 to 15 times larger than the body text. Do not use the middle sizes. A page
with a 96px headline and a 16px body reads as designed. A page with a 24px headline and an
18px body reads as a draft.

### 2.5 The grid rules the page

Place every element on a visible or implied grid. Nothing floats. Align edges hard. When two
blocks sit side by side, their top edges must match to the pixel.

### 2.6 Honest hierarchy

Show importance through size, weight, and position only. Do not show importance through
color alone, and do not show it through an icon. This keeps the interface readable for a
user who cannot see color.

---

## 3. Typography

Typography carries the whole design. Treat it as the primary material.

### 3.1 Typeface

Use one geometric sans-serif family for the whole product. The Bauhaus built its
letterforms from the circle, the triangle, and the square, so a geometric face carries the
style and a grotesk does not. Approved choices, in order:

| Rank | Family | Reason |
|---|---|---|
| 1 | Jost | Futura revival, full weight axis, tall x-height holds up at small sizes |
| 2 | Poppins | Pure geometric, perfect circles, reads more contemporary |
| 3 | Josefin Sans | The most period-correct, but too weak below 16px |

One display face is permitted, and only on the verdict word in the record plate. Set it
in Poiret One, an OFL art-deco geometric that carries the Bauhaus gesture at 48px and
above. Poiret One ships one weight, so never set it bold: the browser synthesises the
weight and thickens the deco strokes. Do not use it below 48px, and do not use it for
prose, labels, or figures.

Do not mix two sans families. Do not add a serif family for "elegance". Do not add a
monospace family. Bayer built the Universal alphabet to remove a second voice from the
page, and this product obeys that. Set a mark number, a serial number, a class code, or
raw JSON in the same family at weight 500, with `font-variant-numeric: tabular-nums` and
0.06em to 0.1em of tracking. The tabular figures give you the column alignment that a
monospace family gives you, and the tracking marks the text as machine data.

A geometric face needs more air than a grotesk. Track display sizes at -0.02em, not
-0.04em, and set uppercase labels at 12px and 0.14em, because circular letterforms lose
legibility faster than grotesk ones as the size drops.

### 3.2 Type scale

Use a large step ratio. A small ratio produces the flat, undesigned look.

| Token | Size | Weight | Tracking | Use |
|---|---|---|---|---|
| `display` | 96-160px | 700 | -0.04em | One per page. The page name. |
| `h1` | 56px | 700 | -0.03em | Section opener |
| `h2` | 32px | 700 | -0.02em | Sub-section |
| `h3` | 20px | 600 | -0.01em | Card title |
| `body` | 16px | 400 | 0 | Paragraphs |
| `small` | 13px | 400 | 0 | Metadata, captions |
| `label` | 11px | 600 | 0.12em | Uppercase eyebrow, nav, table header |

Rules:

- Set tight tracking on large type. Large text at default tracking looks loose and weak.
- Set wide tracking on the small uppercase label only.
- Set the line height to 0.95 for display type, 1.15 for headings, and 1.55 for body text.
- Never set body text below 14px.

### 3.3 Line length and alignment

Hold body text between 45 and 75 characters per line. Align text left and leave the right
edge ragged. Do not justify text, and do not center a paragraph of more than two lines.

### 3.4 Type as image

A headline can act as the image. Set the page name at `display` size, break it across lines
at a deliberate point, and let it fill the top of the screen. This removes the need for a
decorative hero graphic.

---

## 4. Color

### 4.1 The base

The base is monochrome. Pure black, pure white, and a small set of true neutral grays. The
reference shot uses this base with no color at all.

| Token | Value | Use |
|---|---|---|
| `--ink` | `#000000` | Text on light, and dark panel fills |
| `--paper` | `#FFFFFF` | Page background, text on dark |
| `--gray-90` | `#111111` | Dark panel, an alternative to pure black |
| `--gray-60` | `#666666` | Secondary text |
| `--gray-30` | `#B3B3B3` | Disabled text, hairlines on dark |
| `--gray-12` | `#E0E0E0` | Hairline rules, table borders |
| `--gray-04` | `#F5F5F5` | Section band background |

Use true neutrals. Do not use a blue-tinted or warm gray; the tint reads as a default UI kit.

### 4.2 The accent

Bauhaus permits the three primaries. Use them as signal, never as decoration.

| Token | Value | Meaning |
|---|---|---|
| `--red` | `#E63329` | Conflict, refusal, high risk, destructive action |
| `--blue` | `#0B5FD9` | Link, primary action, information |
| `--yellow` | `#F5C518` | Caution, pending, needs review |

Rules:

- Cover no more than 10% of a screen with accent color.
- Use one accent per view. Two accents fight, and three make a toy.
- Pair every accent with a word. Never signal state through color alone.

### 4.3 Contrast

Meet WCAG AA at minimum: 4.5:1 for body text and 3:1 for large text. The black-on-white base
passes with a large margin, so the burden falls on the accent colors and on gray text.
`--gray-60` on `--paper` gives 5.7:1 and passes. `--gray-30` fails on white; use it on dark
only.

---

## 5. Layout and grid

### 5.1 The grid

Use a 12-column grid with a 24px gutter. Set the page maximum width to 1440px. Set the outer
margin to 24px on mobile and 64px on desktop.

### 5.2 The spacing scale

Use an 8px base unit. Permitted values: 8, 16, 24, 32, 48, 64, 96, 128, 192.

Do not invent an intermediate value. If 32px is too small and 48px is too large, the problem
is the layout, not the scale.

### 5.3 Whitespace

Give a section room. Set the vertical padding between major sections to 96px or more on
desktop. Bauhaus layouts are not dense; they are ordered. Empty space is a working element
that groups the content and sets the reading pace.

### 5.4 Composition patterns

Four patterns cover most screens:

1. **The block split.** A full-bleed dark panel against a light panel. Split the width 1:2
   or 2:1, never 1:1.
2. **The stack.** A `display` headline, a rule, then a two-column body. Used for a section
   opener.
3. **The index.** A list of items, one per row, each row a hairline rule with the label on
   the left and the value on the right. Used for results and metadata.
4. **The plate.** A single image or screenshot inside a black frame with generous padding.

### 5.5 Rules and edges

Use a 1px hairline rule to separate rows. Use a 2px to 4px rule as a section divider or an
underline for the active navigation item. Do not use a dotted or dashed border except to
mark a drop zone.

---

## 6. Components

### 6.1 Buttons

A button is a rectangle with a 0px radius.

- **Primary:** `--ink` fill, `--paper` text. Padding 16px 32px. Weight 600.
- **Secondary:** transparent fill, 1px `--ink` border, `--ink` text.
- **Destructive:** `--red` fill, `--paper` text.
- **Hover:** invert the fill and the text color. Do not fade the opacity.
- **Focus:** a 2px `--ink` outline, offset 2px. Never remove the focus ring.

Label a button with a verb: "Check mark", "Export report". Do not label it "Submit" or "OK".

### 6.2 Inputs

Draw an input as a bottom rule only, 1px `--gray-30`, or as a full 1px `--ink` box. Choose
one pattern and hold it. On focus, thicken the rule to 2px and turn it `--ink`. Place the
label above the field, in the `label` token, uppercase.

### 6.3 Cards

A card is a rectangle with a 1px `--gray-12` border or a `--gray-04` fill. A card never has
a shadow. Do not nest a card inside a card.

### 6.4 Tables

Tables suit this product, because a trademark check produces rows of evidence. Use a hairline
rule under each row, an uppercase `label` header, and the `.mono` class for the serial
number and the class code. Align numbers right and text left.

### 6.5 Images

Render photographs in grayscale by default. Crop them into hard rectangles or a full circle.
Do not round the corners, and do not apply a gradient overlay.

---

## 7. Motion

Motion states a fact; it does not entertain.

- Duration: 150ms for a hover or a focus change, 250ms for a panel or a modal.
- Easing: `cubic-bezier(0.2, 0, 0, 1)`.
- Permitted properties: `transform`, `opacity`, `border-color`, `background-color`.
- Move an element along one axis at a time. Do not bounce, do not spin, and do not stagger a
  list by more than 40ms per item.
- Obey `prefers-reduced-motion: reduce`. Remove all transforms and keep the opacity change.

---

## 8. Anti-patterns

Do not use any of the following. Each one breaks the language.

| Anti-pattern | Reason |
|---|---|
| Purple-to-blue gradient | The default AI and SaaS look. It is decoration. |
| Soft drop shadow on a card | It fakes a material that the web does not have. |
| 8px rounded corner everywhere | It removes the geometric edge. |
| Glassmorphism, blur, and translucency | It lowers contrast and hides the grid. |
| A decorative emoji or a 3D illustration | It carries no information. |
| Centered body paragraphs | The ragged left edge slows reading. |
| Two sans-serif families | It splits the voice of the page. |
| A color-only status chip | A color-blind user cannot read it. |
| A middle type scale (18/22/28px) | It removes the hierarchy. |

---

## 9. Application to Mark Checker

The product reports a trademark conflict analysis. The analysis is evidence, so the interface
must read as a document, not as a dashboard.

- **The search page.** Set the mark name at `display` size as the hero. Place the input
  under it as a single bottom-rule field. Show nothing else.
- **The result page.** Open with a `display` verdict word: "CLEAR", "CAUTION", or
  "CONFLICT". Set the verdict word in `--ink` and put the matching accent color on a 4px
  rule above it.
- **The evidence list.** Use the index pattern. One row per cited mark. Show the serial
  number in the `.mono` class on the left, the mark name in `h3` in the middle, and the similarity
  score on the right.
- **The citation.** Set a quoted TTAB or TMEP passage inside a `--ink` panel with `--paper`
  text, at 20px, with generous padding. This is the black quote panel from the reference
  shot.
- **The loading state.** Show a 2px `--ink` progress rule that grows from the left. Do not
  use a spinner, and do not use a skeleton card.

---

## 10. Checklist before merge

Check every UI change against this list:

- [ ] Every corner radius is 0px, or the element is an avatar or a status dot.
- [ ] No element has a box shadow.
- [ ] The page has exactly one `display` headline.
- [ ] Every spacing value comes from the 8px scale.
- [ ] Accent color covers less than 10% of the screen.
- [ ] Every state has a word, not only a color.
- [ ] Body text contrast is 4.5:1 or better.
- [ ] Every interactive element shows a visible focus ring.
- [ ] The layout holds at 320px, 768px, and 1440px width.
- [ ] `prefers-reduced-motion` removes the transforms.
