# CLAUDE.md — EvidenceCompare AI

Guidance for Claude Code (and developers) working in this repository.

## What this is

EvidenceCompare AI is a production-grade web app that compares **two pharmaceutical
molecules** for a **user-defined clinical topic** using only trusted medical evidence,
and produces an interactive, exportable, fully-cited evidence report.

**Prime directive:** *Never fabricate citations. State plainly when evidence is
insufficient.* Every substantive claim must trace to a verified source (DOI/PMID/registry).

## Repository layout

Monorepo. See `docs/03-folder-structure.md`.
- `apps/web` — Next.js 15 + React 19 + TypeScript + Tailwind v4 + shadcn/ui + Framer Motion.
- `apps/api` — FastAPI (Python 3.12) + SQLAlchemy 2 + Postgres/pgvector + Redis + Celery.
- `docs/` — Phase 0 design docs (PRD, architecture, tech stack, schema, API, AI workflow).
- `.claude/skills/` — installed skills (16 UI/viz/frontend packages).

## Design docs (read before building)

| Doc | Contents |
|---|---|
| `docs/00-product-requirements.md` | Personas, inputs/outputs, FR/NFR, acceptance criteria |
| `docs/01-architecture.md` | System diagram, request lifecycle, trust boundary |
| `docs/02-tech-stack.md` | Every stack choice + rationale |
| `docs/03-folder-structure.md` | Directory conventions |
| `docs/04-database-schema.md` | ER diagram + DDL (pgvector) |
| `docs/05-api-specification.md` | REST + SSE endpoints |
| `docs/06-ai-workflow.md` | RAG pipeline, agents, model selection, anti-hallucination |
| `docs/07-multi-agent-architecture.md` | **V3** twelve-agent orchestration: diagrams, per-agent I/O + error handling |

## Multi-agent engine (V3 — IMPORTANT)

Every search runs through the **AI Orchestrator** (`apps/api/app/agents/orchestrator.py`),
which coordinates **twelve** specialist agents over a shared `PipelineState` and
emits progress/logs/timings; persistence stays in `pipeline/engine.py`.

- Agents live in `apps/api/app/agents/` (`interpreter`, `search`, `guideline`,
  `extraction`, `ranking`, `safety`, `conflict`, `verification`, `writer`,
  `visualization`, `report`, `monitor`). Each subclasses `agents.base.Agent`,
  implements `async run(state)`, returns an `AgentOutcome`, and has **both** a
  live-LLM path and a **deterministic offline fallback** (so `pytest` runs keyless).
- Execution is a list of dependency-ordered **stages** (`orchestrator.DEFAULT_PLAN`);
  independent agents in a stage run concurrently. Agents must **not** touch the DB
  (only the orchestrator's progress callback does) — keep them pure over `state`.
- Add a new capability as a **new agent/stage**; don't fold it into an existing one.
  Keep the anti-hallucination rules below intact (verification is a dedicated agent).
- New report artifacts are additive nullable JSON columns (see the latest Alembic
  migration) and surface via `ReportOut` + the frontend Research-Process panel.
- Full design + diagrams: `docs/07-multi-agent-architecture.md`.

## AI / LLM conventions (IMPORTANT)

This project builds on the **Anthropic Claude API**. Use exact, current model IDs:
- **`claude-opus-4-8`** — final report synthesis + confidence scoring ($5/$25 per MTok).
- **`claude-sonnet-5`** — orchestration + most agent steps ($3/$15; intro $2/$10 → 2026-08-31).
- **`claude-haiku-4-5`** — cheap extraction/classification ($1/$5 per MTok).
- Embeddings: **Voyage AI `voyage-3.5`** (Anthropic has no embeddings endpoint), 1024-dim.

API rules for current models (Opus 4.8 / Sonnet 5):
- Use `thinking={"type":"adaptive"}` + `output_config={"effort":"high"}`.
- Do **not** send `budget_tokens`, `temperature`, `top_p`, `top_k` — they 400.
- **Stream** large `max_tokens` calls; use `get_final_message()`.
- Use **structured outputs** (`output_config.format`) — no assistant prefills (they 400).
- Use **prompt caching** on the stable system prompt + shared evidence context.
- When in doubt about the API, invoke the `claude-api` skill — don't guess from memory.

## Anti-hallucination rules (enforced in code, not just prompts)

1. LLM synthesizes only over **retrieved** evidence; the RAG layer is the only thing that
   touches external sources, and it enforces the trusted-source allowlist.
2. Every citation is verified against its source before it can appear in a report.
3. Every claim carries `citation_ids`; zero-citation claims are not rendered as fact.
4. Thin evidence → `confidence: very_low` + `insufficient_evidence: true`, never invention.

## Trusted sources (allowlist)

PubMed, Europe PMC, Crossref, ClinicalTrials.gov, FDA (openFDA), EMA, ACC, AHA, ESC,
KDIGO, ADA, NICE, WHO, Cochrane. Nothing else may become a citation.

## Skills available

Frontend/viz skills are installed in `.claude/skills/`: `tailwindcss`, `shadcn-ui`,
`radix-ui-design-system`, `headlessui`, `motion-framer`, `gsap-react`, `aceternity-ui`,
`magic-ui`, `heroui-react`, `tremor-design-system`, `recharts`, `lucide-icons`,
`react-three-fiber`, `spline-interactive`, `unsplash`, `ai-image-generation`.
(Restart the session to activate newly installed skills.)

## Working style

- Work in phases (see README §Roadmap). Summarize decisions at the end of each phase.
- Keep code modular, typed, documented. Match surrounding style.
- Frontend/backend types stay in sync via OpenAPI-generated `packages/shared-types`.
- Record model ID + prompt version + retrieval snapshot on every report (reproducibility).

## Commands (to be finalized as code lands)

- Local stack: `docker compose up`
- API tests: `cd apps/api && pytest` (offline/deterministic; no keys needed)
- Web e2e: `cd apps/web && npm run test:e2e` (Playwright; builds must exist — `npm run build`).
  Frontend-only specs are self-contained; the authenticated live flow (`e2e/live.spec.ts`)
  is opt-in via `E2E_LIVE=1` with the API running on :8000 (see the spec header).
- Lint/type: `ruff && mypy` (api), `npm run lint && npm run typecheck` (web)
