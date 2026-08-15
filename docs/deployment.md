# Deployment notes

How to host the Open Banking Integration Sandbox as a live demo. This guide uses [Render](https://render.com) for both the FastAPI backend and the React static frontend.

## Architecture (hosted)

| Piece | Render type | Build / start |
|-------|-------------|---------------|
| Backend | Web Service | `pip install -r requirements.txt` → `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Frontend | Static Site | Root: `frontend` → build `npm install && npm run build` → publish `dist` |

The browser loads the static site and calls the API URL set as `VITE_API_BASE` at **build** time.

## Prerequisites

- GitHub repo connected to Render
- Phase 3 Issue 1 merged (`python-dotenv`, `CORS_ORIGINS`, `VITE_API_BASE`)

## 1. Deploy the backend (Web Service)

1. Render → **New** → **Web Service** → select this repo.
2. Settings (typical):
   - **Name:** e.g. `open-banking-sandbox-api`
   - **Runtime:** Python 3
   - **Root Directory:** leave empty (repo root)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **Environment** variables:

| Key | Example / notes |
|-----|-----------------|
| `JWT_SECRET_KEY` | Long random string (`openssl rand -hex 32`) — **required in production** |
| `CORS_ORIGINS` | Your frontend origin(s), comma-separated, e.g. `https://your-app.onrender.com` |

4. Deploy and open `https://<api-service>.onrender.com/health` — expect `{"status":"ok"}`.
5. Check Swagger: `https://<api-service>.onrender.com/docs`

### SQLite caveat

The app uses a local SQLite file (`backend/sandbox.db`). On Render free tier, the filesystem is **ephemeral**: audit logs reset when the service redeploys or sleeps. That is acceptable for a PoC demo. A managed Postgres database would be the next step for durable logs.

### Free-tier cold starts

Free web services may sleep after idle time. The first request after sleep can take ~30–60s. Mention this in demos/interviews.

## 2. Deploy the frontend (Static Site)

1. Render → **New** → **Static Site** → same repo.
2. Settings:
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
3. **Environment** (build-time):

| Key | Value |
|-----|--------|
| `VITE_API_BASE` | `https://<api-service>.onrender.com` (no trailing slash) |

4. Deploy. Note the static site URL (e.g. `https://open-banking-sandbox-ui.onrender.com`).

## 3. Wire CORS after you know the frontend URL

1. In the **API** Web Service env, set:

```text
CORS_ORIGINS=https://<your-static-site>.onrender.com
```

If you also test from local Vite against the hosted API:

```text
CORS_ORIGINS=https://<your-static-site>.onrender.com,http://127.0.0.1:5173,http://localhost:5173
```

2. Redeploy the API (or restart) so CORS picks up the new value.
3. If you change `VITE_API_BASE`, **rebuild** the static site (Vite inlines the value at build time).

## 4. Smoke test the live demo

1. Open the static site URL.
2. Log in with `demo` / `demo`.
3. Fetch aggregate for `C001` and `C999`.
4. Confirm audit logs appear (and may be empty after a fresh redeploy).
5. From a terminal:

```bash
curl -i https://<api-service>.onrender.com/health
curl -i -X POST https://<api-service>.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo"}'
```

## Local vs production env

| Variable | Local | Production |
|----------|--------|------------|
| `JWT_SECRET_KEY` | `.env` at repo root | Render API env |
| `CORS_ORIGINS` | Vite URLs in `.env` | Frontend origin(s) on Render |
| `VITE_API_BASE` | optional `frontend/.env` → `http://127.0.0.1:8000` | Render static site env at build |

Do **not** commit `.env` files with real secrets. Keep `.env.example` as the template.

## After deploy checklist

- [ ] `/health` returns 200 on the API
- [ ] Login works from the hosted UI
- [ ] Aggregate with JWT works; without login UI blocks / API returns 401
- [ ] Audit logs load from the UI
- [ ] Live URLs added to the root README (Phase 3 Issue 4)
