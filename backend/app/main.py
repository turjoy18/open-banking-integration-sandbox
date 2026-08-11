from fastapi import FastAPI

app = FastAPI(title="Open Banking Integration Sandbox")

@app.get("/health")
def health():
    return {"status": "ok"}