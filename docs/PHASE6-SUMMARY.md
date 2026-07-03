# Phase 6 — Testing Summary

**Status:** ✅ Complete · **Date:** 2026-07-04

Adds end-to-end (Playwright) and accessibility (axe) coverage on top of the
existing backend suite, and — critically — a **visual verification pass** that
caught and fixed a real chart-rendering bug the unit tests could not see.

## What's covered

### Backend (unit + integration) — `apps/api`, pytest
- **26 tests** pass, deterministic and network-free (offline evidence + synthesis).
  Auth flow, report lifecycle through the real engine, the anti-hallucination contract,
  GRADE scorer, comparison engine, per-molecule evidence, exports.

### Frontend end-to-end — `apps/web/e2e`, Playwright (Chromium)
- **`report.spec.ts`** — demo report renders all four charts; captures light + dark
  full-page screenshots; comparison rows expand to reveal rationale + citations.
- **`navigation.spec.ts`** — landing hero + CTAs; `/compare` auth-gates to `/login`;
  sample report opens; login form fields present.
- **`accessibility.spec.ts`** — axe-core (WCAG 2.1 A/AA) on landing, login, and the
  **report view with all charts** → **0 violations**.
- **`live.spec.ts`** — full authenticated flow against the real API (register → compare →
  live report with charts). Opt-in via `E2E_LIVE=1` with the API on :8000; **verified
  passing** against the offline engine. Run with `npm run test:e2e`.

## Visual verification (the payoff)

Screenshotting the report (the `dataviz` skill's "render it and look at it" step)
exposed a bug invisible to logic tests: **all chart colours were transparent**. Root
cause — Tailwind v4 `@theme inline` does **not** emit its `--color-*` custom properties
to `:root`, so inline `style={{ background: "var(--color-tier-rct)" }}` resolved to
nothing. Fix: reference the base tokens (`--tier-*`, `--conf-*`, `--primary`, `--accent`)
that *are* on `:root`. After the fix, pyramid bars, timeline dots, heatmap cells, and
risk-benefit marks all render in both themes (screenshots in `e2e/__screenshots__/`).

## Fixes made during Phase 6

- Chart colour bug (above) — `lib/viz.ts` + `risk-benefit-matrix.tsx`.
- **Accessibility contrast**: the heatmap count text used the confidence hue at 80%
  opacity (contrast 3.5–4.4, fails AA). Moved colour to the border + a swatch and kept text
  in ink (dataviz: *text wears text tokens, never the series colour*).
- a11y test stability: wait for entrance animations to settle before axe measures
  (framer-motion opacity transitions momentarily fail contrast mid-flight).
- live e2e stability: wait for the post-register navigation so the register fetch isn't
  aborted by the next navigation.
- Risk-benefit marks pulled in from the plot edges so labels don't clip.

## Performance notes

- Charts are dependency-free **SVG/CSS + Framer Motion** (no runtime charting lib on the
  critical path). Production bundle: report route first-load JS ≈ **159 kB**, shared ≈ 102 kB.
- A formal Lighthouse/perf-budget gate is deferred to Phase 7 CI (where it can run headless
  in the pipeline with the app served). Playwright traces are captured on first retry.

## Tooling added

- `@playwright/test` + Chromium; `@axe-core/playwright`.
- `playwright.config.ts` (webServer starts `next start -p 3100`, reuses a running one).
- npm scripts: `test:e2e`, `test:e2e:report`. `.gitignore` updated for Playwright artifacts.

## Verification snapshot

`pytest` → 26 passed · `tsc --noEmit` clean · `eslint` clean · `playwright test` →
10 passed, 1 skipped (opt-in live) · live flow verified once against the API · axe → 0
violations on all tested pages.

## Next: Phase 7 (Deployment)

Docker Compose (web + api + Postgres/pgvector + Redis), Alembic baseline migration,
CI/CD running lint + pytest + Playwright + a Lighthouse budget, and production config.
