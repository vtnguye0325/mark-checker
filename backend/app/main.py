from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.limiter import limiter
from app.routes.analyze import router as analyze_router
from app.routes.explain import router as explain_router
from app.routes.predict import router as predict_router
from app.services.model_service import is_loaded, warm_up

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
def health() -> dict:
    return {"status": "ok" if is_loaded() else "model_loading"}
