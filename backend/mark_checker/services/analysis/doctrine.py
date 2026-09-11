"""Doctrine retrieval for the analysis stage.

The retrieval is best-effort: a failure returns no doctrine, and the
analysis runs on the classifier signals alone.
"""

from __future__ import annotations

import logging

from mark_checker.services.analysis.prompts import _DOCTRINE_SECTION

log = logging.getLogger(__name__)


def _retrieve_doctrine(
    mark: str,
    description: str,
    nice_class: str,
    label: str,
    attributions: list[dict],
) -> tuple[str, dict]:
    """Return (doctrine_prefix, sources_dict). Both empty/None on failure."""
    try:
        # Imported here, not at module import time, so loading the API does
        # not pull ChromaDB and the embedding model into memory.
        from mark_checker.rag.retriever import format_context, retrieve

        attr_str = ", ".join(
            f"{a['field']}: {a['attribution']:+.2f}"
            for a in attributions[:5]
            if a.get("field") not in ("Translation", "WordNet Flag")
        )
        result = retrieve(mark, description, nice_class, label, attr_str)
        if not result["tmep"] and not result["ttab"]:
            return "", {}
        return _DOCTRINE_SECTION.format(context=format_context(result)), result
    except Exception:
        log.warning("RAG retrieval failed — proceeding without doctrine context", exc_info=True)
        return "", {}
