from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/metadata/dictionary", response_model=dict)
def data_dictionary(
    object_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/governance/metadata/dictionary?object_type=&search="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if object_type:
        params["object_type"] = object_type
        where += " AND object_type = :object_type"
    if search:
        params["search"] = f"%{search}%"
        where += " AND (object_name ILIKE :search OR description ILIKE :search)"
    r = db.execute(text(f"""
        SELECT id, object_type, object_name, description, data_type, owner, tags, created_at
        FROM meta.data_dictionary
        WHERE {where}
        ORDER BY object_type, object_name
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = []
    for row in rows:
        data.append({
            "id": str(row[0]),
            "object_type": row[1],
            "object_name": row[2],
            "description": row[3],
            "data_type": row[4],
            "owner": row[5],
            "tags": list(row[6]) if row[6] else None,
            "created_at": row[7].isoformat() if row[7] else None,
        })
    count_params = {k: v for k, v in params.items() if k not in ("limit", "offset")}
    total = db.execute(text(f"SELECT COUNT(*) FROM meta.data_dictionary WHERE {where}"), count_params).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "last_updated": datetime.utcnow().isoformat() + "Z"}
