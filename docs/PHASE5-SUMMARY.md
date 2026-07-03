# Phase 5 — Visualizations Summary

**Status:** ✅ Complete · **Date:** 2026-07-04

Adds the interactive evidence visualizations to the report view — evidence
pyramid, timeline, confidence heatmap, and risk–benefit matrix — plus an
interactive expandable comparison table. Every chart is driven by the same
verified evidence the rest of the report cites, and was built following the
`dataviz` skill (form-by-job, colour-by-job, validated palettes).

## Charts (all in `apps/web/components/report/viz/`)

- **Evidence pyramid** — verified citations across the study-design hierarchy
  (strongest at top). Bar width = count; colour = **sequential single-hue tier ramp**
  (CVD-safe by construction). Tier + count always directly labelled.
- **Evidence timeline** — each dated citation as a dot on a single year axis,
  coloured by tier, stacked within a year. Tier legend + per-dot hover.
- **Confidence heatmap** — GRADE certainty across every comparison dimension.
  Confidence is a **status** encoding, so each cell always carries its label + citation
  count (never colour-alone); hover reveals the rationale.
- **Risk–benefit matrix** — each molecule placed by evidence coverage: efficacy
  (trials + meta-analyses) on X, safety (labels/contraindications/interactions/special
  populations) on Y. A vs B is **categorical** (primary/accent) with a distinct marker
  shape (circle vs diamond) + direct label as secondary encoding. Captioned as an
  evidence-coverage map, not a clinical risk-benefit verdict.
- **Interactive expandable comparison table** — each row expands to reveal the GRADE
  rationale and the actual supporting citations (indexed, source + year), or a
  "no supporting citation" chip for unsourced rows.

## Colour method (dataviz skill)

- Palettes were **validated with `scripts/validate_palette.js`**, not eyeballed:
  - Molecule pair (primary/accent) → PASS; CVD separation in the 8–12 floor band, so it
    ships **only with secondary encoding** (marker shape + direct labels) — which the
    matrix does.
  - Confidence traffic-light ramp → CVD-fails as a categorical palette (expected for a
    status ramp), so it is used **only as status with an always-present label/icon**
    (the existing `ConfidenceBadge` pattern), never colour-alone.
- Evidence tier uses a **sequential single-hue ramp** with its own monotonic steps per
  theme (`--tier-*` light + dark in `globals.css`), not an auto dark-mode flip.
- Mark specs honoured: 4px rounded bar ends, ≥8px markers, 2px `ring-card` on overlapping
  marks, hover tooltip on every bar/dot/cell, legends for every ≥2-series encoding. The
  comparison table + citation list serve as the backing table view.

## Data plumbing (additive, backward compatible)

- `Citation.study_design` — model + `CitationOut` schema + engine populates it from the
  ranked doc; frontend `Citation.studyDesign` + mapper. Powers pyramid/timeline.
- `Report.molecule_evidence` (JSON) — per-molecule counts by macro-domain (efficacy /
  safety / guideline), computed by `comparison.molecule_evidence()` and persisted by the
  engine; exposed via `MoleculeEvidenceOut`; frontend `Report.moleculeEvidence`. Powers
  the risk–benefit matrix. Demo `SAMPLE_REPORT` carries an illustrative block.
- No migration needed (dev/test uses `create_all`; baseline migration is Phase 7).

## Verification

- API `pytest` → **26 passed** (+`test_molecule_evidence_counts_per_molecule`; lifecycle
  test now asserts citations carry `study_design` and `molecule_evidence` is exposed).
  `mypy` clean (59 files); `ruff` clean on Phase 5 files.
- Web `tsc --noEmit` clean, `eslint` clean, `next build` passes (7 routes). Production
  server renders `/reports/demo` (all four charts) with no server/hydration errors.
- Palette validator run for the molecule pair and confidence ramp (see Colour method).
- Not visually screenshot-verified in this environment (no browser automation installed);
  charts follow the mark/colour specs and the page renders clean.

## Next: Phase 6 (Testing)

Broaden to integration + end-to-end (Playwright) coverage of the report + viz flow,
accessibility (axe) and performance passes, before Phase 7 (Docker / CI-CD / deploy).
