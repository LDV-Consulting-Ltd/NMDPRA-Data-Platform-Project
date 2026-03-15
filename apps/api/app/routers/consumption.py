from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/consumption/benchmarks", response_model=dict)
def consumption_benchmarks(
    month: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/consumption/benchmarks?month="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if month:
        where += " AND date_trunc('month', month) = date_trunc('month', :month::date)"
        params["month"] = month + "-01" if len(month) == 7 else month
    r = db.execute(text(f"""
        SELECT month, product, benchmark_value, unit
        FROM bronze.consumption_benchmark
        WHERE {where}
        ORDER BY month DESC, product
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = [{"month": (row[0].isoformat() if row[0] else None), "product": row[1], "benchmark_value": float(row[2]), "unit": row[3]} for row in rows]
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.consumption_benchmark WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": "active", "last_updated": datetime.utcnow().isoformat() + "Z"}


@router.get("/consumption/truckout", response_model=dict)
def consumption_truckout(
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
    db=Depends(get_db),
):
    """GET /v1/consumption/truckout?from=&to=&product="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if from_:
        params["from"] = from_ + "-01" if len(from_) == 7 else from_
        where += " AND date >= :from::date"
    if to:
        params["to"] = to + "-01" if len(to) == 7 else to
        where += " AND date <= :to::date"
    if product:
        params["product"] = product
        where += " AND product = :product"
    r = db.execute(text(f"""
        SELECT date, product, volume_value, unit
        FROM bronze.actual_consumption_truckout_daily
        WHERE {where}
        ORDER BY date DESC
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = [{"date": (row[0].isoformat() if row[0] else None), "product": row[1], "volume_value": float(row[2]) if row[2] else None, "unit": row[3]} for row in rows]
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.actual_consumption_truckout_daily WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": "active", "last_updated": datetime.utcnow().isoformat() + "Z"}
