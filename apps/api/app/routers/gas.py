from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/gas/infra", response_model=dict)
def gas_infra(
    month: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=200),
    db=Depends(get_db),
):
    """GET /v1/gas/infra?month=&category="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if month:
        where += " AND date_trunc('month', month) = date_trunc('month', :month::date)"
        params["month"] = month + "-01" if len(month) == 7 else month
    if category:
        params["category"] = category
        where += " AND category = :category"
    r = db.execute(text(f"""
        SELECT month, category, item_name, metric_name, metric_value, unit
        FROM bronze.gas_infra
        WHERE {where}
        ORDER BY month DESC, category, item_name
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = []
    for row in rows:
        data.append({
            "month": row[0].isoformat() if row[0] else None,
            "category": row[1],
            "item_name": row[2],
            "metric_name": row[3],
            "metric_value": float(row[4]) if row[4] is not None else str(row[4]) if row[4] is not None else None,
            "unit": row[5],
        })
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.gas_infra WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": "active", "last_updated": datetime.utcnow().isoformat() + "Z"}
