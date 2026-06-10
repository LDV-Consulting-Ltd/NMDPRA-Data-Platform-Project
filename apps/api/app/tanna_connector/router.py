"""PetroGrid Tanna Connector v0.1 routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.database import get_db
from app.tanna_connector.security import require_tanna_token
from app.tanna_connector.services.data_products_service import build_tanna_data_products
from app.tanna_connector.services.decision_products_service import build_tanna_decision_products
from app.tanna_connector.services.entities_service import build_tanna_entities
from app.tanna_connector.services.health_service import build_tanna_health
from app.tanna_connector.services.illuminations_service import build_tanna_illuminations
from app.tanna_connector.services.knowledge_assets_service import build_tanna_knowledge_assets
from app.tanna_connector.services.manifest_service import build_tanna_manifest
from app.tanna_connector.services.patterns_service import build_tanna_patterns
from app.tanna_connector.services.relationships_service import build_tanna_relationships
from app.tanna_connector.services.signals_service import build_tanna_signals
from app.tanna_connector.services.status_service import build_tanna_status

router = APIRouter(
    prefix="/tanna",
    tags=["Tanna Connector"],
    dependencies=[Depends(require_tanna_token)],
)


@router.get("/manifest", response_model=dict)
def get_tanna_manifest(request: Request):
    api_title = getattr(request.app, "title", "NMDPRA Downstream Regulatory Intelligence API")
    return build_tanna_manifest(api_title=api_title)


@router.get("/health", response_model=dict)
def get_tanna_health(db=Depends(get_db)):
    return build_tanna_health(db)


@router.get("/status", response_model=dict)
def get_tanna_status(request: Request, db=Depends(get_db)):
    api_title = getattr(request.app, "title", "NMDPRA Downstream Regulatory Intelligence API")
    return build_tanna_status(db, api_title=api_title)


@router.get("/data-products", response_model=dict)
def get_tanna_data_products():
    return build_tanna_data_products()


@router.get("/entities", response_model=dict)
def get_tanna_entities(db=Depends(get_db)):
    return build_tanna_entities(db)


@router.get("/relationships", response_model=dict)
def get_tanna_relationships(db=Depends(get_db)):
    return build_tanna_relationships(db)


@router.get("/signals", response_model=dict)
def get_tanna_signals(db=Depends(get_db)):
    return build_tanna_signals(db)


@router.get("/patterns", response_model=dict)
def get_tanna_patterns(db=Depends(get_db)):
    return build_tanna_patterns(db)


@router.get("/illuminations", response_model=dict)
def get_tanna_illuminations(db=Depends(get_db)):
    return build_tanna_illuminations(db)


@router.get("/decision-products", response_model=dict)
def get_tanna_decision_products(db=Depends(get_db)):
    return build_tanna_decision_products(db)


@router.get("/knowledge-assets", response_model=dict)
def get_tanna_knowledge_assets(db=Depends(get_db)):
    return build_tanna_knowledge_assets(db)
