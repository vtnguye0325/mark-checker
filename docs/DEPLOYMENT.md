# Deployment

This guide covers the Docker build, a public deployment through a Cloudflare Tunnel, and the
security steps to take before you share the app.

## Requirements

- Docker and Docker Compose.
- A Hugging Face repo id in `HF_MODEL_ID` that holds a Transformers-compatible checkpoint.
- `HF_TOKEN` if the model repo is private or gated.
- `DEEPSEEK_API_KEY` for the `/llm-assess` endpoint.
- `TURNSTILE_SECRET` and `VITE_TURNSTILE_SITE_KEY` for the bot check on `/llm-assess`.

## Docker

The backend image **pre-downloads** the Hugging Face model at **build** time into `/opt/model`
inside the image, and sets `MODEL_DIR` to that path. Set **`HF_MODEL_ID`** to a repo id
(e.g. `org/your-model-repo`).

### Setup

From the project root:

```bash
cp .env.example .env
# Edit .env: set HF_MODEL_ID (required). Set HF_TOKEN if the repo is private/gated.
# Optional: DEEPSEEK_API_KEY for POST /llm-assess; CORS_ORIGINS for extra browser origins.
```

### Production (Nginx + API)

```bash
docker compose up --build
```

- UI: **http://localhost:8080** — static assets; `/ml-predict`, `/llm-explain`,
  `/llm-assess`, `/health` are proxied to the backend.
- API directly: **http://localhost:8000** (optional).

### Published ports

Both services bind to **loopback only**. Nothing in this stack listens on a public
interface.

| Service | Published port | Reachable from |
|---------|----------------|----------------|
| frontend (Nginx) | `127.0.0.1:8080` | The server itself, and `cloudflared` |
| backend (API) | `127.0.0.1:8000` | The server itself |

Two rules explain these bindings:

- **The production host runs more than one app.** Another Compose project owns host
  ports 80 and 443 for its own reverse proxy. This stack must not claim port 80, or
  the deploy fails with `Bind for 0.0.0.0:80 failed: port is already allocated`.
- **Docker bypasses the firewall.** Docker writes its own iptables rules, so a
  `"8000:8000"` mapping is reachable from the internet even when `ufw` allows only
  ports 22, 80, and 443. The `127.0.0.1:` prefix is what keeps the API private.

To check the published ports on the server, run `sudo ss -lptn` and confirm that no
`docker-proxy` process for this stack listens on `0.0.0.0`.

### Development (hot reload)

```bash
docker compose -f docker-compose.dev.yml up --build
```

- Frontend (Vite): **http://localhost:5173** — proxies API routes to the backend container
  (`VITE_API_PROXY_TARGET`).
- Backend: **http://localhost:8000** — `uvicorn --reload` with `./backend` bind-mounted.

### Rerunning containers (`--build` vs `up` only)

You **do not** need `up --build` every time — only when Docker must **rebuild images**.

- **Routine start (reuse existing images):**
  `docker compose -f docker-compose.dev.yml up`
  Same for production: `docker compose up` (omit `--build` unless something below changed).

- **Use `up --build`** when image inputs changed, for example:
  - `backend/Dockerfile`, `backend/requirements.txt`, or **`HF_MODEL_ID` / `HF_TOKEN`**
    (backend model bake)
  - `frontend/Dockerfile`, or frontend **dependencies** baked into the image
    (`package.json` / `package-lock.json`)

- **Dev bind mounts:** edits under `backend/` and `frontend/` are visible inside the
  containers; **Uvicorn `--reload`** and **Vite** pick up app code changes **without**
  rebuilding images.

- **Stop / restart:** `Ctrl+C` or `docker compose -f docker-compose.dev.yml down`, then
  `docker compose -f docker-compose.dev.yml up` again. Add `--build` only when you want
  fresh images.

### Build notes

- **First backend build** downloads the full model; use the Docker layer cache on repeat
  builds with the same `HF_MODEL_ID`.
- **`HF_TOKEN`**: passed as a build-arg for private repos. Do not commit `.env` with
  secrets; for stricter builds, use Docker BuildKit secrets instead of args so tokens do
  not appear in image history.
- **Local `backend/model/`** is not copied into the image (`.dockerignore`); the container
  always uses the prebaked `/opt/model` from Hugging Face.

## Exposing to the internet (Cloudflare Tunnel)

Expose the production stack to the public internet without router port forwarding. Traffic
flows:

**Internet → Cloudflare (HTTPS) → `cloudflared` on your server → Docker frontend on
`localhost:8080`**

Cloudflare recommends **dashboard-managed (remotely-managed) tunnels** for production. The
configuration lives in the Cloudflare dashboard; the server only runs `cloudflared` with a
token.

Official docs: [Create a tunnel (dashboard)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/),
[Run as a service (Linux)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/configure-tunnels/local-management/as-a-service/linux/),
[Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/).

### Prerequisites

| Item | Why |
|------|-----|
| Cloudflare account | Free tier is enough |
| Domain on Cloudflare | Nameservers pointed to Cloudflare; status **Active** |
| App running on the server | `docker compose up -d` and `curl http://localhost:8080` returns `200` |
| Outbound connectivity | Server can reach Cloudflare on ports **443** and **7844** (QUIC) |

You do **not** need router port forwarding, a static public IP, or TLS certificates on the
server (Cloudflare terminates HTTPS for users).

### Initial setup (dashboard-managed tunnel)

1. **Add the domain to Cloudflare** — register or transfer a domain, update the nameservers
   at your registrar, wait until the status is **Active**.

2. **Start the app on the server:**

   ```bash
   docker compose up -d
   curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8080   # expect 200
   ```

3. **Create the tunnel** — Cloudflare dashboard → **Zero Trust → Networks → Connectors →
   Cloudflare Tunnels → Create a tunnel**. Choose connector type **Cloudflared**, name it
   e.g. `trademark-app`, save.

4. **Install `cloudflared` on the server** — use the Linux install command from the
   dashboard, or the official APT repo:

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

6. **Clean up conflicting DNS records** — before you publish, open **DNS → Records** for
   your domain. Delete any existing **A**, **AAAA**, or **CNAME** records for the hostname
   you want to use (e.g. leftover records from Vercel or a previous host). The tunnel cannot
   create its CNAME while a conflicting record exists.

7. **Publish the application** — in the tunnel's **Published applications** tab, add a route:

   | Field | Value |
   |-------|-------|
   | Subdomain | *(empty for root domain, or e.g. `app`)* |
   | Domain | your domain |
   | Path | *(empty — serve the whole site)* |
   | Service type | **HTTP** |
   | URL | `localhost:8080` |

   **Important:** use **HTTP**, not HTTPS. Nginx in Docker serves plain HTTP on port 8080;
   Cloudflare handles HTTPS for visitors.

   Cloudflare creates a CNAME like `<tunnel-id>.cfargotunnel.com` (proxied). Wait ~1 minute,
   then open `https://yourdomain.com`.

### Security before you share publicly

The app has **no built-in login**. Anyone with the URL can use server CPU and DeepSeek API
credits.

- **Cloudflare Access** (recommended) — Zero Trust → Access → Applications → add a
  self-hosted app for your hostname. Use email OTP or Google login.
- **Turnstile** — the `/llm-assess` endpoint requires a valid Cloudflare Turnstile token.
  Set `TURNSTILE_SECRET` (backend) and `VITE_TURNSTILE_SITE_KEY` (frontend build). A
  missing `TURNSTILE_SECRET` fails closed with `503`.
- **Rate limits** — in `.env`:
  ```bash
  RATE_LIMIT_DEFAULT=100/hour
  RATE_LIMIT_ANALYZE=5/hour
  ```
  Then `docker compose down && docker compose up -d`.
- **CORS** (optional; Nginx same-origin usually avoids issues):
  ```bash
  CORS_ORIGINS=https://yourdomain.com
  ```
- **Do not expose port 8000** through the tunnel. Publish only `localhost:8080`; the backend
  stays internal behind Nginx.

### Day-to-day maintenance

| Task | How |
|------|-----|
| Start / stop the app | `docker compose up -d` / `docker compose down` |
| Rebuild after code changes | `docker compose up --build -d` |
| Check app health | `curl http://localhost:8080` and `docker ps` |
| View tunnel status | Zero Trust → Networks → Connectors |
| View tunnel logs | `sudo journalctl -u cloudflared -f` |
| Restart tunnel | `sudo systemctl restart cloudflared` |
| Change hostname or origin | Edit **Published applications** in the dashboard |
| Update `cloudflared` | `sudo apt-get update && sudo apt-get install cloudflared` then `sudo systemctl restart cloudflared` |
| Update secrets / env | Edit `.env`, then `docker compose down && docker compose up -d` |

After a server reboot, both Docker and `cloudflared` come back automatically if the systemd
service is enabled.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| **"An A, AAAA, or CNAME record already exists"** when publishing | Old DNS record for that hostname | Delete conflicting records in **DNS → Records**, then re-save the published application |
| **502 Bad Gateway** | Published app uses **HTTPS** to `localhost:8080` | Edit the route: type **HTTP**, URL `localhost:8080`. Check logs: `sudo journalctl -u cloudflared -f` — look for `originService=https://localhost:8080` or `tls: first record does not look like a TLS handshake` |
| **525 SSL handshake failed** | DNS points to the wrong origin (e.g. old Vercel A records) | Delete old A/CNAME records; make sure the tunnel CNAME exists; the published route saved |
| **404 with `X-Vercel-Error`** | DNS still routes to Vercel, not the tunnel | Delete Vercel A records; add the tunnel published route |
| **Site works on the server, not from the internet** | Tunnel not healthy or no published route | `systemctl status cloudflared`; confirm **Healthy** in the dashboard; confirm the published app targets `localhost:8080` |
| **Tunnel will not connect** | Outbound firewall blocks Cloudflare | Allow outbound TCP/UDP on ports **443** and **7844** |

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

For a temporary demo only — **not for production**. Run from the project root:

```bash
docker compose up -d
# Rename ~/.cloudflared/config.yml temporarily if present
cloudflared tunnel --url http://localhost:8080
```

This prints a random `https://<random>.trycloudflare.com` URL. Limitations: it dies when the
process stops, has a ~200 concurrent request cap, and has no Server-Sent Events.

### Alternative: CLI locally-managed tunnel

For dev, testing, or GitOps workflows where the config lives in a local file. This is not
Cloudflare's recommended production path.

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
    service: http://localhost:8080
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

If you install the service with `sudo`, pass `--config` explicitly — otherwise systemd
looks in `/root/.cloudflared/`.

## CI/CD

A GitHub Actions pipeline at `.github/workflows/ci.yml` runs on every push and pull request
to `main` on **self-hosted local runners**, with four jobs:

| Job | Trigger | What it does |
|-----|---------|-------------|
| **backend-lint** | push + PR | Creates a venv, installs Ruff, runs lint + format check on `backend/` |
| **backend-test** | push + PR | Creates a venv, installs deps, runs `pytest tests/` |
| **frontend-build** | push + PR | `npm ci` + `npm run build` |
| **deploy** | push to `main` only | On the VPS: `git reset --hard origin/main`, `docker compose build`, `docker compose up -d`, then polls the backend `/health` until healthy |

### Required secrets

Configure these in the repo **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|--------|---------|
| `HF_MODEL_ID` | Hugging Face model repo id |
| `HF_TOKEN` | Token for private/gated Hugging Face models |
| `DEEPSEEK_API_KEY` | API key for the `/llm-assess` DeepSeek LLM endpoint |
| `TURNSTILE_SECRET` | Cloudflare Turnstile secret for the bot check |
| `VITE_TURNSTILE_SITE_KEY` | Cloudflare Turnstile site key baked into the frontend build |
