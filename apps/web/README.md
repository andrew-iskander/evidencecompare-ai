# EvidenceCompare AI — Web (Phase 1)

Premium frontend for EvidenceCompare AI. Next.js 15 (App Router) · React 19 ·
TypeScript · Tailwind CSS v4 · shadcn-style components · Framer Motion · next-themes.

## What's implemented in Phase 1

- **Design system & theming** — Tailwind v4 CSS-first tokens (oklch), dark/light mode via
  `next-themes` (defaults to dark), responsive layout, accessible primitives.
- **Landing page** (`/`) — hero, feature grid, disclaimer.
- **Compare flow** (`/compare`) — Molecule A / Molecule B / topic input, swap, example presets.
- **Streaming report view** (`/reports/[id]`) — simulated per-agent pipeline progress,
  progressively revealed sections, side-by-side comparison table with confidence scores,
  per-claim citation markers, references list, export buttons (UI).
- Renders from **sample data** (`lib/placeholder-data.ts`) until the backend (Phase 2/3)
  and real SSE streaming are connected.

> Sample content is illustrative only — not a source of medical truth.

## Run

```bash
pnpm install     # or npm install / yarn
pnpm dev         # http://localhost:3000
```

Other scripts: `pnpm build`, `pnpm start`, `pnpm lint`, `pnpm typecheck`.

> Diagnostics about missing modules disappear after installing dependencies.

## Structure

```
app/
  layout.tsx            # ThemeProvider + header shell
  page.tsx              # landing
  compare/page.tsx      # A/B/topic input
  reports/[id]/page.tsx # report (server) → ReportStream (client)
components/
  ui/                   # button, card, input, label, badge, skeleton
  report/               # confidence-badge, agent-rail, comparison-table,
                        # section-card, citation-list, report-stream
  site-header.tsx, theme-provider.tsx, theme-toggle.tsx
lib/                    # utils (cn), placeholder-data
types/report.ts         # report/section/citation types (later: OpenAPI-generated)
```

## Next (Phase 2+)

- Replace the simulated pipeline with real **SSE** from `GET /reports/{id}/stream`.
- Wire `POST /reports` on the compare form; add auth screens and saved reports.
- Generate `types/` from the backend OpenAPI schema.
