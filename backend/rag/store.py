from __future__ import annotations

import chromadb
from pathlib import Path

_CHROMA_PATH = Path(__file__).parent / "chroma_db"

_client: chromadb.PersistentClient | None = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(_CHROMA_PATH))
    return _client


def get_tmep_collection() -> chromadb.Collection:
    return _get_client().get_or_create_collection(
        "tmep", metadata={"hnsw:space": "cosine"}
    )


def get_ttab_collection() -> chromadb.Collection:
    return _get_client().get_or_create_collection(
        "ttab", metadata={"hnsw:space": "cosine"}
    )


def get_statute_collection() -> chromadb.Collection:
    return _get_client().get_or_create_collection(
        "statute", metadata={"hnsw:space": "cosine"}
    )


def reset_collections() -> None:
    client = _get_client()
    for name in ("tmep", "ttab", "statute"):
        try:
            client.delete_collection(name)
        except Exception:
            pass
