from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the repo root (two levels up from this file) so local dev
# picks up TURNSTILE_SECRET, DISABLE_TURNSTILE, etc. without manual exports.
# In Docker, env vars are injected by compose and load_dotenv is a no-op.
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

from fastapi import FastAPI, Response  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from slowapi import _rate_limit_exceeded_handler  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402

from app.db import init_models  # noqa: E402
from app.limiter import limiter  # noqa: E402
from app.routes.analyze import router as analyze_router  # noqa: E402
from app.routes.explain import router as explain_router  # noqa: E402
from app.routes.predict import router as predict_router  # noqa: E402
from app.services.model_service import is_loaded, warm_up  # noqa: E402

_DEFAULT_CORS = (
    "http://localhost:5173,http://localhost:3000,"
    "http://127.0.0.1:5173,http://127.0.0.1:3000,"
    "http://localhost,http://127.0.0.1,"
    "http://localhost:80,http://127.0.0.1:80"
)
_cors_env = os.getenv("CORS_ORIGINS", _DEFAULT_CORS)
allow_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_models()
    warm_up()
    yield


app = FastAPI(title="Trademark Distinctiveness API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(explain_router)
app.include_router(analyze_router)


@app.get("/health")
def health(response: Response) -> dict:
    if not is_loaded():
        response.status_code = 503
        return {"status": "model_loading"}
    return {"status": "ok"}
