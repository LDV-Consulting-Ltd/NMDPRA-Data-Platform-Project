from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/highlights", response_model=dict)
def get_highlights(
    month: Optional[str] = Query(None, description="YYYY-MM"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/highlights?month="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if month:
        where += " AND date_trunc('month', month) = date_trunc('month', :month::date)"
        params["month"] = month + "-01" if len(month) == 7 else month
    r = db.execute(text(f"""
        SELECT month, metric_name, metric_value, unit
        FROM bronze.performance_highlights
        WHERE {where}
        ORDER BY month DESC, metric_name
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = [{"month": row[0].isoformat() if row[0] else None, "metric_name": row[1], "metric_value": float(row[2]) if row[2] is not None else None, "unit": row[3]} for row in rows]
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.performance_highlights WHERE {where}"), {k: v for k, v in params.items() if k != "limit" and k != "offset"}).scalar() or 0
    return {
        "data": data,
        "meta": {"page": page, "per_page": per_page, "total": total},
        "coverage": {"data_status": "active"},
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }
