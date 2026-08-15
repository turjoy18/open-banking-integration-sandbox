# Open Banking Integration Sandbox

PoC middleware that integrates two mock financial data sources (JSON bank accounts + XML FX rates), returns a unified customer aggregate, and writes request audit logs to SQLite.

Built to demonstrate API integration, JSON/XML handling, JWT auth, testing, and clear technical documentation.

## Live demo
- **Frontend:** https://open-banking-integration-sandbox.onrender.com/
- **API:** https://open-banking-sandbox-api.onrender.com
- **Swagger:** https://open-banking-sandbox-api.onrender.com/docs
Demo login: `demo` / `demo`
> Free-tier Render services may sleep when idle; the first request can take ~30–60s. SQLite audit data may reset on redeploy.

## Features

- `GET /health` — service health check
- `GET /mocks/bank/accounts/{customer_id}` — mock bank data (JSON)
- `GET /mocks/fx/rates` — mock FX rates (XML)
- `POST /auth/login` — mock login; returns a JWT access token
- `GET /aggregate/{customer_id}` — merges bank + FX (requires Bearer JWT) and logs the request
- `GET /audit-logs` — recent SQLite request audit rows (optional `?limit=`; public)
- React dashboard with login, aggregate lookup, and audit log viewer
- Automated API tests with pytest

## Stack

- Python, FastAPI, SQLAlchemy, SQLite, python-jose (JWT)
- pytest + FastAPI TestClient
- React + Vite (dashboard)

## Project tracking

Work was broken into GitHub Issues and tracked on a Project board (Todo / In Progress / Done), similar to a lightweight Jira workflow.

## Setup (Windows / Linux)

```bash
git clone https://github.com/turjoy18/open-banking-integration-sandbox.git
cd open-banking-integration-sandbox
python -m venv .venv
```

Activate the venv:

- Git Bash: `source .venv/Scripts/activate`
- PowerShell: `.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

### JWT secret (optional for local PoC)

Copy `.env.example` to `.env` if you want a custom signing secret:

```bash
cp .env.example .env
```

`JWT_SECRET_KEY` is read from the environment when set. If unset, the app falls back to a local development default (`dev-secret-change-me`). Loading `.env` automatically is planned for the deploy phase; for now you can also export the variable in your shell.

Demo login credentials (PoC only): `demo` / `demo`

## Run the API

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## Example requests

```bash
# Public endpoints
curl http://127.0.0.1:8000/mocks/bank/accounts/C001
curl http://127.0.0.1:8000/mocks/fx/rates
curl http://127.0.0.1:8000/audit-logs
curl "http://127.0.0.1:8000/audit-logs?limit=5"

# Login
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo\",\"password\":\"demo\"}"

# Protected aggregate (replace TOKEN)
curl http://127.0.0.1:8000/aggregate/C001 \
  -H "Authorization: Bearer TOKEN"
curl http://127.0.0.1:8000/aggregate/C999 \
  -H "Authorization: Bearer TOKEN"
```

Sample customers: `C001`, `C002`. Unknown IDs return `404` and are still audited. Missing/invalid tokens on `/aggregate` return `401`.

`GET /audit-logs` returns newest rows first. `limit` defaults to `20` (min `1`, max `100`).

## Tests

```bash
cd backend
pytest -q
```

## Frontend dashboard

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL (usually http://127.0.0.1:5173). Keep the FastAPI server running on port 8000.

Log in with `demo` / `demo`, then fetch an aggregate. More detail: [frontend/README.md](frontend/README.md)

## Docs

- [Architecture](docs/architecture.md)
- [API testing notes](docs/api-testing.md)
- [Deployment](docs/deployment.md)

## Roadmap

- Optional: managed Postgres for durable audit logs
