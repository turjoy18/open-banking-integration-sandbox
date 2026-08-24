# Frontend dashboard

React + Vite UI for the Open Banking Integration Sandbox. Connect a bank (OAuth authorization code), look up a customer aggregate (`/aggregate/{customer_id}`), revoke consents, and view recent audit logs from `/audit-logs`.

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

1. Click **Connect bank** (opens the bank authorize page). Sign in with `demo` / `demo` and approve scopes.
2. After redirect, enter a customer ID (`C001` or `C002` — must match the consented customer).
3. Click **Fetch aggregate** (sends `Authorization: Bearer <token>`).
4. Review accounts, FX rates, and latency — or a 403 if consent was revoked or the customer does not match.
5. Use **Revoke** on an active consent, then fetch again to confirm 403.
6. Check **Recent audit logs** (public; loads on page open; refreshes after each aggregate call).
7. Click **Refresh** to reload logs and update **Last updated**.
8. **Disconnect** clears the stored token from `localStorage`.

## Lint

```bash
npm run lint
```

## Stack

- React + Vite
- ESLint
- Calls `http://127.0.0.1:8000` from the browser
- JWT stored in `localStorage` after `/tpp/oauth/exchange`
