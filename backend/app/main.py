from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

import app.config  # noqa: F401 — load .env before other modules read os.environ
from app.api.aggregate import router as aggregate_router
from app.api.audit_logs import router as audit_logs_router
from app.api.oauth import router as oauth_router
from app.api.consents import router as consents_router
from app.api.tpp import router as tpp_router
from app.api.auth import router as auth_router
from app.api.open_api_accounts import router as open_api_accounts_router
from app.api.open_api_applications import router as open_api_applications_router
from app.api.open_api_products import router as open_api_products_router
from app.api.open_api_payments import router as open_api_payments_router
from app.api.mocks_bank import MOCK_ACCOUNTS, router as mocks_bank_router
from app.api.mocks_fx import router as mocks_fx_router
from app.db import SessionLocal, init_db
from app.services.fx import load_fx_rates


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Open Banking Integration Sandbox", lifespan=lifespan)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(open_api_products_router)
app.include_router(open_api_applications_router)
app.include_router(open_api_accounts_router)
app.include_router(open_api_payments_router)
app.include_router(mocks_bank_router)
app.include_router(mocks_fx_router)
app.include_router(aggregate_router)
app.include_router(audit_logs_router)
app.include_router(oauth_router)
app.include_router(consents_router)
app.include_router(tpp_router)
app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    checks: dict[str, str] = {}
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["db"] = "up"
    except Exception:
        checks["db"] = "down"
    finally:
        db.close()

    checks["bank"] = "up" if MOCK_ACCOUNTS else "down"
    rates, fx_status = load_fx_rates()
    checks["fx"] = "up" if fx_status != "unavailable" and rates else "down"

    ready = all(value == "up" for value in checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ok" if ready else "degraded", "checks": checks},
    )
