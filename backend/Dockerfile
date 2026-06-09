# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm

WORKDIR /app

# Pre-download Hugging Face model into image (build-time)
ARG HF_MODEL_ID
ARG HF_TOKEN
ENV MODEL_DIR=/opt/model
ENV HF_HOME=/root/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Bake WordNet into the image so text_formatter never does a request-time
# download — that would be slow on first use and fail outright in an offline /
# locked-down prod network, silently degrading every prediction.
ENV NLTK_DATA=/usr/share/nltk_data
RUN python -m nltk.downloader -d "${NLTK_DATA}" wordnet omw-1.4

COPY scripts/docker_download_model.py scripts/docker_download_model.py
RUN HF_MODEL_ID="${HF_MODEL_ID}" HF_TOKEN="${HF_TOKEN}" MODEL_DIR="${MODEL_DIR}" \
    python scripts/docker_download_model.py

COPY app/ app/

EXPOSE 8000

# --proxy-headers + --forwarded-allow-ips makes request.client reflect the real
# client behind nginx (accurate logs). Per-IP rate limiting reads X-Forwarded-For
# directly and spoof-resistantly in app/limiter.py.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
