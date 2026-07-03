# Phase 7 — Deployment Summary

**Status:** ✅ Complete · **Date:** 2026-07-04

Containerizes the whole app, adds the Alembic migration baseline, and wires CI/CD
so the stack comes up with a single `docker compose up --build` and every push is
linted, type-checked, tested, and image-built.

## Docker

- **`apps/api/Dockerfile`** — Python 3.12-slim, installs `requirements.txt`, runs as a
  non-root user, ships a `/health` HEALTHCHECK (curl). Default CMD serves uvicorn; the
  compose `migrate`/`worker` services override the command.
- **`apps/web/Dockerfile`** — multi-stage (`deps → builder → runner`) producing a minimal
  Next.js **standalone** image (`output: "standalone"` added to `next.config.mjs`). Runs as
  a non-root user; `NEXT_PUBLIC_API_BASE_URL` is a build arg (baked into the browser bundle).
- **`.dockerignore`** for both apps (excludes venvs, node_modules, caches, `.env`, screenshots).

## Orchestration — `docker-compose.yml`

Six services: **db** (`pgvector/pgvector:pg16`, healthcheck) · **redis** (healthcheck) ·
**migrate** (one-shot `alembic upgrade head`, gates the app on success) · **api**
(`ENV=prod`, Postgres, `PIPELINE_MODE=celery`) · **worker** (Celery) · **web**. Startup
ordering uses `depends_on` conditions (`service_healthy`, `service_completed_successfully`).
All config comes from a root `.env` (see **`.env.example`**); with no AI keys the engine
falls back to offline mode, so the stack is functional out of the box.

## Database migrations (Alembic)

- Baseline migration **`alembic/versions/1e97fd1330a4_initial_schema.py`** captures all 10
  tables (users, molecules, reports, report_sections, comparison_rows w/ `rationale`,
  citations w/ `study_design`, evidence_docs, doc_chunks, agent_runs, exports) plus
  `reports.molecule_evidence`. Verified: `upgrade head` creates the schema and `downgrade
  base` cleanly reverses it on SQLite.
- `psycopg2-binary` added for the sync Alembic driver against Postgres; `env.py` already
  translates the async URL. In prod the API skips `create_all` (`ENV=prod`) and relies on
  the `migrate` service. `doc_chunks.embedding` stays JSON; a pgvector `vector(1024)` + HNSW
  swap is the documented next migration (the db image already ships pgvector).

## CI/CD — `.github/workflows/ci.yml`

Three jobs on push/PR: **api** (ruff → mypy → pytest, offline env), **web** (lint →
typecheck → build → Playwright e2e, uploads the report on failure), **docker** (buildx
builds both images). Pip/npm caches enabled; concurrency cancels superseded runs.

## Repo hygiene / lint config

- Root `.gitignore` (secrets, caches, build output, Playwright artifacts).
- Ruff config hardened so `ruff check .` is green repo-wide and CI-ready:
  `flake8-bugbear.extend-immutable-calls` for FastAPI `Depends`/`Query`/… (the B008 false
  positive), and `extend-exclude = ["alembic/versions"]` (generated code). Auto-fixed the
  UP/I violations, wrapped remaining long lines, and **removed the now-dead
  `pipeline/placeholder.py`** (superseded by the Phase 3 engine).

## Verification

- `ruff check .` clean · `mypy app` clean (58 files) · `pytest` → **26 passed**.
- Web `next build` (standalone) produces `.next/standalone/server.js` + `.next/static`;
  `public/` created so the image COPY is valid.
- `tsc`/`eslint` clean · Playwright → **10 passed, 1 skipped** (opt-in live).
- `docker-compose.yml` and CI workflow validated (YAML parses; services `db/redis/migrate/
  api/worker/web`; jobs `api/web/docker`). **Docker images not built here** (no Docker
  daemon in this environment) — the Dockerfiles/compose are authored to spec and their
  inputs (standalone build, migrations, requirements) are each verified.

## Product status

All seven phases (0–7) complete: a production-grade, RAG-grounded, fully-cited,
confidence-scored, visualized, tested, and containerized molecule-comparison platform with
enforced anti-hallucination guarantees. Follow-ups: pgvector column migration, PDF/PPTX/XLSX
binary export rendering, and a Lighthouse performance budget in CI.
