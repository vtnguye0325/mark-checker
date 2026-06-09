from __future__ import annotations

import os

from openai import OpenAI

from app.services.text_formatter import NICE_DESCRIPTIONS

_PROMPT_TEMPLATE = """\
You are a trademark advisor helping a small business owner understand an AI model's assessment of their trademark application.

TRADEMARK: {mark}
GOODS/SERVICES: {description}
NICE CLASS: {nice_class} — {nice_class_description}
PREDICTION: {label} ({prob_pct}% confidence)
CONFIDENCE TIER: {confidence_tier}
TRANSLATION STATUS: {translation_status}
IN DICTIONARY (WordNet): {wordnet_flag}

FEATURE ATTRIBUTIONS (positive = supports distinctiveness, negative = opposes it):
{attributions_block}

---

Write your response in exactly these four sections:

**What the model found**
State the prediction and confidence tier in plain English. Explain what the confidence tier means practically:
- High confidence: the model sees this as a clear-cut case — the mark's relationship to its goods is either obviously distinctive or obviously descriptive.
- Moderate confidence: the mark has some distinctive qualities but also some signals that could complicate registration.
- Uncertain: the mark sits in a gray zone where reasonable experts could disagree; human legal judgment is essential here.
Do not present this as a legal ruling or guarantee.

**Where this mark sits on the trademark spectrum**
The trademark spectrum runs from strongest to weakest protection: fanciful (invented words) → arbitrary (real words unrelated to the goods) → suggestive (hints at the goods without describing them) → descriptive (directly describes the goods) → generic (the common name for the goods, never protectable).
Based on the attributions, identify the two most plausible tiers this mark could fall into. For each tier, explain in one sentence what specific characteristic of THIS mark and THIS goods/services description supports that placement. Format each tier as a bullet on its own line: `- **TierName** — your one-sentence explanation.` (e.g., `- **Arbitrary** — the word has no connection to the goods.`) Then in a short paragraph after the bullets, explain what would push the mark toward the stronger tier vs. the weaker one — grounding this in the actual relationship between the mark text and the goods/services description, not general definitions.

**Why the model leaned this way — key signals**
Explain the attribution signals in 2–3 short paragraphs (separate each paragraph with a blank line). Each paragraph should focus on one key signal. Start with the mark name: what does the word itself suggest — is it invented, a common word, or does it describe something about the product? Then explain how the goods/services description either reinforced or complicated that signal. Use concrete trademark reasoning: for example, "the word X pushed toward distinctive because it has no obvious connection to {nice_class_description} — a consumer seeing it on a {description} shelf would not immediately understand what the product is." If the mark is in the dictionary or has a translation, explain specifically how that factored in. Never use the words "SHAP," "attribution score," "feature weight," or "model."

**What to do next**
One concrete sentence based on confidence tier:
- High confidence distinctive → the model sees a strong registration candidate; consider filing and consulting a trademark attorney to confirm the classification.
- High confidence non-distinctive → the model flagged significant descriptiveness risk; consult a trademark attorney before filing to explore whether acquired distinctiveness or a different mark formulation could overcome this.
- Uncertain → the outcome is genuinely unclear; a trademark attorney's opinion before filing is strongly recommended given the risk of a descriptiveness refusal.

---

Rules:
- Use exactly `**Section Title**` (bold text on its own line) for each section header — no markdown headings (no # symbols).
- The spectrum section must contain exactly two bullet lines in the format `- **TierName** — one sentence.` before any follow-up paragraph.
- There is no word limit, as long as the response is clear and concise, but informative.
- Never use ML jargon: no "SHAP," "logits," "fine-tuned," "classifier," "probability," "attribution," or "model weight."
- Never use legal jargon without an immediate plain-English gloss in parentheses.
- Never assert a tier as fact — frame as "this mark appears to be" or "this looks more like."
- Never guarantee registration or predict examiner behavior with certainty.
- The spectrum section must reference the actual mark text and goods/services — no generic definitions.\
"""


def analyze_trademark(
    mark: str,
    description: str,
    nice_class: int,
    label: str,
    prob_distinctive: float,
    attributions: list[dict],
) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set")

    # Bound the call so a slow/hung DeepSeek response can't tie up a worker
    # thread indefinitely, and cap retries so a paid endpoint can't fan out.
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
        timeout=30.0,
        max_retries=1,
    )

    attribution_lines = "\n".join(
        f"  {a['field']}: {a['value']!r}  (score: {a['attribution']:+.4f})" for a in attributions
    )

    prompt = _PROMPT_TEMPLATE.format(
        mark=mark,
        description=description,
        nice_class=nice_class,
        nice_class_description=NICE_DESCRIPTIONS.get(nice_class, "unknown class"),
        label=label.replace("_", " "),
        prob_pct=round(prob_distinctive * 100),
        confidence_tier=_confidence_tier(prob_distinctive),
        translation_status=_field_value(attributions, "Translation", "no translation required"),
        wordnet_flag=_field_value(attributions, "WordNet Flag", "mark absent in Wordnet"),
        attributions_block=attribution_lines,
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=700,
    )

    return response.choices[0].message.content.strip()


def _confidence_tier(prob_distinctive: float) -> str:
    # Distance from the 0.5 decision boundary in either direction.
    margin = abs(prob_distinctive - 0.5)
    if margin >= 0.4:
        return "high confidence"
    if margin >= 0.2:
        return "moderate confidence"
    return "low confidence (uncertain)"


def _field_value(attributions: list[dict], field: str, default: str) -> str:
    for a in attributions:
        if a.get("field") == field:
            return a.get("value") or default
    return default
