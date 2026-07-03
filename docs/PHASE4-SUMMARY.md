# Phase 4 — Medical Comparison Engine Summary

**Status:** ✅ Complete · **Date:** 2026-07-04

Turns the Phase 3 evidence engine into a real **medical comparison engine**:
comprehensive, per-molecule comparison tables with explicit GRADE confidence
scoring and a plain-language rationale on every row, plus specialist domain
agents that do real extraction instead of only reporting progress.

## New building blocks

- **GRADE scorer** (`app/rag/grade.py`) — `grade(docs) → {level, score, rationale,
  dimensions}` over six explicit dimensions: study design, evidence volume, directness
  (topic relevance), consistency (tier agreement), recency, precision (sample size).
  A lone low-tier source can never reach `high`. `ranking.confidence_from` now delegates
  here, so **every confidence label in the app comes from one scorer**.
- **Specialist agents** (`app/agents/specialists.py`) — classify verified evidence into
  clinical domains (mechanism, guidelines, trials, meta-analyses, safety,
  contraindications, interactions, special populations) by study design + keyword hints,
  and attribute each document to molecule A / B / both. Offline this is deterministic and
  never invents content; live, the Opus report agent extracts prose closed-book over the
  same evidence.
- **Comparison engine** (`app/pipeline/comparison.py`) — `build_comparison()` emits the
  comprehensive table: overall evidence base, randomized-trial evidence, meta-analytic
  evidence, guideline coverage, safety/labeling, special-population evidence, and a
  **direct head-to-head** row that only counts a *trial comparing A vs B* (not a review
  mentioning both). Each row carries A/B values, GRADE confidence, verified citations, and
  a rationale.

## Richer report

Offline synthesis now produces 11 section types (executive summary → mechanism →
guidelines → trials → meta-analyses → safety → contraindications → interactions →
special populations → limitations → evidence gaps), each GRADE-scored and honestly
marked `insufficient_evidence` when its domain is empty. The live Opus prompt/schema were
extended to cover the same section set and to require a per-row `rationale`.

## API / data changes (additive, backward compatible)

- `ComparisonRow.rationale` (nullable) added to the model, `ComparisonRowOut` schema,
  engine persistence, and the markdown export (new "Rationale" column).
- Frontend: `ComparisonRow.rationale?` type, snake→camel mapper, and the comparison table
  renders the rationale as muted subtext under each attribute. Demo placeholder data updated.
- No Alembic migration needed yet — dev/test uses `create_all`; the initial migration
  baseline is a Phase 7 (deployment) task.

## Anti-hallucination (unchanged contract, now enforced across more surface)

Only verified citations are cited; every comparison row's `citation_ids ⊆` verified refs;
head-to-head requires a real comparative trial; empty domains are reported as insufficient,
never padded. The row rationale explains *why* a confidence level was assigned — no claim
of certainty without the evidence to back it.

## Verification

- `pytest` → **25 passed** (17 prior + 8 new): `test_grade.py` (empty→very_low, high-tier
  beats low-tier, no-high-tier cap, rationale content/dimensions) and `test_comparison.py`
  (rows complete + grounded, head-to-head insufficient offline, head-to-head detection of a
  real comparative trial, per-molecule domain attribution). Lifecycle test now asserts every
  rendered row has a rationale and only cites verified refs.
- `mypy app` → clean (59 files). `ruff` → clean on all Phase 4 files.
- Frontend `tsc --noEmit` clean; `next build` passes (7 routes).

## Next: Phase 5 (Visualizations)

Evidence timelines, evidence heatmaps, risk-benefit matrix, evidence pyramid, and
interactive expandable comparison tables — using the installed viz skills (recharts,
tremor, motion) over the now-structured comparison + GRADE data.
