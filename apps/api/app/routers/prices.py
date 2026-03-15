from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/prices/fuel", response_model=dict)
def fuel_prices(
    month: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=200),
    db=Depends(get_db),
):
    """GET /v1/prices/fuel?month=&city="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if month:
        where += " AND date_trunc('month', month) = date_trunc('month', :month::date)"
        params["month"] = month + "-01" if len(month) == 7 else month
    if city:
        params["city"] = city
        where += " AND city = :city"
    r = db.execute(text(f"""
        SELECT month, city, indicative_price, min_price, max_price, avg_price, unit, notes
        FROM bronze.fuel_prices_city
        WHERE {where}
        ORDER BY month DESC, city
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = []
    for row in rows:
        data.append({
            "month": row[0].isoformat() if row[0] else None,
            "city": row[1],
            "indicative_price": float(row[2]) if row[2] is not None else None,
            "min_price": float(row[3]) if row[3] is not None else None,
            "max_price": float(row[4]) if row[4] is not None else None,
            "avg_price": float(row[5]) if row[5] is not None else None,
            "unit": row[6] or "NGN/L",
            "notes": row[7],
        })
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.fuel_prices_city WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": "active", "last_updated": datetime.utcnow().isoformat() + "Z"}
