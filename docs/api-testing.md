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
- Aggregate success with consent-bound JWT
- Consent mismatch (C001 token vs C002) → `403` and audit row
- Audit logs empty list, ordering after aggregates, `limit`, and invalid `limit`
- Login success / failure (deprecated TPP path)
- Aggregate missing token, invalid token, and wrong auth scheme → `401`
- OAuth: bad client secret, reused authorization code, state mismatch
- Missing `accounts.read`, revoke then aggregate `403`

Tests use FastAPI `TestClient` and an in-memory SQLite DB via dependency overrides. Protected aggregate tests complete the authorization-code flow (authorize form POST + `/tpp/oauth/exchange`).

## Manual checks

With the server running:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/audit-logs

# Login is deprecated for TPP access; use the authorize page in a browser
# or POST /oauth/authorize then /tpp/oauth/exchange.

# Expect 401 without token
curl -i http://127.0.0.1:8000/aggregate/C001
```

Also use http://127.0.0.1:8000/docs — authorize with the bearer token after login.

In the React dashboard, confirm:

1. Connect bank (`demo` / `demo` on the authorize page)
2. Aggregate fetch works and audit rows appear
3. Revoke consent, then aggregate returns 403
4. Disconnect clears the stored token
5. Audit table still loads without a bank connection
6. **Refresh** updates **Last updated** and reloads the table
