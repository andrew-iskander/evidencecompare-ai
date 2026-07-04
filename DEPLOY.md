# Deploying EvidenceCompare AI for free

This guide puts a permanent, shareable link in your colleague's hands at **zero
cost**, using two free hosting tiers:

- **API (FastAPI)** → [Render](https://render.com) free tier
- **Web (Next.js)** → [Vercel](https://vercel.com) free "Hobby" tier

Both run the app in **offline mode**: demo evidence, no API keys, no Postgres, no
Redis. (Live mode with real evidence + the Claude API costs money — keep it
offline for free sharing.)

> **Order matters.** Deploy the API first (Step 1), because the web app needs the
> API's URL. Then deploy the web app (Step 2). Then lock down CORS (Step 3).

---

## Prerequisites

- The repo is pushed to GitHub: `github.com/andrew-iskander/evidencecompare-ai`
- A GitHub account (you already have one)
- The `render.yaml` and `$PORT`-aware Dockerfile in this repo (already set up)

---

## Step 1 (card-free, recommended) — Deploy the API to Hugging Face Spaces

Render now requires a **credit card on file** even for its free tier. Hugging Face
Spaces is free, needs **no card**, and runs real Docker containers. Files to paste
live in `deploy/huggingface/`.

1. Go to **huggingface.co** → **Sign Up** (free, no card).
2. Top-right avatar → **New Space**.
   - **Owner**: you · **Space name**: `evidencecompare-api`
   - **License**: leave default · **Space SDK**: **Docker** → **Blank**
   - **Hardware**: **CPU basic (free)** · **Visibility**: Public (or Private)
   - Click **Create Space**.
3. The Space opens on its **Files** tab. Add the two files from
   `deploy/huggingface/` in this repo:
   - Open the existing **`README.md`** → **Edit** → replace its contents with
     `deploy/huggingface/README.md` → **Commit**.
   - **Add file → Create a new file** → name it **`Dockerfile`** → paste
     `deploy/huggingface/Dockerfile` → **Commit**.
4. The Space auto-builds (**~4–8 min**; watch the **Logs**/**App** tab). When it
   says **Running**, your API URL is:
   `https://<your-username>-evidencecompare-api.hf.space`
5. **Verify:** open `https://<...>.hf.space/health` — you should see JSON with
   `"evidence_mode": "offline"`.

> Use this URL (with `/api/v1` appended) as `NEXT_PUBLIC_API_BASE_URL` in Step 2.
> To restrict CORS later (Step 3): Space **Settings → Variables and secrets →
> New variable** `CORS_ORIGINS` = your Vercel URL. To pull newer code: Space
> **Settings → Factory rebuild**.

---

## Step 1 (alternative) — Deploy the API to Render (requires a card)

Two ways; the Blueprint is easiest.

### Option A — Blueprint (uses `render.yaml`, near one-click)
1. Go to **render.com** → sign up with GitHub (free).
2. **New +** → **Blueprint** → select `evidencecompare-ai`.
3. Render reads `render.yaml` and creates the **evidencecompare-api** service with
   the right env vars. Click **Apply**.
4. Wait for the build → copy the service URL, e.g.
   `https://evidencecompare-api.onrender.com`.

### Option B — Manual
1. **New +** → **Web Service** → pick `evidencecompare-ai`.
2. Root directory: `apps/api` · Runtime: **Docker** · Instance type: **Free**.
3. Environment variables:
   - `EVIDENCE_MODE=offline`
   - `LLM_MODE=offline`
   - `CORS_ORIGINS=*`   (temporary — tightened in Step 3)
4. Deploy → copy the URL.

**Verify:** open `https://<your-api>.onrender.com/health` — you should see a JSON
health payload showing `evidence_mode: offline`.

---

## Step 2 — Deploy the Web to Vercel

1. Go to **vercel.com** → sign up with GitHub (free).
2. **Add New… → Project** → import `evidencecompare-ai`.
3. **Root Directory**: `apps/web` (click Edit and select it).
4. **Environment Variables** — add:
   - `NEXT_PUBLIC_API_BASE_URL` = `https://<your-api>.onrender.com/api/v1`
     (the Render URL from Step 1, **with `/api/v1` on the end**)
5. **Deploy** → you get your shareable link, e.g.
   `https://evidencecompare-ai.vercel.app`.

> This value is baked into the browser bundle at **build time**. If you change the
> API URL later, redeploy the web app so the new value takes effect.

---

## Step 3 — Lock down CORS

1. Back in **Render** → your API service → **Environment**.
2. Change `CORS_ORIGINS` from `*` to your exact Vercel URL, e.g.
   `https://evidencecompare-ai.vercel.app` (no trailing slash).
3. Save → Render redeploys automatically.

**Send the Vercel link to your colleague.** Done. ✅

---

## Good to know (free-tier behavior)

- **Cold starts:** Render's free API sleeps after ~15 min idle. The first request
  after a pause takes ~30–60 s to wake up, then it's fast again. Not a bug.
- **Data resets:** SQLite lives inside the container; a redeploy starts it fresh.
  Fine for a demo. For persistent data you'd add a managed Postgres (paid) and set
  `DATABASE_URL`.
- **Custom domains:** both Vercel and Render let you attach one free later.
- **Non-commercial:** Vercel Hobby and Render Free are for non-commercial use.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Web loads but every action errors / "Network error" | `NEXT_PUBLIC_API_BASE_URL` is wrong or missing `/api/v1`. Fix it in Vercel and redeploy. |
| Browser console shows a CORS error | `CORS_ORIGINS` on Render doesn't match the Vercel URL exactly (scheme + host, no trailing slash). |
| API build fails on Render | Confirm Root directory = `apps/api` and Runtime = Docker. |
| First load very slow | Cold start — normal on the free tier. Wait ~1 min. |
