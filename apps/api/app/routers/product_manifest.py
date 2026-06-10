"""PetroGrid product surfaces — manifest, registry, intelligence layers, relationships."""
from fastapi import APIRouter, Depends, Request

from app.data_product_registry import build_data_product_registry
from app.database import get_db
from app.product_decisions import build_decision_products_response
from app.product_entities import build_entities_response
from app.product_illuminations import build_illuminations_response
from app.product_knowledge_assets import build_knowledge_assets_response
from app.product_manifest import build_product_manifest
from app.product_patterns import build_patterns_response
from app.product_relationships import build_relationships_response
from app.product_signals import build_signals_response

router = APIRouter(prefix="/product", tags=["Product"])


@router.get("/manifest", response_model=dict)
def get_product_manifest(request: Request):
    """
    Formal PetroGrid capability surface (v0.1) for internal services and future Tanna integration.
    Describes only implemented or partially implemented features; unsupported items are listed explicitly.
    """
    api_title = getattr(request.app, "title", "NMDPRA Downstream Regulatory Intelligence API")
    return build_product_manifest(api_title=api_title)


@router.get("/data-products", response_model=dict)
def get_data_products():
    """
    PetroGrid data product registry (v0.1): API-, bronze-, and gold-backed products only.
    Silver is excluded (schema only; not populated). No invented products.
    """
    return build_data_product_registry()


@router.get("/signals", response_model=dict)
def get_product_signals(db=Depends(get_db)):
    """
    PetroGrid Signals v0.1: rule-based attention indicators from existing operational,
    governance, and API evidence. Read-only; no persistence.
    """
    return build_signals_response(db)


@router.get("/patterns", response_model=dict)
def get_product_patterns(db=Depends(get_db)):
    """
    PetroGrid Patterns v0.1: rule-based clustered signal structures.
    Derived from Signals v0.1 only. Read-only; no persistence.
    """
    return build_patterns_response(db)


@router.get("/illuminations", response_model=dict)
def get_product_illuminations(db=Depends(get_db)):
    """
    PetroGrid Illuminations v0.1: rule-based operational context from signals and patterns.
    Read-only; no persistence. Not decisions or AI narratives.
    """
    return build_illuminations_response(db)


@router.get("/decision-products", response_model=dict)
def get_decision_products(db=Depends(get_db)):
    """
    PetroGrid Decision Products v0.1: rule-based decision-support objects from
    signals, patterns, and illuminations. Read-only; not automated decisions.
    """
    return build_decision_products_response(db)


@router.get("/relationships", response_model=dict)
def get_product_relationships(db=Depends(get_db)):
    """
    PetroGrid Relationship Model v0.1: evidence-backed links between data products,
    tables, source files, lineage nodes, and knowledge assets. Read-only.
    """
    return build_relationships_response(db)


@router.get("/entities", response_model=dict)
def get_product_entities(db=Depends(get_db)):
    """
    PetroGrid Entities v0.1: evidence-backed business objects from schema, registry,
    and safe read-only queries. Read-only; no persistence.
    """
    return build_entities_response(db)


@router.get("/knowledge-assets", response_model=dict)
def get_knowledge_assets(db=Depends(get_db)):
    """
    PetroGrid Knowledge Assets v0.1: documentation, diagrams, OpenAPI, and governance
    metadata surfaces. Read-only; no ingestion or AI summaries.
    """
    return build_knowledge_assets_response(db)
