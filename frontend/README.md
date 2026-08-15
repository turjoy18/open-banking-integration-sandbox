# Frontend dashboard

React + Vite UI for the Open Banking Integration Sandbox. Log in to obtain a JWT, look up a customer aggregate (`/aggregate/{customer_id}`), and view recent audit logs from `/audit-logs`.

## Live demo
- **Frontend:** https://open-banking-integration-sandbox.onrender.com/
- **API:** https://open-banking-sandbox-api.onrender.com
- **Swagger:** https://open-banking-sandbox-api.onrender.com/docs
Demo login: `demo` / `demo`
> Free-tier Render services may sleep when idle; the first request can take ~30–60s. SQLite audit data may reset on redeploy.

## Prerequisites

- Node.js + npm
- Backend running on `http://127.0.0.1:8000` (CORS allows Vite on port 5173)

## Setup

```bash
cd frontend
npm install
```

## Run

```bash
npm run dev
```

Open the Vite URL (usually http://127.0.0.1:5173 or http://localhost:5173).

In another terminal, keep the API up:

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Usage

1. Log in with demo credentials: `demo` / `demo`.
2. Enter a customer ID (`C001` or `C002`).
3. Click **Fetch aggregate** (sends `Authorization: Bearer <token>`).
4. Review accounts, FX rates, and latency — or the error for unknown IDs (e.g. `C999`).
5. Check **Recent audit logs** (public; loads on page open; refreshes after each aggregate call).
6. Click **Refresh** to reload logs and update **Last updated**.
7. **Log out** clears the stored token from `localStorage`.

## Lint

```bash
npm run lint
```

## Stack

- React + Vite
- ESLint
- Calls `http://127.0.0.1:8000` from the browser
- JWT stored in `localStorage` after `/auth/login`
