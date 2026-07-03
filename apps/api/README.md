# EvidenceCompare AI — API (Phase 2)

FastAPI backend: JWT auth, user accounts, saved reports, a simulated async
evidence pipeline, and an SSE progress stream. Runs on **SQLite** for dev/test and
**PostgreSQL + pgvector** in production (pgvector columns land in Phase 3).

## What's implemented in Phase 2

- **Auth** — register, login, refresh, `me` (JWT access/refresh, argon2 hashing).
- **Molecules** — `/molecules/search` (seed list; RxNorm/ATC normalization in Phase 3).
- **Reports** — create (202 + async pipeline), get (full report), list mine, delete,
  share token, and **SSE** progress stream (`/reports/{id}/stream`).
- **Exports** — markdown rendered inline; pdf/pptx/xlsx recorded (binary rendering Phase 7).
- **Pipeline** — 8-agent orchestration with per-agent progress + cost accounting,
  producing a structurally-complete report from a **placeholder** synthesizer.
  The real RAG evidence engine replaces the placeholder in Phase 3 (same shape).

> Report content in Phase 2 is illustrative scaffolding, not medical truth.

## Run

```bash
python -m venv .venv && . .venv/Scripts/activate   # (Windows) or source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload                       # http://localhost:8000
```

- OpenAPI docs: `http://localhost:8000/docs`
- Health: `GET /health`

## Test

```bash
pytest                 # SQLite + eager pipeline, no Postgres/Redis needed
```

## Pipeline modes (`PIPELINE_MODE`)

- `background` (default dev) — runs on the event loop via `asyncio.create_task`; SSE streams live progress.
- `eager` — runs inline (used by tests for determinism).
- `celery` — hands off to a Celery worker (requires Redis): `celery -A app.workers.celery_app.celery_app worker`.

## Structure

```
app/
  main.py                # app factory, CORS, lifespan (dev create_all)
  core/                  # config (pydantic-settings), security (JWT/argon2), logging
  db/                    # async engine/session, Base, init_db
  models/                # SQLAlchemy: user, molecule, report + sections/rows/citations/agent_runs/exports
  schemas/               # Pydantic request/response
  api/v1/routes/         # auth, molecules, reports (+SSE), exports
  services/              # auth, report, export logic
  pipeline/              # agent roster, placeholder synthesizer, orchestrator
  workers/               # celery app + task
alembic/                 # migrations (autogenerate vs Postgres in Phase 3)
tests/                   # pytest (auth + reports, incl. SSE + ownership)
```

## Next (Phase 3)

Replace `pipeline/placeholder.py` with the real RAG engine: trusted-source clients,
Voyage embeddings, pgvector hybrid search, evidence ranking, and citation verification —
plus the real Claude calls (Opus 4.8 / Sonnet 5 / Haiku 4.5). The API surface and SSE
contract stay the same, so the frontend and these tests keep working.
