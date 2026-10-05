"""llm_error_detail must not read an ordinary quota 429 as billing exhaustion.

A billing 503 tells the user nothing to do and carries no retry guidance. A
free-tier quota message names the plan and the billing details, so the billing
markers must stay narrow and the quota check must run first.
"""

from __future__ import annotations

import httpx
import openai
import pytest

from mark_checker.core.llm_errors import llm_error_detail


def _rate_limit_error(message: str) -> openai.RateLimitError:
    request = httpx.Request("POST", "https://provider.example/v1/chat")
    response = httpx.Response(429, request=request, headers={"retry-after": "42"})
    return openai.RateLimitError(message, response=response, body=None)


@pytest.mark.parametrize(
    "message",
    [
        "You exceeded your current quota, please check your plan and billing details.",
        "Rate limit reached. Check your plan and billing details for more.",
    ],
)
def test_a_free_tier_quota_message_is_not_billing_exhaustion(message):
    mapped = llm_error_detail(_rate_limit_error(message))
    assert mapped.status_code == 429


def test_a_daily_quota_message_wins_over_the_billing_words():
    mapped = llm_error_detail(
        _rate_limit_error("Quota exceeded: requests per day. Check your plan and billing details.")
    )
    assert mapped.status_code == 429
    assert "today" in mapped.detail


def test_real_billing_exhaustion_is_still_a_503():
    mapped = llm_error_detail(_rate_limit_error("Your prepayment credits are depleted."))
    assert mapped.status_code == 503
