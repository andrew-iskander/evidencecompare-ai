# EvidenceCompare AI — API on Hugging Face Spaces (Docker SDK)
# Self-contained: clones the public monorepo and serves apps/api in offline mode.
# Paste this as the Space's Dockerfile (alongside the README.md in this folder).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    EVIDENCE_MODE=offline \
    LLM_MODE=offline \
    CORS_ORIGINS=*

# git clones the source; build-essential compiles any wheels; curl for health.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# HF Spaces convention: run as a non-root user with uid 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Pull the API from the public monorepo (a Factory Rebuild re-pulls latest).
RUN git clone --depth 1 https://github.com/andrew-iskander/evidencecompare-ai /home/user/src

WORKDIR /home/user/src/apps/api
RUN pip install --user --upgrade pip && pip install --user -r requirements.txt

EXPOSE 8000
# app_port in README.md tells HF to route here.
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
