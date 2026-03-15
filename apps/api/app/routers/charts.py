from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/charts/series", response_model=dict)
def charts_series(
    chart_name: Optional[str] = Query(None),
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    period_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(200, ge=1, le=500),
    db=Depends(get_db),
):
    """GET /v1/charts/series?chart_name=&from=&to=&period_type="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if chart_name:
        params["chart_name"] = chart_name
        where += " AND chart_name = :chart_name"
    if from_:
        params["from"] = from_
        where += " AND (period_date >= :from::date OR period_month >= :from::date)"
    if to:
        params["to"] = to
        where += " AND (period_date <= :to::date OR period_month <= :to::date)"
    if period_type:
        params["period_type"] = period_type
        where += " AND period_type = :period_type"
    r = db.execute(text(f"""
        SELECT chart_name, series_name, period_type, period_date, period_month, value, unit
        FROM bronze.chart_series_values
        WHERE {where}
        ORDER BY period_month DESC NULLS LAST, period_date DESC NULLS LAST, series_name
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = []
    for row in rows:
        data.append({
            "chart_name": row[0],
            "series_name": row[1],
            "period_type": row[2],
            "period_date": row[3].isoformat() if row[3] else None,
            "period_month": row[4].isoformat() if row[4] else None,
            "value": float(row[5]),
            "unit": row[6],
        })
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.chart_series_values WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": "active", "last_updated": datetime.utcnow().isoformat() + "Z"}
