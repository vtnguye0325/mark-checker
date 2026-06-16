from __future__ import annotations

import logging
import os
import time

from openai import OpenAI

from app.services.text_formatter import NICE_DESCRIPTIONS

log = logging.getLogger(__name__)

_DOCTRINE_SECTION = """\
LEGAL DOCTRINE AND ILLUSTRATIVE CASES (retrieved from TMEP and TTAB):
{context}

Ground your spectrum placement and signals analysis in the doctrine above.
When citing a TMEP section use "TMEP §XXXX". When citing a case use the mark name.

---

"""

_SYSTEM_PROMPT = """\
You are a trademark advisor helping a small business owner understand an AI classifier's assessment of their trademark application.

Write your response in exactly these four sections:

**What the model found**
State the prediction and confidence tier in plain English. Explain what the confidence tier means practically:
- High confidence: the classifier sees this as a clear-cut case — the mark's relationship to its goods is either obviously distinctive or obviously descriptive.
- Moderate confidence: the mark has some distinctive qualities but also some signals that could complicate registration.
- Uncertain: the mark sits in a gray zone where reasonable experts could disagree; human legal judgment is essential here.
Do not present this as a legal ruling or guarantee.

**Where this mark sits on the trademark spectrum**
The trademark spectrum runs from strongest to weakest protection: fanciful (invented words) → arbitrary (real words unrelated to the goods) → suggestive (hints at the goods without describing them) → descriptive (directly describes the goods) → generic (the common name for the goods, never protectable).
Identify the two most plausible tiers this mark could fall into. For each tier, explain in one sentence what specific characteristic of THIS mark and THIS goods/services description supports that placement. Format each tier as a bullet on its own line: `- **TierName** — your one-sentence explanation.` (e.g., `- **Arbitrary** — the word has no connection to the goods.`) Then in a short paragraph after the bullets, explain what would push the mark toward the stronger tier vs. the weaker one — grounding this in the actual relationship between the mark text and the goods/services description. If legal doctrine was retrieved, cite the most relevant TMEP section (e.g., TMEP §1209.01) to anchor the tier placement.

**Why the classifier leaned this way — key signals**
Explain the signals in 2–3 short paragraphs (separate each with a blank line). Each paragraph should focus on one key signal. Start with the mark name: what does the word itself suggest — is it invented, a common word, or does it describe something about the product? Then explain how the goods/services description either reinforced or complicated that signal. Use concrete trademark reasoning: for example, "the word X pushed toward distinctive because it has no obvious connection to the goods in its class — a consumer seeing it on the shelf would not immediately understand what the product is." If the mark is in the dictionary or has a translation, explain specifically how that factored in.

**What to do next**
One concrete sentence based on confidence tier:
- High confidence distinctive → this looks like a strong registration candidate; consider filing and consulting a trademark attorney to confirm the classification.
- High confidence non-distinctive → significant descriptiveness risk was flagged; consult a trademark attorney before filing to explore whether acquired distinctiveness or a different mark formulation could overcome this.
- Uncertain → the outcome is genuinely unclear; a trademark attorney's opinion before filing is strongly recommended given the risk of a descriptiveness refusal.

---

Rules:
- Keep the whole response under ~400 words. Be clear and concise; never pad.
- Headers: exactly `**Section Title**` on its own line — no `#` markdown headings.
- Spectrum section: exactly two bullets `- **TierName** — one sentence.` before any follow-up paragraph.
- TMEP citations: cite only section numbers that literally appear in the retrieved doctrine above. Never invent or recall one from memory. If none fit, write "no directly applicable TMEP section was retrieved" instead of guessing.
- No jargon: no ML terms ("SHAP," "logits," "fine-tuned," "probability," "feature weight"); gloss any legal term in plain English in parentheses on first use.
- Do not quote the raw confidence percentage — translate it to the tier (high / moderate / uncertain) in plain words. Field labels from the user message (e.g. "CONFIDENCE TIER", "IN DICTIONARY (WordNet)") are internal inputs — never echo them verbatim.
- Never assert a tier as fact ("this mark appears to be…"), never guarantee registration, never predict examiner behavior with certainty.\
"""

_USER_TMPL = """\
TRADEMARK: {mark}
GOODS/SERVICES: {description}
NICE CLASS: {nice_class} — {nice_class_description}
PREDICTION: {label} ({prob_pct}% confidence)
CONFIDENCE TIER: {confidence_tier}
TRANSLATION STATUS: {translation_status}
IN DICTIONARY (WordNet): {wordnet_flag}

SIGNALS (positive = supports distinctiveness, negative = opposes it):
{attributions_block}\
"""


def analyze_trademark(
    mark: str,
    description: str,
    nice_class: int,
    label: str,
    prob_distinctive: float,
    attributions: list[dict],
) -> dict:
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
        f"  {a['field']}: {a['value']}  ({a['attribution']:+.4f})" for a in attributions
    )

    t_start = time.perf_counter()
    log.debug("analyze start  mark=%r", mark)

    t0 = time.perf_counter()
    doctrine_prefix, sources = _retrieve_doctrine(
        mark, description, str(nice_class), label, attributions
    )
    log.debug("RAG retrieval: %.2fs", time.perf_counter() - t0)
    user_content = doctrine_prefix + _USER_TMPL.format(
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

    t1 = time.perf_counter()
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        max_tokens=1000,
    )
    log.debug("final LLM call: %.2fs", time.perf_counter() - t1)
    log.debug("analyze total: %.2fs", time.perf_counter() - t_start)

    return {
        "analysis": response.choices[0].message.content.strip(),
        "sources": sources or None,
        "prompt": {"system": _SYSTEM_PROMPT, "user": user_content},
    }


def _retrieve_doctrine(
    mark: str,
    description: str,
    nice_class: str,
    label: str,
    attributions: list[dict],
) -> tuple[str, dict]:
    """Return (doctrine_prefix, sources_dict). Both empty/None on failure."""
    try:
        try:
            from rag.retriever import format_context, retrieve
        except ImportError:
            from backend.rag.retriever import format_context, retrieve

        attr_str = ", ".join(
            f"{a['field']}: {a['attribution']:+.2f}"
            for a in attributions[:5]
            if a.get("field") not in ("Translation", "WordNet Flag")
        )
        result = retrieve(mark, description, nice_class, label, attr_str)
        if not result["tmep"] and not result["ttab"] and not result.get("statute"):
            return "", {}
        return _DOCTRINE_SECTION.format(context=format_context(result)), result
    except Exception:
        log.warning("RAG retrieval failed — proceeding without doctrine context", exc_info=True)
        return "", {}


def _confidence_tier(prob_distinctive: float) -> str:
    # Distance from the 0.5 decision boundary in either direction.
    margin = abs(prob_distinctive - 0.5)
    if margin >= 0.4:
        return "high"
    if margin >= 0.2:
        return "moderate"
    return "uncertain"


def _field_value(attributions: list[dict], field: str, default: str) -> str:
    for a in attributions:
        if a.get("field") == field:
            return a.get("value") or default
    return default
