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

## Open

- [ ] **Step 6 — Consolidate the tests and the scripts.**
      1. Split `tests/` into `tests/unit/` and `tests/api/`, because
         `test_api.py` now holds route tests, error-mapping tests, and
         Turnstile tests together.
      2. Move the shared builders (`_ANALYZE_PAYLOAD`, `_rate_limit_error`,
         `_post_analyze_raising`, the `_row()` helper in `test_history.py`)
         into `conftest.py` as fixtures.
      3. Fix the ruff errors in the scripts that predate this work:
         `scripts/build_rag_index.py` lines 18-22 (`E402`) and
         `scripts/eval_rag_retrieval.py` lines 248 and 280 (`F541`).
      4. Give `scripts/` a short README that says what each script needs, and
         delete `scripts/__pycache__` from the tree if git tracks it.

- [ ] **Step 7 — Give the frontend one API module.** Three files call `fetch`
      directly: `components/HistoryPanel.jsx`, `hooks/useTrademarkPipeline.js`,
      and `hooks/useAuth.js`. Each repeats the base URL, the credentials mode,
      and its own error reading.
      1. Add `frontend/src/lib/api.js` with one request helper plus a named
         function per endpoint: `predict`, `explain`, `assess`, `history`,
         `historyRecord`, and the auth calls.
      2. Read the error body in one place, so a `detail` string and a
         `Retry-After` header reach the caller the same way every time.
      3. Move the three call sites onto it and keep the components free of
         URLs.

- [ ] **Step 8 — Clean up the docs.** `docs/` mixes live documentation with
      finished plans, generated reports, and binary output.
      1. Keep `API.md`, `DEPLOYMENT.md`, `DEVELOPMENT.md`, `ENGINEERING.md`,
         `DESIGN_PRINCIPLES.md`, and `RAG.md` as the live set.
      2. Move the finished plans (`PLAN.md`, `IMPLEMENTATION_PLAN_D.md`,
         `README_REWRITE_PLAN.md`, `FRONTEND_CRITIQUE.md`) under
         `docs/archive/`, or delete the ones the git history already covers.
      3. Decide what happens to the generated files: the
         `architecture-review-*.html` report, the `langgraph-workflow*`
         HTML, JSON, and PNG output, and `Final_Report.pdf`. Either gitignore
         the generated set or move it out of `docs/`.
      4. Point the root `README.md` at the live set.

## Then

Start Phase 10 on the reorganized tree.
