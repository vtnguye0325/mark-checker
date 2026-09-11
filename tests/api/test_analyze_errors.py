"""POST /llm-assess — provider failures.

The handler in mark_checker/core/llm_errors.py maps the provider exception to
the response. That handler never sees the session, so the route must write
``analysis_error`` on its way out, or the row keeps its stage-2 shape and the
history page shows the check as pending for good.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import openai

from mark_checker.core.limiter import limiter


# ---------------------------------------------------------------------------
# The mapping from the provider error to the response
# ---------------------------------------------------------------------------


def test_analyze_billing_exhausted_returns_503(post_analyze_raising, rate_limit_error):
    r = post_analyze_raising(rate_limit_error("prepayment credits depleted"))
    assert r.status_code == 503
    assert r.json()["detail"] == "The analysis service is unavailable right now."


def test_analyze_daily_quota_returns_429_with_the_daily_message(
    post_analyze_raising, rate_limit_error
):
    r = post_analyze_raising(rate_limit_error("quota: requests per day exceeded"))
    assert r.status_code == 429
    assert "today" in r.json()["detail"]


def test_analyze_rate_limit_returns_429_with_retry_after(post_analyze_raising, rate_limit_error):
    r = post_analyze_raising(rate_limit_error("too many requests"))
    assert r.status_code == 429
    assert r.headers["retry-after"] == "42"
    assert "busy" in r.json()["detail"]


def test_analyze_connection_error_returns_503(post_analyze_raising):
    exc = openai.APIConnectionError(
        request=httpx.Request("POST", "https://provider.example/v1/chat")
    )
    r = post_analyze_raising(exc)
    assert r.status_code == 503


# ---------------------------------------------------------------------------
# The failure that the route records on the query row
# ---------------------------------------------------------------------------


def test_analyze_provider_error_records_the_failed_stage(
    client, analyze_payload, rate_limit_error, monkeypatch
):
    limiter.reset()
    monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
    monkeypatch.setenv("DISABLE_TURNSTILE", "true")
    with (
        patch(
            "mark_checker.api.analyze.analyze_trademark",
            side_effect=rate_limit_error("too many requests"),
        ),
        patch("mark_checker.api.analyze.update_query_stage", new_callable=AsyncMock) as mock_stage,
    ):
        r = client.post("/llm-assess", json=analyze_payload)

    assert r.status_code == 429
    mock_stage.assert_awaited_once()
    values = mock_stage.await_args.args[3]
    assert values["analysis"] is None
    assert "busy" in values["analysis_error"]


def test_analyze_runtime_error_records_a_fixed_message(client, analyze_payload, monkeypatch):
    """The stored message must not carry the internals that the log carries."""
    from mark_checker.api.analyze import _RUNTIME_FAILURE_DETAIL

    limiter.reset()
    monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
    monkeypatch.setenv("DISABLE_TURNSTILE", "true")
    with (
        patch(
            "mark_checker.api.analyze.analyze_trademark",
            side_effect=RuntimeError("DEEPSEEK_API_KEY environment variable is not set"),
        ),
        patch("mark_checker.api.analyze.update_query_stage", new_callable=AsyncMock) as mock_stage,
    ):
        r = client.post("/llm-assess", json=analyze_payload)

    assert r.status_code == 503
    # The client reads the same fixed message. The key name stays in the log.
    assert r.json()["detail"] == _RUNTIME_FAILURE_DETAIL
    values = mock_stage.await_args.args[3]
    assert values["analysis"] is None
    assert "DEEPSEEK_API_KEY" not in values["analysis_error"]
    assert values["analysis_error"] == _RUNTIME_FAILURE_DETAIL


def test_analyze_success_clears_a_previous_failure(client, analyze_payload, monkeypatch):
    limiter.reset()
    monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
    monkeypatch.setenv("DISABLE_TURNSTILE", "true")
    with (
        patch("mark_checker.api.analyze.analyze_trademark") as mock_analyze,
        patch("mark_checker.api.analyze.update_query_stage", new_callable=AsyncMock) as mock_stage,
    ):
        mock_analyze.return_value = {"analysis": "Looks strong.", "sources": None}
        r = client.post("/llm-assess", json=analyze_payload)

    assert r.status_code == 200
    values = mock_stage.await_args.args[3]
    assert values["analysis"] == "Looks strong."
    assert values["analysis_error"] is None
