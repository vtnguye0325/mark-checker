# RAG layer

The `/llm-assess` endpoint grounds DeepSeek responses in real legal doctrine with a ChromaDB
vector store (embedded mode — no separate server or exposed port). The store holds three
collections: `tmep` (Trademark Manual of Examining Procedure sections), `ttab` (TTAB ex parte
decisions and landmark court opinions), and `statute` (Lanham Act / 37 CFR, reserved for a
future chatbot).

## Why this layer exists

The classifier learns what examiners decided, not what the doctrine requires. Vy Nguyen's MS
thesis (§7.6) names this gap directly. The RAG layer retrieves **what the law requires** —
TMEP rules per Abercrombie tier, plus TTAB decisions as illustrations — and never uses
filing outcomes, the training dataset, or examiner-behavior statistics.

## Retrieval strategy

`backend/rag/agent.py` runs a DeepSeek tool-calling loop (up to 2 rounds, each capped at
`max_tokens=200`). The agent gets the mark, the description, the NICE class, the classifier
label, and the top attribution tokens, plus two tools: `search_tmep(query)` and
`search_ttab(query)`. It writes targeted doctrine queries with exact Abercrombie vocabulary,
sees the results, and refines once if the first TMEP hits are off-target. The collected
chunks are deduplicated by id and formatted into the analysis prompt, TMEP doctrine first,
TTAB illustrations second.

An agent is used instead of HyDE (one fixed hypothetical paragraph, embedded blindly) so the
retrieval can self-correct and route naturally — a surname mark triggers a §1211 query
without being pre-programmed to do so.

Embeddings use `bge-base-en-v1.5`, run locally or through the Hugging Face Inference API.

## Building the index

**The index is not baked into the Docker image.** Build it on the host before you start the
stack. The compose file bind-mounts `./data/chroma` into the container at `/data/chroma`, so
the index persists across restarts and redeploys without an image rebuild.

### First deploy (required before `docker compose up`)

Build the baseline index (landmark TTAB cases only — no external data files needed):

```bash
CHROMA_PATH=./data/chroma python scripts/build_rag_index.py
```

Then start the stack:

```bash
docker compose up -d
```

### Full index (optional — adds TMEP, TTAB bulk, Lanham Act)

The source data files are not committed to the repo — obtain them separately and place them
under `backend/rag/data/`.

```bash
CHROMA_PATH=./data/chroma python scripts/build_rag_index.py \
  --tmep backend/rag/data/tmep_2026.zip \
  --ttab backend/rag/data/ttab_bulk.zip \
  --lanham backend/rag/data/tmlaw.pdf
```

### Rebuilding from scratch

```bash
docker compose down
rm -rf ./data/chroma
CHROMA_PATH=./data/chroma python scripts/build_rag_index.py --reset \
  --tmep backend/rag/data/tmep_2026.zip \
  --ttab backend/rag/data/ttab_bulk.zip \
  --lanham backend/rag/data/tmlaw.pdf
docker compose up -d
```

### Evaluating retrieval quality

```bash
CHROMA_PATH=./data/chroma python scripts/eval_rag_retrieval.py
```

## Notes

- Embedded mode (`chromadb.PersistentClient`) — no HTTP server, no port to expose.
- `chromadb` is pinned in `requirements.txt`; major versions have breaking on-disk format
  changes — upgrade intentionally and rebuild the index after.
- `/llm-assess` returns `503` (not `500`) when `DEEPSEEK_API_KEY` is missing.
- If RAG retrieval fails, the endpoint proceeds without doctrine context rather than erroring.
- `CHROMA_PATH` defaults to `backend/rag/chroma_db/` for local (non-Docker) runs.
