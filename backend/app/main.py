from fastapi import FastAPI

from app.api.mocks_bank import router as mocks_bank_router
from app.api.mocks_fx import router as mocks_fx_router

app = FastAPI(title="Open Banking Integration Sandbox")
app.include_router(mocks_bank_router)
app.include_router(mocks_fx_router)

@app.get("/health")
def health():
    return {"status": "ok"}