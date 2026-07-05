# EvidenceCompare AI

[![CI](https://github.com/andrew-iskander/evidencecompare-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/andrew-iskander/evidencecompare-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> A premium AI medical-evidence intelligence platform that compares **two pharmaceutical
> molecules** for a **user-defined clinical topic** using only trusted evidence — and
> produces an interactive, fully-cited, exportable report.

**Core promise:** never fabricate citations; clearly state when evidence is insufficient.

Example: **A:** Telmisartan · **B:** Valsartan · **Topic:** Cardioprotection.

---

## What it produces

An interactive evidence report with: executive summary · side-by-side comparison table
(with confidence scores) · mechanism of action · guideline recommendations · randomized
trials · meta-analyses · systematic reviews · safety · contraindications · drug
interactions · special populations · limitations · evidence gaps · references (DOI/PMID)
· export to **PDF, PPTX, Excel, Markdown**.

## Trusted data sources

PubMed · Europe PMC · Crossref · ClinicalTrials.gov · FDA · EMA · ACC · AHA · ESC ·
KDIGO · ADA · NICE · WHO · Cochrane. *No source outside this allowlist can become a citation.*

## Tech stack (summary)

- **Frontend:** Next.js 15, React 19, TypeScript, Tailwind v4, shadcn/ui, Framer Motion, Recharts/Tremor.
- **Backend:** FastAPI (Python 3.12), PostgreSQL 16 + pgvector, Redis, Celery, JWT auth.
- **AI:** Claude API — `claude-opus-4-8` (synthesis), `claude-sonnet-5` (agents),
  `claude-haiku-4-5` (extraction); Voyage AI `voyage-3.5` embeddings.

Full rationale: [`docs/02-tech-stack.md`](docs/02-tech-stack.md).

## Architecture

RAG-grounded, **multi-agent** evidence engine behind an async API. A central
orchestrator runs **twelve specialized agents** in dependency-ordered stages
(independent agents run concurrently) and produces one seamless, fully-cited report.
See [`docs/07-multi-agent-architecture.md`](docs/07-multi-agent-architecture.md)
(Mermaid pipeline / agent-interaction / sequence diagrams + per-agent I/O and error
handling), [`docs/01-architecture.md`](docs/01-architecture.md), and
[`docs/06-ai-workflow.md`](docs/06-ai-workflow.md).

**V3 twelve-agent pipeline:** Clinical-Question Interpreter → Search → Guideline →
Trial-Extraction → Evidence-Ranking → Safety → Conflict-Resolution →
Citation-Verification → Medical-Writer → Visualization → Report-Generator →
Continuous-Evidence Monitor. An optional **Research Process** panel (hidden by
default) exposes the pipeline's queries, ranking/verification decisions, safety
matrix, conflict reconciliation, and per-agent timing.

## Documentation

| Doc | Contents |
|---|---|
| [PRD](docs/00-product-requirements.md) | Requirements, personas, acceptance criteria |
| [Architecture](docs/01-architecture.md) | System design, request lifecycle |
| [Tech stack](docs/02-tech-stack.md) | Stack + decisions |
| [Folder structure](docs/03-folder-structure.md) | Repo layout |
| [Database schema](docs/04-database-schema.md) | ER + DDL (pgvector) |
| [API spec](docs/05-api-specification.md) | REST + SSE |
| [AI workflow](docs/06-ai-workflow.md) | RAG, agents, model tiering |
| [Multi-agent engine (V3)](docs/07-multi-agent-architecture.md) | Twelve-agent orchestration, diagrams, per-agent I/O + error handling |
| [Phase 0 summary](docs/PHASE0-SUMMARY.md) | Decisions log |
| [Upgrade summary](docs/UPGRADE-SUMMARY.md) | Dynamic AI engine (U1–U4): orchestrator, caching, transparency |
| [CLAUDE.md](CLAUDE.md) | Dev/agent guide |

## Roadmap (phases)

- **Phase 0 — Design** ✅ requirements, architecture, stack, schema, API, AI workflow. ([summary](docs/PHASE0-SUMMARY.md))
- **Phase 1 — Frontend** ✅ premium UI, dark/light, responsive, streaming report view. ([summary](docs/PHASE1-SUMMARY.md))
- **Phase 2 — Backend** ✅ FastAPI, Postgres, Redis, auth, saved reports. ([summary](docs/PHASE2-SUMMARY.md))
- **Phase 3 — Evidence engine** ✅ RAG, embeddings, ranking, citation verification. ([summary](docs/PHASE3-SUMMARY.md))
- **Phase 4 — Comparison engine** ✅ confidence-scored comparison tables (GRADE). ([summary](docs/PHASE4-SUMMARY.md))
- **Phase 5 — Visualizations** ✅ timeline, heatmap, risk-benefit matrix, evidence pyramid. ([summary](docs/PHASE5-SUMMARY.md))
- **Phase 6 — Testing** ✅ unit, integration, e2e (Playwright), accessibility (axe). ([summary](docs/PHASE6-SUMMARY.md))
- **Phase 7 — Deployment** ✅ Docker Compose, Alembic migrations, CI/CD. ([summary](docs/PHASE7-SUMMARY.md))

**Upgrade — Dynamic AI Evidence Engine** ✅ ([summary](docs/UPGRADE-SUMMARY.md))
- **U1** — AI orchestrator coordinating 6 specialist agents + structured trial extraction.
- **U2** — report caching, manual refresh, and living-evidence (up-to-date / update-available).
- **U3** — 3-layer AI transparency (Retrieved Evidence / AI Interpretation / Clinical Summary),
  conflicting-evidence flagging, clinical pearls.
- **U4** — live-mode enablement (`/health` reports live-readiness; `start-app-live.bat`).

**Version 3 — Multi-Agent Medical Research Engine** ✅ ([architecture](docs/07-multi-agent-architecture.md))
- Central **orchestrator** running **twelve** specialized agents in dependency-ordered,
  partly-concurrent stages, with structured execution logs + per-agent timings.
- New agents: Clinical-Question Interpreter (PICO), Safety (comparative matrix),
  Conflict-Resolution (reconciliation), dedicated Citation-Verification gate,
  Visualization, Report-Generator, Continuous-Evidence Monitor — alongside the
  repurposed Search (ranked study list) and Evidence-Ranking (scoring) agents.
- Optional **Research Process** transparency panel (hidden by default). Backward
  compatible with V2 (additive nullable columns; offline engine still deterministic).

## Getting started

### Full stack with Docker

```bash
cp .env.example .env       # optionally add ANTHROPIC_API_KEY / VOYAGE_API_KEY
docker compose up --build  # web:3000, api:8000, worker, postgres+pgvector, redis
```

Web → http://localhost:3000 · API docs → http://localhost:8000/docs. With no AI keys the
engine runs fully in **offline mode** (local fixtures + extractive synthesis) — no external
calls, still end-to-end functional. Add `ANTHROPIC_API_KEY` (and optionally `VOYAGE_API_KEY`,
`NCBI_API_KEY`) and use `EVIDENCE_MODE=auto LLM_MODE=auto` for genuinely dynamic, Claude-written
reports over current literature. Confirm at `http://localhost:8000/health` → `modes.llm_live_ready`.
On Windows, **`start-app.bat`** runs offline and **`start-app-live.bat`** runs live (keys from `apps/api/.env`).

### Local dev (without Docker)

```bash
# API — http://localhost:8000  (SQLite, offline engine, no keys needed)
cd apps/api && python -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt
EVIDENCE_MODE=offline LLM_MODE=offline .venv/Scripts/python -m uvicorn app.main:app --reload

# Web — http://localhost:3000
cd apps/web && npm install && npm run dev
```

### Tests

```bash
cd apps/api && pytest                    # 51 backend tests (offline, deterministic)
cd apps/web && npm run build && npm run test:e2e   # Playwright e2e + axe accessibility
```

## Disclaimer

Decision-support tool for clinicians and researchers. **Not** a diagnostic device and not
a substitute for professional clinical judgment.
