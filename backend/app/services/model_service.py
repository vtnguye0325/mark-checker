from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

_DEFAULT_MODEL_DIR = str(Path(__file__).resolve().parents[2] / "model")

MAX_LEN = 256


def get_model_dir() -> str:
    """Resolve the model directory: ``MODEL_DIR`` env var or the bundled path."""
    return os.getenv("MODEL_DIR", _DEFAULT_MODEL_DIR)


def warm_up() -> None:
    """Eagerly load the model so the first request doesn't pay cold-start cost.

    Called from the FastAPI lifespan startup; a load failure here crashes the
    worker at boot (surfaced via /ready) instead of on a user's first request.
    """
    _load(get_model_dir())


def is_loaded() -> bool:
    """True once the model has been loaded into the cache."""
    return _load.cache_info().currsize > 0


@lru_cache(maxsize=1)
def _load(model_dir: str):
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")

    tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=True, trust_remote_code=True)
    try:
        model = AutoModelForSequenceClassification.from_pretrained(
            model_dir,
            num_labels=2,
            trust_remote_code=True,
            attn_implementation="eager",
            reference_compile=False,
        )
    except TypeError:
        model = AutoModelForSequenceClassification.from_pretrained(
            model_dir,
            num_labels=2,
            trust_remote_code=True,
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    return tokenizer, model, device


_FIELD_LABELS = [
    "Mark",
    "Goods & Services",
    "Translation",
    "WordNet Flag",
    "Mark Length",
    "NICE Category",
    "NICE Description",
    "Pseudo Mark",
]


def _score_batch(texts: list[str], model_dir: str) -> list[float]:
    """Return prob_distinctive for each text in one forward pass."""
    tokenizer, model, device = _load(model_dir)
    enc = tokenizer(
        texts,
        truncation=True,
        max_length=MAX_LEN,
        padding=True,
        return_tensors="pt",
    )
    enc = {k: v.to(device) for k, v in enc.items()}
    with torch.no_grad():
        logits = model(**enc).logits
    return torch.softmax(logits, dim=1)[:, 1].tolist()


def predict_one(text: str, model_dir: str | None = None) -> dict:
    """
    Args:
        text: Pre-formatted bert_input_processed string (use text_formatter.format_input).
        model_dir: Local directory, or a Hugging Face repo id passed to ``from_pretrained``;
            defaults to ``MODEL_DIR`` env var or the bundled ``backend/model`` path.

    Returns:
        {"label": str, "prob_distinctive": float, "prob_not_distinctive": float}
        label is "distinctive" when prob_distinctive >= 0.5, else "not_distinctive".
    """
    if model_dir is None:
        model_dir = get_model_dir()

    tokenizer, model, device = _load(model_dir)

    enc = tokenizer(
        text,
        truncation=True,
        max_length=MAX_LEN,
        padding=False,
        return_tensors="pt",
    )
    enc = {k: v.to(device) for k, v in enc.items()}

    with torch.no_grad():
        logits = model(**enc).logits

    probs = torch.softmax(logits, dim=1)[0]
    prob_not = float(probs[0])
    prob_dis = float(probs[1])

    return {
        "label": "distinctive" if prob_dis >= 0.5 else "not_distinctive",
        "prob_distinctive": round(prob_dis, 4),
        "prob_not_distinctive": round(prob_not, 4),
    }


def explain_one(fields: list[str], model_dir: str | None = None) -> dict:
    """
    Field-level leave-one-out attribution via a single batched forward pass.

    For each of the 8 input fields, blanks it out and measures the change in
    prob_distinctive vs the baseline. attribution = baseline - masked_prob;
    positive means the field supports distinctiveness.

    Args:
        fields: The ordered field parts from ``text_formatter.format_fields``
            (NOT the joined string). Operating on the parts directly keeps each
            attribution aligned with its field even when a user-supplied value
            (mark/description/translation/pseudo_mark) contains '. ' — re-splitting
            the joined string on '. ' would shift every field's value/attribution.
        model_dir: Local directory, HF repo id, or ``None`` for ``MODEL_DIR`` / default path.

    Returns the same keys as predict_one plus an 'attributions' list sorted
    by abs(attribution) descending.
    """
    if model_dir is None:
        model_dir = get_model_dir()

    text = ". ".join(fields)
    texts = [text]
    for i in range(len(fields)):
        masked = list(fields)
        masked[i] = ""
        texts.append(". ".join(masked))

    scores = _score_batch(texts, model_dir)
    baseline = scores[0]

    attributions = []
    for i, label in enumerate(_FIELD_LABELS):
        masked_prob = scores[i + 1] if i + 1 < len(scores) else baseline
        attributions.append(
            {
                "field": label,
                "value": fields[i] if i < len(fields) else "",
                "attribution": round(baseline - masked_prob, 4),
            }
        )

    attributions.sort(key=lambda x: abs(x["attribution"]), reverse=True)

    return {
        "label": "distinctive" if baseline >= 0.5 else "not_distinctive",
        "prob_distinctive": round(baseline, 4),
        "prob_not_distinctive": round(1.0 - baseline, 4),
        "attributions": attributions,
    }
