"""
Full RAG retrieval pipeline.

Delegates to agent.py for agentic tool-calling retrieval,
then formats collected chunks for injection into the analysis prompt.
"""

from rag.agent import run_agent


def retrieve(
    mark: str,
    description: str,
    nice_class: str,
    label: str,
    attributions: str,
) -> dict:
    return run_agent(mark, description, nice_class, label, attributions)


def format_context(retrieval_result: dict) -> str:
    lines = ["LEGAL DOCTRINE:"]
    for i, chunk in enumerate(retrieval_result["tmep"], 1):
        lines.append(f"[{i}] {chunk['text']}")

    statute_chunks = retrieval_result.get("statute", [])
    if statute_chunks:
        lines.append("\nSTATUTORY AUTHORITY:")
        offset = len(retrieval_result["tmep"])
        for i, chunk in enumerate(statute_chunks, offset + 1):
            meta = chunk["metadata"]
            lines.append(f"[{i}] {meta.get('citation', '')} — {chunk['text']}")

    lines.append("\nILLUSTRATIVE CASES:")
    offset = len(retrieval_result["tmep"]) + len(statute_chunks)
    for i, chunk in enumerate(retrieval_result["ttab"], offset + 1):
        meta = chunk["metadata"]
        prefix = f"{meta.get('mark', '')} (NC{meta.get('nice_class', '')}, {meta.get('outcome', '')})"
        lines.append(f"[{i}] {prefix} — {chunk['text']}")

    return "\n".join(lines)
