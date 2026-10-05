"""The analysis stage: retrieve doctrine, prompt the LLM, return the text.

``analyze_trademark`` is the only public name in this package.
"""

from __future__ import annotations

from mark_checker.core.llm_client import get_llm_client
from mark_checker.services.analysis.graph import run_analysis
from mark_checker.services.analysis.tiers import _confidence_tier

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
    # provider is not configured. analyze() maps that to a 503. Call it here,
    # before the graph starts, so a missing key fails fast.
    get_llm_client()

    return run_analysis(
        mark,
        description,
        nice_class,
        label,
        prob_distinctive,
        attributions,
        _confidence_tier(prob_distinctive),
    )
