"""
Full RAG retrieval pipeline.

1. Generate HyDE paragraph (cheap LLM call)
2. Embed it with bge-base-en-v1.5
3. Query TMEP and TTAB collections in parallel
4. Return merged context dict
"""

import os
from concurrent.futures import ThreadPoolExecutor

from backend.rag.hyde import generate_hyde_paragraph
from backend.rag.embedder import embed_query
from backend.rag.store import get_tmep_collection, get_ttab_collection

_TMEP_N = int(os.environ.get("RAG_TMEP_N_RESULTS", "3"))
_TTAB_N = int(os.environ.get("RAG_TTAB_N_RESULTS", "2"))


def _query_collection(collection, embedding: list[float], n: int) -> list[dict]:
    results = collection.query(query_embeddings=[embedding], n_results=n)
    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        chunks.append({"text": doc, "metadata": meta})
    return chunks


def retrieve(
    mark: str,
    description: str,
    nice_class: str,
    label: str,
    attributions: str,
) -> dict:
    hypothesis = generate_hyde_paragraph(mark, description, nice_class, label, attributions)
    embedding = embed_query(hypothesis)

    tmep_col = get_tmep_collection()
    ttab_col = get_ttab_collection()

    with ThreadPoolExecutor(max_workers=2) as pool:
        tmep_future = pool.submit(_query_collection, tmep_col, embedding, _TMEP_N)
        ttab_future = pool.submit(_query_collection, ttab_col, embedding, _TTAB_N)
        tmep_chunks = tmep_future.result()
        ttab_chunks = ttab_future.result()

    return {
        "hypothesis": hypothesis,
        "tmep": tmep_chunks,
        "ttab": ttab_chunks,
    }


def format_context(retrieval_result: dict) -> str:
    lines = ["LEGAL DOCTRINE:"]
    for i, chunk in enumerate(retrieval_result["tmep"], 1):
        lines.append(f"[{i}] {chunk['text']}")

    lines.append("\nILLUSTRATIVE CASES:")
    offset = len(retrieval_result["tmep"])
    for i, chunk in enumerate(retrieval_result["ttab"], offset + 1):
        meta = chunk["metadata"]
        prefix = f"{meta.get('mark', '')} (NC{meta.get('nice_class', '')}, {meta.get('outcome', '')})"
        lines.append(f"[{i}] {prefix} — {chunk['text']}")

    return "\n".join(lines)
