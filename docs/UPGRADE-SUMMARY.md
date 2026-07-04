# Upgrade Summary — Dynamic AI Medical Evidence Engine (U1–U4)

This upgrade transforms EvidenceCompare AI from a single-call comparison tool into a
**dynamic, multi-agent, evidence-driven research platform**. Every search generates a new
report from freshly retrieved evidence; nothing is templated or hardcoded. The whole
system runs **offline by default** (deterministic fixtures + extractive synthesis, no keys)
and becomes genuinely **live** — Claude-written reports over current literature — the moment
an `ANTHROPIC_API_KEY` is provided. Rollback point: git tag `v1-complete`.

## U1 — AI Orchestrator + 6 specialist agents + structured extraction

The pipeline is now an **orchestrator** (`app/agents/orchestrator.py`) coordinating six
specialized agents, each with a live-LLM path and a deterministic offline fallback:

| Agent | Role |
|---|---|
| Search | Generates optimized queries, retrieves from trusted sources |
| Evidence-Ranking | Embeds, GRADE-scores, verifies citations |
| Trial-Extraction | Pulls structured data per study |
| Guideline | Summarizes guideline recommendations |
| Comparison | Builds the side-by-side comparison |
| Medical-Writer | Produces the clinician-facing narrative |

Structured **trial extractions** (HR, RR, CI, p-value, population, intervention, comparator,
outcomes, adverse events, strengths, limitations) are stored in a new `trial_extractions`
table and shown in an "Extracted Trial Data" panel. Anti-hallucination is preserved:
verified-only citations, invented-reference dropping, and honest "Not reported" nulls.

## U2 — Caching + manual refresh + living evidence

- **Caching**: reports carry a normalized `query_key`; the same query is reused within
  `REPORT_CACHE_TTL_HOURS` (default 168h) unless `refresh=true`.
- **Manual refresh**: `POST /reports/{id}/refresh` re-runs a fresh report from the same inputs.
- **Living evidence**: each report stores an `evidence_fingerprint`; `POST /reports/{id}/check-updates`
  re-retrieves and flags `update_available` when newer high-tier evidence appears, else
  `up_to_date`. A daily Celery-beat sweep (`scan_stale_reports`) automates this when a beat
  scheduler runs. The UI shows a freshness badge + Check-for-updates + Refresh buttons.

## U3 — AI transparency (3 layers) + conflict flag + clinical pearls

- **Three transparency layers**, never mixed: **Retrieved Evidence** (raw facts — comparison,
  extractions, charts, citations), **AI Interpretation** (synthesized narrative), and
  **Clinical Summary** (executive summary + clinical pearls). Each section carries a `layer`.
- **Conflicting-evidence flag** (`app/pipeline/quality.py`): flags a molecule whose studies
  report opposite, statistically significant effect directions; shown as a callout.
- **Clinical Pearls**: a new section of practical, cited takeaways.

## U4 — Live-mode enablement + verification

- `/health` reports the active `modes` (`evidence_mode`, `llm_mode`, `llm_live_ready`,
  `embeddings_live_ready`) so you can confirm at a glance whether reports are live or offline.
- `apps/api/.env.example` documents every mode + key; `docker-compose.yml` already passes
  keys/modes to the api + worker services.
- `start-app-live.bat` launches the stack in `auto` mode, reading keys from `apps/api/.env`.

### Enabling live mode

1. Create `apps/api/.env` with at least:
   ```
   ANTHROPIC_API_KEY=sk-ant-...      # required for live AI synthesis + agents
   VOYAGE_API_KEY=pa-...             # optional; better embeddings
   NCBI_API_KEY=...                  # optional; higher PubMed limits
   NCBI_EMAIL=you@example.com
   ```
2. Run **`start-app-live.bat`** (or set `EVIDENCE_MODE=auto LLM_MODE=auto` and start uvicorn).
3. Confirm at `http://localhost:8000/health` → `modes.llm_live_ready: true`.

With no key, `auto` mode safely falls back to offline — the app is always runnable.

## Verification

- **Backend**: 40 pytest (offline/deterministic), `ruff` + `mypy` clean; Alembic migration
  chain (initial → trial_extractions → cache/freshness → layers/conflicts) upgrades and
  downgrades cleanly on SQLite.
- **Frontend**: `tsc` + ESLint + `next build` clean; 10 Playwright e2e + axe accessibility
  (0 serious violations) + the opt-in live flow (`E2E_LIVE=1`) asserting the six-agent
  pipeline, extracted trial data, freshness controls, and the three transparency layers.
