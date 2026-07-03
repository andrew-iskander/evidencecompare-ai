# Phase 3 — Evidence Engine (RAG) Summary

**Status:** ✅ Complete · **Date:** 2026-07-04

The placeholder synthesizer is gone. `POST /reports` now drives a real
Retrieval-Augmented-Generation engine: retrieve from trusted sources → embed →
rank (GRADE-inspired) → verify every citation → synthesize with Claude (or an
offline extractive fallback). The anti-hallucination contract is enforced in
code, not just prompts, and is covered by tests.

## Pipeline (`app/pipeline/engine.py`)

```
retrieve (trusted sources) → embed (Voyage/offline) → hybrid rank + GRADE
  → verify citations (resolve DOI/PMID/registry) → synthesize (Opus 4.8 / offline)
  → persist evidence_docs, doc_chunks, citations, comparison_rows, sections
```

Orchestrator (`orchestrator.py`) pre-creates the 8 `agent_runs` and streams
per-agent `running → done` state as the engine advances, so the SSE contract from
Phase 2 is unchanged for the frontend.

## Delivered

- **Trusted-source clients** (`app/evidence/`) — PubMed (E-utilities), Europe PMC,
  Crossref, ClinicalTrials.gov, openFDA. Each normalizes to `RawDoc` with study-design
  classification. A failing source is isolated, not fatal.
- **Allowlist + dedupe** (`registry.py`) — only `TRUSTED_SOURCES` survive; dedupe by
  DOI → PMID → source id. Modes: `offline` (fixtures), `live` (real APIs),
  `auto` (live, fall back to fixtures if the network yields nothing).
- **Embeddings** (`rag/embeddings.py`) — Voyage `voyage-3.5` in live mode; deterministic
  hashed bag-of-words fallback offline/in tests. Cosine similarity drives relevance.
- **Ranking** (`rag/ranking.py`) — composite of relevance (0.4), evidence-tier design
  weight (0.3), recency (0.15), sample size (0.15); GRADE-inspired confidence bands.
- **Citation verification** (`rag/verifier.py`) — resolves DOI (doi.org) / PubMed /
  registry URLs over HTTP in live mode; records with no identifier can never be cited.
  Only verified docs are persisted as `citations` and re-keyed contiguously (`c1..cN`).
- **Synthesis** (`llm/synthesizer.py`) —
  - **Live:** Claude Opus 4.8, `thinking=adaptive`, `effort=high`, **structured outputs**
    (JSON schema), prompt caching on the system prompt, streamed via `get_final_message()`.
    A `_sanitize` pass drops any citation ref the model invented (defense in depth).
  - **Offline:** deterministic extractive synthesis that only asserts *"this cited item
    exists and is relevant"* — no invented clinical conclusions.
- **Persistence** — `evidence_docs` + `doc_chunks` (embedding stored as JSON for SQLite
  portability; swaps to a pgvector `vector` column + HNSW in prod).

## Anti-hallucination enforcement (in code)

1. Synthesis is closed-book: the LLM only sees retrieved, verified evidence.
2. Citation-verification gate: unverified identifiers never become citations.
3. Every rendered claim/row references only verified `ref_key`s (`_sanitize` + tests).
4. **Direct head-to-head means a *trial* comparing A vs B** — a class-level meta-analysis
   or guideline that merely mentions both no longer counts. Thin head-to-head evidence is
   reported as `insufficient_evidence: true`, never padded.
5. Reproducibility: `model_synthesis`, `prompt_version`, and `source_snapshot`
   (mode, candidate/ranked/verified counts) stored per report.

## Configuration (`app/core/config.py`)

`EVIDENCE_MODE` (auto|live|offline) · `LLM_MODE` (auto|live|offline) ·
`ANTHROPIC_API_KEY` · `VOYAGE_API_KEY` · `NCBI_EMAIL`/`NCBI_API_KEY` ·
`MAX_DOCS_PER_SOURCE` · `TOP_K_CITATIONS` · model IDs (`claude-opus-4-8` /
`claude-sonnet-5` / `claude-haiku-4-5`, `voyage-3.5`). Absent keys → automatic
offline fallback, so the full engine is runnable and testable with no secrets.

## Verification

- `pytest` → **17 passed** (12 prior + 5 new `test_engine.py`): trusted-source-only
  retrieval, every rendered citation verified, honest no-head-to-head reporting,
  evidence-tier ranking order, invented-ref sanitization.
- Test suite pinned to `EVIDENCE_MODE=offline` / `LLM_MODE=offline` → deterministic,
  network-free, no API keys required.
- `mypy app` → clean (55 files). Report lifecycle test asserts the anti-hallucination
  contract end-to-end through the real engine.

## Notes / follow-ups

- `doc_chunks.embedding` is JSON today for SQLite parity; production migration swaps it to
  a pgvector column + HNSW index and moves ANN search into SQL (hybrid vector + trigram).
- Live-mode cost accounting flows through `agent_runs` / `reports.token_cost_usd`
  (offline synthesis is $0).

## Next: Phase 4 (Medical comparison engine) → Phase 5 (Visualizations)

Deepen comparison-table generation with richer confidence scoring and specialist-agent
extraction (guideline positions, trial endpoints, safety matrix), then the frontend
evidence visualizations (timelines, heatmaps, risk-benefit matrix, evidence pyramid).
