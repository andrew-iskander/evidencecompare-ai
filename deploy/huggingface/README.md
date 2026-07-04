---
title: EvidenceCompare AI API
emoji: 🧬
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
---

# EvidenceCompare AI — API (Hugging Face Space)

FastAPI backend running in **offline mode** (demo evidence, no API keys, no
Postgres/Redis). Built straight from the public monorepo
`github.com/andrew-iskander/evidencecompare-ai` (`apps/api`).

- Health check: `/health`
- Interactive docs: `/docs`

> The two files in this folder (`README.md` + `Dockerfile`) are the exact
> contents to paste into a Hugging Face **Docker Space**. See the repo root
> `DEPLOY.md` for the full walkthrough.
