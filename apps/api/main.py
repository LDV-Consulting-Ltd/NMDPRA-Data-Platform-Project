"""
NMDPRA Downstream Regulatory Intelligence API - Business + Governance endpoints.
"""
from contextlib import asynccontextmanager
from time import time
from uuid import uuid4

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    reports,
    highlights,
    refineries,
    consumption,
    prices,
    gas,
    charts,
    vessels,
    archive,
    governance_dq,
    governance_metadata,
    governance_lineage,
    governance_audit,
    governance_health,
    admin_pipeline,
    pipeline_status,
    data_layers,
    seed_demo,
    start_airflow,
)
from app.database import get_db
from app.middleware import audit_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # shutdown if needed


app = FastAPI(
    title="NMDPRA Downstream Regulatory Intelligence API",
    description="Business and governance APIs for NMDPRA downstream regulatory data.",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(audit_middleware)

app.include_router(reports.router, prefix="/v1", tags=["Reports"])
app.include_router(highlights.router, prefix="/v1", tags=["Oil & Gas"])
app.include_router(refineries.router, prefix="/v1", tags=["Oil & Gas"])
app.include_router(consumption.router, prefix="/v1", tags=["Oil & Gas"])
app.include_router(prices.router, prefix="/v1", tags=["Oil & Gas"])
app.include_router(gas.router, prefix="/v1", tags=["Oil & Gas"])
app.include_router(charts.router, prefix="/v1", tags=["Oil & Gas"])
app.include_router(vessels.router, prefix="/v1", tags=["Vessels"])
app.include_router(archive.router, prefix="/v1", tags=["Archived"])
app.include_router(governance_dq.router, prefix="/v1/governance", tags=["Governance"])
app.include_router(governance_metadata.router, prefix="/v1/governance", tags=["Governance"])
app.include_router(governance_lineage.router, prefix="/v1/governance", tags=["Governance"])
app.include_router(governance_audit.router, prefix="/v1/governance", tags=["Governance"])
app.include_router(governance_health.router, prefix="/v1/governance", tags=["Governance"])
app.include_router(admin_pipeline.router, prefix="/v1", tags=["Admin"])
app.include_router(seed_demo.router, prefix="/v1/admin", tags=["Admin"])
app.include_router(start_airflow.router, prefix="/v1/admin", tags=["Admin"])
app.include_router(pipeline_status.router, prefix="/v1", tags=["Pipeline"])
app.include_router(data_layers.router, prefix="/v1", tags=["Data layers"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
