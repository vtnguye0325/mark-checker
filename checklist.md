# Production-Readiness Checklist — Trademark Distinctiveness App

Review date: 2026-06-04
Scope: FastAPI backend (`backend/`), React/Vite frontend (`frontend/`), Docker/Compose deployment.

Legend: 🔴 Blocker · 🟠 High · 🟡 Medium · 🟢 Nice-to-have · ✅ Already good

---

## ✅ What's already solid

- [x] Clean service/route separation (`routes/` thin, `services/` holds logic).
- [x] Pydantic request validation with field constraints (`min_length`, `ge/le` on `nice_class`).
- [x] Multi-stage frontend Docker build; nginx serves static assets and proxies API.
- [x] Healthcheck wired into compose with `depends_on: service_healthy`.
- [x] Model cached with `lru_cache`, runs under `torch.no_grad()`, batched attribution in one forward pass.
- [x] Request cancellation on the frontend via `AbortController`.
- [x] `.env`, `myenv/`, `model/`, `.DS_Store` are gitignored and **not** tracked. Secrets not in git.
- [x] `.dockerignore` excludes `.env`, `.venv`, `model/`, caches.
- [x] Frontend dependency lock file (`package-lock.json`) committed.
- [x] API + service unit tests exist and cover validation paths.

---

## 🔴 Blockers — fix before any production deploy

- [ ] **Rate limiting is defeated behind nginx.** `app/limiter.py` uses `get_remote_address`, which reads `request.client.host`. Behind the nginx proxy every request appears to come from the nginx container IP, so all users share one `100/hour` bucket — one user can exhaust everyone's quota, and per-user limiting does not work. nginx already sets `X-Forwarded-For` (`frontend/nginx.conf`), but the backend ignores it.
  - Fix: launch uvicorn with `--proxy-headers --forwarded-allow-ips="*"` (or the nginx subnet) **and** configure slowapi to key off the forwarded client IP. Verify with two different client IPs.
- [ ] **No request-size / string-length caps → DoS vector.** `PredictRequest` / `ExplainRequest` / `AnalyzeRequest` set `min_length` but no `max_length` on `mark`, `description`, `translation`, `pseudo_mark`. A multi-MB `description` is tokenized and (in `/analyze`) sent to a paid LLM. Add `max_length` to every string field (e.g. mark ≤ 200, description ≤ 2000) and set nginx `client_max_body_size` (e.g. `1m`).
- [ ] **`/analyze` LLM call has no timeout and abuse exposure.** `llm_service.analyze_trademark` builds an `OpenAI` client per request with no `timeout=` and no retry budget; a slow DeepSeek response ties up a worker thread indefinitely. It's also an unauthenticated, money-spending endpoint. Add a client timeout (e.g. 30s), cap retries, and gate/throttle it harder than the local-inference endpoints (or require a key).
- [ ] **WordNet data is downloaded at request time, not baked into the image.** `text_formatter._wordnet_flag` calls `nltk.download("wordnet")` inside the request path on first use (confirmed not present in `backend/Dockerfile`). First request does a network fetch — slow, and **fails in an offline/locked-down prod network**, silently degrading every prediction (always "mark absent in Wordnet"). Bake `python -m nltk.downloader wordnet omw-1.4` into the Dockerfile.

## 🟠 High — correctness & resilience

- [ ] **Field-attribution split is fragile and can misalign.** `model_service.explain_one` splits the formatted string on `". "` and zips parts to `_FIELD_LABELS` positionally. NICE descriptions and user `description` text can contain `". "`, producing more than 8 parts and shifting every field's `value`/`attribution` — wrong explanations shown to users. Format with an unambiguous delimiter, or carry field boundaries from `format_input` instead of re-splitting.
- [ ] **Cold-start latency / health lies about readiness.** The model loads lazily on the first `/predict`. `/health` returns `{"status":"ok"}` before the model is loaded, so compose marks the backend "healthy" and the frontend goes live while the first real request blocks on a multi-second model load. Preload the model in a FastAPI `startup` event (or a `lifespan` handler) and have `/health` (or a separate `/ready`) report model-loaded status.
- [ ] **Single uvicorn process, no worker management.** `CMD ["uvicorn", ...]` runs one process with no `--workers` and no supervisor. CPU-bound torch inference will serialize; one crash takes the service down. Use gunicorn+uvicorn workers (or `--workers N`) sized to CPUs, and confirm the `lru_cache` model load cost per worker is acceptable (consider memory).
- [ ] **Silent frontend failures on `/explain` and `/analyze`.** In `App.jsx`, `handleExplain` / `handleAnalyze` only `console.error` on failure — the user sees nothing after a successful prediction if these fail. Surface a non-blocking inline error/notice for each.
- [ ] **No global error handling / logging on the backend.** Unhandled exceptions in `predict_one` (e.g. model load failure) return a bare 500 with no logged context. Add a logging config (structured/JSON), request logging, and an exception handler that logs the traceback while returning a safe message.

## 🟡 Medium — hardening & reproducibility

- [ ] **Containers run as root.** Neither Dockerfile sets a non-root `USER`. Add a dedicated unprivileged user in both `backend/Dockerfile` and the nginx stage.
- [ ] **Unpinned Python dependencies → non-reproducible builds.** `backend/requirements.txt` uses loose/no pins (`torch>=2.1.0`, bare `numpy`, `nltk`, `accelerate`). A rebuild can pull breaking versions. Pin exact versions (and ideally a hash-locked file via pip-tools/uv).
- [ ] **Model is pinned only by repo id, no revision.** `docker_download_model.py` / `snapshot_download` take `HF_MODEL_ID` with no `revision=`. Pin a commit SHA for supply-chain integrity and reproducibility.
- [ ] **`trust_remote_code=True`** in `model_service._load` executes arbitrary code from the model repo at load time. Acceptable only if you own/trust the repo and pin its revision (see above) — document this and the pin.
- [ ] **No TLS / security headers.** `frontend/nginx.conf` listens on plain `:80` with no `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, or CSP, and no cache headers for hashed assets. Terminate TLS (or document the upstream LB that does), add security headers, and set long-lived `Cache-Control` for `/assets/*` while keeping `index.html` uncached.
- [ ] **CI is absent.** No `.github/workflows`. Add a pipeline that runs backend tests, frontend build, and lint on every PR. Note: current API tests (`tests/test_api.py`) load the real model, so CI needs the model available or those tests mocked — decide and wire it.
- [ ] **No frontend lint/format config.** No ESLint/Prettier. Add configs and a `lint` script so `npm run build` is gated on clean lint.

## 🟢 Nice-to-have / polish

- [ ] No `LICENSE` file at repo root.
- [ ] `/predict` and `/explain` re-run `format_input` independently and the frontend calls `/predict` then `/explain` with the same payload (two model forward passes). Consider returning attributions from `/predict` or caching the formatted input to halve inference cost.
- [ ] `analyze_trademark` constructs a new `OpenAI` client on every call — hoist to a module-level singleton.
- [ ] Add metrics (Prometheus `/metrics`) and basic latency/error dashboards.
- [ ] Add an API version prefix (`/v1/...`) so future changes don't break clients.
- [ ] `start.sh` and `docker-compose.dev.yml` are dev-only — confirm they're documented as such in the README so they aren't mistaken for prod entrypoints.

---

## Suggested order of attack

1. Rate-limit/proxy-headers + input size caps + LLM timeout (🔴 security/abuse).
2. Bake WordNet into the image (🔴 correctness in prod network).
3. Fix the attribution split bug (🟠 user-facing correctness).
4. Model preload + readiness health + multi-worker serving (🟠 reliability).
5. Logging, non-root containers, pinned deps + model revision (🟡 hardening).
6. CI, lint, TLS/security headers (🟡 process & edge).
