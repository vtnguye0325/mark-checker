# Sub-plan — Phase 10, make `/llm-assess` a LangGraph agent

## Goal

Replace the fixed sequence behind `/llm-assess` with a LangGraph state machine
that can loop back on its own retrieval and check its own draft. The route, the
request and response models, the database stages, and the frontend hook stay
exactly as they are.

Two scope decisions are already made:

1. **The analysis stage only.** `/ml-predict` and `/llm-explain` keep their
   current shape. The graph lives behind `analyze_trademark()`.
2. **LangGraph with the raw provider SDK.** The nodes keep calling
   `get_llm_client()` from `backend/mark_checker/core/llm_client.py`. Do not add
   `langchain-openai`, `ChatOpenAI`, or LangChain message objects. The provider
   switch and the Gemini compatibility fixes stay where they are.
3. **LangSmith for tracing, opt-in.** Tracing is off unless
   `LANGSMITH_TRACING=true`. LangGraph traces the nodes by itself. The raw
   OpenAI client gets `langsmith.wrappers.wrap_openai()`, which wraps the raw
   SDK and adds no LangChain message objects, so decision 2 still holds.

---

## What the app does today

The frontend hook `frontend/src/hooks/useTrademarkPipeline.js` makes three
sequential calls.

| Step | Endpoint | Work |
|---|---|---|
| 1 | `POST /ml-predict` | `format_mark()` builds the field text, `predict_one()` runs the local ModernBERT model, the route writes a `Query` row and returns `query_id`. |
| 2 | `POST /llm-explain` | `explain_one()` computes leave-one-out field attributions, saved on the query row. |
| 3 | `POST /llm-assess` | `analyze_trademark()` retrieves doctrine, then drafts the analysis. |

Inside step 3, `analyze_trademark()` in
`backend/mark_checker/services/analysis/__init__.py:22`:

1. `_retrieve_doctrine()` in `services/analysis/doctrine.py` calls
   `mark_checker.rag.retriever.retrieve()`, which calls
   `mark_checker.rag.agent.run_agent()` — a hand-written tool-calling loop of at most
   `MAX_ROUNDS = 2` over `search_tmep` and `search_ttab`. Each tool call embeds
   its query with the local bge-base model and queries one ChromaDB collection.
   Chunks are deduplicated by id.
2. `format_context()` builds the `LEGAL DOCTRINE` and `ILLUSTRATIVE CASES`
   block, and `_DOCTRINE_SECTION` wraps it. The three prompt constants live in
   `services/analysis/prompts.py`.
3. One chat call with `_SYSTEM_PROMPT` and `_USER_TMPL` produces the
   four-section analysis at `temperature=0.2`, `max_tokens=1000`.

### The three weaknesses this phase fixes

1. **A silent empty retrieval.** When the agent calls no tool, or when both
   collections return nothing, `_retrieve_doctrine()` returns `("", {})` and the
   draft runs with no doctrine at all. Nothing in the logs marks the analysis as
   ungrounded, and the response still looks normal.
2. **Unchecked citations.** `_SYSTEM_PROMPT` tells the model to cite only TMEP
   sections that appear in the retrieved text. No code verifies that. An
   invented `TMEP §1052` reaches the user as fact.
3. **Unchecked structure.** The prompt asks for four exact headers and a word
   budget. `parseSections()` in `frontend/src/lib/parseLegalAnalysis.js` splits
   the text on any `**bold**` or `#` line. A missing header merges two sections
   on the record page, and nothing notices.

A state machine fixes all three, because a graph can route on the state it just
produced. A straight-line function cannot.

---

## Target graph

```
retrieve ─┬─(tool_calls present)──> search ─┬─(rounds < MAX_RETRIEVAL_ROUNDS)──> retrieve
          └─(no tool call)────────────────┴─> backfill ──> draft ──> validate
                                                                        │
                                                (violations, max once)  ├──> revise ──> END
                                                                        └──> END
```

| Node | Work | LLM calls |
|---|---|---|
| `retrieve` | Asks the model which searches to run. | 1 |
| `search` | Runs every tool call in the last assistant message, collects and deduplicates chunks, appends one tool message per call. | 0 |
| `backfill` | Runs only when no TMEP chunk was collected. Sends one deterministic query built from the mark and the goods. | 0 (one embedding) |
| `draft` | The four-section analysis. | 1 |
| `validate` | Deterministic checks on the draft. | 0 |
| `revise` | One repair call naming the violations. | 1, only on failure |

Happy path: 2 to 3 LLM calls, the same as today. Worst case: 4.

---

## Ordered steps

### Step 1 — Add the dependency

1. `backend/.venv/bin/pip install "langgraph>=1.0"`. Confirm the interpreter:
   the repository has a root `.venv` **and** `backend/.venv`, and only
   `backend/.venv` carries `openai`, `torch`, and `chromadb`. Install into
   `backend/.venv`.
2. Add `langgraph>=1.0` to `backend/requirements.txt`, under the RAG block.
3. Regenerate `backend/requirements.lock` from the repository root with
   `pip-compile --output-file=backend/requirements.lock backend/requirements.txt`,
   the command in the lock header. The
   deploy job installs from the lock, so a missing entry breaks production while
   the local tests stay green.
4. Check the transitive weight before you commit. LangGraph pulls
   `langgraph-checkpoint`, `langgraph-prebuilt`, `langgraph-sdk`, and
   `langchain-core`. `langchain-text-splitters` already pulls `langchain-core`,
   so the new weight is small, but confirm the Docker image size against
   `docker-compose.yml`.

5. Add `langsmith` to `backend/requirements.txt` as a direct entry. The lock
   already pins `langsmith==0.8.16` through `langchain-core`, but
   `llm_client.py` will import it directly. A direct import that relies on a
   transitive pin breaks when the parent package drops it.

**Verify:** `backend/.venv/bin/python -c "from langgraph.graph import StateGraph; from langsmith.wrappers import wrap_openai"`.

### Step 2 — Add the validation constants to the prompts module

The prompts already live in `backend/mark_checker/services/analysis/prompts.py`,
apart from the code that uses them. The graph imports them from there, so no
import cycle is possible.

1. Do not change `_DOCTRINE_SECTION`, `_SYSTEM_PROMPT`, or `_USER_TMPL` in this
   phase. A prompt change and a control-flow change in one commit make a
   regression impossible to attribute.
2. Add two new constants to `prompts.py`:
   - `REQUIRED_HEADERS` — the four `**Section Title**` lines, in order, copied
     byte for byte from `_SYSTEM_PROMPT`: `**What the model found**`,
     `**Where this mark sits on the trademark spectrum**`,
     `**Why the classifier leaned this way — key signals**`, and
     `**What to do next**`. The third header contains an em dash. Copy it from
     the prompt. Do not type it.
   - `REPAIR_TMPL` — the repair instruction. It takes `violations` and `draft`,
     tells the model to keep the same conclusions and the four headers, and asks
     for the corrected analysis with no preamble.
3. `backend/pyproject.toml` already exempts
   `mark_checker/services/analysis/prompts.py` from `E501` and `RUF001`. No
   change is necessary.

**Verify:** run `ruff check mark_checker/services/analysis/prompts.py` from
`backend/`. Then run `git diff` and confirm that the three old constants did not
change.

### Step 3 — Write the graph module

Write `backend/mark_checker/services/analysis/graph.py`. It belongs to the
`services` layer, so it can import `rag` and `core`, and it must not import
`api`. `tests/unit/test_import_layering.py` enforces that direction.

#### 3a. The state

```python
class AnalysisState(TypedDict, total=False):
    # Inputs, fixed for the whole run.
    mark: str
    description: str
    nice_class: int
    label: str
    prob_distinctive: float
    attributions: list[dict]
    confidence_tier: str
    # Retrieval.
    messages: list[dict]
    tmep: Annotated[dict[str, dict], _merge_chunks]
    ttab: Annotated[dict[str, dict], _merge_chunks]
    rounds: int
    # Drafting.
    draft: str
    violations: list[str]
    revisions: int
```

Two points that decide whether this works:

- `tmep` and `ttab` are **dicts keyed by chunk id**, with a reducer that keeps
  the first chunk seen. That is the deduplication `run_agent()` did with
  `setdefault`, expressed as a LangGraph reducer, so a node returns only the
  chunks it found and never has to merge by hand.
- `messages` has **no reducer**. Each node returns the whole list. The
  provider's chat API needs the assistant message and its tool messages in one
  ordered list, and a naive append reducer makes a partial write during a
  retry produce a message list the API rejects.

#### 3b. Reach the retrieval helpers

Do not copy the tool definitions or the search bodies. Import them inside a
function, as `_retrieve_doctrine()` does today, so that loading the API does not
pull ChromaDB and the embedding model into memory:

```python
def _rag():
    from mark_checker.rag import agent as rag_agent

    return rag_agent
```

`mark_checker` is an installed package, so one absolute import works from
uvicorn and from pytest. Do not add a fallback import.

Wrap the two searches in one `_search(tool_name, query)` helper. It calls
`rag_agent._search_tmep()` or `rag_agent._search_ttab()`. The tests patch that
single name, so they never touch ChromaDB or the embedding model. Import
`format_context` from `mark_checker.rag.retriever` in the same lazy way.

`rag/agent.py` and `rag/retriever.py` stay on disk and unchanged. `run_agent()`
becomes unused by the live path, but the RAG evaluation scripts and
`backend/mark_checker/rag/README.md` still describe it. Deleting it belongs in
a later cleanup, not here.

#### 3c. The nodes

**`_node_retrieve`** — builds the message list on the first pass from
`rag_agent._SYSTEM` and `rag_agent._USER_TMPL`, with the attribution string
built the way `_retrieve_doctrine()` builds it (top 5, skipping `Translation`
and `WordNet Flag`). Calls the model with `tools=rag_agent._TOOLS`,
`tool_choice="auto"`, `max_tokens=200`, `temperature=0.1`.

Keep the Gemini fix: when the assistant message carries `tool_calls` and no
content, set `content=""` before you append it. Without it the follow-up request
is rejected and retrieval silently returns nothing.

Wrap the call in `try/except`. On failure, log a warning, return the message
list unchanged and `rounds + 1`. The run then falls to `backfill`, which still
produces doctrine. **Do not let this failure reach the route**: a dead retrieval
must not turn into a 503 when a full analysis is still possible.

**`_node_search`** — reads `state["messages"][-1]["tool_calls"]`. For each call:

- Malformed JSON arguments or a missing `query` key: append a tool message
  saying the call was skipped, and continue. Every tool call must get a tool
  message, or the next request is malformed.
- A raised search: log, append a tool message naming the backend as
  unavailable, continue.
- Success: collect into the node's own `tmep` / `ttab` dict and append the
  short result line the old loop used, so the model can judge whether to refine.

**`_node_backfill`** — returns `{}` immediately when `state["tmep"]` is
non-empty. Otherwise runs one `_search("search_tmep", ...)` with a query built from the mark,
the description, and fixed doctrine vocabulary. Catches its own exception and
returns `{}`. This is the node that removes weakness 1.

**`_node_draft`** — builds the user content with `_draft_prompt()` (below) and
makes the analysis call with today's parameters. Keep the existing empty-content
guard: raise `RuntimeError` naming `finish_reason`. That is the one exception
the route must see, and `analyze()` already maps it to a 503.

**`_node_validate`** — no LLM call. Collects `violations`:

- Any of `REQUIRED_HEADERS` missing from the draft.
- Word count above `WORD_BUDGET`.
- Any `TMEP §NNNN` in the draft not supported by a retrieved chunk.

Use `re.compile(r"TMEP\s*§+\s*(\d+(?:\.\d+)*)")`. It must match `TMEP §1209.01`,
`TMEP § 1202`, and the trailing `(b)` subsection letter must not join the
number.

Support rule: a cited section counts when it equals a retrieved
`section_number`, when a retrieved section starts with `cited + "."`, or when
the cited section starts with `retrieved + "."`. A parent and a child both
carry the same doctrine. Plain `startswith` without the dot is wrong: it would
accept `§120` against `§1209.01`.

**`_node_revise`** — sends system prompt, the original draft prompt, the draft
as an assistant message, and `REPAIR_TMPL`. On any exception or empty content,
log a warning, increment `revisions`, and **keep the first draft**. A repair
failure must never lose an analysis the user could have read.

#### 3d. The edges

| From | Condition | To |
|---|---|---|
| `retrieve` | last message is an assistant message with `tool_calls` | `search` |
| `retrieve` | otherwise | `backfill` |
| `search` | `rounds >= MAX_RETRIEVAL_ROUNDS` | `backfill` |
| `search` | otherwise | `retrieve` |
| `backfill` | always | `draft` |
| `draft` | always | `validate` |
| `validate` | `violations` and `revisions < MAX_REVISIONS` | `revise` |
| `validate` | otherwise | `END` |
| `revise` | always | `END` |

Set `recursion_limit` on `invoke()` to `2 * MAX_RETRIEVAL_ROUNDS + 8`. The
default of 25 also holds, but an explicit limit turns a future edge mistake into
a clear error instead of a long loop against a paid API.

#### 3e. Compilation and entry point

Compile once into a module-level cache. The graph holds no per-request state, so
one compiled graph serves every request. Compiling per request wastes work on
the hot path.

`run_analysis(...)` invokes the graph and returns
`{"analysis": str, "sources": dict | None}` — the exact shape `analyze()` and
`update_query_stage()` already consume. Build `sources` as
`{"tmep": [...], "ttab": [...], "rounds": int}` from the state dicts, and return
`None` when both lists are empty, because `AnalyzeResponse.sources` is optional
and the frontend branches on it.

Log one summary line at the end: elapsed time, rounds, revisions, and the two
chunk counts. Keep the per-node timing lines the old code had, so the Phase 9
latency logs stay comparable.

#### 3f. Tracing metadata

Pass a `config` to `invoke()` so that each LangSmith trace is easy to find and
filter:

```python
config = {
    "recursion_limit": 2 * MAX_RETRIEVAL_ROUNDS + 8,
    "run_name": "llm-assess",
    "tags": ["analysis", LLM_PROVIDER],
    "metadata": {"model": LLM_MODEL, "nice_class": nice_class, "label": label},
}
```

Do not put the mark or the description in `metadata`. Metadata stays visible
when `LANGSMITH_HIDE_INPUTS=true` hides the inputs.

Node names become span names in the trace, so keep the short names from the
table in 3c (`retrieve`, `search`, `backfill`, `draft`, `validate`, `revise`).
When tracing is off, LangGraph ignores this config except `recursion_limit`.

#### 3g. Configuration

| Variable | Default | Effect |
|---|---|---|
| `RAG_MAX_ROUNDS` | 2 | Maximum retrieval rounds. |
| `ANALYSIS_MAX_REVISIONS` | 1 | Maximum repair passes. |
| `ANALYSIS_WORD_BUDGET` | 480 | Word limit `validate` enforces. |
| `LANGSMITH_TRACING` | unset | `true` turns on LangSmith traces. Leave it unset in production unless you accept that prompts go to LangSmith. |
| `LANGSMITH_API_KEY` | unset | The LangSmith key. Tracing needs it. |
| `LANGSMITH_PROJECT` | `default` | Set it to `mark-checker` so that the traces go to one project. |
| `LANGSMITH_HIDE_INPUTS`, `LANGSMITH_HIDE_OUTPUTS` | unset | `true` removes the prompts or the completions from the traces and keeps the graph shape and the timings. |

480, not 400: the prompt says "under ~400 words", and a hard 400 would fire a
repair on nearly every good draft. Set the gate above the target.

Add all of them to `.env.example` with a one-line comment each. Leave
`LANGSMITH_TRACING` commented out.

#### 3h. Wrap the LLM client

In `backend/mark_checker/core/llm_client.py`, wrap the client inside
`get_llm_client()` only when tracing is on:

```python
client = OpenAI(api_key=key, base_url=_CONFIG["base_url"], timeout=30.0, max_retries=1)
if os.getenv("LANGSMITH_TRACING", "").strip().lower() == "true":
    from langsmith.wrappers import wrap_openai
    client = wrap_openai(client)
return client
```

Three points:

- The wrap happens once, because `get_llm_client()` has `@lru_cache`. A change
  to `LANGSMITH_TRACING` needs a restart. Write that in the docstring.
- The wrapped client keeps the same `chat.completions.create()` signature and
  raises the same `openai` exceptions. The 429 and `APIError` handlers in
  `analyze.py` still see the original exception types. Confirm this in the
  live run in Step 6.
- The import stays inside the `if`, so a production image with tracing off
  never loads the wrapper.

Without this wrap, the trace shows the nodes and their timings, but not the
prompts, the tool calls, or the token counts.

### Step 4 — Reduce `analyze_trademark()` to a wrapper

`analyze_trademark()` in `services/analysis/__init__.py` keeps its signature and
its return shape. `mark_checker/api/analyze.py` calls it through
`run_in_threadpool`. The route tests patch
`mark_checker.api.analyze.analyze_trademark` in `tests/api/conftest.py`,
`tests/api/test_analyze_errors.py`, and `tests/api/test_analyze_turnstile.py`.

It now does three things:

1. Call `get_llm_client()` once, so a missing API key raises before the graph
   starts. `analyze()` maps that `RuntimeError` to a 503.
2. Compute `_confidence_tier(prob_distinctive)` from `tiers.py`. Do not change
   `tiers.py`: the tier is the classifier's own rule, not prompt text.
3. Call `run_analysis()` from `graph.py` and return its result.

Delete `services/analysis/doctrine.py`, because the graph replaces
`_retrieve_doctrine()`. The graph imports `_field_value` from `tiers.py` for
`_draft_prompt()`. Keep `__all__ = ["analyze_trademark"]`.

**Verify:** `grep -rn "analyze_trademark\|_retrieve_doctrine" backend/mark_checker tests`
shows the route, the wrapper, and the route test patches. It shows no
`_retrieve_doctrine`.

### Step 5 — Tests

Write `tests/unit/test_analysis_graph.py`. Every LLM call and every search is faked,
so the suite stays offline and fast.

Fakes:

- `_message(content, tool_calls)` — a `SimpleNamespace` with `content`,
  `tool_calls`, and a `model_dump(exclude_none=True)` that returns the dict
  shape the real SDK returns.
- `FakeClient(scripted)` — pops one scripted message per chat call and records
  the kwargs, so a test can assert on the prompt that was sent.
- `_chunks(tool_name)` — chunk dicts with `metadata["section_number"] =
  "1209.01"` and the TTAB metadata keys `format_context` reads.

Patch `get_llm_client` and `_search` on the graph module with
`patch.object`.

Add an autouse fixture to the test file that runs
`monkeypatch.delenv("LANGSMITH_TRACING", raising=False)`. A developer with
tracing on in `.env` must not send fake test runs to LangSmith. The
`set -a; . ./.env` step below loads that variable too.

Required cases:

| Test | Asserts |
|---|---|
| Happy path | Four headers present, `sources` carries both lists, and the draft prompt contains `LEGAL DOCTRINE`. |
| Invented citation | `§1052` is gone from the final text and exactly 3 chat calls were made. |
| Missing header | The repair pass ran and the final text has all four headers. |
| Valid draft | No repair pass: exactly 2 chat calls. |
| Backfill | The agent calls no tool, `search_ttab` returns nothing, and `sources["tmep"]` is still non-empty. |
| Dead retrieval | Every search raises. `sources` is `None` and the analysis still has its headers. |
| Empty draft | `pytest.raises(RuntimeError, match="empty analysis")`. |
| Failed repair | The repair call raises and the first draft is returned unchanged. |
| Tracing off | With `LANGSMITH_TRACING` unset, `get_llm_client()` returns a plain `OpenAI` instance. Call `get_llm_client.cache_clear()` before and after. |
| Section support | Parametrized: `1209`/`{1209.01}` true, `1209.01`/`{1209}` true, `1052`/`{1209.01}` false, `120`/`{1209.01}` false. |

Two traps to avoid when scripting the fakes:

- When the scripted assistant message carries tool calls and `rounds` is still
  below the maximum, the graph goes **back to `retrieve`**. Script a second
  no-tool message, or the fake runs out of messages inside `draft`.
- In the failed-repair test, select the repair call by `len(kwargs["messages"])
  == 4`, not by a call counter. The counter changes whenever the retrieval path
  changes, and the test then fails for the wrong reason.

**Verify:** the environment. `tests/api/conftest.py` imports
`mark_checker.main`, which needs `SESSION_SECRET` and `GOOGLE_CLIENT_ID`. The new
file is a unit test and must not import `mark_checker.main`. Run
`set -a; . ./.env; set +a` before the full suite, or the API tests error at
setup.

### Step 6 — Full verification

1. `set -a; . ./.env; set +a; backend/.venv/bin/python -m pytest tests -q`.
   The baseline on 2026-09-13 is 75 passed, 63 skipped. Expect 88 passed after
   the new file lands (8 single cases, 4 parametrized section cases, and the
   tracing case), with the same 63 skipped, because `backend/model/` is
   absent locally.
2. `backend/.venv/bin/python -m ruff check` and `ruff format --check` on every
   touched file. Run ruff from `backend/`, because `pyproject.toml` lives there
   and the per-file ignores are relative to it.
3. One live run against the real provider with `RAG_MAX_ROUNDS=2`. Read the
   logs and confirm: the retrieval rounds, whether `backfill` fired, whether
   `validate` found violations, and the total latency against the Phase 9
   numbers.
4. Repeat the live run with `LANGSMITH_TRACING=true`. Open the trace in
   LangSmith and confirm: the six node names appear, the retrieval loop shows
   one span per round, the LLM spans show the prompts and the token counts, and
   the run carries the `llm-assess` name and the provider tag. Then set a wrong
   `LANGSMITH_API_KEY` and confirm that the analysis still returns.
5. Open the record page in the frontend for that run. `parseSections()` must
   return four sections, and the sources panel must still render.

---

## Failure paths — trace each one before you ship

| Failure | Required result |
|---|---|
| The retrieval planning call raises | `backfill` still runs, the draft still happens, `sources` may be `None`. No 5xx. |
| A ChromaDB search raises | A tool message records it, the run continues, `sources` is `None` when nothing was collected. |
| Malformed tool arguments | One tool message per call is still appended, the next request stays valid. |
| The agent calls no tool at all | `backfill` supplies TMEP doctrine. This is the common Gemini case when the thinking budget eats the 200-token cap. |
| The draft returns empty content | `RuntimeError` naming `finish_reason`, mapped to a 503 by `analyze()`. |
| The repair call raises or returns empty | The first draft is returned. The user sees an analysis. |
| The provider returns 429 or `APIError` | The exception leaves `invoke()` unwrapped and reaches the handlers in `analyze.py`, which already split billing, daily quota, and per-minute limits. **Do not catch broad exceptions in `draft` or `revise`**, or those handlers stop working and every provider limit turns into a generic 503. |
| Every retrieval path returns nothing | The draft runs with no doctrine block, exactly as today, and `validate` then rejects any TMEP citation, because the retrieved set is empty. Confirm the repair prompt can satisfy that: the model must be able to drop the citation and say no applicable section was retrieved, which `_SYSTEM_PROMPT` already allows. |

| LangSmith is unreachable or the key is wrong | The langsmith client sends traces from a background thread and logs the error. The request returns a normal analysis. No 5xx. |
| `LANGSMITH_TRACING=true` with no `LANGSMITH_API_KEY` | The same as above: a logged warning, no request failure. Do not add a startup check that raises, because tracing is not needed to serve a request. |
| Tracing on during the test run | The autouse fixture removes the variable, so no trace leaves the machine. |

The "every retrieval path returns nothing" row is the one to test by hand. A validator that demands a citation
the model cannot supply would loop the repair pass for nothing.

---

## Risks

1. **Latency.** A repair pass adds a full 1000-token call. Measure the repair
   rate on the first day. If it fires on most requests, the prompt is the
   problem, not the draft — fix the prompt rather than raising the budget.
2. **Free-tier request count.** Phase 9 sized the Gemini free tier against three
   requests per analysis. The worst case is now four. Divide the daily cap by
   four, not three, and update the number in `docs/ENGINEERING.md`.
3. **A false invented-citation verdict.** The support rule only sees TMEP
   chunks. If a TTAB chunk quotes a TMEP section the TMEP search did not return,
   a correct citation is flagged. Accept it for now: the repair pass replaces
   the citation with one that was retrieved, which is still accurate.
4. **Data sent to LangSmith.** With tracing on, LangSmith cloud receives the
   user's mark, description, the retrieved doctrine, and the full analysis.
   Keep tracing off in production by default. If production tracing is needed,
   set `LANGSMITH_HIDE_INPUTS=true` and `LANGSMITH_HIDE_OUTPUTS=true`, and
   record the decision in `docs/ENGINEERING.md`.
5. **A header drift.** `REQUIRED_HEADERS` must match the headers in
   `_SYSTEM_PROMPT` exactly. `parseSections()` accepts any bold line, so the
   frontend does not catch a drift. If a later phase rewords a header, change
   `REQUIRED_HEADERS` in the same commit. Put that note in a comment next to
   both constants.

---

## Out of scope

- No checkpointer and no resume. That needs predict and explain inside the same
  graph, which is a whole-pipeline change.
- No streamed node events to the frontend. The hook still waits for one JSON
  response.
- No document grading node that scores each chunk for relevance. `backfill`
  covers the empty case; per-chunk grading costs another LLM call and should be
  judged on the logs this phase produces.
- No deletion of `rag/agent.py` or `rag/retriever.py`.
- No prompt rewording.
- No LangGraph Studio (`langgraph dev`) and no `langgraph.json`. Add them later
  as a development tool if the traces are not enough.
- No LangSmith datasets or evaluations. The RAG evaluation scripts stay as
  they are.

---

## Deliverables

| File | Change |
|---|---|
| `backend/mark_checker/services/analysis/graph.py` | New. State, nodes, edges, `run_analysis()`. |
| `backend/mark_checker/services/analysis/prompts.py` | Adds `REQUIRED_HEADERS` and `REPAIR_TMPL`. |
| `backend/mark_checker/services/analysis/__init__.py` | Reduced to the wrapper. |
| `backend/mark_checker/services/analysis/doctrine.py` | Deleted. |
| `backend/mark_checker/core/llm_client.py` | The opt-in `wrap_openai()` wrap. |
| `tests/unit/test_analysis_graph.py` | New. The ten cases above, and the fixture that turns tracing off. |
| `backend/requirements.txt`, `backend/requirements.lock` | `langgraph>=1.0`, `langsmith`. |
| `.env.example` | The three analysis variables and the four LangSmith variables. |
| `docs/ENGINEERING.md` | The new worst-case request count per analysis, and how to turn on tracing and what data it sends. |
| `backend/mark_checker/rag/README.md` | A note that the live path now runs the graph, and `run_agent()` serves the evaluation scripts. |
