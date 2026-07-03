# Phase 1 — Frontend Summary

**Status:** ✅ Complete · **Date:** 2026-07-03

Premium frontend scaffolded under `apps/web`, built and runtime-verified.

## Stack (installed & building)

Next.js **15.5.20** (App Router) · React 19 · TypeScript (strict) · Tailwind CSS **v4**
(CSS-first, oklch tokens) · shadcn-style UI primitives · Framer Motion · next-themes ·
lucide-react · recharts (dep, used in Phase 5).

> `next@15.1.0` was bumped to `15.5.x` to clear CVE-2025-66478.

## Delivered

- **Design system & theming** — `app/globals.css` oklch light/dark tokens exposed via
  `@theme`; class-based dark mode; `ThemeProvider` (defaults dark) + `ThemeToggle`;
  responsive layout shell with sticky header.
- **UI primitives** — `components/ui/`: button (CVA variants), card, input, label, badge, skeleton.
- **Landing** (`/`) — hero with grid backdrop, feature grid, disclaimer.
- **Compare flow** (`/compare`) — Molecule A/B + topic inputs, swap, example presets, validation.
- **Streaming report view** (`/reports/[id]`) — simulated 8-agent pipeline rail (Framer
  Motion), progressively revealed sections, confidence-scored comparison table, per-claim
  citation markers + "unsourced"/"insufficient evidence" states, references list, export buttons.
- **Types & sample data** — `types/report.ts`, `lib/placeholder-data.ts`
  (Telmisartan vs Valsartan / Cardioprotection, illustrative only).

## Verification

- `tsc --noEmit` → exit 0 (clean).
- `next build` → success; routes `/`, `/compare`, `/reports/[id]` compile.
- Runtime: `next start`, all three routes return **200**; report page renders inputs SSR.

## Design decisions

- Hand-scaffolded (not `create-next-app`) for deterministic, reviewable files.
- Minimal shadcn-style primitives (no Radix Slot yet) — `buttonVariants` on `Link` instead
  of `asChild`. Add full shadcn/Radix set as needed in later UI work.
- Report page is a server component (awaits `searchParams`) → passes inputs to the
  `ReportStream` client component; avoids `useSearchParams`/Suspense friction.
- Pipeline streaming is **simulated** in Phase 1; real SSE (`GET /reports/{id}/stream`)
  arrives with the backend (Phase 2/3).

## Next: Phase 2 (Backend)

FastAPI + Postgres/pgvector + Redis + Celery, JWT auth, saved reports, and the real
`POST /reports` + SSE stream the frontend is already shaped for. Then generate
`apps/web/types` from the backend OpenAPI schema to replace the hand-written types.
