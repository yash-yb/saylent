import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, SessionLocal
from . import models  # noqa: F401 (register models on Base)
from .routers import national, phc, alerts, redistribution, federated
from .compute import run_compute_cycle

app = FastAPI(
    title="Project API",
    description="Federated AI platform for national PHC network resilience — "
                 "BRICS Track 3: Smart Health & Supply Chain Resilience.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(national.router)
app.include_router(phc.router)
app.include_router(alerts.router)
app.include_router(redistribution.router)
app.include_router(federated.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from . import models as m
        if db.query(m.PHC).count() == 0:
            from .seed_data import run_seed
            run_seed()
        db2 = SessionLocal()
        try:
            run_compute_cycle(db2)
        finally:
            db2.close()
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "name": "Project",
        "status": "ok",
        "docs": "/docs",
        "description": "Federated AI platform for national health resource & "
                        "supply chain resilience across a PHC network.",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
