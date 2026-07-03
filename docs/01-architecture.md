# EvidenceCompare AI — System Architecture

**Phase:** 0 (Design) · **Last updated:** 2026-07-03

---

## 1. High-level architecture

```mermaid
flowchart TB
    subgraph Client["Frontend — Next.js / React / TS"]
        UI[Report UI + Dashboards]
        Stream[SSE / streaming client]
    end

    subgraph Edge["API Gateway — FastAPI"]
        Auth[Auth / JWT]
        REST[REST + SSE endpoints]
        RL[Rate limiting]
    end

    subgraph Core["Evidence Engine"]
        Orches[Agent Orchestrator]
        RAG[RAG Retrieval + Ranking]
        Verify[Citation Verifier]
        Compare[Comparison Engine]
        Report[Report Generator]
    end

    subgraph Agents["Specialized AI Agents"]
        A1[Search]
        A2[Guideline]
        A3[Trial]
        A4[Meta-analysis]
        A5[Safety]
        A6[Evidence Ranking]
        A7[Citation Verification]
        A8[Report Generation]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL + pgvector)]
        REDIS[(Redis cache + queue)]
        OBJ[(Object storage — exports)]
    end

    subgraph External["Trusted External Sources"]
        PM[PubMed / Europe PMC]
        CR[Crossref]
        CT[ClinicalTrials.gov]
        FDA[openFDA / EMA]
        GL[Guideline bodies]
    end

    subgraph AIProviders["AI Providers"]
        CLAUDE[Claude API — Opus 4.8 / Sonnet 5 / Haiku 4.5]
        VOYAGE[Voyage AI — embeddings]
    end

    UI --> REST
    Stream -.SSE.-> REST
    REST --> Auth --> Orches
    Orches --> RAG --> Verify --> Compare --> Report
    Orches --> A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8
    RAG --> External
    RAG --> VOYAGE
    Agents --> CLAUDE
    Core --> PG
    Core --> REDIS
    Report --> OBJ
```

---

## 2. Request lifecycle (generate a report)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Next.js
    participant API as FastAPI
    participant Q as Redis/Celery
    participant O as Orchestrator
    participant RAG as Retrieval
    participant LLM as Claude
    participant DB as Postgres+pgvector

    U->>FE: A, B, Topic
    FE->>API: POST /reports
    API->>DB: create report(status=queued)
    API->>Q: enqueue job
    API-->>FE: 202 {report_id}
    FE->>API: GET /reports/{id}/stream (SSE)
    Q->>O: run pipeline
    O->>RAG: retrieve(A,B,topic) from trusted sources
    RAG->>DB: upsert docs + embeddings
    O->>LLM: rank / extract / synthesize (per agent)
    O->>DB: persist sections + citations (verified)
    O-->>API: progress events
    API-->>FE: SSE section/agent updates
    O->>DB: status=complete
    FE->>U: interactive report
```

---

## 3. Component responsibilities

| Component | Responsibility |
|---|---|
| **Frontend (Next.js)** | Input form, streaming report view, dashboards, visualizations, export triggers, auth UI |
| **API Gateway (FastAPI)** | AuthN/Z, request validation, SSE streaming, rate limiting, job enqueue |
| **Orchestrator** | Runs the agent pipeline, manages state machine, emits progress events |
| **RAG Retrieval** | Query trusted APIs, normalize, dedupe, embed (Voyage), vector + keyword search |
| **Evidence Ranking** | Score by design/recency/size/relevance; GRADE-style confidence |
| **Citation Verifier** | Resolve every DOI/PMID/registry ID against source before inclusion |
| **Comparison Engine** | Build side-by-side rows with confidence scores |
| **Report Generator** | Compose sections, enforce per-claim attribution, structured output |
| **Data Layer** | Postgres (relational + pgvector), Redis (cache/queue), object storage (exports) |

---

## 4. Async processing

- Report generation is a **background job** (Celery worker, Redis broker).
- API returns `202` + `report_id`; client subscribes to **SSE** for live progress.
- Long LLM calls use **streaming** (`.stream()` / `get_final_message()`), never blocking a
  request thread past sensible timeouts.
- Idempotency: a normalized `(A, B, topic, source_snapshot)` key enables cache reuse.

---

## 5. Caching & cost strategy

- **Redis** caches: normalized drug lookups, upstream API responses (TTL per source
  license), completed report payloads.
- **Prompt caching (Claude):** stable system prompts + shared evidence context cached to
  cut input cost on multi-agent passes over the same evidence set.
- **Model tiering:** cheap extraction on Haiku 4.5, orchestration on Sonnet 5, final
  synthesis + confidence scoring on Opus 4.8 (see `06-ai-workflow.md`).

---

## 6. Trust boundary

- Only the **RAG layer** talks to external evidence sources; the allowlist is enforced there.
- The LLM never "browses" freely for citations — it only synthesizes over **retrieved,
  verified** records passed in context. This is the core anti-hallucination control.

---

## 7. Environments

- **Local:** Docker Compose (frontend, api, worker, postgres+pgvector, redis).
- **CI:** GitHub Actions (lint, type-check, unit/integration/e2e, build images).
- **Prod:** containerized backend + worker; managed Postgres w/ pgvector; managed Redis;
  frontend on Vercel or container. See `07` deployment (Phase 7).
