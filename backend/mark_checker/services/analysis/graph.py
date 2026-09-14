"""The analysis stage, as a LangGraph state machine.

Replaces the fixed retrieve-then-draft sequence with a graph that can loop on
its own retrieval and check its own draft:

    retrieve -> search -> retrieve   (until a round limit or no tool call)
             -> backfill -> draft -> validate -> revise -> END

The nodes still call ``get_llm_client()`` from ``core.llm_client`` — no
LangChain chat model, no LangChain message objects. See
``plans/phase-10-langgraph-analysis-agent.md`` for the design.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Annotated, TypedDict

import openai
from langgraph.graph import END, StateGraph

from mark_checker.core.llm_client import LLM_MODEL, LLM_PROVIDER, get_llm_client
from mark_checker.services.analysis.prompts import (
    _DOCTRINE_SECTION,
    _SYSTEM_PROMPT,
    _USER_TMPL,
    REPAIR_TMPL,
    REQUIRED_HEADERS,
)
from mark_checker.services.analysis.tiers import _field_value
from mark_checker.services.text_formatter import NICE_DESCRIPTIONS

log = logging.getLogger(__name__)

# --- Configuration (3g) -----------------------------------------------------


def _env_int(name: str, default: int, minimum: int) -> int:
    """Read a non-negative int from the environment.

    A bad value logs a warning and uses the default. A crash here would stop
    the API import, and every route would fail, not only /llm-assess.
    """
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        log.warning("%s=%r is not an int — using %d", name, raw, default)
        return default
    if value < minimum:
        log.warning("%s=%d is below %d — using %d", name, value, minimum, minimum)
        return minimum
    return value


MAX_RETRIEVAL_ROUNDS = _env_int("RAG_MAX_ROUNDS", 2, 1)
MAX_REVISIONS = _env_int("ANALYSIS_MAX_REVISIONS", 1, 0)
WORD_BUDGET = _env_int("ANALYSIS_WORD_BUDGET", 480, 1)

_CITATION_RE = re.compile(r"TMEP\s*§+\s*(\d+(?:\.\d+)*)")


# --- Reach the RAG helpers lazily (3b) --------------------------------------
# Imported inside functions, not at module import time, so loading the API
# does not pull ChromaDB and the embedding model into memory. `mark_checker`
# is an installed package, so one absolute import works from uvicorn and from
# pytest — no fallback import is needed.


def _rag():
    from mark_checker.rag import agent as rag_agent

    return rag_agent


def _search(tool_name: str, query: str) -> list[dict]:
    """Run one named search against the RAG backend.

    A single entry point, so tests patch this one name and never touch
    ChromaDB or the embedding model.
    """
    rag_agent = _rag()
    if tool_name == "search_tmep":
        return rag_agent._search_tmep(query)
    if tool_name == "search_ttab":
        return rag_agent._search_ttab(query)
    raise ValueError(f"unknown tool {tool_name!r}")


def _format_context(result: dict) -> str:
    from mark_checker.rag.retriever import format_context

    return format_context(result)


# --- The state (3a) ---------------------------------------------------------


def _merge_chunks(left: dict[str, dict], right: dict[str, dict]) -> dict[str, dict]:
    """Keep the first chunk seen for a given id — the dedup `run_agent()` did
    with `setdefault`, expressed as a reducer, so a node returns only the
    chunks it found.
    """
    merged = dict(left or {})
    for chunk_id, chunk in (right or {}).items():
        merged.setdefault(chunk_id, chunk)
    return merged


class AnalysisState(TypedDict, total=False):
    # Inputs, fixed for the whole run.
    mark: str
    description: str
    nice_class: int
    label: str
    prob_distinctive: float
    attributions: list[dict]
    confidence_tier: str
    # Retrieval. `messages` has no reducer: each node returns the whole list,
    # because the provider's chat API needs the assistant message and its
    # tool messages in one ordered list, and a naive append reducer would
    # produce a message list the API rejects on a partial write.
    messages: list[dict]
    tmep: Annotated[dict[str, dict], _merge_chunks]
    ttab: Annotated[dict[str, dict], _merge_chunks]
    rounds: int
    # Drafting.
    draft: str
    violations: list[str]
    revisions: int


# --- Prompt assembly ---------------------------------------------------------


def _attribution_lines(attributions: list[dict]) -> str:
    return "\n".join(
        f"  {a['field']}: {a['value']}  ({a['attribution']:+.4f})" for a in attributions
    )


def _attribution_str(attributions: list[dict]) -> str:
    # Top 5, skipping the two fields that are not SHAP signals — the same
    # filter the old `_retrieve_doctrine()` used, before Phase 10 moved this
    # into the `retrieve` node.
    return ", ".join(
        f"{a['field']}: {a['attribution']:+.2f}"
        for a in attributions[:5]
        if a.get("field") not in ("Translation", "WordNet Flag")
    )


def _draft_prompt(state: AnalysisState) -> str:
    tmep = list(state.get("tmep", {}).values())
    ttab = list(state.get("ttab", {}).values())
    doctrine_prefix = ""
    if tmep or ttab:
        doctrine_prefix = _DOCTRINE_SECTION.format(
            context=_format_context({"tmep": tmep, "ttab": ttab})
        )
    return doctrine_prefix + _USER_TMPL.format(
        mark=state["mark"],
        description=state["description"],
        nice_class=state["nice_class"],
        nice_class_description=NICE_DESCRIPTIONS.get(state["nice_class"], "unknown class"),
        label=state["label"].replace("_", " "),
        prob_pct=round(state["prob_distinctive"] * 100),
        confidence_tier=state["confidence_tier"],
        translation_status=_field_value(
            state["attributions"], "Translation", "no translation required"
        ),
        wordnet_flag=_field_value(state["attributions"], "WordNet Flag", "mark absent in Wordnet"),
        attributions_block=_attribution_lines(state["attributions"]),
    )


# --- Nodes (3c) --------------------------------------------------------------


def _node_retrieve(state: AnalysisState) -> dict:
    rag_agent = _rag()
    client = get_llm_client()

    messages = state.get("messages")
    if not messages:
        messages = [
            {"role": "system", "content": rag_agent._SYSTEM},
            {
                "role": "user",
                "content": rag_agent._USER_TMPL.format(
                    mark=state["mark"],
                    description=state["description"],
                    nice_class=state["nice_class"],
                    label=state["label"],
                    attributions=_attribution_str(state["attributions"]),
                ),
            },
        ]

    rounds = state.get("rounds", 0)
    t0 = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=rag_agent._TOOLS,
            tool_choice="auto",
            max_tokens=200,
            temperature=0.1,
        )
        msg = response.choices[0].message
        assistant_msg = msg.model_dump(exclude_none=True)
        # The Gemini compatibility layer rejects the follow-up request when
        # the assistant message carries tool_calls and no content. Send
        # content="" rather than omit it.
        if msg.tool_calls and not assistant_msg.get("content"):
            assistant_msg["content"] = ""
        messages = [*messages, assistant_msg]
    except Exception:
        # A dead retrieval planner must not turn into a 503 when a full
        # analysis is still possible without it. Fall through to backfill.
        log.warning("retrieve node failed — falling back to backfill", exc_info=True)
        return {"messages": messages, "rounds": rounds + 1}

    log.info("retrieve round %d: %.2fs", rounds + 1, time.perf_counter() - t0)
    return {"messages": messages, "rounds": rounds + 1}


def _node_search(state: AnalysisState) -> dict:
    messages = list(state["messages"])
    last = messages[-1]
    tool_calls = last.get("tool_calls") or []

    tmep: dict[str, dict] = {}
    ttab: dict[str, dict] = {}

    for tool_call in tool_calls:
        call_id = tool_call["id"]
        fn = tool_call["function"]
        fn_name = fn["name"]
        try:
            args = json.loads(fn["arguments"])
            query = args["query"]
        except (json.JSONDecodeError, KeyError, TypeError):
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": "Error: malformed tool arguments — skipped.",
                }
            )
            continue

        try:
            chunks = _search(fn_name, query)
        except Exception:
            log.warning("%s failed", fn_name, exc_info=True)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": f"Error: {fn_name} backend unavailable.",
                }
            )
            continue

        if fn_name == "search_tmep":
            for c in chunks:
                tmep.setdefault(c["id"], c)
            sections = ", ".join(f"§{c['metadata'].get('section_number', '?')}" for c in chunks)
            result_line = f"Found {len(chunks)} chunks: {sections}"
        else:
            for c in chunks:
                ttab.setdefault(c["id"], c)
            result_line = f"Found {len(chunks)} TTAB chunks"

        messages.append({"role": "tool", "tool_call_id": call_id, "content": result_line})

    return {"messages": messages, "tmep": tmep, "ttab": ttab}


def _node_backfill(state: AnalysisState) -> dict:
    if state.get("tmep"):
        return {}
    try:
        query = (
            f"{state['mark']} {state['description']} distinctiveness merely descriptive "
            "acquired distinctiveness Abercrombie spectrum"
        )
        chunks = _search("search_tmep", query)
        return {"tmep": {c["id"]: c for c in chunks}}
    except Exception:
        log.warning("backfill search failed — proceeding without doctrine", exc_info=True)
        return {}


def _node_draft(state: AnalysisState) -> dict:
    client = get_llm_client()
    user_content = _draft_prompt(state)

    t0 = time.perf_counter()
    # No broad except here. An openai 429 or APIError must reach analyze.py's
    # handlers unwrapped, or every provider limit turns into a generic 503.
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        max_tokens=1000,
    )
    log.info("draft: %.2fs", time.perf_counter() - t0)

    choice = response.choices[0]
    content = choice.message.content
    if not content or not content.strip():
        # The one exception the route must see: analyze() maps a RuntimeError
        # to a 503 the user can act on.
        raise RuntimeError(
            f"the model returned an empty analysis (finish_reason={choice.finish_reason})"
        )
    return {"draft": content.strip()}


def _section_supported(cited: str, retrieved: set[str]) -> bool:
    """A cited section counts when it equals a retrieved one, when a
    retrieved section is a child of it (starts with "cited."), or when the
    cited section is a child of a retrieved one. Plain `startswith` without
    the dot would wrongly accept "120" against "1209.01".
    """
    for section in retrieved:
        if cited == section:
            return True
        if section.startswith(cited + ".") or cited.startswith(section + "."):
            return True
    return False


def _node_validate(state: AnalysisState) -> dict:
    draft = state["draft"]
    violations = []

    for header in REQUIRED_HEADERS:
        if header not in draft:
            violations.append(f"missing header: {header}")

    word_count = len(draft.split())
    if word_count > WORD_BUDGET:
        violations.append(f"too long: {word_count} words, budget is {WORD_BUDGET}")

    retrieved_sections = {
        s
        for c in state.get("tmep", {}).values()
        if (s := c.get("metadata", {}).get("section_number"))
    }
    for match in _CITATION_RE.finditer(draft):
        cited = match.group(1)
        if not _section_supported(cited, retrieved_sections):
            violations.append(f"invented citation: TMEP §{cited}")

    return {"violations": violations}


def _node_revise(state: AnalysisState) -> dict:
    client = get_llm_client()
    revisions = state.get("revisions", 0)
    draft = state["draft"]

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _draft_prompt(state)},
                {"role": "assistant", "content": draft},
                {
                    "role": "user",
                    "content": REPAIR_TMPL.format(
                        violations="\n".join(f"- {v}" for v in state.get("violations", [])),
                        draft=draft,
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=1000,
        )
    except openai.APIError:
        # A 429 or a quota error is an operator-visible problem, not a repair
        # failure. Let it reach analyze.py's handlers unmasked instead of
        # silently reporting the first draft as a clean success.
        raise
    except Exception:
        log.warning("repair pass failed — keeping the first draft", exc_info=True)
        return {"draft": draft, "revisions": revisions + 1}

    content = response.choices[0].message.content
    if not content or not content.strip():
        log.warning("repair pass returned empty content — keeping the first draft")
        return {"draft": draft, "revisions": revisions + 1}
    return {"draft": content.strip(), "revisions": revisions + 1}


# --- The edges (3d) ----------------------------------------------------------


def _after_retrieve(state: AnalysisState) -> str:
    last = state["messages"][-1]
    if last.get("role") == "assistant" and last.get("tool_calls"):
        return "search"
    return "backfill"


def _after_search(state: AnalysisState) -> str:
    if state.get("rounds", 0) >= MAX_RETRIEVAL_ROUNDS:
        return "backfill"
    return "retrieve"


def _after_validate(state: AnalysisState) -> str:
    if state.get("violations") and state.get("revisions", 0) < MAX_REVISIONS:
        return "revise"
    return END


def _build_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("retrieve", _node_retrieve)
    graph.add_node("search", _node_search)
    graph.add_node("backfill", _node_backfill)
    graph.add_node("draft", _node_draft)
    graph.add_node("validate", _node_validate)
    graph.add_node("revise", _node_revise)

    graph.set_entry_point("retrieve")
    graph.add_conditional_edges("retrieve", _after_retrieve, ["search", "backfill"])
    graph.add_conditional_edges("search", _after_search, ["backfill", "retrieve"])
    graph.add_edge("backfill", "draft")
    graph.add_edge("draft", "validate")
    graph.add_conditional_edges("validate", _after_validate, ["revise", END])
    graph.add_edge("revise", END)
    return graph.compile()


# Compiled once at import time. The graph holds no per-request state, so one
# compiled graph serves every request — compiling per request wastes work on
# the hot path.
_GRAPH = _build_graph()


def run_analysis(
    mark: str,
    description: str,
    nice_class: int,
    label: str,
    prob_distinctive: float,
    attributions: list[dict],
    confidence_tier: str,
) -> dict:
    """Run the analysis graph. Returns {"analysis": str, "sources": dict | None},
    the exact shape `analyze()` and `update_query_stage()` already consume.
    """
    t_start = time.perf_counter()
    initial_state: AnalysisState = {
        "mark": mark,
        "description": description,
        "nice_class": nice_class,
        "label": label,
        "prob_distinctive": prob_distinctive,
        "attributions": attributions,
        "confidence_tier": confidence_tier,
        "messages": [],
        "tmep": {},
        "ttab": {},
        "rounds": 0,
        "revisions": 0,
    }

    config = {
        "recursion_limit": 2 * MAX_RETRIEVAL_ROUNDS + 8,
        "run_name": "llm-assess",
        "tags": ["analysis", LLM_PROVIDER],
        # Never put the mark or the description here: metadata stays visible
        # when LANGSMITH_HIDE_INPUTS=true hides the inputs.
        "metadata": {"model": LLM_MODEL, "nice_class": nice_class, "label": label},
    }

    final_state = _GRAPH.invoke(initial_state, config=config)

    tmep = list(final_state.get("tmep", {}).values())
    ttab = list(final_state.get("ttab", {}).values())
    sources = None
    if tmep or ttab:
        sources = {"tmep": tmep, "ttab": ttab, "rounds": final_state.get("rounds", 0)}

    log.info(
        "analyze total: %.2fs  rounds=%d revisions=%d tmep=%d ttab=%d",
        time.perf_counter() - t_start,
        final_state.get("rounds", 0),
        final_state.get("revisions", 0),
        len(tmep),
        len(ttab),
    )

    return {"analysis": final_state["draft"], "sources": sources}
