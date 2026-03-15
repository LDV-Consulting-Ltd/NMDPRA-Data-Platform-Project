"""Archived feeds: DailyTruckout, StockReport (last data 2023)."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from app.database import get_db

router = APIRouter()


def _archived_status():
    return "archived"


@router.get("/archive/truckout/depot", response_model=dict)
def archive_truckout_depot(
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=200),
    db=Depends(get_db),
):
    """GET /v1/archive/truckout/depot?from=&to= - Archived (last published 2023)."""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if from_:
        params["from"] = from_
        where += " AND report_date >= :from::date"
    if to:
        params["to"] = to
        where += " AND report_date <= :to::date"
    r = db.execute(text(f"""
        SELECT report_date, product, depot_name, truck_count, volume_litres
        FROM bronze.truckout_by_depot_daily
        WHERE {where}
        ORDER BY report_date DESC, depot_name
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = [{"report_date": (row[0].isoformat() if row[0] else None), "product": row[1], "depot_name": row[2], "truck_count": row[3], "volume_litres": float(row[4]) if row[4] is not None else None} for row in rows]
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.truckout_by_depot_daily WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": _archived_status(), "last_updated": datetime.utcnow().isoformat() + "Z"}


@router.get("/archive/truckout/state", response_model=dict)
def archive_truckout_state(
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=200),
    db=Depends(get_db),
):
    """GET /v1/archive/truckout/state?from=&to= - Archived (last published 2023)."""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if from_:
        params["from"] = from_
        where += " AND report_date >= :from::date"
    if to:
        params["to"] = to
        where += " AND report_date <= :to::date"
    r = db.execute(text(f"""
        SELECT report_date, product, state_name, truck_count, volume_litres
        FROM bronze.truckout_by_state_daily
        WHERE {where}
        ORDER BY report_date DESC, state_name
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = [{"report_date": (row[0].isoformat() if row[0] else None), "product": row[1], "state_name": row[2], "truck_count": row[3], "volume_litres": float(row[4]) if row[4] is not None else None} for row in rows]
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.truckout_by_state_daily WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": _archived_status(), "last_updated": datetime.utcnow().isoformat() + "Z"}


@router.get("/archive/stock/summary", response_model=dict)
def archive_stock_summary(
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/archive/stock/summary?from=&to= - Archived (last published 2023)."""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if from_:
        params["from"] = from_
        where += " AND report_date >= :from::date"
    if to:
        params["to"] = to
        where += " AND report_date <= :to::date"
    r = db.execute(text(f"""
        SELECT report_date, product, land_stock_litres, marine_stock_litres, total_stock_less_dead_litres,
               dead_stock_litres, total_stock_incl_dead_litres, land_days_sufficiency, marine_days_sufficiency, total_days_sufficiency
        FROM bronze.stock_days_sufficiency_summary
        WHERE {where}
        ORDER BY report_date DESC, product
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = []
    for row in rows:
        data.append({
            "report_date": row[0].isoformat() if row[0] else None,
            "product": row[1],
            "land_stock_litres": float(row[2]) if row[2] is not None else None,
            "marine_stock_litres": float(row[3]) if row[3] is not None else None,
            "total_stock_less_dead_litres": float(row[4]) if row[4] is not None else None,
            "dead_stock_litres": float(row[5]) if row[5] is not None else None,
            "total_stock_incl_dead_litres": float(row[6]) if row[6] is not None else None,
            "land_days_sufficiency": float(row[7]) if row[7] is not None else None,
            "marine_days_sufficiency": float(row[8]) if row[8] is not None else None,
            "total_days_sufficiency": float(row[9]) if row[9] is not None else None,
        })
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.stock_days_sufficiency_summary WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": _archived_status(), "last_updated": datetime.utcnow().isoformat() + "Z"}


@router.get("/archive/stock/ledger", response_model=dict)
def archive_stock_ledger(
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """GET /v1/archive/stock/ledger?from=&to= - Archived (last published 2023)."""
    offset = (page - 1) * per_page
    params = {"limit": per_page, "offset": offset}
    where = "1=1"
    if from_:
        params["from"] = from_
        where += " AND report_date >= :from::date"
    if to:
        params["to"] = to
        where += " AND report_date <= :to::date"
    r = db.execute(text(f"""
        SELECT report_date, product, opening_stock_litres, receipts_litres, evacuation_litres, book_closing_litres,
               actual_closing_litres, dead_stock_litres, closing_operational_litres, nat_avg_daily_consumption_litres, days_sufficiency, prev_days_sufficiency
        FROM bronze.stock_ledger_by_product
        WHERE {where}
        ORDER BY report_date DESC, product
        LIMIT :limit OFFSET :offset
    """), params)
    rows = r.fetchall()
    data = []
    for row in rows:
        data.append({
            "report_date": row[0].isoformat() if row[0] else None,
            "product": row[1],
            "opening_stock_litres": float(row[2]) if row[2] is not None else None,
            "receipts_litres": float(row[3]) if row[3] is not None else None,
            "evacuation_litres": float(row[4]) if row[4] is not None else None,
            "book_closing_litres": float(row[5]) if row[5] is not None else None,
            "actual_closing_litres": float(row[6]) if row[6] is not None else None,
            "dead_stock_litres": float(row[7]) if row[7] is not None else None,
            "closing_operational_litres": float(row[8]) if row[8] is not None else None,
            "nat_avg_daily_consumption_litres": float(row[9]) if row[9] is not None else None,
            "days_sufficiency": float(row[10]) if row[10] is not None else None,
            "prev_days_sufficiency": float(row[11]) if row[11] is not None else None,
        })
    total = db.execute(text(f"SELECT COUNT(*) FROM bronze.stock_ledger_by_product WHERE {where}"), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar() or 0
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total}, "data_status": _archived_status(), "last_updated": datetime.utcnow().isoformat() + "Z"}
