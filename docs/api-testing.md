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

Tests use FastAPI `TestClient` and an in-memory SQLite DB via dependency overrides.

## Manual checks

With the server running:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/aggregate/C001
curl -i http://127.0.0.1:8000/aggregate/C999
```

Also use http://127.0.0.1:8000/docs to exercise endpoints interactively.
