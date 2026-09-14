"""The analysis graph, offline: every LLM call and every search is faked.

Patches `get_llm_client` and `_search` on `graph` itself, so no test touches
ChromaDB, the embedding model, or a real provider. See
`plans/phase-10-langgraph-analysis-agent.md` step 5 for the case table.

Two scripting traps this file works around:

- When the scripted assistant message carries tool calls and `rounds` is
  still below `MAX_RETRIEVAL_ROUNDS`, the graph goes back to `retrieve`. A
  test that scripts a tool-call message must also script a second, no-tool
  message, or the fake client runs out of messages inside `draft`.
- The repair call is selected by `len(kwargs["messages"]) == 4`, not by a
  call counter, because the counter changes whenever the retrieval path
  changes.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import openai
import pytest

from mark_checker.services.analysis import graph
from mark_checker.services.analysis.prompts import REQUIRED_HEADERS

# ---------------------------------------------------------------------------
# Autouse fixture — a developer with tracing on in .env must not send fake
# test runs to LangSmith.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_tracing(monkeypatch):
    for name in ("LANGSMITH_TRACING", "LANGSMITH_TRACING_V2", "LANGCHAIN_TRACING_V2"):
        monkeypatch.delenv(name, raising=False)
    # The graph reads these limits from the environment at import time. Pin
    # them, so a value in .env cannot change the scripted call sequence.
    monkeypatch.setattr(graph, "MAX_RETRIEVAL_ROUNDS", 2)
    monkeypatch.setattr(graph, "MAX_REVISIONS", 1)
    monkeypatch.setattr(graph, "WORD_BUDGET", 480)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


def _message(content: str | None, tool_calls: list[dict] | None = None) -> SimpleNamespace:
    """A stand-in for the SDK's `choices[0].message`."""

    def model_dump(exclude_none: bool = False) -> dict:
        # The real SDK drops every None field when exclude_none=True.
        dumped = {"role": "assistant", "content": content, "tool_calls": tool_calls}
        if exclude_none:
            dumped = {k: v for k, v in dumped.items() if v is not None}
        return dumped

    return SimpleNamespace(content=content, tool_calls=tool_calls, model_dump=model_dump)


class FakeClient:
    """Pops one scripted message per chat call and records the kwargs sent."""

    def __init__(self, scripted: list[SimpleNamespace]):
        self._scripted = list(scripted)
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs) -> SimpleNamespace:
        self.calls.append(kwargs)
        message = self._scripted.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")])


def _tool_call(call_id: str, tool_name: str, query: str = "distinctiveness") -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": tool_name, "arguments": json.dumps({"query": query})},
    }


def _chunks(tool_name: str, n: int = 1, section: str = "1209.01") -> list[dict]:
    if tool_name == "search_tmep":
        return [
            {
                "id": f"tmep-{i}",
                "text": f"TMEP doctrine {i}",
                "metadata": {"section_number": section},
            }
            for i in range(n)
        ]
    return [
        {
            "id": f"ttab-{i}",
            "text": f"TTAB case {i}",
            "metadata": {"mark": "WIDGETCO", "nice_class": 9, "outcome": "affirmed"},
        }
        for i in range(n)
    ]


_DRAFT_OK = "\n\n".join([*REQUIRED_HEADERS, "See TMEP §1209.01 for support."])
_DRAFT_MISSING_HEADER = "\n\n".join([*REQUIRED_HEADERS[:-1], "No closing section here."])
_DRAFT_INVENTED_CITATION = "\n\n".join(
    [*REQUIRED_HEADERS, "See TMEP §1052, which does not exist here."]
)
_DRAFT_NO_CITATION = "\n\n".join([*REQUIRED_HEADERS, "No applicable section was retrieved."])

_INPUTS = dict(
    mark="WIDGETCO",
    description="downloadable software for widgets",
    nice_class=9,
    label="distinctive",
    prob_distinctive=0.82,
    attributions=[{"field": "mark_text", "value": "WIDGETCO", "attribution": 0.31}],
    confidence_tier="high",
)


def _run(client: FakeClient, search_side_effect):
    with (
        patch.object(graph, "get_llm_client", return_value=client),
        patch.object(graph, "_search", side_effect=search_side_effect),
    ):
        return graph.run_analysis(**_INPUTS)


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------


def test_happy_path_has_all_headers_and_both_sources():
    # Round 1: the agent calls both tools. Round 2: it stops (trap #1).
    client = FakeClient(
        [
            _message(
                None,
                tool_calls=[_tool_call("c1", "search_tmep"), _tool_call("c2", "search_ttab")],
            ),
            _message("no further searches needed"),
            _message(_DRAFT_OK),
        ]
    )

    def search(tool_name, _query):
        return _chunks(tool_name)

    result = _run(client, search)

    for header in REQUIRED_HEADERS:
        assert header in result["analysis"]
    assert result["sources"]["tmep"]
    assert result["sources"]["ttab"]

    draft_call = client.calls[-1]
    assert "LEGAL DOCTRINE" in draft_call["messages"][-1]["content"]


def test_invented_citation_is_removed_after_repair():
    # Retrieve calls no tool, so backfill supplies the one real section.
    client = FakeClient(
        [
            _message("no search needed"),
            _message(_DRAFT_INVENTED_CITATION),
            _message(_DRAFT_OK),
        ]
    )

    def search(tool_name, _query):
        return _chunks(tool_name)

    result = _run(client, search)

    assert "§1052" not in result["analysis"]
    assert len(client.calls) == 3


def test_missing_header_triggers_repair_that_restores_all_four():
    client = FakeClient(
        [
            _message("no search needed"),
            _message(_DRAFT_MISSING_HEADER),
            _message(_DRAFT_OK),
        ]
    )

    def search(tool_name, _query):
        return _chunks(tool_name)

    result = _run(client, search)

    for header in REQUIRED_HEADERS:
        assert header in result["analysis"]
    assert len(client.calls) == 3


def test_valid_draft_needs_no_repair():
    client = FakeClient(
        [
            _message("no search needed"),
            _message(_DRAFT_OK),
        ]
    )

    def search(tool_name, _query):
        return _chunks(tool_name)

    _run(client, search)

    assert len(client.calls) == 2


def test_backfill_supplies_tmep_when_the_agent_calls_no_tool():
    client = FakeClient(
        [
            _message("no search needed"),
            _message(_DRAFT_OK),
        ]
    )

    def search(tool_name, _query):
        assert tool_name == "search_tmep"
        return _chunks("search_tmep")

    result = _run(client, search)

    assert result["sources"]["tmep"]


def test_dead_retrieval_still_produces_a_full_analysis():
    # Round 1: a tool call, which fails. Round 2: the agent stops. Backfill
    # then also fails. The draft must still run and read cleanly.
    client = FakeClient(
        [
            _message(None, tool_calls=[_tool_call("c1", "search_tmep")]),
            _message("giving up on search"),
            _message(_DRAFT_NO_CITATION),
        ]
    )

    def search(_tool_name, _query):
        raise RuntimeError("chromadb unavailable")

    result = _run(client, search)

    assert result["sources"] is None
    for header in REQUIRED_HEADERS:
        assert header in result["analysis"]


def test_empty_draft_raises_runtime_error():
    client = FakeClient(
        [
            _message("no search needed"),
            _message(""),
        ]
    )

    def search(tool_name, _query):
        return _chunks(tool_name)

    with pytest.raises(RuntimeError, match="empty analysis"):
        _run(client, search)


def test_failed_repair_keeps_the_first_draft():
    client = FakeClient(
        [
            _message("no search needed"),
            _message(_DRAFT_INVENTED_CITATION),
        ]
    )
    original_create = client._create

    def intercept_repair(**kwargs):
        # Select the repair call by shape, not by a call counter (trap #2).
        if len(kwargs["messages"]) == 4:
            raise RuntimeError("repair backend down")
        return original_create(**kwargs)

    client.chat.completions.create = intercept_repair

    def search(tool_name, _query):
        return _chunks(tool_name)

    result = _run(client, search)

    assert result["analysis"] == _DRAFT_INVENTED_CITATION


def test_repair_rate_limit_propagates_out_of_run_analysis():
    client = FakeClient(
        [
            _message("no search needed"),
            _message(_DRAFT_INVENTED_CITATION),
        ]
    )
    original_create = client._create

    def intercept_repair(**kwargs):
        if len(kwargs["messages"]) == 4:
            request = httpx.Request("POST", "https://provider.example/v1/chat")
            response = httpx.Response(429, request=request)
            raise openai.RateLimitError("rate limited", response=response, body=None)
        return original_create(**kwargs)

    client.chat.completions.create = intercept_repair

    def search(tool_name, _query):
        return _chunks(tool_name)

    with pytest.raises(openai.RateLimitError):
        _run(client, search)


def test_tracing_off_returns_a_plain_openai_client(monkeypatch):
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    from openai.resources.chat.completions import Completions

    from mark_checker.core import llm_client
    from mark_checker.core.llm_client import get_llm_client

    monkeypatch.setenv(llm_client._CONFIG["key_var"], "fake-key-for-test")

    get_llm_client.cache_clear()
    try:
        client = get_llm_client()
        assert type(client) is openai.OpenAI
        # wrap_openai() keeps the OpenAI type and replaces `create` in place,
        # so the type check alone passes with tracing on. Check `create` too.
        assert getattr(client.chat.completions.create, "__func__", None) is Completions.create
    finally:
        get_llm_client.cache_clear()


@pytest.mark.parametrize(
    "cited, retrieved, supported",
    [
        ("1209", {"1209.01"}, True),
        ("1209.01", {"1209"}, True),
        ("1052", {"1209.01"}, False),
        ("120", {"1209.01"}, False),
    ],
)
def test_section_supported(cited, retrieved, supported):
    assert graph._section_supported(cited, retrieved) is supported
