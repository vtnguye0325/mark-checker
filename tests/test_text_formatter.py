"""Unit tests for text_formatter — no model required."""

from __future__ import annotations

import pytest


from app.services.text_formatter import (
    NICE_DESCRIPTIONS,
    _pseudo_mark,
    _translation,
    _wordnet_flag,
    format_fields,
    format_input,
)


# ---------------------------------------------------------------------------
# format_input — structure
# ---------------------------------------------------------------------------


def test_format_input_has_eight_fields():
    result = format_input("APPLE", "computers", 9)
    parts = result.split(". ")
    assert len(parts) == 8


def test_format_input_first_field_is_mark():
    result = format_input("APPLE", "computers", 9)
    assert result.startswith("APPLE")


def test_format_input_strips_whitespace():
    result = format_input("  APPLE  ", "  computers  ", 9)
    assert result.startswith("APPLE")
    parts = result.split(". ")
    assert parts[1] == "computers"


def test_format_input_nice_category_field():
    result = format_input("NIKE", "footwear", 25)
    assert "NICE category is 25" in result


def test_format_input_mark_length_field():
    result = format_input("TWO WORDS", "clothing", 25)
    assert "mark length is 2" in result


def test_format_input_nice_description_embedded():
    result = format_input("NIKE", "footwear", 25)
    assert NICE_DESCRIPTIONS[25] in result


def test_format_input_unknown_nice_class_empty_description():
    # nice_class 99 doesn't exist; NICE_DESCRIPTIONS.get returns ""
    result = format_input("MARK", "goods", 99)
    parts = result.split(". ")
    assert parts[6] == ""


# ---------------------------------------------------------------------------
# format_fields — boundaries (drives the attribution alignment fix)
# ---------------------------------------------------------------------------


def test_format_fields_returns_eight():
    assert len(format_fields("APPLE", "computers", 9)) == 8


def test_format_fields_join_equals_format_input():
    args = ("APPLE", "computers and software", 9, "la pomme", "apple")
    assert ". ".join(format_fields(*args)) == format_input(*args)


def test_format_fields_keeps_period_laden_description_intact():
    # A description containing '. ' must stay a SINGLE field — this is exactly
    # what would have shifted every field if attribution re-split the joined
    # string on '. '.
    desc = "Sells phones. Also tablets. And cases."
    fields = format_fields("APPLE", desc, 9)
    assert len(fields) == 8
    assert fields[0] == "APPLE"
    assert fields[1] == desc


# ---------------------------------------------------------------------------
# _translation
# ---------------------------------------------------------------------------


def test_translation_empty_returns_default():
    assert _translation("") == "no translation required"


def test_translation_whitespace_returns_default():
    assert _translation("   ") == "no translation required"


def test_translation_returns_verbatim():
    assert _translation("apple") == "apple"


def test_translation_strips_surrounding_whitespace():
    assert _translation("  la pomme  ") == "la pomme"


# ---------------------------------------------------------------------------
# _pseudo_mark
# ---------------------------------------------------------------------------


def test_pseudo_mark_explicit_input():
    assert _pseudo_mark("apple") == "Pseudo mark is apple"


def test_pseudo_mark_empty_means_none():
    # Empty input means there is no pseudo mark — no derivation from the mark.
    assert _pseudo_mark("") == "no Pseudo mark"


def test_pseudo_mark_whitespace_only_means_none():
    assert _pseudo_mark("   ") == "no Pseudo mark"


def test_pseudo_mark_strips_surrounding_whitespace():
    assert _pseudo_mark("  my mark  ") == "Pseudo mark is my mark"


# ---------------------------------------------------------------------------
# _wordnet_flag
# ---------------------------------------------------------------------------


def test_wordnet_flag_common_english_word():
    assert _wordnet_flag("apple") == "mark present in Wordnet"


def test_wordnet_flag_all_caps_common_word():
    # lowercasing should still find the word
    assert _wordnet_flag("APPLE") == "mark present in Wordnet"


def test_wordnet_flag_multi_word_one_real_one_invented():
    # "computer" is in WordNet; "xyzzy" is not — any() should return True
    assert _wordnet_flag("computer xyzzy") == "mark present in Wordnet"


def test_wordnet_flag_invented_word_absent():
    assert _wordnet_flag("xyzzyquux") == "mark absent in Wordnet"


def test_wordnet_flag_all_invented_tokens():
    assert _wordnet_flag("xyzzyquux blorfnik") == "mark absent in Wordnet"


def test_wordnet_flag_raises_when_unavailable():
    # WordNet is baked into the image; a genuinely missing corpus is a
    # deployment error and must fail loudly, not silently return "absent"
    # (which would corrupt the WordNet field of every prediction).
    import sys

    from app.services import text_formatter as tf

    tf._wordnet.cache_clear()
    saved = sys.modules.get("nltk.corpus", ...)
    sys.modules["nltk.corpus"] = (
        None  # makes `from nltk.corpus import wordnet` raise ImportError
    )
    try:
        with pytest.raises(RuntimeError, match="WordNet"):
            _wordnet_flag("apple")
    finally:
        if saved is ...:
            sys.modules.pop("nltk.corpus", None)
        else:
            sys.modules["nltk.corpus"] = saved
        tf._wordnet.cache_clear()  # reset so later tests reload the real corpus


# ---------------------------------------------------------------------------
# NICE_DESCRIPTIONS completeness
# ---------------------------------------------------------------------------


def test_all_45_nice_classes_present():
    assert set(NICE_DESCRIPTIONS.keys()) == set(range(1, 46))


def test_nice_descriptions_non_empty():
    for cls, desc in NICE_DESCRIPTIONS.items():
        assert len(desc) > 0, f"Class {cls} description is empty"
