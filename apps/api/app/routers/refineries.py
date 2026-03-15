from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


@router.get("/refineries/status", response_model=dict)
def refineries_status(
    month: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/refineries/status?month="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if month:
        where += " AND date_trunc('month', month) = date_trunc('month', :month::date)"
        params["month"] = month + "-01" if len(month) == 7 else month
    r = db.execute(text(f"""
        SELECT month, refinery_name, refinery_type, capacity_bpsd, utilization_pct, product, avg_supply_value, avg_supply_unit, status, notes
        FROM bronze.refinery_status
        WHERE {where}
        ORDER BY month DESC, refinery_name
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = []
    for row in rows:
        data.append({
            "month": row[0].isoformat() if row[0] else None,
            "refinery_name": row[1],
            "refinery_type": row[2],
            "capacity_bpsd": float(row[3]) if row[3] is not None else None,
            "utilization_pct": float(row[4]) if row[4] is not None else None,
            "product": row[5],
            "avg_supply_value": float(row[6]) if row[6] is not None else None,
            "avg_supply_unit": row[7],
            "status": row[8],
            "notes": row[9],
        })
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.refinery_status WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": "active", "last_updated": datetime.utcnow().isoformat() + "Z"}


@router.get("/refineries/modular", response_model=dict)
def refineries_modular(
    month: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/refineries/modular?month="""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if month:
        where += " AND date_trunc('month', month) = date_trunc('month', :month::date)"
        params["month"] = month + "-01" if len(month) == 7 else month
    r = db.execute(text(f"""
        SELECT month, refinery_name, capacity_utilization_pct, avg_ago_supply_value, avg_ago_supply_unit, status
        FROM bronze.modular_refinery_output
        WHERE {where}
        ORDER BY month DESC, refinery_name
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = [{"month": (row[0].isoformat() if row[0] else None), "refinery_name": row[1], "capacity_utilization_pct": float(row[2]) if row[2] is not None else None, "avg_ago_supply_value": float(row[3]) if row[3] is not None else None, "avg_ago_supply_unit": row[4], "status": row[5]} for row in rows]
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.modular_refinery_output WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": "active", "last_updated": datetime.utcnow().isoformat() + "Z"}
