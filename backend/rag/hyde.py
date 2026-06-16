"""
HyDE — Hypothetical Document Embedding.

Cheap LLM call that generates a short legal reasoning paragraph
rich in Abercrombie vocabulary. Used as the retrieval query vector.
"""

import os

from openai import OpenAI

_client: OpenAI | None = None

_SYSTEM = (
    "You are a trademark law expert. Write a concise legal reasoning paragraph "
    "using precise Abercrombie doctrine vocabulary: generic, merely descriptive, "
    "primary significance, secondary meaning, suggestive, arbitrary, fanciful, "
    "acquired distinctiveness, imagination test. Do not state a conclusion — "
    "only articulate the relevant legal considerations."
)

_USER_TMPL = """\
Mark: {mark}
Description: {description}
NICE class: {nice_class}
Classification label: {label}
SHAP attributions (top tokens): {attributions}

Write a 3-4 sentence hypothetical legal reasoning paragraph about the distinctiveness \
of this mark under the Abercrombie spectrum."""


def generate_hyde_paragraph(
    mark: str,
    description: str,
    nice_class: str,
    label: str,
    attributions: str,
) -> str:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com",
        )

    response = _client.chat.completions.create(
        model="deepseek-chat",
        messages=[
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
        ],
        max_tokens=150,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()
