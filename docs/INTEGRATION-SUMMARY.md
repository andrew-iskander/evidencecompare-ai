# Frontend ↔ Backend Integration Summary

**Status:** ✅ Complete · **Date:** 2026-07-03

The Phase 1 frontend is now wired to the live Phase 2 backend. The simulated pipeline is
replaced by real API calls + SSE for authenticated reports; the `/reports/demo` sample view
still works offline without login.

## Delivered (frontend)

- **API client** (`lib/api.ts`) — typed fetch wrapper with JWT injection, automatic
  refresh-on-401 + retry, and snake_case→camelCase mappers (`mapReport`, `mapAgents`).
  Endpoints: auth (register/login/me/refresh), reports (create/get/list/delete), `streamUrl`.
- **Auth** (`components/auth-provider.tsx`) — React context storing tokens in `localStorage`,
  restoring the session via `/auth/me` on load; `useAuth()` hook.
- **Login/Register** (`app/login`) — single page with mode toggle, error surfacing, `next=` redirect.
- **Header** — auth-aware: "Sign in" when logged out; "My reports", "New comparison",
  email, and sign-out when logged in.
- **Compare** (`app/compare`) — auth-guarded; submits real `POST /reports`, routes to the new report.
- **Live report view** (`components/report/live-report-stream.tsx`) — loads the report,
  opens a real **EventSource** to `/reports/{id}/stream?token=`, maps `status`/`agent`/
  `section`/`complete`/`error` events to the agent rail + status, fetches the full report on
  `complete`, and renders comparison table + sections + citations. Auto-retry handled by EventSource.
- **Report entry router** (`report-entry.tsx`) — `/reports/demo` → offline sample;
  any other id → auth-guarded live view.
- **My reports** (`app/reports`) — lists saved reports, status badges, open, delete.

## Verification

- `tsc --noEmit` → exit 0; `next build` → success (7 routes: `/`, `/login`, `/compare`,
  `/reports`, `/reports/[id]`, + not-found).
- **Contract check** — backend JSON keys exactly match the frontend mapper
  (`molecule_a`, `section_key`, `insufficient_evidence`, `value_a/value_b`, `citation_ids`,
  `ref_key`, `agents[].agent/label/state`, `cost_usd`).
- **CORS** — preflight + actual responses echo `Access-Control-Allow-Origin: http://localhost:3000`
  with credentials.
- **Browser-equivalent cross-origin flow** (with `Origin` header) — register→201, login,
  authenticated `POST /reports`, list, and **SSE via `?token=` delivered 14 events incl.
  `complete`**. Both servers booted; all frontend routes return 200.

## Run the full stack locally

```bash
# terminal 1 — backend
cd apps/api && . .venv/Scripts/activate
JWT_SECRET=dev-secret-key-at-least-32-bytes-long uvicorn app.main:app --port 8000

# terminal 2 — frontend
cd apps/web
# .env.local: NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
npm run dev    # http://localhost:3000
```

Flow: `/login` (register) → `/compare` → live streaming report → `/reports` (saved).

## Notes / follow-ups

- A headless browser click-through (Playwright) belongs in Phase 6; here the exact HTTP
  sequence the browser performs was validated at the wire level.
- Export buttons are still visual; wiring `POST /reports/{id}/exports` + download is a small
  follow-up.
- Report content remains placeholder until the Phase 3 RAG evidence engine replaces
  `apps/api/app/pipeline/placeholder.py`.
