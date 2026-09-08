"""One place that builds the LLM client.

`/llm-assess` runs on the Gemini API free tier by default. Set
`LLM_PROVIDER=deepseek` to switch back to the paid DeepSeek API. Both speak the
OpenAI-compatible chat API, so only the base URL, the key, and the model change.
"""

from __future__ import annotations

import os
from functools import lru_cache

from openai import OpenAI

_PROVIDERS = {
    "gemini": {
        "key_var": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        # gemini-flash-lite-latest tracks Google's current Flash-Lite model —
        # fast, cheap, minimal thinking, so it does not spend the agent's
        # 200-token budget before it emits a tool call.
        "default_model": "gemini-flash-lite-latest",
    },
    "deepseek": {
        "key_var": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
    },
}

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
if LLM_PROVIDER not in _PROVIDERS:
    raise RuntimeError(f"LLM_PROVIDER={LLM_PROVIDER!r} is not one of {sorted(_PROVIDERS)}")

_CONFIG = _PROVIDERS[LLM_PROVIDER]

# LLM_MODEL overrides the provider default. An empty value falls back.
LLM_MODEL = os.getenv("LLM_MODEL", "").strip() or _CONFIG["default_model"]


@lru_cache(maxsize=1)
def get_llm_client() -> OpenAI:
    """Return the cached OpenAI client for the chosen provider.

    Raises RuntimeError, naming the missing variable, when the key for the
    chosen provider is unset. `/llm-assess` maps that to a 503.
    """
    key = os.environ.get(_CONFIG["key_var"])
    if not key:
        raise RuntimeError(f"{_CONFIG['key_var']} environment variable is not set")
    return OpenAI(
        api_key=key,
        base_url=_CONFIG["base_url"],
        timeout=30.0,
        max_retries=1,
    )
