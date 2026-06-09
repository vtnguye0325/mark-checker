"""Integration tests for model_service — loads the real model."""

from __future__ import annotations

import math

from app.services import model_service
from app.services.model_service import explain_one, predict_one
from app.services.text_formatter import format_input


def _predict(mark: str, description: str, nice_class: int) -> dict:
    text = format_input(mark, description, nice_class)
    return predict_one(text)


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------


def test_predict_one_returns_required_keys():
    result = _predict("APPLE", "computers", 9)
    assert set(result.keys()) == {"label", "prob_distinctive", "prob_not_distinctive"}


def test_predict_one_label_is_valid_string():
    result = _predict("APPLE", "computers", 9)
    assert result["label"] in {"distinctive", "not_distinctive"}


def test_predict_one_probs_in_unit_interval():
    result = _predict("APPLE", "computers", 9)
    assert 0.0 <= result["prob_distinctive"] <= 1.0
    assert 0.0 <= result["prob_not_distinctive"] <= 1.0


def test_predict_one_probs_sum_to_one():
    result = _predict("APPLE", "computers", 9)
    total = result["prob_distinctive"] + result["prob_not_distinctive"]
    assert math.isclose(total, 1.0, abs_tol=0.01)


def test_predict_one_label_consistent_with_prob():
    result = _predict("APPLE", "computers", 9)
    if result["prob_distinctive"] >= 0.5:
        assert result["label"] == "distinctive"
    else:
        assert result["label"] == "not_distinctive"


# ---------------------------------------------------------------------------
# Canonical examples — sanity check
# ---------------------------------------------------------------------------


def test_apple_computers_is_distinctive():
    result = _predict("APPLE", "computers and computer software", 9)
    assert result["label"] == "distinctive"
    assert result["prob_distinctive"] > 0.7


def test_coined_mark_is_distinctive():
    # Fanciful / coined marks should score high
    result = _predict("XYLOQUARTZ", "industrial cleaning products", 3)
    assert result["label"] == "distinctive"


# ---------------------------------------------------------------------------
# explain_one — field/attribution alignment (no model: scoring is mocked)
# ---------------------------------------------------------------------------

_FIELDS = [
    "APPLE",
    "Sells phones. Also tablets. And cases.",  # contains '. ' on purpose
    "no translation required",
    "mark absent in Wordnet",
    "mark length is 1",
    "NICE category is 9",
    "computers and computer software",
    "no Pseudo mark",
]


def test_explain_one_aligns_each_field_despite_periods(monkeypatch):
    # Baseline + one masked variant per field. Give each masked variant a
    # distinct score so a misalignment would be detectable.
    def fake_score_batch(texts, model_dir):
        assert len(texts) == len(_FIELDS) + 1  # baseline + 8 masks, no over-splitting
        return [0.90] + [0.01 * i for i in range(len(texts) - 1)]

    monkeypatch.setattr(model_service, "_score_batch", fake_score_batch)

    result = explain_one(_FIELDS)
    assert len(result["attributions"]) == 8

    by_field = {a["field"]: a["value"] for a in result["attributions"]}
    # The period-laden description stays whole and on the right field.
    assert by_field["Goods & Services"] == "Sells phones. Also tablets. And cases."
    assert by_field["Mark"] == "APPLE"
    assert by_field["Pseudo Mark"] == "no Pseudo mark"


def test_explain_one_masks_each_field_independently(monkeypatch):
    # Record what gets masked: the i-th masked text must blank exactly field i.
    seen = []

    def fake_score_batch(texts, model_dir):
        seen.extend(texts)
        return [0.5] * len(texts)

    monkeypatch.setattr(model_service, "_score_batch", fake_score_batch)
    explain_one(_FIELDS)

    # seen[0] is baseline; seen[i+1] is field i blanked.
    for i in range(len(_FIELDS)):
        expected = list(_FIELDS)
        expected[i] = ""
        assert seen[i + 1] == ". ".join(expected)
