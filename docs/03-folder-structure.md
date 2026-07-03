# EvidenceCompare AI — Folder Structure

**Phase:** 0 (Design) · **Last updated:** 2026-07-03

Monorepo with a Next.js frontend and a FastAPI backend, orchestrated by Docker Compose.

```
Project2/
├── CLAUDE.md                     # Agent/dev guide (root)
├── README.md
├── docker-compose.yml            # local: web, api, worker, postgres+pgvector, redis, minio
├── .env.example
├── docs/                         # Phase 0 design docs (this folder)
│   ├── 00-product-requirements.md
│   ├── 01-architecture.md
│   ├── 02-tech-stack.md
│   ├── 03-folder-structure.md
│   ├── 04-database-schema.md
│   ├── 05-api-specification.md
│   ├── 06-ai-workflow.md
│   └── PHASE0-SUMMARY.md
├── skills/                       # source skill packages (staging)
├── .claude/
│   └── skills/                   # installed skills (active)
│
├── apps/
│   ├── web/                      # Next.js 15 frontend
│   │   ├── app/                  # App Router
│   │   │   ├── (marketing)/      # landing
│   │   │   ├── (app)/            # authed dashboard
│   │   │   │   ├── compare/      # A/B/topic input
│   │   │   │   └── reports/[id]/ # streaming report view
│   │   │   ├── api/              # route handlers (BFF, if needed)
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── ui/               # shadcn/ui primitives
│   │   │   ├── report/           # section renderers
│   │   │   └── viz/              # timeline, heatmap, pyramid, risk-benefit
│   │   ├── lib/                  # api client, sse, hooks, utils
│   │   ├── stores/               # zustand
│   │   ├── types/                # shared TS types (generated from OpenAPI)
│   │   ├── tests/                # vitest + playwright
│   │   ├── tailwind.config.ts
│   │   └── package.json
│   │
│   └── api/                      # FastAPI backend
│       ├── app/
│       │   ├── main.py           # app factory, routers, middleware
│       │   ├── core/             # config, security, logging, rate limit
│       │   ├── api/v1/           # routers: auth, reports, molecules, exports
│       │   ├── models/           # SQLAlchemy ORM models
│       │   ├── schemas/          # Pydantic request/response
│       │   ├── db/               # session, migrations (alembic/)
│       │   ├── services/         # business logic
│       │   ├── evidence/         # source clients (pubmed, crossref, ctgov, fda, guidelines)
│       │   ├── rag/              # embeddings (voyage), chunking, hybrid search, ranking
│       │   ├── agents/           # search, guideline, trial, meta, safety, ranking, verify, report
│       │   ├── llm/              # claude client wrapper, model tiering, prompt cache
│       │   ├── pipeline/         # orchestrator + state machine
│       │   ├── exports/          # pdf, pptx, xlsx, markdown renderers
│       │   └── workers/          # celery tasks
│       ├── tests/                # pytest (unit + integration)
│       ├── alembic/              # migration scripts
│       ├── pyproject.toml
│       └── Dockerfile
│
├── packages/
│   └── shared-types/             # OpenAPI-generated types shared FE/BE
│
└── .github/workflows/            # ci.yml (lint, typecheck, test, build)
```

## Conventions

- **API versioning** under `/api/v1`. Breaking changes → `/api/v2`.
- **Agents** are single-responsibility modules under `app/agents/`, each with a typed
  input/output contract and its own prompt (versioned).
- **Evidence source clients** never called directly by agents — only through the `rag`
  layer, which enforces the trusted-source allowlist.
- **Types** flow from OpenAPI → `packages/shared-types` → frontend, to keep FE/BE in sync.
- **Prompts** live beside their agent as versioned constants (`prompt_v1`, ...), recorded
  on each report for reproducibility.
