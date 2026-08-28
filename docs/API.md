# API reference

Base URL in local dev: `http://localhost:8000`. In production, Nginx proxies the four paths
below to the backend; every other path serves the static frontend.

## Input format

The model was trained on an 8-field string joined with `". "`:

```
{mark}. {description}. {translation}. {wordnet_flag}. mark length is {n}.
NICE category is {k}. {nice_description}. {pseudo_mark}
```

`text_formatter.format_mark()` builds this representation automatically and returns a
`FormattedMark` with two attributes: `.text` (the joined string passed to the tokenizer) and
`.fields` (the individual parts used for leave-one-out attribution). If you feed raw mark
text without the description and the NICE metadata, the accuracy drops.

## Rate limiting

All endpoints are limited **per IP address**: `RATE_LIMIT_DEFAULT` (default `100/hour`) for
`/ml-predict` and `/llm-explain`, and `RATE_LIMIT_ANALYZE` (default `5/hour`) for the paid
`/llm-assess` endpoint. Requests over the limit receive `429 Too Many Requests` with a
`Retry-After` header. The counter resets on a rolling hourly window.

## `GET /health`

```
200 OK
{"status": "ok"}
```

Returns `503 {"status": "model_loading"}` until the model finishes loading at worker startup.

## `POST /ml-predict`

Runs the model on the given inputs and returns a distinctiveness prediction.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mark` | string | yes | The trademark literal element (e.g. `"APPLE"`) |
| `description` | string | yes | Goods/services description filed with the mark |
| `nice_class` | int (1–45) | yes | NICE classification class number |
| `translation` | string | no | English translation if the mark is a foreign word |
| `pseudo_mark` | string | no | Space-separated constituent words for compound marks |

**Example:**

```bash
curl -X POST http://localhost:8000/ml-predict \
  -H "Content-Type: application/json" \
  -d '{
    "mark": "APPLE",
    "description": "computers and computer software",
    "nice_class": 9
  }'
```

**Response (200 OK):**

```json
{
  "label": "distinctive",
  "prob_distinctive": 0.9492,
  "prob_not_distinctive": 0.0508,
  "formatted_input": "APPLE. computers and computer software. ..."
}
```

`label` is `"distinctive"` when `prob_distinctive >= 0.5`, otherwise `"not_distinctive"`.
`formatted_input` is the full 8-field string fed to the model.

## `POST /llm-explain`

Runs leave-one-out attribution: blanks each of the 8 input fields in turn, measures the
change in `prob_distinctive` vs the baseline, and returns per-field attribution scores.

**Request body:** same fields as `/ml-predict`.

**Response (200 OK):**

```json
{
  "label": "distinctive",
  "prob_distinctive": 0.9492,
  "prob_not_distinctive": 0.0508,
  "formatted_input": "...",
  "attributions": [
    { "field": "Mark",             "value": "APPLE", "attribution":  0.3201 },
    { "field": "Goods & Services", "value": "computers and computer software", "attribution": 0.0843 }
  ]
}
```

`attribution` is `baseline_prob − masked_prob`. A positive value means the field pushes
toward distinctiveness; a negative value pushes against it. The results are sorted by
`abs(attribution)` descending.

## `POST /llm-assess`

Sends the prediction and the attributions to DeepSeek and returns a plain-English legal
analysis in four sections: *What the model found*, *Where this mark sits on the trademark
spectrum*, *Why the classifier leaned this way — key signals*, and *What to do next*. The RAG
layer grounds the analysis in retrieved TMEP and TTAB doctrine (see [RAG.md](RAG.md)).

Requires `DEEPSEEK_API_KEY` in the environment. Requires a valid Cloudflare Turnstile token
in `turnstile_token` unless `DISABLE_TURNSTILE=true`.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mark` | string | yes | Trademark literal element |
| `description` | string | yes | Goods/services description |
| `nice_class` | int (1–45) | yes | NICE class number |
| `label` | string | yes | `"distinctive"` or `"not_distinctive"` from `/ml-predict` or `/llm-explain` |
| `prob_distinctive` | float | yes | Probability score from `/ml-predict` or `/llm-explain` |
| `attributions` | array | yes | Attribution list from `/llm-explain` (max 16) |
| `turnstile_token` | string | no | Cloudflare Turnstile token |

**Response (200 OK):**

```json
{
  "analysis": "**What the model found**\n...",
  "sources": { "tmep": [ ... ], "ttab": [ ... ] }
}
```

`sources` is `null` when RAG retrieval returns nothing.

**Errors:** `503` if `DEEPSEEK_API_KEY` is not configured or Turnstile is not configured;
`429` when the analyze rate limit is hit.

## Validation errors (422)

Returned for missing required fields, `nice_class` outside 1–45, or an empty
`mark` / `description`.
