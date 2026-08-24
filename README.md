# Open Banking Integration Sandbox

PoC middleware that acts as a mock **bank (ASPSP)** and **TPP**: OAuth2 authorization-code consent, a unified customer aggregate from mock bank JSON + FX XML, and SQLite request audit logs.

Built to demonstrate Open API integration, JSON/XML handling, consent-bound JWTs, testing, and clear technical documentation.

This is **not** FAPI, mTLS, PAR, or JARM. Tokens are HS256. Do not treat it as production bank-grade security.

## Live demo
- **Frontend:** https://open-banking-integration-sandbox.onrender.com/
- **API:** https://open-banking-sandbox-api.onrender.com
- **Swagger:** https://open-banking-sandbox-api.onrender.com/docs
Demo bank login (authorize page): `demo` / `demo`
> Free-tier Render services may sleep when idle; the first request can take ~30–60s. SQLite audit data may reset on redeploy.

## Features

- `GET /health` — service health check
- `GET /oauth/authorize` — bank-hosted consent page (authorization code)
- `POST /oauth/token` — confidential client exchanges `code` for a consent-bound JWT
- `POST /tpp/oauth/exchange` — dashboard exchanges `code`+`state` (secret stays on the server)
- `GET /consents` / `DELETE /consents/{id}` / `POST /oauth/revoke` — list and revoke consent
- `GET /mocks/bank/accounts/{customer_id}` — mock bank data (JSON)
- `GET /mocks/fx/rates` — mock FX rates (XML)
- `POST /auth/login` — deprecated demo JWT without consent (not for TPP access)
- `GET /aggregate/{customer_id}` — merges bank + FX (Bearer + active `accounts.read` consent)
- `GET /audit-logs` — recent SQLite request audit rows (optional `?limit=`; public)
- React dashboard: Connect bank, consent revoke, aggregate lookup, audit log viewer
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

Copy `.env.example` to `.env` if you want a custom signing secret or TPP client values:

```bash
cp .env.example .env
```

`JWT_SECRET_KEY` and `OAUTH_CLIENT_*` are read from the environment when set. Defaults match local Vite at `http://127.0.0.1:5173/callback`.

Bank customer login on the authorize page (PoC only): `demo` / `demo`

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

# Bank consent (HTML). Approve in a browser, or POST the form:
# GET /oauth/authorize?response_type=code&client_id=sandbox-tpp&redirect_uri=http://127.0.0.1:5173/callback&scope=accounts.read&state=xyz

# After a code is issued, the TPP exchanges it (secret stays on the API):
# curl -X POST http://127.0.0.1:8000/tpp/oauth/exchange \
#   -H "Content-Type: application/json" \
#   -d "{\"code\":\"CODE\",\"state\":\"xyz\"}"

# Protected aggregate (replace TOKEN). Token customer must match the path.
curl http://127.0.0.1:8000/aggregate/C001 \
  -H "Authorization: Bearer TOKEN"
```

Sample customers: `C001`, `C002`. A token for C001 requesting C002 returns `403`. Missing/invalid tokens return `401`. Revoked or missing `accounts.read` consent returns `403`.

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

Open http://127.0.0.1:5173 (not `localhost`, so the OAuth redirect URI matches). Keep the FastAPI server running on port 8000.

Click **Connect bank**, sign in with `demo` / `demo` on the bank page, then fetch an aggregate. More detail: [frontend/README.md](frontend/README.md)

## Docs

- [Architecture](docs/architecture.md)
- [API testing notes](docs/api-testing.md)
- [Deployment](docs/deployment.md)

## Roadmap

- Optional: managed Postgres for durable audit logs
