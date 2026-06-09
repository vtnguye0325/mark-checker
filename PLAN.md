# Production Readiness Review

**App:** Trademark Distinctiveness Classifier
**Score:** 5 / 10
**Date:** 2026-06-08

---

## Summary

The codebase has a solid architectural foundation — clean service/route separation, Pydantic validation, rate limiting, multi-stage Docker builds, a comprehensive test suite (89 tests), and thoughtful UI state management. However, several critical gaps in observability, error resilience, and deployment automation make this not yet ready for real users in a live environment. The three highest-priority issues are: (1) the ML model loads on the first user request because `warm_up()` is never wired up, (2) there is no logging or global error handling anywhere, and (3) there is no CI/CD pipeline — every deploy is manual and unrepeatable.

---

## Environment & Configuration

| Status | Finding | Recommendation |
|--------|---------|----------------|
| ⚠️ | **Live DeepSeek API key in `.env` on disk** (`sk-20126b2ea2644d248f2623948f9cd3a2`). Also passed via `docker-compose.yml` `environment:` — visible in `docker inspect`. | Rotate the key immediately. Use Docker secrets or a vault (e.g., 1Password CLI, `sops`) instead of compose `environment:`. |
| ⚠️ | **`HF_TOKEN` passed as Docker build-arg** — embeds the token in the image layer history (`docker history`). | Use Docker BuildKit `--secret` mounts instead of `ARG`. This is already documented in README as a known improvement. |
| ⚠️ | **Single `.env` file for all environments.** `CORS_ORIGINS` defaults include localhost variants even in production. No `.env.dev` / `.env.prod` separation. | Separate into `.env.dev` and `.env.prod`; restrict production CORS origins to the actual deployment domain only. |
| ✅ | `.env` is in `.gitignore`; secrets are not tracked in git. | No action needed. |

## Error Handling & Logging

| Status | Finding | Recommendation |
|--------|---------|----------------|
| ❌ | **No global exception handler on the backend.** Only a `RateLimitExceeded` handler is registered (`backend/app/main.py:26`). Any unhandled exception in `/predict` or `/explain` returns a raw FastAPI 500 with traceback. | Add `@app.exception_handler(Exception)` that logs the full traceback server-side and returns a sanitized JSON response. |
| ❌ | **Zero structured logging.** No `import logging` in any Python file. Only `console.error()` (frontend, 2 calls) and `print()` (download script). No request IDs, no latency tracking. | Add `structlog` or stdlib `logging` with JSON output; log request ID, method, path, status, and duration on every request. |
| ❌ | **No React Error Boundary.** If any component throws during render, the entire React tree unmounts with a blank screen. | Wrap `<App />` in a class-based `<ErrorBoundary>` with `componentDidCatch` and a fallback UI. |
| ❌ | **`warm_up()` is defined but never called** (`backend/app/services/model_service.py:22`). `backend/app/main.py` has no `lifespan` handler. The model loads lazily on the first user request (~5-10s delay). | Wire `warm_up()` into a FastAPI `@asynccontextmanager` lifespan handler so the model loads at boot. |
| ⚠️ | **Frontend silently swallows `/explain` and `/analyze` errors.** `App.jsx:82-84` and `110-112` catch errors but only `console.error()` — no user-facing feedback. | Surface a dismissible error banner or inline warning when attribution or LLM analysis fails. |
| ⚠️ | **Pydantic validation errors exposed raw to users.** Messages like `"field required"` from FastAPI's `RequestValidationError` are passed verbatim to the frontend error banner. | Add an exception handler that maps validation errors to user-friendly messages (e.g., "Mark is required"). |
| ⚠️ | **Backend `/predict` and `/explain` have zero try/catch.** Any model or tokenizer failure propagates as a raw 500 with no structured response. | Wrap route handlers in try/except, log traceback server-side, return a sanitized 500. |

## Performance & Caching

| Status | Finding | Recommendation |
|--------|---------|----------------|
| ❌ | **No Cache-Control headers anywhere.** Neither nginx nor FastAPI sets `Cache-Control`, `ETag`, or `Expires`. Vite produces content-hashed filenames (e.g., `assets/index-abc123.js`) that are ideal for immutable caching, but the config doesn't leverage it. | Add `location /assets/ { expires 1y; add_header Cache-Control "public, immutable"; }` to `frontend/nginx.conf`. Keep `index.html` uncached. |
| ❌ | **`/health` returns OK before the model is loaded.** Docker healthcheck marks the service "healthy" while it's still warming up. The first real request blocks on a multi-second model load. | Have `/health` (or a separate `/ready` endpoint) check `model_service.is_loaded()`. Better yet: wire `warm_up()` into the lifespan so health implies readiness. |
| ⚠️ | **Single uvicorn worker, no concurrency.** `backend/Dockerfile:37` runs `uvicorn` without `--workers`. PyTorch inference blocks the single process, serializing all requests. | Add `--workers 2` (or more) to uvicorn, or use gunicorn with `UvicornWorker`. Monitor memory — PyTorch models are large. |
| ✅ | **Model and WordNet baked into Docker image at build time.** No runtime network downloads. | Good — no action needed. |

## Reliability & Stability

| Status | Finding | Recommendation |
|--------|---------|----------------|
| ❌ | **No CI/CD pipeline.** No `.github/workflows/` exists. Tests (89 across 4 files) must be run manually. Deployment is manual `docker compose up --build -d` with no repeatability guarantees. | Add a GitHub Actions workflow that runs `pytest tests/` on push, builds Docker images, and optionally deploys. |
| ❌ | **No rollback capability.** No release tags, no blue/green deployment, no way to revert a bad deploy quickly. | Document a rollback procedure. Tag Docker images with git SHAs. Keep previous image tags to allow quick revert. |
| ⚠️ | **Python dependencies unpinned.** `requirements.txt` uses `>=` or bare names (`torch>=2.1.0`, bare `numpy`, `nltk`). | Pin all dependencies with hashes (e.g., `pip freeze > requirements-locked.txt`). |
| ⚠️ | **Model revision not pinned.** `docker_download_model.py` calls `snapshot_download` with no `revision=` — builds are non-reproducible. | Pin `revision="<commit-sha>"` in `snapshot_download()`. |
| ⚠️ | **Frontend has no client-side validation library.** Uses `noValidate` on the form with only a truthiness check (`canSubmit`). Invalid data hits the backend before the user knows. | Add basic frontend validation — at minimum, enforce `maxLength` on inputs to match Pydantic limits. |
| ✅ | **Rate limiting implemented.** slowapi with 100/hr default, 20/hr for `/analyze`. Custom `_client_ip()` correctly resolves the real IP from `X-Forwarded-For` (trusts rightmost entry). | Good — no action needed. |
| ✅ | **Pydantic validation on all routes** with `min_length`/`max_length` on strings, range bounds on `nice_class` (1-45) and probabilities (0.0-1.0). | Good — no action needed. |
| ✅ | **Docker healthcheck configured** with 15s interval, 5s timeout, 5 retries, 30s start period. Frontend depends on backend being healthy. | Good — but see the `/health`-lies-about-readiness issue above. |

## Deployment & CI/CD

| Status | Finding | Recommendation |
|--------|---------|----------------|
| ❌ | **No CI/CD pipeline.** Tests exist but aren't automated. Deploy is a manual SSH + docker-compose sequence. | Add GitHub Actions with a workflow file. Steps: run `pytest`, build both images, push to a registry, SSH and deploy. |
| ❌ | **No monitoring or observability.** No metrics endpoint, no Sentry/Datadog, no structured logging. Production issues are invisible until users report them. | Add `prometheus_fastapi_instrumentator` for metrics and Sentry for error tracking. Add Grafana dashboard basics. |
| ⚠️ | **Containers run as root.** No `USER` directive in either Dockerfile. | Add `USER nobody` (or `appuser`) to both Dockerfiles. |
| ⚠️ | **Nginx has no security headers.** No CSP, HSTS, `X-Frame-Options`, or `X-Content-Type-Options`. | Add security headers: `add_header X-Frame-Options "SAMEORIGIN"; add_header X-Content-Type-Options "nosniff";` |
| ✅ | **Multi-stage frontend Docker build** (node → nginx-alpine). Model and WordNet baked into image. `package-lock.json` committed for reproducible npm installs. | Good — no action needed. |

## User Experience

| Status | Finding | Recommendation |
|--------|---------|----------------|
| ✅ | **Loading states for all three phases** — predict shows dot animation, explain shows inline spinner, analyze shows LLM loading card. | Good. |
| ✅ | **Empty states handled** — both "no mark yet" (placeholder icon) and "mark entered, awaiting submission" are shown. | Good. |
| ✅ | **Double-submission protection** — submit button disabled during loading + `AbortController` cancels in-flight requests on re-submit. | Good. |
| ❌ | **No Error Boundary component** — a render crash anywhere in the component tree takes down the entire app. | Add a class-based `<ErrorBoundary>` component wrapping `<App />` in `main.jsx`. |
| ⚠️ | **No toast/notification system** — users receive no success confirmation or ephemeral feedback. Only inline error banners and state transitions. | Consider a lightweight notification library or a simple in-app notification component. |
| ⚠️ | **Google Fonts missing `font-display: swap`** — invisible text during font load (FOUT). | Append `&display=swap` to the Google Fonts URL in `index.html:10-13`. |
| ✅ | **Mobile responsive** — viewport meta tag, `clamp()` font sizes, flex-wrap, `@media (max-width: 768px)` breakpoint. | Consider a tablet breakpoint, but functional as-is. |

---

## Top 3 Fixes

### 1. Wire up `warm_up()` and fix `/health` (Critical)

The model currently loads on the first user request — a ~5-10 second delay that will cause timeouts and a terrible first impression. A ready-to-use `warm_up()` function exists at `backend/app/services/model_service.py:22` but is never called. `backend/app/main.py:40` has a `/health` endpoint that returns `{"status": "ok"}` before the model is loaded, so the Docker healthcheck marks the service "healthy" when it's still warming up.

**Fix:**
```python
# backend/app/main.py
from contextlib import asynccontextmanager
from app.services.model_service import warm_up, is_loaded

@asynccontextmanager
async def lifespan(app: FastAPI):
    warm_up()
    yield

app = FastAPI(title="...", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok" if is_loaded() else "warming_up"}
```

### 2. Add global error handling + structured logging (Critical)

When things break in production, there is no record of what happened. No logging library exists anywhere — only `console.error()` calls on the frontend and `print()` statements in the build script. There is no global exception handler on the backend, so unhandled errors return raw FastAPI 500s with no server-side trace. There is no React Error Boundary, so a render crash produces a blank white screen with no console error surfaced to the user.

**Fix:**
- Backend: add `structlog` or stdlib `logging`, register `@app.exception_handler(Exception)` that logs the full traceback and returns a sanitized JSON error.
- Frontend: wrap `<App />` in a class-based `<ErrorBoundary>` with `componentDidCatch` and a fallback UI.

### 3. Add a CI/CD pipeline (High)

Every deploy is a manual SSH session running `docker compose up --build -d`. There is no automated test runner, no build artifact tagging, and no rollback path. The 89 tests spanning unit, integration, API, and regression coverage are excellent — but they only provide value if they run before every deploy.

**Fix:** Add `.github/workflows/ci.yml` that runs `pytest tests/` on every push, builds both Docker images, and optionally deploys to the server. Tag images with git SHAs to enable rollback.
