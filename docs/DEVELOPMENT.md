# Development

## Requirements

- Python 3.11+
- Node 20+ (frontend)
- **Local (non-Docker) runs:** model weights at `backend/model/` (or set `MODEL_DIR` to a
  local folder or a Hugging Face repo id).
- **Docker runs:** the model is baked from `HF_MODEL_ID` at image build time into
  `/opt/model` (see [DEPLOYMENT.md](DEPLOYMENT.md)).

Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

`requirements.txt` installs `torch`, `transformers`, `huggingface_hub`, `accelerate`,
`fastapi`, `uvicorn`, `nltk`, `openai`, `slowapi`, `chromadb`, and supporting libraries.

## Running the backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server starts at `http://localhost:8000`. The model loads at worker startup (~5–10 s on
CPU); `/health` returns `503` until it is ready.

## Running the frontend

```bash
cd frontend
npm install
npm run dev        # Vite dev server at http://localhost:5173, proxies API paths
```

## Tests

Install the test dependencies and run the suite from the project root:

```bash
pip install pytest pytest-asyncio httpx
python -m pytest tests/ -v
```

| File | What it tests | Loads model? |
|------|--------------|:------------:|
| `tests/test_text_formatter.py` (26 tests) | `format_mark()` output, the 8-field layout, NICE descriptions, translation, pseudo mark | No |
| `tests/test_model_service.py` (9 tests) | `predict_one()` return shape, probability bounds, `label` consistency, canonical examples | Yes |
| `tests/test_api.py` (20 tests) | `/health` and `/ml-predict` endpoints, all 422 validation cases | Yes |
| `tests/test_model_predictions.py` | Regression suite — 50 known-good predictions from `predictions.csv`; catches model drift | Yes |

The model-loading files pay a ~5–10 s cost on the first test and stay fast for the rest of
the session.

## Smoke test

Runs known-correct predictions from `data/predictions.csv` through the live model and
verifies they match. The CSV is not committed to the repo — generate it from your training
evaluation output and place it at `data/predictions.csv` first.

```bash
python scripts/smoke_test.py
python scripts/smoke_test.py --verbose   # prints all 8 input fields + raw result per case
```

Expected output: `50 passed, 0 failed`.

## Project structure

```
mark-checker/
├── docker-compose.yml           # Production: Nginx + FastAPI
├── docker-compose.dev.yml       # Development: Vite + Uvicorn --reload
├── .env.example                 # Copy to .env for Docker (HF_MODEL_ID, etc.)
├── backend/
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, rate limiter, /health, lifespan warm-up
│   │   ├── limiter.py           # Shared slowapi Limiter (per-IP, X-Forwarded-For aware)
│   │   ├── turnstile.py         # Cloudflare Turnstile verify dependency for /llm-assess
│   │   ├── routes/
│   │   │   ├── predict.py       # POST /ml-predict
│   │   │   ├── explain.py       # POST /llm-explain
│   │   │   └── analyze.py       # POST /llm-assess
│   │   └── services/
│   │       ├── model_service.py # ModelHandle, predict_one(), explain_one()
│   │       ├── llm_service.py   # DeepSeek analysis + RAG doctrine retrieval
│   │       └── text_formatter.py# format_mark() → FormattedMark{.text, .fields}
│   ├── rag/                     # RAG layer — grounds LLM analysis in legal doctrine
│   │   ├── embedder.py          # bge-base-en-v1.5, local or HF Inference API
│   │   ├── store.py             # ChromaDB PersistentClient, tmep + ttab + statute collections
│   │   ├── agent.py             # DeepSeek tool-calling loop → targeted doctrine queries
│   │   ├── retriever.py         # run agent → collect chunks → format_context()
│   │   └── ingest/
│   │       ├── tmep_loader.py   # Parse TMEP zip at section boundaries
│   │       ├── ttab_loader.py   # Parse TTAB bulk data, filter ex parte decisions
│   │       ├── lanham_loader.py # Parse the Lanham Act / 37 CFR PDF
│   │       └── landmark_cases.json  # Seeded landmark court opinions
│   ├── model/                   # Fine-tuned weights (local dev only)
│   └── scripts/
│       └── build_rag_index.py
├── docs/                        # DEPLOYMENT, API, RAG, DEVELOPMENT, PLAN
├── scripts/
│   ├── build_rag_index.py       # Ingest TMEP/TTAB/Lanham into ChromaDB (idempotent)
│   ├── eval_rag_retrieval.py    # Section reachability + spot-check eval
│   └── smoke_test.py            # Predictions end-to-end against the live model
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf               # Prod: reverse-proxy /ml-predict, /llm-explain, /llm-assess, /health
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── hooks/
│       │   └── useTrademarkPipeline.js  # /ml-predict → /llm-explain → /llm-assess pipeline state
│       ├── components/          # MarkForm, ResultPanel, AttributionChart, ProbBar, llm/*
│       └── lib/
│           └── parseLegalAnalysis.js    # Pure parsers for the LLM analysis sections
└── tests/
    ├── conftest.py
    ├── test_text_formatter.py
    ├── test_model_service.py
    ├── test_api.py
    └── test_model_predictions.py
```
