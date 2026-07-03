# Phase 2 — Backend Summary

**Status:** ✅ Complete · **Date:** 2026-07-03

FastAPI backend scaffolded under `apps/api`, built and verified end-to-end (12 tests +
live server run). Runs on SQLite for dev/test; Postgres/pgvector wiring ready for Phase 3.

## Stack (installed & tested)

FastAPI · SQLAlchemy 2.0 (async) · Pydantic v2 / pydantic-settings · PyJWT · argon2-cffi ·
aiosqlite (dev/test) / asyncpg (prod) · Celery + Redis (wired) · Alembic (scaffold).

## Delivered

- **Auth** — `/auth/register`, `/login`, `/refresh`, `/me`. JWT access/refresh, argon2 hashing.
- **Molecules** — `/molecules/search` (seed list; RxNorm/ATC in Phase 3).
- **Reports** — `POST /reports` (202 + async dispatch), `GET /reports/{id}` (full),
  `GET /reports` (list mine), `DELETE`, `POST /{id}/share`, and **SSE**
  `GET /reports/{id}/stream` (token via query for EventSource).
- **Exports** — `POST /reports/{id}/exports` + `GET /exports/{id}`; markdown rendered inline
  (with per-claim citation markers + unsourced/insufficient flags), pdf/pptx/xlsx recorded.
- **Evidence pipeline** — 8-agent orchestrator with live per-agent progress, GRADE-style
  section/row confidence, per-agent token+USD cost accounting, and honest
  insufficient-evidence sections. Synthesis is a **placeholder** (real RAG = Phase 3).
- **Models** — users, molecules, reports, report_sections, comparison_rows, evidence_docs,
  citations (with `verified` gate), agent_runs, exports.
- **Infra** — CORS, health check, lifespan `create_all` (dev), Dockerfile, Alembic env,
  Celery app/task, `.env.example`.

## Pipeline modes (`PIPELINE_MODE`)

`background` (default, asyncio task — live SSE) · `eager` (inline, used by tests) ·
`celery` (Redis-backed worker).

## Verification

- `pytest` → **12 passed** (auth flow, refresh, dup/401, molecule search, report lifecycle,
  list, SSE stream, markdown export, ownership 403, 404, delete 204).
- Live `uvicorn` run: `/health` ok, OpenAPI served at `/openapi.json` (+ `/docs`).
- Live end-to-end (background mode): register → login → `POST /reports` (202) →
  **SSE streamed real `running→done` agent transitions + section reveals + `complete`** →
  final `GET` returned complete report (4 sections, 3 verified citations, cost $0.0704).

## Design decisions

- **SSE by DB-polling** the report + agent_runs (works with or without Redis; Redis
  pub/sub is a Phase 3 optimization). Frontend already shaped for these events.
- **Eager pipeline mode** for deterministic tests without a broker.
- pgvector columns + `doc_chunks` deferred to Phase 3 so Phase 2 runs on SQLite; the
  `evidence_docs`/`citations` tables and the `verified` gate already exist.
- 202 + async dispatch matches the API spec; report content is placeholder scaffolding.

## Next: Phase 3 (Evidence engine) + integration

- Replace `pipeline/placeholder.py` with the real RAG engine: trusted-source clients,
  Voyage embeddings, pgvector hybrid search, evidence ranking, citation verification,
  and real Claude calls (Opus 4.8 / Sonnet 5 / Haiku 4.5).
- Wire the frontend to the live API (auth screens, `POST /reports`, real SSE) and generate
  `apps/web/types` from the backend OpenAPI schema. API surface + SSE contract are stable.
