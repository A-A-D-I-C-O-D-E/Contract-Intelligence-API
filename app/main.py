# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import ingest, extract, ask, audit, stream, admin, webhook as webhook_router
from .core.metrics import METRICS

app = FastAPI(title="Contract Intelligence API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(ingest.router, prefix="/api")
app.include_router(extract.router, prefix="/api")
app.include_router(ask.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(stream.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(webhook_router.router, prefix="/api")

@app.get("/")
def root():
    return {"service": "contract-intelligence", "metrics": METRICS.get_snapshot()}
