# EvidenceCompare AI — Tech Stack & Decisions

**Phase:** 0 (Design) · **Last updated:** 2026-07-03

Each choice lists the decision and the *why*. Alternatives considered noted where relevant.

---

## Frontend

| Concern | Choice | Why |
|---|---|---|
| Framework | **Next.js 15 (App Router)** | SSR/streaming, RSC, mature ecosystem; matches prompt |
| Language | **TypeScript** (strict) | Type safety across UI + API client |
| UI runtime | **React 19** | Concurrent features, streaming UI |
| Styling | **Tailwind CSS v4** | Utility-first, dark/light theming (installed skill: `tailwindcss`) |
| Components | **shadcn/ui + Radix** | Accessible primitives (skills: `shadcn-ui`, `radix-ui-design-system`, `headlessui`) |
| Animation | **Framer Motion (motion)** + GSAP for hero | Polished micro-interactions (skills: `motion-framer`, `gsap-react`) |
| Premium accents | **Aceternity UI / Magic UI** | Hero + marketing polish (skills present) |
| Charts | **Recharts** (+ Tremor for dashboards) | Evidence heatmaps, risk-benefit, timelines (skills: `recharts`, `tremor-design-system`) |
| Icons | **Lucide** | Tree-shakeable icon set (skill: `lucide-icons`) |
| State/data | **TanStack Query + Zustand** | Server cache + light client state |
| Theming | **next-themes** | Dark/light toggle |
| Streaming | **SSE (EventSource)** | Live per-agent progress |

## Backend

| Concern | Choice | Why |
|---|---|---|
| API framework | **FastAPI (Python 3.12)** | Async, Pydantic v2 validation, SSE support; matches prompt |
| ORM | **SQLAlchemy 2.0 + Alembic** | Typed models + migrations |
| Validation | **Pydantic v2** | Request/response + settings |
| Background jobs | **Celery + Redis** | Long report pipelines off the request path |
| Auth | **JWT (access/refresh)**, argon2 password hashing | Stateless auth, saved reports |
| Rate limiting | **slowapi / Redis token bucket** | Protect upstream + LLM budget |

## Data

| Concern | Choice | Why |
|---|---|---|
| Primary DB | **PostgreSQL 16** | Relational core |
| Vector store | **pgvector** extension | Keep vectors in Postgres — one datastore, hybrid search |
| Cache / broker | **Redis 7** | Response cache + Celery broker |
| Object storage | **S3-compatible** (MinIO local) | Store generated exports |

## AI / Evidence

| Concern | Choice | Why |
|---|---|---|
| LLM provider | **Anthropic Claude API** | Report gen + agents |
| Report synthesis | **`claude-opus-4-8`** ($5/$25 per MTok, 1M ctx, adaptive thinking) | Highest-quality synthesis + confidence scoring |
| Orchestration / mid reasoning | **`claude-sonnet-5`** ($3/$15; intro $2/$10 through 2026-08-31) | Cost-effective agent steps |
| Cheap extraction / classification | **`claude-haiku-4-5`** ($1/$5 per MTok) | Metadata parsing, relevance labels |
| Embeddings | **Voyage AI `voyage-3.5`** | Anthropic has no embeddings endpoint; Voyage is the recommended partner |
| SDK | **`anthropic` Python SDK** | Streaming, tool use, structured outputs, prompt caching |

> Model IDs are exact per the current catalog. Use adaptive thinking
> (`thinking={"type":"adaptive"}`) + `output_config={"effort": ...}` on 4.8/Sonnet 5;
> `budget_tokens`/`temperature` are rejected on these models.

## Evidence source clients

- PubMed / Europe PMC (E-utilities / REST), Crossref REST, ClinicalTrials.gov API v2,
  openFDA, guideline-body sources. Each wrapped in a rate-limited, cached client.

## Tooling & quality

| Concern | Choice |
|---|---|
| FE lint/format | ESLint + Prettier |
| BE lint/format | Ruff + Black + mypy |
| FE tests | Vitest + Testing Library + Playwright (e2e) |
| BE tests | pytest + httpx AsyncClient |
| a11y | axe-core in CI |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Diagrams | Mermaid (in-repo) |

## Key rationale

- **pgvector over a dedicated vector DB (Pinecone/Weaviate):** single datastore, hybrid
  keyword+vector, simpler ops for v1. Revisit at scale.
- **Model tiering:** most tokens are cheap extraction/ranking → Haiku/Sonnet; reserve
  Opus 4.8 for final synthesis where quality and confidence scoring matter most.
- **Claude for synthesis, Voyage for vectors:** best-in-class reasoning + a real
  embeddings API, since Anthropic does not provide embeddings.
