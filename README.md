# Mark Checker

**Is your brand name strong enough to register as a trademark?**

Type the name, say what you sell, and pick a class. Mark Checker gives you an instant read
on how the name scores, shows which part of what you typed drove that score, and explains
it in plain English.

This is a first read, not legal advice. Read [What this is not](#what-this-is-not) before
you act on a result.

---

## Try it

1. **Enter a mark.** The name you want to register.
2. **Describe the goods or services.** What you actually sell under that name.
3. **Pick a NICE class.** The international category the trademark office files you under.
   The list gives you all 45 in plain words, such as *Class 21 — Kitchenware & Glassware*.

Two fields are optional. Fill **Translation** if the name is a foreign word, and **Pseudo
mark** if the name runs words together, such as *zephyr line* inside ZEPHYRLINE.

![The entry form, with the mark ZEPHYRLINE, the goods "insulated water bottles", and Class
21 selected](docs/assets/01-enter-a-mark.jpg)

---

## What you get back

### The finding

The record opens with the call and the score. A score near 1.00 means the name looks
inherently distinctive. A score near 0.00 means it reads as the plain word for the product.

The example below scores **0.98** and lands on **Fanciful** — the strongest tier, because
ZEPHYRLINE is an invented word with no meaning tied to drinkware.

![The finding "Distinctive" with a score of 0.98, and the Abercrombie spectrum with Fanciful
marked](docs/assets/02-the-verdict.jpg)

### Where the name sits on the spectrum

Trademark law grades every name on one scale, called the Abercrombie spectrum. The record
prints all five tiers and marks yours:

| Tier | What it means for you |
|---|---|
| **Generic** | The plain word for the product. Never registrable. |
| **Descriptive** | Describes a quality of the product. Needs proof that buyers already link the name to you. |
| **Suggestive** | Hints at the product without naming it. Registrable. |
| **Arbitrary** | A real word with no tie to the product, such as APPLE for computers. Registrable. |
| **Fanciful** | An invented word, such as KODAK. Strongest protection. |

### Why it decided that

The app blanks each field you typed, one at a time, and measures how much the score moves.
The swing is that field's contribution. You see whether the name itself carried the result
or whether the goods description did.

In the example, the mark text pushed **+0.07 toward** distinctive and the goods description
barely moved the needle — which is what you want. A name that only scores well because of
the goods you paired it with is a weaker name.

![The "Basis for the finding" chart, showing the per-field contribution to the
score](docs/assets/03-basis-for-the-finding.jpg)

### The written analysis

Below the chart, the record adds two more parts:

- **Authority relied on** — the actual TMEP sections and TTAB decisions that apply to a name
  like yours. The app retrieves them first and is allowed to cite only what it retrieved, so
  every citation points at a real document you can look up.
- **What to do next** — plain-English suggestions, such as which word to change if the name
  reads as descriptive.

---

## The legal part

**Mark Checker is not a lawyer and does not give legal advice.** It is a first read that
tells you where you stand before you pay for an opinion. Use it to shorten the list of names
you take to an attorney, not to replace one.

### What the score is

The score is a prediction of *inherent distinctiveness* — one question out of the several
the trademark office asks. It comes from a model trained on past USPTO decisions. That means
it reflects how examiners have actually ruled, which is not always the same as what the
doctrine says in principle.

### What this is not

The app does **not**:

- **Search for conflicting marks.** A perfectly distinctive name is still refused if someone
  else already registered a similar one for similar goods. You must run a clearance search.
- **Assess acquired distinctiveness.** A descriptive name can still register if you prove
  buyers already connect it to you. The app cannot measure that.
- **Predict your examiner.** Two examiners can disagree on the same name.
- **Cover anything but the word.** Logos, colors, shapes, and sounds are outside its scope.
- **Advise on any country but the United States.** The TMEP and the TTAB are US authorities.

### Your data

The name and description you type go to the app's own model, and to a language model that
writes the explanation. Do not type anything you must keep confidential. The app stores no
account and keeps no history — close the page and the record is gone.

### Words you will meet

| Term | Meaning |
|---|---|
| **Mark** | The name you want to protect. |
| **Goods and services** | What you sell under that name. |
| **NICE class** | One of 45 international categories. You file in the class that matches what you sell. |
| **Distinctive** | The name can identify you as the source, so it can be registered. |
| **Descriptive** | The name describes the product, so it needs extra proof to register. |
| **TMEP** | The trademark office's own examination manual. |
| **TTAB** | The board that decides appeals. Its decisions are public. |
| **Pseudo mark** | The separate words inside a run-together name. |

You will meet these same words on the trademark office's own forms, so the app uses them
instead of friendlier substitutes.

---

Built by Vy Nguyen.
