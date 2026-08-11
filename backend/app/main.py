from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.aggregate import router as aggregate_router
from app.api.mocks_bank import router as mocks_bank_router
from app.api.mocks_fx import router as mocks_fx_router
from app.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Open Banking Integration Sandbox", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mocks_bank_router)
app.include_router(mocks_fx_router)
app.include_router(aggregate_router)

@app.get("/health")
def health():
    return {"status": "ok"}