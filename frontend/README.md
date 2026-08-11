# Frontend dashboard

React + Vite UI for the Open Banking Integration Sandbox. Look up a customer aggregate from the FastAPI backend (`/aggregate/{customer_id}`).

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

1. Enter a customer ID (`C001` or `C002`).
2. Click **Fetch aggregate**.
3. Review accounts, FX rates, and latency — or the error for unknown IDs (e.g. `C999`).

## Lint

```bash
npm run lint
```

## Stack

- React + Vite
- ESLint
- Calls `http://127.0.0.1:8000` from the browser
