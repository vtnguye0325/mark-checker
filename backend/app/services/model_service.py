from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

_DEFAULT_MODEL_DIR = str(Path(__file__).resolve().parents[2] / "model")

MAX_LEN = 256


# ---------------------------------------------------------------------------
# Model lifecycle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelHandle:
    """A loaded, eval-ready model + tokenizer bound to a device.

    Exists as a named type so inference functions can accept it as an
    injectable dependency — tests pass a fake handle, production code calls
    ``_load()`` to obtain the real one.
    """

    tokenizer: Any
    model: Any
    device: torch.device


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
def _load(model_dir: str) -> ModelHandle:
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
    return ModelHandle(tokenizer=tokenizer, model=model, device=device)


def _resolve_handle(model_dir: str | None, handle: ModelHandle | None) -> ModelHandle:
    """Return the provided handle, or load from model_dir (defaulting to env)."""
    if handle is not None:
        return handle
    return _load(model_dir if model_dir is not None else get_model_dir())


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------


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


def _score_batch(texts: list[str], handle: ModelHandle) -> list[float]:
    """Return prob_distinctive for each text in one forward pass."""
    enc = handle.tokenizer(
        texts,
        truncation=True,
        max_length=MAX_LEN,
        padding=True,
        return_tensors="pt",
    )
    enc = {k: v.to(handle.device) for k, v in enc.items()}
    with torch.no_grad():
        logits = handle.model(**enc).logits
    return torch.softmax(logits, dim=1)[:, 1].tolist()


def predict_one(
    text: str,
    model_dir: str | None = None,
    *,
    model_handle: ModelHandle | None = None,
) -> dict:
    """
    Args:
        text: Pre-formatted bert_input_processed string (use text_formatter.format_mark).
        model_dir: Local directory, or a Hugging Face repo id; defaults to ``MODEL_DIR``
            env var or the bundled ``backend/model`` path.
        model_handle: Pre-loaded ``ModelHandle`` for injection (e.g. in tests). When
            provided, ``model_dir`` is ignored.

    Returns:
        {"label": str, "prob_distinctive": float, "prob_not_distinctive": float}
        label is "distinctive" when prob_distinctive >= 0.5, else "not_distinctive".
    """
    handle = _resolve_handle(model_dir, model_handle)

    enc = handle.tokenizer(
        text,
        truncation=True,
        max_length=MAX_LEN,
        padding=False,
        return_tensors="pt",
    )
    enc = {k: v.to(handle.device) for k, v in enc.items()}

    with torch.no_grad():
        logits = handle.model(**enc).logits

    probs = torch.softmax(logits, dim=1)[0]
    prob_not = float(probs[0])
    prob_dis = float(probs[1])

    return {
        "label": "distinctive" if prob_dis >= 0.5 else "not_distinctive",
        "prob_distinctive": round(prob_dis, 4),
        "prob_not_distinctive": round(prob_not, 4),
    }


def explain_one(
    fields: list[str],
    model_dir: str | None = None,
    *,
    model_handle: ModelHandle | None = None,
) -> dict:
    """Field-level leave-one-out attribution via a single batched forward pass.

    For each of the 8 input fields, blanks it out and measures the change in
    prob_distinctive vs the baseline. attribution = baseline - masked_prob;
    positive means the field supports distinctiveness.

    Args:
        fields: The ordered field parts from ``text_formatter.format_mark().fields``
            (NOT the joined string). Operating on the parts directly keeps each
            attribution aligned with its field even when a user-supplied value
            (mark/description/translation/pseudo_mark) contains '. ' — re-splitting
            the joined string on '. ' would shift every field's value/attribution.
        model_dir: Local directory, HF repo id, or ``None`` for ``MODEL_DIR`` / default path.
        model_handle: Pre-loaded ``ModelHandle`` for injection (e.g. in tests). When
            provided, ``model_dir`` is ignored.

    Returns the same keys as predict_one plus an 'attributions' list sorted
    by abs(attribution) descending.
    """
    handle = _resolve_handle(model_dir, model_handle)

    text = ". ".join(fields)
    texts = [text]
    for i in range(len(fields)):
        masked = list(fields)
        masked[i] = ""
        texts.append(". ".join(masked))

    scores = _score_batch(texts, handle)
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
