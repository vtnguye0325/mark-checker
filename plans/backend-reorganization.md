# Codebase reorganization

Tracker for the reorganization that runs before Phase 10 (the LangGraph
analysis agent in `plans/phase-10-langgraph-analysis-agent.md`).

Status keys: `[x]` done, `[ ]` open.

## Done and committed

- [x] **Step 1 — Rename the package.** `app` became `mark_checker`, so the
      import root matches the project name and the installed distribution.
- [x] **Step 2 — Split the API layer.** One router per route file under
      `backend/mark_checker/api/`: `analyze`, `auth`, `explain`, `history`,
      `predict`. `main.py` only builds the app and includes the routers.
- [x] **Step 3 — Extract the core layer.** `backend/mark_checker/core/` holds
      `auth`, `db`, `limiter`, `llm_client`, `llm_errors`, `models`, and
      `turnstile`. Provider errors now map in one app-wide handler.
- [x] **Step 4 — Group the services and the RAG code.** Pydantic models moved
      to `schemas/`, business logic to `services/` (with the prompt and
      doctrine code under `services/analysis/`), and retrieval to `rag/`
      (with the loaders under `rag/ingest/`). `tests/test_import_layering.py`
      guards the direction of the imports.

## Done, in the working tree, not committed

These two fixes came from the review of Steps 1-4.

- [x] **Fix 1 — `scripts/smoke_test.py` imports.** The script still imported
      the deleted `app` package behind a `sys.path` hack, so every run died
      with an `ImportError`. It now imports the installed package.
- [x] **Fix 2 — A failed stage 3 no longer reads as pending.** Step 3 moved
      the provider error mapping to an app-wide handler, so an
      `openai.APIError` skipped `update_query_stage` and the history page
      showed the check as pending for good. The fix spans five files:
      - `core/models.py`: new `queries.analysis_error` column.
      - `core/db.py`: an idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
        in `init_models`, because `create_all` never adds a column to a table
        that already exists. **Delete this block in Step 5.**
      - `core/llm_errors.py`: `llm_error_detail()` splits the mapping out of
        the response, so the route and the handler read the same text.
      - `api/analyze.py`: an `except openai.APIError` branch records the
        failure on the row, then re-raises for the handler.
      - `api/history.py` and `frontend/src/components/HistoryPanel.jsx`: carry
        `analysis_error` through to the user.
      - `tests/test_api.py`: two regression tests. `tests/test_history.py`:
        the fake row gained the new field.

Suite after these fixes: 64 passed, 63 skipped. Ruff is clean on the touched
files.

### Step 5

- [x] **Step 5 — Add Alembic.** `alembic` is a backend dependency, the
      revisions live in `backend/alembic/versions/`, and `init_models` upgrades
      the database to `head` on every start.
      - `0001_baseline` holds the schema as it stood before
        `queries.analysis_error`; `0002_query_analysis_error` adds that column.
      - A database that predates Alembic gets stamped with `0001_baseline`
        first, so the upgrade never tries to rebuild the live tables.
      - `create_all` and the `_BACKFILL_DDL` block from Fix 2 are gone.
      - `docs/DEPLOYMENT.md` gained a "Database migrations" section.
      Checked against a throwaway Postgres 16: a fresh database, a second boot,
      and a legacy database without `analysis_error` all end on
      `0002_query_analysis_error`. `alembic revision --autogenerate` reports no
      drift against the models.

## Done, in the working tree, not committed (Steps 6-8)

- [x] **Step 6 — Consolidate the tests and the scripts.** `tests/unit/` holds
      the pure-function, model, and import-layering tests; `tests/api/` holds
      the route tests. `test_api.py` split into `test_health.py`,
      `test_predict.py`, `test_analyze_turnstile.py`, and
      `test_analyze_errors.py`.
      - `tests/conftest.py` keeps only the model-dependent skip rule. The rule
        now names `test_predict.py`, where every validation case ends in 422.
      - `tests/api/conftest.py` holds the shared fixtures: `client`, the
        auth-and-session override, `predict_payload`, `analyze_payload`,
        `mock_turnstile_client`, `rate_limit_error`, `post_analyze_raising`,
        and `history_row`.
      - `scripts/build_rag_index.py` no longer trips `E402`, and
        `scripts/eval_rag_retrieval.py` no longer trips `F541`.
      - `scripts/README.md` says what each script needs. `__pycache__` is out
        of the index.

- [x] **Step 7 — Give the frontend one API module.**
      `frontend/src/lib/api.js` holds one `request()` helper plus `predict`,
      `explain`, `assess`, `history`, `historyRecord`, `me`,
      `signInWithGoogle`, and `signOut`.
      - `request()` owns the base URL, the cookie mode, the single 401 retry,
        and the error reading. A non-2xx response throws an `ApiError` that
        carries `status`, `detail`, and `retryAfter`, so a `detail` string and
        a `Retry-After` header reach every caller the same way.
      - `HistoryPanel.jsx`, `useTrademarkPipeline.js`, and `useAuth.js` hold no
        URL and call no `fetch`.

- [x] **Step 8 — Clean up the docs.** The live set is `API.md`,
      `DEPLOYMENT.md`, `DEVELOPMENT.md`, `ENGINEERING.md`,
      `DESIGN_PRINCIPLES.md`, and `RAG.md`.
      - `docs/archive/` holds the finished plans (`PLAN.md`,
        `IMPLEMENTATION_PLAN_D.md`, `README_REWRITE_PLAN.md`,
        `FRONTEND_CRITIQUE.md`) and the generated output (the
        architecture-review HTML and `Final_Report.pdf`), with a README that
        says what each one is.
      - `.gitignore` now drops future `docs/architecture-review-*.html` and
        `docs/langgraph-workflow*` output.
      - The root `README.md` gained a Documentation table that points at the
        live set. `docs/DEVELOPMENT.md` carries the new test layout.

### Fixes from the review of Steps 6-8

The review found four defects in code that predates this work.

- [x] **`api/analyze.py`** — the stage-3 `RuntimeError` path returned
      `str(exc)` to the client, so a missing provider key or a missing corpus
      path left the backend. It now returns `_RUNTIME_FAILURE_DETAIL`, the same
      text that the row carries.
- [x] **`services/query_store.py` and `api/predict.py`** — both caught
      `SQLAlchemyError` only. An unreachable Postgres makes asyncpg raise a
      bare `OSError` subclass outside that hierarchy, so the error escaped and
      masked the provider error with a 500. Both catches now name `OSError`,
      and a failed rollback no longer escapes either.
- [x] **`core/llm_errors.py`** — `_BILLING_MARKERS` held "billing" and "check
      your plan", the exact words of a Gemini free-tier quota 429, so an
      ordinary quota error read as billing exhaustion and returned a 503 with
      no retry guidance. The markers are narrow now, and the daily-quota check
      runs first.
- New tests: `tests/unit/test_query_store.py` and
  `tests/unit/test_llm_error_mapping.py`.

Suite after Steps 6-8: 75 passed, 63 skipped. Ruff is clean on `backend/`,
`scripts/`, and `tests/`. The frontend build passes.

## Then

Start Phase 10 on the reorganized tree.
