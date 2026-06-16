# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Bake WordNet so text_formatter never does a request-time download.
ENV NLTK_DATA=/usr/share/nltk_data
RUN python -m nltk.downloader -d "${NLTK_DATA}" wordnet omw-1.4

COPY app/ app/
COPY rag/ rag/

# MODEL_DIR accepts a local path or a HF repo id (e.g. "org/model-name").
# HF_TOKEN is required for private repos.
# The classifier model is downloaded on first boot into the hf-cache volume.
ENV MODEL_DIR=""
ENV HF_TOKEN=""
ENV HF_HOME=/hf-cache

# Bake the BGE embedding model into /opt/models — never masked by hf-cache volume.
# Loading by absolute path at runtime means no HuggingFace network HEAD check.
# To pin a deterministic revision, replace snapshot_download call with:
#   snapshot_download('BAAI/bge-base-en-v1.5', revision='<sha>', local_dir=...)
# Get the SHA once: python -c "from huggingface_hub import model_info; print(model_info('BAAI/bge-base-en-v1.5').sha)"
ENV BGE_DIR=/opt/models/bge-base-en-v1.5
RUN python3 <<'PYEOF'
from huggingface_hub import snapshot_download
snapshot_download('BAAI/bge-base-en-v1.5', local_dir='/opt/models/bge-base-en-v1.5')
print('BGE model baked to /opt/models/bge-base-en-v1.5')
PYEOF

# Seed the TTAB collection with landmark cases (bundled JSON; no external data
# required). The chroma_db is baked into the image layer; Docker seeds the
# named volume from it on first mount so a fresh deploy has a working baseline.
RUN python3 <<'PYEOF'
import sys; sys.path.insert(0, '/app')
from rag.store import get_ttab_collection
from rag.embedder import embed_documents
from rag.ingest.ttab_loader import load_landmark_chunks
chunks = load_landmark_chunks('/app/rag/ingest/landmark_cases.json')
col = get_ttab_collection()
texts = [c['text'] for c in chunks]
col.upsert(
    ids=[c['id'] for c in chunks],
    documents=texts,
    embeddings=embed_documents(texts),
    metadatas=[c['metadata'] for c in chunks],
)
print(f'Seeded {len(chunks)} landmark chunks')
PYEOF

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
