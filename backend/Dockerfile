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

# Bake WordNet into the image so text_formatter never does a request-time download.
ENV NLTK_DATA=/usr/share/nltk_data
RUN python -m nltk.downloader -d "${NLTK_DATA}" wordnet omw-1.4

COPY app/ app/

# MODEL_DIR accepts a local path or a HF repo id (e.g. "org/model-name").
# HF_TOKEN is required for private repos.
# The model is downloaded on first boot and cached in the hf-model volume.
ENV MODEL_DIR=""
ENV HF_TOKEN=""
ENV HF_HOME=/hf-cache

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
