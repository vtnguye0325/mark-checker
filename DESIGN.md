---
name: Mark Checker
description: A calm spectrum instrument for careful review of model findings.
colors:
  ink: "#171815"
  paper: "#F5F5F1"
  olive: "#C5C9A9"
  olive-light: "#E0E3CF"
  line: "#8F9477"
  muted: "#4B503E"
  dim-ink: "#CFD1C1"
  error: "#A13622"
typography:
  display:
    fontFamily: "Archivo, Helvetica, Arial, sans-serif"
    fontSize: "clamp(52px, 8vw, 96px)"
    fontWeight: 700
    lineHeight: 0.88
    letterSpacing: "-0.04em"
  body:
    fontFamily: "Archivo, Helvetica, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Archivo, Helvetica, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0.1em"
rounded:
  none: "0px"
  circle: "50%"
  pill: "999px"
spacing:
  gutter: "clamp(20px, 5vw, 72px)"
  row: "14px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.none}"
    padding: "14px 22px"
    height: "52px"
  input-text:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "9px 12px"
    height: "44px"
  dial-node:
    backgroundColor: "{colors.olive-light}"
    textColor: "{colors.ink}"
    rounded: "{rounded.circle}"
    size: "44px"
---

# Design System: Mark Checker

## Overview

**Creative North Star: “The Spectrum Instrument”**

The interface helps a person read one uncertain model finding. Olive gives the dial its own field. Paper gives evidence a quiet surface. Dark type and thin rules show order.

The landing page teaches the five categories. The result page marks a valid model score and names its category. The words keep the result clear without relying on color or motion.

**Key Characteristics:**
- One five-part dial supports exploration and results.
- Large roman sans type gives the page a clear order.
- Paper surfaces, olive fields, and thin rules separate content.
- Square controls and circular dial marks define the main shapes.

## Colors

The palette uses olive for the spectrum, paper for reading, and dark ink for type and actions.

### Primary
- **Instrument Olive** (#C5C9A9): Main landing field, result dial field, and selected spectrum row.
- **Pale Olive** (#E0E3CF): Inactive dial nodes, notices, and quiet state surfaces.

### Neutral
- **Near Black Ink** (#171815): Main type, buttons, and the result band.
- **Soft Paper** (#F5F5F1): Page background and text on dark fields.
- **Olive Rule** (#8F9477): Dividers and dial outlines. Use it for decoration, not small text.
- **Deep Muted Green** (#4B503E): Supporting text and labels.
- **Brick Error** (#A13622): Error text and visible focus outlines.
- **On-Ink Quiet Text** (#CFD1C1): Supporting text on ink surfaces.

### Named Rules
**The Score Language Rule.** Name each value a “model score.” Do not present it as a chance of registration.

## Typography

**Display Font:** Archivo (with Helvetica, Arial, sans-serif fallbacks).
**Body Font:** Archivo (with Helvetica, Arial, sans-serif fallbacks).
**Label Font:** Archivo (with Helvetica, Arial, sans-serif fallbacks).

**Character:** The single sans family keeps headings, evidence, and controls in one voice. Large headings use tight tracking; body text stays in sentence case.

### Hierarchy
- **Display** (700, 52–96px responsive, 0.88 line height): Landing headline. The result verdict uses 48–96px with a 0.9 line height.
- **Section heading** (700, 42–88px responsive, 0.94 line height): Form, method, and page titles.
- **Evidence title** (700, 30–54px responsive, 0.98 line height): Result sections.
- **Body** (400, 16–18px, 1.45–1.5 line height): Main copy and explanations. Keep long text near 66–68 characters per line.
- **Label** (600, 12px, 0.1em tracking): Short labels, states, and section numbers. Use uppercase only for short labels.

### Named Rules
**The One Voice Rule.** Use Archivo for display type, body type, and labels. Use tight tracking for large type, not for long reading text.

## Layout

Use an open two-column landing hero on wide screens. Place the headline beside the dial. At 900px and below, stack the dial under the message. At 600px and below, use one column for the form and result dial.

Use a 48px page gutter at widths of 900px and above. Use a 20px gutter below 900px. Use ruled rows for evidence and form fields. Keep the body copy near 66–68 characters per line. The result view places the finding first, then its reading, sources, reasons, and submitted input.

Keep the category text list inside its own region on mobile. Fit controls within a 320px viewport. Do not allow page-wide horizontal scroll.

## Elevation & Depth

The system is flat. It uses olive and paper fields, spacing, and thin rules to separate areas. It does not use shadows. Dial rings and rules add structure without suggesting a gauge of legal certainty.

## Shapes

Use square corners on buttons, fields, and reading surfaces. Use circles for the dial, nodes, and small brand mark. The navigation may use pill-shaped links. Use 1px rules for data and dial outlines. Keep at least 12px of space inside colored notices and error panels.

## Components

### Primary Button
Use an ink fill, paper text, square corners, and a 52px minimum height. Use 14px 22px padding. Change the fill on hover and show a 3px focus outline.

### Text Field
Use a transparent paper surface with a bottom rule. Keep the field at least 44px high. Give it a visible label and 16px or larger text. Show a focus outline and keep values when a request fails.

### Navigation
Use compact links in a flexible row. Let the row wrap below the brand on mobile. Keep controls at least 36px high, and retain a clear focus outline.

### Spectrum Dial
Use five numbered nodes around radial ticks. In explore mode, a selected node updates the category name, score range, definition, and example. In result mode, place a marker only for a valid score. Show category and score as text. Keep the mobile category list available for keyboard use.

### Result
Show the mark, context, finding, model score, and category. Keep the finding visible if a later evidence request fails. State each loading and error condition in words.

## Do's and Don'ts

### Do:
- **Do** use the same palette and dial on the landing and result views.
- **Do** show categories, scores, and errors in text as well as color.
- **Do** keep the submitted form values after a failed prediction.
- **Do** show a marker only when the score is a valid number from 0 to 1.
- **Do** keep the mobile category list and its buttons usable by keyboard.

### Don't:
- **Don't** present a model score as a chance of registration.
- **Don't** show a result marker when the score is missing or invalid.
- **Don't** use sample evidence in an empty result.
- **Don't** let motion hide content or imply certainty.
- **Don't** use radial ticks as background texture.
