# Open Banking Integration Sandbox

PoC middleware that integrates two mock financial data sources (JSON bank accounts + XML FX rates), returns a unified customer aggregate, and writes request audit logs to SQLite.

Built to demonstrate API integration, JSON/XML handling, testing, and clear technical documentation.

## Features

- `GET /health` — service health check
- `GET /mocks/bank/accounts/{customer_id}` — mock bank data (JSON)
- `GET /mocks/fx/rates` — mock FX rates (XML)
- `GET /aggregate/{customer_id}` — merges bank + FX and logs the request
- `GET /audit-logs` — recent SQLite request audit rows (optional `?limit=`)
- React dashboard with aggregate lookup and audit log viewer
- Automated API tests with pytest

## Stack

- Python, FastAPI, SQLAlchemy, SQLite
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

## Run the API

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## Example requests

```bash
curl http://127.0.0.1:8000/mocks/bank/accounts/C001
curl http://127.0.0.1:8000/mocks/fx/rates
curl http://127.0.0.1:8000/aggregate/C001
curl http://127.0.0.1:8000/aggregate/C999
curl http://127.0.0.1:8000/audit-logs
curl "http://127.0.0.1:8000/audit-logs?limit=5"
```

Sample customers: `C001`, `C002`. Unknown IDs return `404` and are still audited.

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

More detail: [frontend/README.md](frontend/README.md)

## Docs

- [Architecture](docs/architecture.md)
- [API testing notes](docs/api-testing.md)

## Roadmap

- JWT auth for protected routes
- Deployable demo (env-based API URL + hosted backend/frontend)
