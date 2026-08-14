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
- Aggregate success and 404 paths
- Audit logs empty list, ordering after aggregates, `limit`, and invalid `limit`

Tests use FastAPI `TestClient` and an in-memory SQLite DB via dependency overrides.

## Manual checks

With the server running:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/aggregate/C001
curl -i http://127.0.0.1:8000/aggregate/C999
curl -i http://127.0.0.1:8000/audit-logs
curl -i "http://127.0.0.1:8000/audit-logs?limit=5"
```

Also use http://127.0.0.1:8000/docs to exercise endpoints interactively.

In the React dashboard, confirm:

1. Audit table loads on page open
2. Fetching `C001` / `C999` adds rows
3. **Refresh** updates **Last updated** and reloads the table
