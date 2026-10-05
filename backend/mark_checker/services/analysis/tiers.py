"""Small pure helpers that shape the prompt inputs."""

from __future__ import annotations


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
