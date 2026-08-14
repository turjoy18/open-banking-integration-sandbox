# API testing notes

## Automated tests

From `backend/`:

```bash
pytest -q
```

Coverage includes:

- Health check
- Known / unknown bank customers
- FX XML response + parser
- Aggregate success and 404 paths (with valid JWT)
- Audit logs empty list, ordering after aggregates, `limit`, and invalid `limit`
- Login success / failure
- Aggregate missing token, invalid token, and wrong auth scheme → `401`

Tests use FastAPI `TestClient` and an in-memory SQLite DB via dependency overrides. Protected aggregate tests log in first via `POST /auth/login`.

## Manual checks

With the server running:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/audit-logs

# Expect 401 without token
curl -i http://127.0.0.1:8000/aggregate/C001

# Login
curl -i -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo\",\"password\":\"demo\"}"

# Use the returned access_token
curl -i http://127.0.0.1:8000/aggregate/C001 \
  -H "Authorization: Bearer TOKEN"
curl -i http://127.0.0.1:8000/aggregate/C999 \
  -H "Authorization: Bearer TOKEN"
```

Also use http://127.0.0.1:8000/docs — authorize with the bearer token after login.

In the React dashboard, confirm:

1. Log in with `demo` / `demo`
2. Aggregate fetch works and audit rows appear
3. Log out disables aggregate fetch
4. Audit table still loads without login
5. **Refresh** updates **Last updated** and reloads the table
