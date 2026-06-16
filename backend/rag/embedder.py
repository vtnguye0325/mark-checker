from __future__ import annotations

import os

import numpy as np

_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
_MODEL_NAME = "BAAI/bge-base-en-v1.5"

# Set EMBEDDER=hf_api in env to use HuggingFace Inference API instead of local model.
# Requires HF_TOKEN env var. Defaults to local (CPU/GPU auto-selected).
_USE_HF_API = os.environ.get("EMBEDDER", "local") == "hf_api"


# ---------------------------------------------------------------------------
# Local path (default): sentence-transformers, auto-selects CPU or GPU
# ---------------------------------------------------------------------------
_local_model = None


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(_MODEL_NAME)
    return _local_model


def _local_embed(texts: list[str]) -> list[list[float]]:
    return _get_local_model().encode(texts, normalize_embeddings=True).tolist()


# ---------------------------------------------------------------------------
# HF Inference API path: no local model, needs HF_TOKEN
# ---------------------------------------------------------------------------
_hf_client = None


def _get_hf_client():
    global _hf_client
    if _hf_client is None:
        from huggingface_hub import InferenceClient

        _hf_client = InferenceClient(token=os.environ["HF_TOKEN"])
    return _hf_client


def _hf_embed(texts: list[str]) -> list[list[float]]:
    client = _get_hf_client()
    result = client.feature_extraction(texts, model=_MODEL_NAME)
    arr = np.array(result, dtype=np.float32)
    # Normalize to unit vectors for cosine similarity (matches local behaviour)
    norms = np.linalg.norm(arr, axis=-1, keepdims=True)
    arr = arr / np.maximum(norms, 1e-10)
    return arr.tolist()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def embed_documents(texts: list[str]) -> list[list[float]]:
    if _USE_HF_API:
        return _hf_embed(texts)
    return _local_embed(texts)


def embed_query(text: str) -> list[float]:
    prefixed = _QUERY_PREFIX + text
    if _USE_HF_API:
        return _hf_embed([prefixed])[0]
    return _local_embed([prefixed])[0]
