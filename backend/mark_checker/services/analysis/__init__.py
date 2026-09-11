"""The analysis stage: retrieve doctrine, prompt the LLM, return the text.

``analyze_trademark`` is the only public name in this package.
"""

from __future__ import annotations

import logging
import time

from mark_checker.core.llm_client import LLM_MODEL, get_llm_client
from mark_checker.services.analysis.doctrine import _retrieve_doctrine
from mark_checker.services.analysis.prompts import _SYSTEM_PROMPT, _USER_TMPL
from mark_checker.services.analysis.tiers import _confidence_tier, _field_value
from mark_checker.services.text_formatter import NICE_DESCRIPTIONS

log = logging.getLogger(__name__)

__all__ = ["analyze_trademark"]


def analyze_trademark(
    mark: str,
    description: str,
    nice_class: int,
    label: str,
    prob_distinctive: float,
    attributions: list[dict],
) -> dict:
    # get_llm_client raises RuntimeError, naming the missing key, when the
    # provider is not configured. analyze() maps that to a 503.
    client = get_llm_client()

    attribution_lines = "\n".join(
        f"  {a['field']}: {a['value']}  ({a['attribution']:+.4f})" for a in attributions
    )

    t_start = time.perf_counter()
    log.info(
        "analyze start  mark=%r class=%d label=%s prob=%.2f",
        mark,
        nice_class,
        label,
        prob_distinctive,
    )

    t0 = time.perf_counter()
    doctrine_prefix, sources = _retrieve_doctrine(
        mark, description, str(nice_class), label, attributions
    )
    log.info(
        "RAG retrieval: %.2fs  tmep=%s ttab=%s",
        time.perf_counter() - t0,
        bool(sources.get("tmep")) if sources else False,
        bool(sources.get("ttab")) if sources else False,
    )
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
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        max_tokens=1000,
    )
    log.info(
        "LLM call: %.2fs  tokens_in=%s tokens_out=%s",
        time.perf_counter() - t1,
        getattr(response.usage, "prompt_tokens", "?"),
        getattr(response.usage, "completion_tokens", "?"),
    )
    log.info("analyze total: %.2fs", time.perf_counter() - t_start)
    log.debug("prompt system=%r user=%r", _SYSTEM_PROMPT, user_content)

    # A Gemini safety filter or an exhausted token budget returns content=None.
    # Raise a RuntimeError naming finish_reason; analyze() turns it into a 503
    # the user can act on, instead of an AttributeError and a 500.
    choice = response.choices[0]
    content = choice.message.content
    if not content or not content.strip():
        raise RuntimeError(
            f"the model returned an empty analysis (finish_reason={choice.finish_reason})"
        )

    return {
        "analysis": content.strip(),
        "sources": sources or None,
    }
