# Phase 0 — Decisions Summary

**Status:** ✅ Complete · **Date:** 2026-07-03

Phase 0 is design only — no application code, per the master prompt ("do NOT jump into coding").

## Deliverables produced

- [x] Product requirements — `docs/00-product-requirements.md`
- [x] System architecture (+ Mermaid) — `docs/01-architecture.md`
- [x] Tech stack + rationale — `docs/02-tech-stack.md`
- [x] Folder structure — `docs/03-folder-structure.md`
- [x] Database schema (ER + DDL, pgvector) — `docs/04-database-schema.md`
- [x] API specification (REST + SSE) — `docs/05-api-specification.md`
- [x] AI workflow (RAG, agents, model tiering, anti-hallucination) — `docs/06-ai-workflow.md`
- [x] CLAUDE.md — root
- [x] README — root

## Key decisions

| Decision | Choice | Why |
|---|---|---|
| Repo shape | Monorepo (`apps/web`, `apps/api`, `packages/shared-types`) | Shared types, one CI |
| Frontend | Next.js 15 / React 19 / TS / Tailwind v4 / shadcn / Framer Motion | Prompt-specified, polished, installed skills cover it |
| Backend | FastAPI / SQLAlchemy 2 / Celery | Async, typed, background pipelines |
| Vector store | pgvector in Postgres | One datastore, hybrid search, simpler ops for v1 |
| Synthesis model | `claude-opus-4-8` ($5/$25) | Highest-quality synthesis + confidence scoring |
| Agent/orchestration model | `claude-sonnet-5` ($3/$15, intro $2/$10) | Cost-effective reasoning |
| Extraction model | `claude-haiku-4-5` ($1/$5) | High-volume, low-stakes labeling |
| Embeddings | Voyage `voyage-3.5` (1024-dim) | Anthropic has no embeddings API |
| Anti-hallucination | Closed-book synthesis + citation-verification gate + per-claim attribution | Enforces "never fabricate citations" |
| Async model | 202 + Celery job + SSE progress | Long pipelines off the request path |

## Open questions to resolve before/within later phases

- Exact per-source rate limits & caching TTLs (respect each API's terms).
- RxNorm/ATC normalization source and offline fallback.
- Guideline ingestion: which bodies expose structured feeds vs. require parsing.
- Export rendering approach for PPTX/PDF (server-side templating vs. code-execution).
- Auth hardening details (refresh rotation, session revocation).
- Hosting target for prod (all-container vs. Vercel + container API).

## Next: Phase 1 (Frontend)

Scaffold `apps/web`, design system + theming (dark/light), the A/B/topic input flow, and
the streaming report view with placeholder data — before wiring the real backend.
