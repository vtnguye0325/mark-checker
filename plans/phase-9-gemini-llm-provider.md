# Sub-plan — Phase 9, move the LLM calls to Gemini

## Goal

Run `/llm-assess` on the Gemini API free tier instead of the paid DeepSeek
API, and keep DeepSeek reachable by one environment variable.

## What the app calls today

Three modules build an OpenAI client and point it at `https://api.deepseek.com`:

| File | Call | Shape |
|---|---|---|
| `backend/app/services/llm_service.py:134` | the analysis | one chat call, `max_tokens=1000`, `temperature=0.2` |
| `backend/rag/agent.py:194` | doctrine retrieval | tool calling, up to `MAX_ROUNDS = 2` chat calls, `max_tokens=200` |
| `backend/rag/hyde.py:47` | nothing | dead code — no module imports it |

`retriever.retrieve` delegates to `run_agent`, so the agent is on the live path.
**One `/llm-assess` therefore sends up to three LLM requests, not one.** Size the
free-tier budget against three.

Gemini publishes an OpenAI-compatible endpoint at
`https://generativelanguage.googleapis.com/v1beta/openai/`. The OpenAI SDK, the
message shapes, `response.choices[0].message.content`, and `response.usage` all
carry over. So this phase changes configuration and error handling, not the
prompt or the parsing.

## Decisions to make before any code changes

1. **Free-tier data use — decided.** Google may use free-tier API content to
   improve its products. The prompts carry the user's mark and goods
   description. This is acceptable for now. State it plainly in
   `docs/ENGINEERING.md`, and tell the user in the UI before they run a check,
   because the mark is their business information and Phase 8 stores it against
   a named account. Revisit if the app takes paying users.
2. **The model.** Prefer a Flash model. Check the free-tier request-per-minute
   and request-per-day caps in the Google AI Studio console, then divide by three
   to get the real `/llm-assess` ceiling.
3. **Thinking budget.** A 2.5-series Gemini model thinks before it answers, and
   the thinking tokens count against `max_tokens`. The agent asks for
   `max_tokens=200`. A thinking model can spend that whole budget and return
   empty content with `finish_reason="length"`, which reads as "no tool calls"
   and silently turns the doctrine retrieval off. Either pick a model that does
   not think, or raise the agent's cap and disable thinking through `extra_body`.
   Verify this on the first call, not after a week of empty citations.

## Ordered steps

### Step 1 — One place that builds the client

Write `backend/app/services/llm_client.py`:

1. Read `LLM_PROVIDER` (default `gemini`), `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`,
   and `LLM_MODEL`.
2. Export `get_llm_client()` and `LLM_MODEL`. Return a cached `OpenAI` client,
   with `timeout=30.0` and `max_retries=1`, as `llm_service.py` sets today.
3. Raise `RuntimeError` when the key for the chosen provider is unset. Keep the
   message naming the missing variable, because `/llm-assess` maps that to a 503.
4. Point `llm_service.py` and `rag/agent.py` at this module. Delete
   `backend/rag/hyde.py`, and drop its two lines from `backend/rag/README.md`.
   Nothing imports it, so it would rot as the only un-migrated call site.

### Step 2 — Map the provider's errors to a 503

`analyze` catches `RuntimeError` only (`backend/app/routes/analyze.py:60`). Every
other exception becomes a 500 with no message. The free tier makes two of them
routine:

1. Catch `openai.RateLimitError` and return **429** with the `Retry-After` header
   the response carries. The frontend already renders a 429 wait time
   (`useTrademarkPipeline.js:106`), so the user sees "try again in N seconds"
   rather than a broken panel.
2. Catch `openai.APIError` and `openai.APITimeoutError` and return **503**.
3. Separate the two 429s. A per-minute cap carries a `Retry-After` of seconds,
   and the existing frontend line fits it. A per-day cap does not: the wait is
   hours. Return a distinct message that names the daily quota, so the user
   stops retrying instead of hammering a closed door.
4. Leave the Phase 8 behavior alone: `/llm-assess` still writes no row on
   failure, because `update_query_stage` runs only after a result exists.

### Step 3 — Guard an empty completion

A Gemini safety filter, or an exhausted token budget, returns a message whose
`content` is `None`. Today `response.choices[0].message.content.strip()` raises
`AttributeError` on that path, which becomes a 500.

1. In `llm_service.py`, read the content, and when it is empty raise
   `RuntimeError` naming `finish_reason`. The route turns that into a 503 the
   user can act on.
2. In `agent.py`, treat an empty message as "no tool calls" — the loop already
   breaks on that — but log at WARNING with `finish_reason`. Without the log, a
   thinking-budget failure looks exactly like a model that chose not to search.

### Step 4 — Prove the agent's tool calling survives the port

This is the step most likely to fail, and the one whose failure is quietest.

`agent.py:210` appends `msg.model_dump(exclude_none=True)` — an assistant message
carrying `tool_calls` and no content — then sends it back with the tool results.
Gemini's compatibility layer is stricter than DeepSeek about that shape.

1. Run one `/llm-assess` with the log at INFO and read the
   `agent round N LLM: … tool_calls=N` lines. A first round with `tool_calls=0`
   means the port failed.
2. Confirm the row: `select jsonb_array_length(sources->'tmep') from queries
   order by created_at desc limit 1;`. A null `sources` column means no doctrine
   was retrieved.
3. **Why this matters:** `_retrieve_doctrine` catches every exception and returns
   `("", {})`. The analysis then runs with no doctrine, and the prompt's own rule
   makes the model write "no directly applicable TMEP section was retrieved".
   The endpoint returns 200 and the answer looks plausible. **A broken agent
   costs the whole RAG feature and reports nothing.** If the message shape is
   rejected, send `content: ""` instead of omitting it.

### Step 5 — Compare the output quality

The prompt in `_SYSTEM_PROMPT` demands an exact four-section layout, two spectrum
bullets in a fixed format, and TMEP citations drawn only from the retrieved text.
`RecordPlate` parses those sections, so a model that drifts breaks the display.

1. Pick five marks that span the spectrum — one fanciful, one arbitrary, one
   suggestive, one descriptive, one generic.
2. Run each on DeepSeek, then on Gemini, and diff the four section headers, the
   bullet format, and whether every cited TMEP section appears in `sources`.
3. An invented citation is the failure that matters most. It is the one a user
   cannot detect and would act on.

### Step 6 — Configuration and documentation

1. `.env.example` — add `GEMINI_API_KEY`, `LLM_PROVIDER`, and `LLM_MODEL`. Keep
   `DEEPSEEK_API_KEY` and mark it optional.
2. `docker-compose.yml` — pass the three new variables. Relax
   `DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY:?…}` to a plain default, or a deploy
   with no DeepSeek key fails at startup for a key it no longer needs.
3. `docker-compose.dev.yml` — the same, with defaults.
4. Update `docs/ENGINEERING.md:86`, `docs/RAG.md:87`, `docs/API.md:109`,
   `docs/API.md:135`, `docs/DEPLOYMENT.md:11`, `docs/DEPLOYMENT.md:27`, and
   `start.sh:8`. Each names DeepSeek or `DEEPSEEK_API_KEY` today.

## Failure modes, traced end to end

| Failure | Behavior |
|---|---|
| `GEMINI_API_KEY` unset | `get_llm_client` raises `RuntimeError`. `/llm-assess` returns 503 naming the variable. Stages 1 and 2 still work, and the query row keeps a null `analysis`. |
| Free-tier request-per-minute cap hit | 429 with `Retry-After`. The pipeline already shows the wait time. The row keeps a null `analysis`, which the history view reads as an incomplete check. |
| Free-tier request-per-day cap hit | The same 429 path, but it lasts until the quota resets. **Show the cap; never fall back to DeepSeek automatically.** The message must say the daily limit is reached and name the reset, not "try again in N seconds", because the wait is hours. |
| Safety filter blocks the answer | `content` is `None`. Step 3 raises, and the route returns 503. Without Step 3 this is a 500 and an `AttributeError` in the log. |
| Thinking budget eats `max_tokens` in the agent | Empty content, no tool calls, the loop breaks after one round. The doctrine is missing and the analysis still returns 200. Step 3's WARNING is the only signal. |
| Gemini rejects the assistant tool-call message | The agent raises, `_retrieve_doctrine` catches it, and the analysis runs with no doctrine. The endpoint returns 200. Step 4 is what catches this. |
| Gemini unreachable | `APITimeoutError` after 30 seconds, with one retry. The route returns 503. The user waits up to 60 seconds first, so consider lowering the timeout for a free tier. |
| The model drifts from the four-section format | `RecordPlate` renders a partial or empty panel. Step 5 is what catches this, before users do. |

## Not in this phase

- No provider abstraction beyond one module and one environment variable. Two
  providers behind one OpenAI-compatible SDK do not need an interface.
- No automatic failover from Gemini to DeepSeek. It spends money silently.
  `LLM_PROVIDER=deepseek` is the deliberate switch, and a person throws it.
- No change to the prompts, the RAG corpus, or the retrieval parameters. Change
  the provider first, then judge quality against a fixed prompt.
