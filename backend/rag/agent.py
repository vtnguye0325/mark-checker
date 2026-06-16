"""
Agentic RAG — DeepSeek tool-calling loop.

Agent receives mark info and two tools (search_tmep, search_ttab).
Statute search is reserved for the chatbot; not wired here.
Runs up to MAX_ROUNDS, collecting and deduplicating chunks.
Stops early when agent returns without a tool call.
"""

from __future__ import annotations

import json
import logging
import os
import time

from openai import OpenAI

from rag.embedder import embed_query
from rag.store import get_tmep_collection, get_ttab_collection

log = logging.getLogger(__name__)

MAX_ROUNDS = 2
_TMEP_N = int(os.environ.get("RAG_TMEP_N_RESULTS", "3"))
_TTAB_N = int(os.environ.get("RAG_TTAB_N_RESULTS", "2"))

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_tmep",
            "description": (
                "Search the Trademark Manual of Examining Procedure (TMEP) for relevant "
                "doctrine sections. Prioritize §§1209-1213 for distinctiveness questions. "
                "Use precise Abercrombie vocabulary in the query."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Legal doctrine query. Examples: "
                            "'merely descriptive ingredient name refusal section 2(e)(1)', "
                            "'surname primarily merely a surname primary significance', "
                            "'acquired distinctiveness secondary meaning five years use'"
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_ttab",
            "description": (
                "Search TTAB ex parte decisions and landmark court opinions for illustrative "
                "examples of trademark doctrine applied to real marks."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Query describing the mark type and issue. Example: "
                            "'compound descriptive term ingredient name not distinctive affirmed'"
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },
]

_SYSTEM = """\
You are a trademark doctrine retrieval agent. Find the most relevant TMEP sections \
and TTAB decisions for a distinctiveness analysis under the Abercrombie spectrum.

Strategy:
- In your FIRST response, call both tools in parallel: search_tmep (doctrine) and \
search_ttab (illustrative case).
- If and only if the tmep results are clearly off-target, call search_tmep once more \
with a refined query. Do NOT repeat search_ttab.
- After your first response (or one refinement at most), return your final answer \
with NO further tool calls. Do not loop.

Use exact trademark vocabulary: fanciful, arbitrary, suggestive, merely descriptive, \
generic, acquired distinctiveness, secondary meaning, primary significance test, \
imagination test, Abercrombie spectrum. Cite primary statute when relevant."""

_USER_TMPL = """\
Retrieve legal doctrine for this trademark distinctiveness analysis:

Mark: {mark}
Description: {description}
NICE class: {nice_class}
Classifier label: {label}
SHAP attributions (top tokens): {attributions}

Find the TMEP doctrine and TTAB cases most relevant to this mark's position on the \
Abercrombie spectrum."""

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com",
        )
    return _client


def _search_tmep(query: str) -> list[dict]:
    col = get_tmep_collection()
    emb = embed_query(query)
    results = col.query(query_embeddings=[emb], n_results=_TMEP_N)
    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append(
            {
                "id": results["ids"][0][i],
                "text": doc,
                "metadata": results["metadatas"][0][i],
            }
        )
    return chunks


def _search_ttab(query: str) -> list[dict]:
    col = get_ttab_collection()
    emb = embed_query(query)
    results = col.query(query_embeddings=[emb], n_results=_TTAB_N)
    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append(
            {
                "id": results["ids"][0][i],
                "text": doc,
                "metadata": results["metadatas"][0][i],
            }
        )
    return chunks


def run_agent(
    mark: str,
    description: str,
    nice_class: str,
    label: str,
    attributions: str,
) -> dict:
    """
    Run the agentic retrieval loop.

    Returns:
        {
            "tmep": list[chunk],  # deduped, ordered by first appearance
            "ttab": list[chunk],
            "rounds": int,        # how many LLM calls were made
        }
    """
    client = _get_client()

    messages: list[dict] = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": _USER_TMPL.format(
                mark=mark,
                description=description,
                nice_class=nice_class,
                label=label,
                attributions=attributions,
            ),
        },
    ]

    # Ordered dicts preserve insertion order; key = chunk id for dedup
    collected_tmep: dict[str, dict] = {}
    collected_ttab: dict[str, dict] = {}
    rounds = 0

    for _ in range(MAX_ROUNDS):
        rounds += 1
        _t = time.perf_counter()
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=_TOOLS,
            tool_choice="auto",
            max_tokens=200,
            temperature=0.1,
        )
        log.debug("agent round %d LLM: %.2fs", rounds, time.perf_counter() - _t)

        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            break

        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
                query = args["query"]
            except (json.JSONDecodeError, KeyError):
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": "Error: malformed tool arguments — skipped.",
                    }
                )
                continue

            _ts = time.perf_counter()
            if fn_name == "search_tmep":
                chunks = _search_tmep(query)
                for c in chunks:
                    collected_tmep.setdefault(c["id"], c)
                sections = ", ".join(f"§{c['metadata']['section_number']}" for c in chunks)
                tool_result = f"Found {len(chunks)} chunks: {sections}"

            elif fn_name == "search_ttab":
                chunks = _search_ttab(query)
                for c in chunks:
                    collected_ttab.setdefault(c["id"], c)
                tool_result = f"Found {len(chunks)} TTAB chunks"

            else:
                tool_result = "Unknown tool"

            elapsed = time.perf_counter() - _ts
            log.debug("%s embed+query: %.2fs", fn_name, elapsed)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )

    return {
        "tmep": list(collected_tmep.values()),
        "ttab": list(collected_ttab.values()),
        "rounds": rounds,
    }
