from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/lineage/nodes", response_model=dict)
def lineage_nodes(db=Depends(get_db)):
    """GET /v1/governance/lineage/nodes"""
    r = db.execute(text("SELECT node_id, layer, object_name, object_type FROM meta.lineage_node ORDER BY layer, object_name"))
    rows = r.fetchall()
    data = [{"node_id": str(row[0]), "layer": row[1], "object_name": row[2], "object_type": row[3]} for row in rows]
    return {"data": data, "last_updated": datetime.utcnow().isoformat() + "Z"}


@router.get("/lineage/edges", response_model=dict)
def lineage_edges(
    layer: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=200),
    db=Depends(get_db),
):
    """GET /v1/governance/lineage/edges?layer="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if layer:
        params["layer"] = layer
        where += " AND (n_from.layer = :layer OR n_to.layer = :layer)"
    r = db.execute(text(f"""
        SELECT e.id, e.from_node_id, e.to_node_id, e.transform_name, e.transform_version, e.created_at
        FROM meta.lineage_edge e
        JOIN meta.lineage_node n_from ON n_from.node_id = e.from_node_id
        JOIN meta.lineage_node n_to ON n_to.node_id = e.to_node_id
        WHERE {where}
        ORDER BY e.created_at DESC
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = []
    for row in rows:
        data.append({
            "id": str(row[0]),
            "from_node_id": str(row[1]),
            "to_node_id": str(row[2]),
            "transform_name": row[3],
            "transform_version": row[4],
            "created_at": row[5].isoformat() if row[5] else None,
        })
    count_params = {k: v for k, v in params.items() if k not in ("limit", "offset")}
    total = db.execute(text(f"""
        SELECT COUNT(*) FROM meta.lineage_edge e
        JOIN meta.lineage_node n_from ON n_from.node_id = e.from_node_id
        JOIN meta.lineage_node n_to ON n_to.node_id = e.to_node_id
        WHERE {where}
    """), count_params).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "last_updated": datetime.utcnow().isoformat() + "Z"}
