# Sub-plan — Phase 8, Google accounts and query history

## Goal

Add a Google sign-in to Mark Checker, and store every check that a signed-in user
runs in a Postgres database.

Three decisions set the shape of this phase:

1. **Sign-in.** The browser gets a Google ID token from Google Identity Services.
   The backend verifies that token, then issues its own session JWT in an
   HttpOnly cookie. The backend never asks Google for an access token or a
   refresh token, because the app calls no Google API on the user's behalf.
2. **Database.** Postgres, in a new compose service, reached through async
   SQLAlchemy and `asyncpg`.
3. **Access.** A session is required for all three check endpoints. Anonymous
   visitors see a sign-in screen and nothing else.

## Batches — what to land together

The eleven steps are one order, not four. Ship them as four batches. Each batch
below leaves the app working and is worth its own commit.

One constraint sets the grouping: **Step 6 makes the backend reject every request
that carries no session cookie, and the frontend does not send one until Step
10.** Split those two across batches and the app is broken in between.

Step 11 splits by path. The `/auth` proxy rules are needed in Batch B, the
`/history` rules in Batch D, and the documentation at the end.

### Batch A — Storage, connected to nothing (Steps 1, 2, 3)

Postgres runs, the tables exist, and no route reads or writes them. App behavior
is unchanged.

- Verify: `docker compose up`, `/health` returns ok, and
  `psql -c '\dt'` lists `users` and `queries`.
- Risk: none. Nothing calls the new code.

### Batch B — Sign-in, before anything depends on it (Steps 4, 5, 9, `/auth` proxy)

The Google round trip works end to end, and the check routes still accept
anonymous callers. The gate blocks the UI, so you exercise the real sign-in flow,
but no backend route can break from a missing cookie yet.

- Verify: sign in, `GET /auth/me` returns your email, the `users` row appears with
  a `last_login_at`, sign out clears the cookie, and a reload shows the gate.
- Risk: low. A failure here blocks the UI but corrupts nothing.
- Do the sign-in round trip before Batch C. Google client ids, redirect origins,
  and cookie flags are where this phase actually goes wrong, and this batch
  isolates all three.

### Batch C — The lock and the write (Steps 6, 7, 10 in part)

**Land these together, in one commit.** Step 6 requires a session on the three
check routes, and the pipeline change in Step 10 — `credentials: 'include'` plus
`query_id` — is what keeps them reachable. Step 7 rides along because it needs the
same `request.state.user` that Step 6 introduces.

- Verify: a full check writes one `queries` row with all three stages filled in;
  a check run in a private window returns 401; the sixth `/llm-assess` in an hour
  returns 429.
- Risk: highest in the phase. This is also where the `def` to `async def`
  conversion lands, so watch that a prediction still returns in about the same
  time. A slower response means the CPU work escaped the threadpool.

### Batch D — History (Steps 8, rest of 10, `/history` proxy, docs)

Read-only and additive. `GET /history`, the history panel, and the documentation.

- Verify: the list shows your own checks and no one else's; a `query_id` from
  another account returns 404.
- Risk: low. Nothing here changes the check flow.

### Do not combine

- **Batch B with Batch C.** Debugging a Google client id and a broken pipeline at
  once costs more than the extra commit saves.
- **Batch D with Batch C.** History reads rows that Batch C must first prove it
  writes correctly.

## Checkpoints — the steps inside each batch

Tick a box when the step is written and its verify line passes. Do not start the
next batch until the current batch's verify block passes, because each batch
proves an assumption the next one depends on.

### Batch A — Storage, connected to nothing

- [x] Add the `postgres:16-alpine` service, the `pgdata` volume, the healthcheck,
      and `depends_on: service_healthy` on the backend. Publish no port.
- [x] Add the same to `docker-compose.dev.yml`, with its own volume, and publish
      `127.0.0.1:5432:5432` so `psql` can reach the dev database.
- [x] Add the new variables to `.env.example` and to both compose files.
- [x] Add `sqlalchemy[asyncio]`, `asyncpg`, `PyJWT`, and `google-auth` to
      `backend/requirements.txt`.
- [x] Write `backend/app/db.py` — engine, `AsyncSessionLocal`, `Base`,
      `get_session`, `init_models` with the retry loop.
- [x] Write `backend/app/models.py` — `User` and `Query`, with the composite
      index on `(user_id, created_at DESC)`.
- [x] Call `await init_models()` from `lifespan` in `backend/app/main.py`.
- [ ] **Verify.** `docker compose up --build`. `/health` returns ok. `psql -c
      '\dt'` lists `users` and `queries`. Run a normal check through the UI and
      confirm nothing changed.

Batch A is written. Only the verify step is open.

### Batch B — Sign-in, before anything depends on it

- [ ] Write `backend/app/auth.py` — `verify_google_id_token`,
      `create_session_token`, `current_user`. Stash the user on
      `request.state.user`. Raise at import when `SESSION_SECRET` or
      `GOOGLE_CLIENT_ID` is unset.
- [ ] Write `backend/app/routes/auth.py` — `POST /auth/google`,
      `POST /auth/logout`, `GET /auth/me`. Upsert on `google_sub`.
- [ ] Mount the auth router and set `allow_credentials=True` on the CORS
      middleware in `backend/app/main.py`.
- [ ] Add `location /auth` to `frontend/nginx.conf` and `/auth` to the vite dev
      proxy.
- [ ] Add the GIS script tag to `frontend/index.html`. Add
      `VITE_GOOGLE_CLIENT_ID` as a build arg in `frontend/Dockerfile` and in the
      compose build section.
- [ ] Write `frontend/src/hooks/useAuth.js` with the three-value `status`.
- [ ] Write `frontend/src/components/SignInGate.jsx`, using the poll-until-ready
      pattern from `TurnstileWidget.jsx`.
- [ ] Gate the app in `App.jsx`. Add the email and the sign-out button to
      `RecordBar.jsx`.
- [ ] **Do not touch the three check routes in this batch.** They must still
      accept an anonymous caller, so a sign-in mistake cannot break them.
- [ ] **Verify.** Sign in. `GET /auth/me` returns your email. A `users` row
      appears with `last_login_at` set. Sign out clears the cookie. A reload
      shows the gate, not a flash of the form.

### Batch C — The lock and the write

Land every box below in one commit. Step 6 requires the cookie and the pipeline
change sends it; separately, the app is broken in between.

- [ ] Convert `predict` and `explain` to `async def`, and wrap `predict_one` and
      `explain_one` in `run_in_threadpool`.
- [ ] Add `current_user` and `get_session` to all three check routes.
- [ ] `/ml-predict` inserts the query row and returns `query_id`. A failed insert
      returns 503.
- [ ] `/llm-explain` and `/llm-assess` accept an optional `query_id` and update
      the row where `id = query_id AND user_id = user.id`. A failed update logs
      at ERROR and still returns the result.
- [ ] Add `_session_key` to `backend/app/limiter.py`. Stack the account limit and
      the IP limit on `/llm-assess`.
- [ ] Add `credentials: 'include'` to all three fetches in
      `useTrademarkPipeline.js`, and thread `query_id` through them.
- [ ] Treat a 401 from any stage as an expired session: clear the user, show the
      gate, do not retry.
- [ ] **Verify.** One full check writes one row with all three stages filled in.
      A check in a private window returns 401. The sixth `/llm-assess` in an hour
      returns 429. A prediction still returns in about the same time as before —
      a slower one means the CPU work escaped the threadpool.

### Batch D — History

- [ ] Write `backend/app/routes/history.py` — `GET /history` and
      `GET /history/{query_id}`, both filtered by `user_id` in the query itself.
      Return 404, not 403, for another user's row.
- [ ] Mount the history router. Add `location /history` to `nginx.conf` and to
      the vite proxy.
- [ ] Write `frontend/src/components/HistoryPanel.jsx`. Add the history toggle to
      `RecordBar.jsx`.
- [ ] Render a selected record through the existing part components.
- [ ] Add the styles to `App.css`.
- [ ] Update `.env.example`, `docs/API.md`, `docs/DEPLOYMENT.md`,
      `docs/ENGINEERING.md`, and the README.
- [ ] **Verify.** The list shows your own checks and no one else's. A `query_id`
      from another account returns 404.

## Current state

The app has no database and no user concept. `backend/app/main.py` mounts three
routers — `/ml-predict`, `/llm-explain`, `/llm-assess` — plus `/health`. Cloudflare
Turnstile guards `/llm-assess`, and slowapi rate-limits every route per client IP.
The frontend runs the three endpoints as one pipeline in
`frontend/src/hooks/useTrademarkPipeline.js`, and nginx proxies each path by name.

## Data model

One user row per Google account. One query row per check, not per HTTP call.

### `users`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | Generated by the app. |
| `google_sub` | `text` unique, not null | Google's stable subject id. The identity key. |
| `email` | `text` not null | For display only. |
| `name` | `text` null | Google profile name. |
| `picture` | `text` null | Google avatar URL. |
| `created_at` | `timestamptz` not null | |
| `last_login_at` | `timestamptz` not null | |

Key the user on `google_sub`, never on `email`. A Google account can change its
email address, and the subject id stays the same.

### `queries`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | Returned to the browser as `query_id`. |
| `user_id` | `uuid` FK → `users.id`, not null, indexed | `ON DELETE CASCADE`. |
| `created_at` | `timestamptz` not null, indexed | Sorts the history list. |
| `mark` | `text` not null | |
| `description` | `text` not null | |
| `nice_class` | `integer` not null | |
| `translation` | `text` not null, default `''` | |
| `pseudo_mark` | `text` not null, default `''` | |
| `label` | `text` null | Stage 1 result. |
| `prob_distinctive` | `double precision` null | Stage 1 result. |
| `formatted_input` | `text` null | Stage 1 result. |
| `attributions` | `jsonb` null | Stage 2 result. |
| `analysis` | `text` null | Stage 3 result. |
| `sources` | `jsonb` null | Stage 3 result. |

The stage 2 and stage 3 columns start null. A row with `analysis` still null
means the check stopped after stage 1 or stage 2, which is a fact worth keeping.

Create the tables from SQLAlchemy metadata at startup. Do not add Alembic in this
phase; add it when the schema first needs to change under live data.

## Files to create

**Backend**

- `backend/app/db.py` — async engine, session factory, `Base`, the `get_session`
  dependency, and `init_models()`.
- `backend/app/models.py` — the `User` and `Query` ORM classes.
- `backend/app/auth.py` — Google ID token verification, session JWT mint and
  read, and the `current_user` dependency.
- `backend/app/routes/auth.py` — `POST /auth/google`, `POST /auth/logout`,
  `GET /auth/me`.
- `backend/app/routes/history.py` — `GET /history`, `GET /history/{query_id}`.

**Frontend**

- `frontend/src/hooks/useAuth.js` — session state, sign-in, sign-out.
- `frontend/src/components/SignInGate.jsx` — the Google button and the blocked
  state.
- `frontend/src/components/HistoryPanel.jsx` — the list of past checks.

## Files to change

- `backend/requirements.txt` — add `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.29`,
  `PyJWT>=2.8`, `google-auth>=2.30`.
- `backend/app/main.py` — call `init_models()` in `lifespan`, mount the two new
  routers, set `allow_credentials=True` on the CORS middleware.
- `backend/app/routes/predict.py` — require a session, create the query row,
  return `query_id`.
- `backend/app/routes/explain.py` — require a session, update the query row.
- `backend/app/routes/analyze.py` — require a session, update the query row.
- `backend/app/limiter.py` — add a session-keyed key function and the two new
  `/llm-assess` limits.
- `frontend/src/hooks/useTrademarkPipeline.js` — send the cookie, thread
  `query_id` through the three calls.
- `frontend/src/App.jsx` — wrap the app in the sign-in gate, add the account
  strip and the history view.
- `frontend/src/components/RecordBar.jsx` — show the signed-in email, the history
  link, and the sign-out button.
- `frontend/src/App.css` — styles for the gate, the account strip, and the
  history list.
- `frontend/index.html` — load `https://accounts.google.com/gsi/client`.
- `frontend/vite.config.js` — proxy `/auth` and `/history`.
- `frontend/nginx.conf` — proxy `/auth` and `/history`.
- `frontend/Dockerfile` — accept `VITE_GOOGLE_CLIENT_ID` as a build arg.
- `docker-compose.yml` and `docker-compose.dev.yml` — add the Postgres service
  and the new environment variables.
- `.env.example` — document the new variables.
- `docs/API.md` and `README.md` — document the sign-in step and the new routes.

## New environment variables

| Name | Where | Purpose |
|---|---|---|
| `GOOGLE_CLIENT_ID` | backend | The `aud` value that a Google ID token must carry. |
| `VITE_GOOGLE_CLIENT_ID` | frontend build | The same id, embedded in the bundle. Public. |
| `SESSION_SECRET` | backend | HS256 key for the session JWT. Secret. |
| `SESSION_TTL_HOURS` | backend | Session lifetime. Default 168 (7 days). |
| `COOKIE_SECURE` | backend | `false` for plain-HTTP local dev. Default `true`. |
| `POSTGRES_PASSWORD` | compose | Postgres superuser password. |
| `DATABASE_URL` | backend | `postgresql+asyncpg://markchecker:...@postgres:5432/markchecker` |
| `RATE_LIMIT_ANALYZE_USER` | backend | `/llm-assess` cap per account. Default `5/hour`. |
| `RATE_LIMIT_ANALYZE_IP` | backend | `/llm-assess` cap per IP, across all accounts. Default `20/hour`. |

## Ordered steps

### Step 1 — Postgres in compose

1. Add a `postgres:16-alpine` service to `docker-compose.yml`. Set
   `POSTGRES_USER=markchecker`, `POSTGRES_DB=markchecker`, and
   `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}`.
2. Mount a named `pgdata` volume at `/var/lib/postgresql/data`.
3. Publish no port. The backend reaches Postgres on the compose network. A
   published port bypasses ufw, which is the problem that commit 6fa1994 fixed.
4. Add a healthcheck: `pg_isready -U markchecker`, interval 10s, retries 5.
5. Make the `backend` service depend on `postgres` with
   `condition: service_healthy`, and pass `DATABASE_URL` and the auth variables.
6. Repeat in `docker-compose.dev.yml` with a separate volume name, and there
   publish `127.0.0.1:5432:5432` so `psql` can reach the dev database.

### Step 2 — `backend/app/db.py`

1. Read `DATABASE_URL`. Raise at import time when it is unset, in the same
   fail-closed style as `TURNSTILE_SECRET`.
2. Build `create_async_engine(url, pool_pre_ping=True)`. `pool_pre_ping` drops
   connections that Postgres closed while the backend was idle.
3. Export `AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)`.
4. Write `async def get_session()` that yields one session per request.
5. Write `async def init_models()` that runs `Base.metadata.create_all`. Retry up
   to 10 times, 2 seconds apart, then re-raise. Postgres can pass its healthcheck
   a moment before it accepts connections, and the retry loop covers that gap.

### Step 3 — `backend/app/models.py`

Write the two classes from the tables above, with SQLAlchemy 2.0
`Mapped` / `mapped_column` annotations. Put the index on `queries.user_id` and a
composite index on `(user_id, created_at DESC)`, because the history list always
sorts by time inside one user.

### Step 4 — `backend/app/auth.py`

1. `verify_google_id_token(token) -> dict`.
   - Call `google.oauth2.id_token.verify_oauth2_token(token, Request(), CLIENT_ID)`.
   - That call is blocking and fetches Google's certificates, so run it through
     `starlette.concurrency.run_in_threadpool`. The certificates are cached in
     process after the first call.
   - Reject the token when `email_verified` is not true.
   - Map `ValueError` to `HTTPException(401, "Invalid Google token")`, and a
     transport error to `HTTPException(503, "Cannot reach Google right now")`.
     The two failures need different messages, because one is the user's problem
     and the other is not.
2. `create_session_token(user)` — HS256 JWT with `sub` (the app's user id),
   `email`, `iat`, and `exp`.
3. `current_user(request) -> SessionUser` — read the `session` cookie, decode it,
   return a small dataclass of `id` and `email`. Raise `HTTPException(401)` on a
   missing, malformed, or expired token.
   - **This dependency reads no database.** The JWT is self-contained, so a
     Postgres outage cannot log every user out.
   - Assign the result to `request.state.user` before returning it. Step 7 reads
     it from there, which saves a second decode of the same cookie.
4. Raise at import time when `SESSION_SECRET` or `GOOGLE_CLIENT_ID` is unset.

### Step 5 — `backend/app/routes/auth.py`

1. `POST /auth/google`, body `{ "credential": "<id token>" }`.
   - Verify the token.
   - Upsert the user on `google_sub`: insert, or update `email`, `name`,
     `picture`, and `last_login_at`. Use
     `insert(...).on_conflict_do_update(index_elements=["google_sub"])` so two
     parallel logins cannot race into a duplicate-key error.
   - Set the `session` cookie: `httponly=True`, `samesite="lax"`,
     `secure=COOKIE_SECURE`, `path="/"`, `max_age=SESSION_TTL_HOURS * 3600`.
   - `SameSite=Lax` blocks the cookie on cross-site POST, which is what protects
     the three check endpoints from CSRF. Keep every state-changing route on POST.
   - Return the public user fields.
2. `POST /auth/logout` — delete the cookie. Return 204.
3. `GET /auth/me` — return the session claims, or 401. The frontend calls this
   once on load to learn whether a session exists, because it cannot read an
   HttpOnly cookie itself.

### Step 6 — Record the query in the three check routes

One check writes one row across three calls.

1. `/ml-predict` — add `_user: SessionUser = Depends(current_user)` and
   `session: AsyncSession = Depends(get_session)`. After the prediction, insert
   the query row with the stage 1 fields, and add `query_id` to
   `PredictResponse`.
2. `/llm-explain` — accept an optional `query_id` in the request body. After the
   attributions are computed, update that row's `attributions`, but only where
   `Query.id == query_id AND Query.user_id == user.id`. The `user_id` term is
   what stops one user from writing into another user's row.
3. `/llm-assess` — the same pattern for `analysis` and `sources`.
4. Both routes are `def`, not `async def`, today, so FastAPI runs them in a
   worker thread. An async database session cannot be used from there. Convert
   both to `async def` and wrap the CPU work — `predict_one` and `explain_one` —
   in `run_in_threadpool`, which keeps the current threadpool behavior and frees
   the event loop.

### Step 7 — Re-key the `/llm-assess` rate limit to the account

The IP key was the only identity the app had. Now that a session is required, an
account is the better unit: one office or one campus behind a single address no
longer shares one bucket, and a user cannot reset their cap by changing network.

1. Add `_session_key(request)` to `backend/app/limiter.py`. Return
   `f"user:{request.state.user.id}"` when `current_user` has stashed a user, and
   fall back to `f"ip:{_client_ip(request)}"` otherwise. The `user:` and `ip:`
   prefixes stop a user id and an address from ever colliding on one bucket.
   - The fallback is reachable in one case only: a route that uses this key
     function without also depending on `current_user`. Log at WARNING when it
     fires, because that combination is a wiring mistake.
2. The ordering this relies on: FastAPI resolves dependencies before it calls the
   endpoint, and `@limiter.limit` wraps the endpoint. So `current_user` has
   already run — and has already returned 401 for a bad cookie — by the time the
   key function reads `request.state`.
3. Stack two limits on `/llm-assess`, because neither one alone is enough:

   ```python
   @router.post("/llm-assess", response_model=AnalyzeResponse)
   @limiter.limit(ANALYZE_USER_LIMIT, key_func=_session_key)
   @limiter.limit(ANALYZE_IP_LIMIT)
   async def analyze(...):
   ```

   The account limit is the real cap. The IP limit stays as the backstop against
   one person who registers many Google accounts from one machine, which the
   account limit cannot see. Set the IP limit looser than the account limit, or
   it defeats the change — a shared office address must still fit several users.
4. Leave `/ml-predict` and `/llm-explain` on the IP key. They spend no money, and
   the global `default_limits` already covers them.
5. Keep Turnstile on `/llm-assess`. A Google account is cheap to create, so it is
   not by itself a bot control.
6. **Known limit, do not fix in this phase.** slowapi counts in process memory.
   The counters reset on every deploy, and they are per worker. That is accurate
   enough while the backend runs one uvicorn worker, which it does. A second
   worker or a second container needs shared storage (Redis) before these numbers
   mean anything. Note this in `docs/ENGINEERING.md`.

### Step 8 — `GET /history`

1. `GET /history?limit=50&offset=0` — return the caller's rows, newest first,
   with the summary fields only: `id`, `created_at`, `mark`, `nice_class`,
   `label`, `prob_distinctive`. Cap `limit` at 100.
2. `GET /history/{query_id}` — return one full row, filtered by `user_id`.
   Return 404, not 403, when the row belongs to somebody else, so the endpoint
   does not confirm that the id exists.
3. Filter by `user_id` in the query itself. Never fetch a row and then compare.

### Step 9 — Frontend session

1. Add the GIS script to `index.html`.
2. Write `useAuth`:
   - On mount, `GET /auth/me` with `credentials: 'include'`. A 401 means signed
     out, which is a normal state and not an error to display.
   - `signIn(credential)` posts to `/auth/google`, then stores the returned user.
   - `signOut()` posts to `/auth/logout`, clears the user, and calls
     `google.accounts.id.disableAutoSelect()` so the next visit does not sign the
     user straight back in.
   - Return `{ user, status, signIn, signOut }` where `status` is `loading`,
     `signed-in`, or `signed-out`. The app must render nothing decisive while the
     status is `loading`, or every reload flashes the sign-in screen.
3. Write `SignInGate`: render `google.accounts.id.renderButton` into a ref, in the
   same poll-until-ready pattern that `TurnstileWidget.jsx` already uses for
   `window.turnstile`. Set the callback to `signIn(response.credential)`.
4. `App.jsx` returns the gate while `status !== 'signed-in'`.

### Step 10 — Frontend pipeline and history

1. Add `credentials: 'include'` to all three fetches in
   `useTrademarkPipeline.js`. Without it the browser sends no cookie and every
   call returns 401.
2. Keep `query_id` from the `/ml-predict` response in the hook, and send it in
   the `/llm-explain` and `/llm-assess` bodies.
3. Treat a 401 from any stage as "the session expired": clear the user in
   `useAuth` and show the gate. Do not retry.
4. `HistoryPanel` lists `GET /history`. Selecting a row loads the full record
   from `GET /history/{id}` and renders it through the existing part components,
   because a stored row carries the same fields the live pipeline produces.
5. Put the email, a history toggle, and a sign-out button in `RecordBar`.

### Step 11 — Proxies and docs

1. Add `location /auth` and `location /history` blocks to `nginx.conf`, copying
   the header set from the existing blocks.
2. Add `/auth` and `/history` to the vite dev proxy.
3. Add `VITE_GOOGLE_CLIENT_ID` as a build arg in `frontend/Dockerfile` and in the
   compose build section.
4. Update `.env.example`, `docs/API.md`, `docs/DEPLOYMENT.md`, and the README.

## Failure modes, traced end to end

| Failure | Behavior |
|---|---|
| `DATABASE_URL`, `SESSION_SECRET`, or `GOOGLE_CLIENT_ID` unset | The module raises at import. The container exits and the deploy fails loudly. A silent unauthenticated deploy is the worse outcome. |
| Postgres not ready at startup | `init_models()` retries 10 times over 20 seconds, then re-raises. Compose restarts the backend. |
| Postgres unreachable during `/ml-predict` | Return 503, "Cannot save your check right now." The row is the point of the feature, so a dropped row must be visible. Log at ERROR. |
| Postgres unreachable during `/llm-explain` or `/llm-assess` | Log at ERROR and still return the result. The DeepSeek call already cost money and the user must see the answer. The row keeps a null column, which the history view reads as an incomplete check. |
| Postgres unreachable during `GET /history` | Return 503. The history view shows "History is unavailable right now." The check flow stays usable, because `current_user` reads no database. |
| Google certificate endpoint unreachable | `POST /auth/google` returns 503, and the gate shows "Cannot reach Google right now. Try again." Existing sessions keep working, because they are verified against `SESSION_SECRET`, not against Google. |
| Expired session JWT | Every protected route returns 401. The pipeline clears the user and shows the gate. |
| A user sends another user's `query_id` | The `UPDATE` matches zero rows, because the `WHERE` clause carries `user_id`. Log at WARNING. Return the result. |
| A user sends a `query_id` that does not exist | The same zero-row path. No error to the caller. |
| Account hits the `/llm-assess` cap | 429 with `Retry-After`. The pipeline already handles this case and shows the wait time. |
| `request.state.user` missing on a limited route | The key function falls back to the IP key and logs a WARNING. The route still limits; it just limits the wrong unit. |
| The browser blocks third-party cookies | The session cookie is first-party, set by the app's own origin, so it survives. GIS runs in its own popup or iframe and needs no cookie from this app. |

## Open points

- **Data retention.** The plan stores every check with no expiry. Decide a
  retention window and a delete-my-data route before the app takes real users.
