# Trademark Distinctiveness App

Binary trademark distinctiveness classifier backed by a fine-tuned **ModernBERT-base** model (Abercrombie spectrum collapsed to `distinctive` / `not_distinctive`). The backend exposes a REST API for prediction, feature attribution, and LLM-powered legal analysis via DeepSeek.

## Project structure

```
trademark_app/
├── docker-compose.yml           # Production: Nginx + FastAPI
├── docker-compose.dev.yml       # Development: Vite + Uvicorn --reload
├── .env.example                 # Copy to .env for Docker (HF_MODEL_ID, etc.)
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, rate limiter, /health
│   │   ├── limiter.py           # Shared slowapi Limiter instance (100 req/hr per IP)
│   │   ├── routes/
│   │   │   ├── predict.py       # POST /predict
│   │   │   ├── explain.py       # POST /explain
│   │   │   └── analyze.py       # POST /analyze
│   │   └── services/
│   │       ├── model_service.py # Model loader, predict_one(), explain_one()
│   │       ├── llm_service.py   # DeepSeek analysis via OpenAI-compat client
│   │       └── text_formatter.py# Builds bert_input_processed string
│   ├── scripts/
│   │   └── docker_download_model.py  # HF snapshot at image build time
│   ├── model/                   # Fine-tuned weights (local dev; Docker uses /opt/model from HF)
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── nginx.conf               # Prod: reverse-proxy API paths to backend
│   ├── vite.config.js
│   ├── package.json
│   └── src/
├── data/
│   └── predictions.csv          # Saved predictions from training eval (used by smoke test)
├── scripts/
│   └── smoke_test.py            # Runs 50 known-correct predictions end-to-end
└── tests/
    ├── conftest.py
    ├── test_text_formatter.py   # Unit tests — no model required
    ├── test_model_service.py    # Integration tests — loads model
    └── test_api.py              # FastAPI endpoint tests
```

## Requirements

- Python 3.9+
- **Local (non-Docker) runs:** model weights at `backend/model/` (or set `MODEL_DIR` to a local folder or Hugging Face repo id).
- **Docker runs:** model is baked from `HF_MODEL_ID` at image build time into `/opt/model` (see [Docker](#docker)).

Install dependencies:

```bash
cd trademark_app/backend
pip install -r requirements.txt
```

The `requirements.txt` installs: `torch`, `transformers`, `huggingface_hub`, `accelerate`, `fastapi`, `uvicorn`, `nltk`, `openai`, `slowapi`, and supporting libraries.

## Docker

Images **pre-download** your Hugging Face model at **build** time into `/opt/model` inside the backend image (`MODEL_DIR` is set accordingly). You must set **`HF_MODEL_ID`** to a repo id (e.g. `org/your-model-repo`) that contains a Transformers-compatible checkpoint.

### Setup

From `trademark_app/`:

```bash
cp .env.example .env
# Edit .env: set HF_MODEL_ID (required). Set HF_TOKEN if the repo is private/gated.
# Optional: DEEPSEEK_API_KEY for POST /analyze; CORS_ORIGINS for extra browser origins.
```

### Production (Nginx + API)

```bash
cd trademark_app
docker compose up --build
```

- UI: **http://localhost** (port 80) — static assets; `/predict`, `/explain`, `/analyze`, `/health` are proxied to the backend.
- API directly: **http://localhost:8000** (optional).

### Development (hot reload)

```bash
cd trademark_app
docker compose -f docker-compose.dev.yml up --build
```

- Frontend (Vite): **http://localhost:5173** — proxies API routes to the backend container (`VITE_API_PROXY_TARGET`).
- Backend: **http://localhost:8000** — `uvicorn --reload` with `./backend` bind-mounted.

### Rerunning containers (`--build` vs `up` only)

You **do not** need `up --build` every time—only when Docker should **rebuild images**.

- **Routine start (reuse existing images):**
  `docker compose -f docker-compose.dev.yml up`
  Same for production: `docker compose up` (omit `--build` unless something below changed).

- **Use `up --build`** (or `docker compose build` then `up`) when image inputs changed, for example:
  - `backend/Dockerfile`, `backend/requirements.txt`, or **`HF_MODEL_ID` / `HF_TOKEN`** (backend model bake)
  - `frontend/Dockerfile`, or frontend **dependencies** baked into the image (`package.json` / `package-lock.json`)

- **Dev bind mounts:** edits under `./backend` and `./frontend` are visible inside the containers; **Uvicorn `--reload`** and **Vite** pick up app code changes **without** rebuilding images.

- **Stop / restart:** `Ctrl+C` or `docker compose -f docker-compose.dev.yml down`, then `docker compose -f docker-compose.dev.yml up` again. Add `--build` only when you intentionally want fresh images.

### Build notes

- **First backend build** downloads the full model; use Docker layer cache on repeat builds with the same `HF_MODEL_ID`.
- **`HF_TOKEN`**: passed as a build-arg for private repos. Avoid committing `.env` with secrets; for stricter builds, use Docker BuildKit secrets instead of args so tokens do not appear in image history.
- **Local `backend/model/`** is not copied into the image (`.dockerignore`); the container always uses the prebaked `/opt/model` from Hugging Face.

## Exposing to the internet (Cloudflare Tunnel)

Expose the production stack to the public internet without router port forwarding. Traffic flows:

**Internet → Cloudflare (HTTPS) → `cloudflared` on your server → Docker frontend on `localhost:80`**

Cloudflare recommends **dashboard-managed (remotely-managed) tunnels** for production. Configuration lives in the Cloudflare dashboard; the server only runs `cloudflared` with a token. See also `PLAN.md` for the full deployment checklist.

Official docs: [Create a tunnel (dashboard)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/), [Run as a service (Linux)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/configure-tunnels/local-management/as-a-service/linux/), [Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/).

### Prerequisites

| Item | Why |
|------|-----|
| Cloudflare account | Free tier is enough |
| Domain on Cloudflare | Nameservers pointed to Cloudflare; status **Active** |
| App running on the server | `docker compose up -d` and `curl http://localhost` returns `200` |
| Outbound connectivity | Server can reach Cloudflare on ports **443** and **7844** (QUIC) |

You do **not** need router port forwarding, a static public IP, or TLS certificates on the server (Cloudflare terminates HTTPS for users).

### Initial setup (dashboard-managed tunnel)

1. **Add domain to Cloudflare** — register or transfer a domain, update nameservers at your registrar, wait until status is **Active**.

2. **Start the app on the server:**

   ```bash
   cd trademark_app
   docker compose up -d
   curl -s -o /dev/null -w '%{http_code}\n' http://localhost   # expect 200
   ```

3. **Create the tunnel** — Cloudflare dashboard → **Zero Trust → Networks → Connectors → Cloudflare Tunnels → Create a tunnel**. Choose connector type **Cloudflared**, name it e.g. `trademark-app`, save.

4. **Install `cloudflared` on the server** — use the Linux install command from the dashboard, or the official APT repo:

   ```bash
   sudo mkdir -p --mode=0755 /usr/share/keyrings
   curl -fsSL https://pkg.cloudflare.com/cloudflare-public-v2.gpg | sudo tee /usr/share/keyrings/cloudflare-public-v2.gpg >/dev/null
   echo 'deb [signed-by=/usr/share/keyrings/cloudflare-public-v2.gpg] https://pkg.cloudflare.com/cloudflared any main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
   sudo apt-get update && sudo apt-get install cloudflared
   cloudflared --version
   ```

5. **Install the tunnel service** — copy the token from the dashboard:

   ```bash
   sudo cloudflared service install <TOKEN>
   sudo systemctl start cloudflared
   sudo systemctl status cloudflared
   ```

   Confirm the connector shows **Healthy** in Zero Trust → Networks → Connectors.

6. **Clean up conflicting DNS records** — before publishing, open **DNS → Records** for your domain. Delete any existing **A**, **AAAA**, or **CNAME** records for the hostname you want to use (e.g. leftover records from Vercel or a previous host). The tunnel cannot create its CNAME while a conflicting record exists.

7. **Publish the application** — in the tunnel's **Published applications** tab, add a route:

   | Field | Value |
   |-------|-------|
   | Subdomain | *(empty for root domain, or e.g. `app`)* |
   | Domain | your domain |
   | Path | *(empty — serve the whole site)* |
   | Service type | **HTTP** |
   | URL | `localhost:80` |

   **Important:** use **HTTP**, not HTTPS. Nginx in Docker serves plain HTTP on port 80; Cloudflare handles HTTPS for visitors.

   Cloudflare creates a CNAME like `<tunnel-id>.cfargotunnel.com` (proxied). Wait ~1 minute, then open `https://yourdomain.com`.

### Security before sharing publicly

The app has **no built-in login**. Anyone with the URL can use server CPU and DeepSeek API credits.

- **Cloudflare Access** (recommended) — Zero Trust → Access → Applications → add a self-hosted app for your hostname. Use email OTP or Google login.
- **Rate limits** — in `.env`:
  ```bash
  RATE_LIMIT_DEFAULT=100/hour
  RATE_LIMIT_ANALYZE=20/hour
  ```
  Then `docker compose down && docker compose up -d`.
- **CORS** (optional; Nginx same-origin usually avoids issues):
  ```bash
  CORS_ORIGINS=https://yourdomain.com
  ```
- **Do not expose port 8000** via the tunnel. Only `localhost:80` should be published; the backend stays internal behind Nginx.

### Day-to-day maintenance

| Task | How |
|------|-----|
| Start / stop the app | `docker compose up -d` / `docker compose down` |
| Rebuild after code changes | `docker compose up --build -d` (see [Docker](#docker)) |
| Check app health | `curl http://localhost` and `docker ps` |
| View tunnel status | Zero Trust → Networks → Connectors |
| View tunnel logs | `sudo journalctl -u cloudflared -f` |
| Restart tunnel | `sudo systemctl restart cloudflared` |
| Change hostname or origin | Edit **Published applications** in the dashboard |
| Update `cloudflared` | `sudo apt-get update && sudo apt-get install cloudflared` then `sudo systemctl restart cloudflared` |
| Update secrets / env | Edit `.env`, then `docker compose down && docker compose up -d` |

After a server reboot, both Docker and `cloudflared` should come back automatically if the systemd service is enabled.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| **"An A, AAAA, or CNAME record already exists"** when publishing | Old DNS record for that hostname | Delete conflicting records in **DNS → Records**, then re-save the published application |
| **502 Bad Gateway** | Published app uses **HTTPS** to `localhost:80` | Edit route: type **HTTP**, URL `localhost:80`. Check logs: `sudo journalctl -u cloudflared -f` — look for `originService=https://localhost:80` or `tls: first record does not look like a TLS handshake` |
| **525 SSL handshake failed** | DNS points to wrong origin (e.g. old Vercel A records) | Delete old A/CNAME records; ensure tunnel CNAME exists; published route saved successfully |
| **404 with `X-Vercel-Error`** | DNS still routes to Vercel, not the tunnel | Delete Vercel A records; add tunnel published route |
| **Site works on server, not from internet** | Tunnel not healthy or no published route | `systemctl status cloudflared`; confirm **Healthy** in dashboard; confirm published app targets `localhost:80` |
| **Tunnel won't connect** | Outbound firewall blocks Cloudflare | Allow outbound TCP/UDP on ports **443** and **7844** |

**Diagnostic commands on the server:**

```bash
# App responding locally?
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1/

# Containers up?
docker ps

# Tunnel running?
systemctl status cloudflared

# Recent tunnel errors?
sudo journalctl -u cloudflared --since '30 min ago' --no-pager
```

### Quick test without a domain (TryCloudflare)

For a temporary demo only — **not for production**:

```bash
docker compose up -d
# Rename ~/.cloudflared/config.yml temporarily if present
cloudflared tunnel --url http://localhost:80
```

Prints a random `https://<random>.trycloudflare.com` URL. Limitations: dies when the process stops, ~200 concurrent request cap, no Server-Sent Events.

### Alternative: CLI locally-managed tunnel

For dev, testing, or GitOps workflows where config lives in a local file. Not Cloudflare's recommended production path.

```bash
cloudflared tunnel login
cloudflared tunnel create trademark-app
```

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL-UUID>
credentials-file: /home/<USER>/.cloudflared/<TUNNEL-UUID>.json

ingress:
  - hostname: trademark.yourdomain.com
    service: http://localhost:80
  - service: http_status:404
```

Then:

```bash
cloudflared tunnel ingress validate
cloudflared tunnel route dns trademark-app trademark.yourdomain.com
cloudflared tunnel run trademark-app                              # foreground test
sudo cloudflared --config /home/<USER>/.cloudflared/config.yml service install
sudo systemctl start cloudflared
```

If installing the service with `sudo`, pass `--config` explicitly — otherwise systemd looks in `/root/.cloudflared/`.

## Running the backend

```bash
cd trademark_app/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server starts at `http://localhost:8000`. The model loads on the first request (~5–10 s on CPU); subsequent requests are fast.

## Rate limiting

All endpoints are limited to **100 requests per hour per IP address**. Requests over the limit receive `429 Too Many Requests`. The counter resets on a rolling hourly window. Since a full UI analysis calls `/predict` + `/explain` + `/analyze` sequentially, this allows roughly 33 complete analyses per IP per hour.

## API reference

### `GET /health`

```
200 OK
{"status": "ok"}
```

---

### `POST /predict`

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
curl -X POST http://localhost:8000/predict \
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

`label` is `"distinctive"` when `prob_distinctive >= 0.5`, otherwise `"not_distinctive"`. `formatted_input` is the full 8-field string fed to the model.

---

### `POST /explain`

Runs leave-one-out attribution: blanks each of the 8 input fields in turn, measures the change in `prob_distinctive` vs the baseline, and returns per-field attribution scores.

**Request body:** same fields as `/predict`.

**Response (200 OK):**

```json
{
  "label": "distinctive",
  "prob_distinctive": 0.9492,
  "prob_not_distinctive": 0.0508,
  "formatted_input": "...",
  "attributions": [
    { "field": "Mark",             "value": "APPLE", "attribution":  0.3201 },
    { "field": "Goods & Services", "value": "computers and computer software", "attribution": 0.0843 },
    ...
  ]
}
```

`attribution` is `baseline_prob − masked_prob`. Positive values mean the field pushes toward distinctiveness; negative values push against it. Results are sorted by `abs(attribution)` descending.

---

### `POST /analyze`

Sends the prediction and attributions to DeepSeek and returns a plain-English legal analysis structured into four sections: *What the model found*, *Where this mark sits on the trademark spectrum*, *Why the model leaned this way*, and *What to do next*.

Requires `DEEPSEEK_API_KEY` to be set in the environment. Returns `503` if the key is missing.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mark` | string | yes | Trademark literal element |
| `description` | string | yes | Goods/services description |
| `nice_class` | int (1–45) | yes | NICE class number |
| `label` | string | yes | `"distinctive"` or `"not_distinctive"` from `/predict` or `/explain` |
| `prob_distinctive` | float | yes | Probability score from `/predict` or `/explain` |
| `attributions` | array | yes | Attribution list from `/explain` |

**Response (200 OK):**

```json
{
  "analysis": "**What the model found**\n..."
}
```

**Errors:** `503` if `DEEPSEEK_API_KEY` is not configured.

---

**Validation errors (422):** returned for missing required fields, `nice_class` outside 1–45, or empty `mark`/`description`.

## Running the tests

### 1. Install test dependencies

```bash
pip install pytest
```

### 2. Run all tests

From the `trademark_app/` directory:

```bash
python -m pytest tests/ -v
```

### 3. Run individual test files

| Command | What it tests | Loads model? |
|---------|--------------|:------------:|
| `python -m pytest tests/test_text_formatter.py -v` | Input formatting logic, NICE descriptions, translation, pseudo mark | No |
| `python -m pytest tests/test_model_service.py -v` | `predict_one()` return shape, probability bounds, canonical examples | Yes |
| `python -m pytest tests/test_api.py -v` | `/health` and `/predict` endpoints, all 422 validation error cases | Yes |

Unit tests in `test_text_formatter.py` are fast (no model load). The other two files load the model on first run (~5–10 s on CPU) and stay fast for subsequent tests in the same session.

### 4. What each test covers

**`test_text_formatter.py`** (18 tests)
- `format_input` produces exactly 8 dot-separated fields
- Mark, NICE category, mark length, and NICE description fields are correctly placed
- `translation`: empty input → `"no translation required"`, non-empty → returned verbatim
- `_pseudo_mark`: explicit input returned verbatim; empty/whitespace → `"no Pseudo mark"`
- All 45 NICE classes present and non-empty in `NICE_DESCRIPTIONS`

**`test_model_service.py`** (7 tests)
- Response has keys `label`, `prob_distinctive`, `prob_not_distinctive`
- Both probabilities are in `[0.0, 1.0]` and sum to 1.0
- `label` is always `"distinctive"` or `"not_distinctive"`
- `label` is consistent with `prob_distinctive >= 0.5`
- Canonical: `APPLE` / computers (class 9) → `distinctive` with prob > 0.7
- Coined mark (`XYLOQUARTZ`) → `distinctive`

**`test_api.py`** (14 tests)
- `GET /health` → 200 `{"status": "ok"}`
- `POST /predict` happy path → 200 with all four response fields
- Optional fields `translation` and `pseudo_mark` appear in `formatted_input`
- 422 on: missing `mark`, missing `description`, missing `nice_class`, empty `mark`, `nice_class = 0`, `nice_class = 46`

## Smoke test

Runs the first 50 correct predictions from `data/predictions.csv` through the live model and verifies they match:

```bash
# From trademark_app/
python scripts/smoke_test.py
python scripts/smoke_test.py --verbose   # prints all 8 input fields + raw result per case
```

Expected output: `50 passed, 0 failed`.

## CI/CD

A GitHub Actions pipeline is configured at `.github/workflows/ci.yml`. It runs on every push and pull request to `main`, with five jobs:

| Job | Trigger | What it does |
|-----|---------|-------------|
| **lint-backend** | push + PR | Ruff lint check + format check on `backend/`, `tests/`, `scripts/` |
| **test-backend** | push + PR | Installs Python deps + NLTK data, runs unit tests (`tests/test_text_formatter.py` — no model needed) |
| **build-frontend** | push + PR | `npm ci` + `npm run build` |
| **docker-build** | after lint + test + build | Builds both Docker images via BuildKit with GitHub Actions cache layering, verifies imports |
| **deploy** | push to `main` only | SSH into server, git pull, writes `.env`, `docker compose up --build -d`, runs health check |

The pipeline uses the `docker/build-push-action` with `type=gha` caching, so repeat builds reuse the model layer (saved from the Hugging Face download).

### Required secrets

Configure these in your repo **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|--------|---------|
| `HF_MODEL_ID` | Hugging Face model repo id (e.g. `vtnguye/automating-abercrombie`) |
| `HF_TOKEN` | Token for private/gated Hugging Face models |
| `DEEPSEEK_API_KEY` | API key for the `/analyze` DeepSeek LLM endpoint |
| `DEPLOY_HOST` | Production server IP or domain |
| `DEPLOY_USER` | SSH username for deployment |
| `DEPLOY_SSH_KEY` | SSH private key (deploy key) |
| `DEPLOY_DOMAIN` | Production domain (used for `CORS_ORIGINS`) |

### Running tests locally

```bash
pip install pytest
python -m pytest tests/test_text_formatter.py -v   # unit tests, fast, no model
python -m pytest tests/ -v                          # all tests (loads model)
```

See [Running the tests](#running-the-tests) for details.

## Input format

The model was trained on an 8-field string joined with `". "`:

```
{mark}. {description}. {translation}. {wordnet_flag}. mark length is {n}.
NICE category is {k}. {nice_description}. {pseudo_mark}
```

`text_formatter.format_input()` builds this string automatically from your inputs. Feeding raw mark text without description and NICE metadata will degrade accuracy.
