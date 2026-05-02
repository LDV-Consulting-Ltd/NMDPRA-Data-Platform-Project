"""Seed demo / library data into bronze so Prices, Sufficiency, Refineries, Gas, Vessels, Archive show something.
Library rule: monthly granularity = past 2 years (24 months); daily = 2 years coverage (one row per month)."""
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text

from app.database import get_db
from app.seed_library import library_daily_dates, library_month_dates, vary_price, vary_value

router = APIRouter()


def _require_admin(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    token = os.environ.get("ADMIN_RUN_TOKEN", "")
    if not token or x_admin_token != token:
        raise HTTPException(401, "Unauthorized")


@router.post("/seed-demo")
def seed_demo(db=Depends(get_db), _: None = Depends(_require_admin)):
    """Insert library demo rows: 2 years monthly + 2 years coverage for daily. Requires X-Admin-Token."""
    file_id = str(uuid.uuid4())
    now = datetime.utcnow()
    try:
        db.execute(text("""
            INSERT INTO bronze.file_registry (file_id, source_name, source_page_url, pdf_url, status, discovered_at)
            VALUES (:id, 'oilgasdata', 'https://www.nmdpra.gov.ng/OilGasData', 'https://example.com/demo.pdf', 'active', :now)
        """), {"id": file_id, "now": now})
    except Exception:
        r = db.execute(text("SELECT file_id FROM bronze.file_registry LIMIT 1"))
        row = r.fetchone()
        file_id = str(row[0]) if row else file_id
    db.commit()

    fid = file_id
    months = library_month_dates()
    daily_dates = library_daily_dates()

    def ins(q, p):
        db.execute(text(q), p)

    try:
        # --- Monthly: 2 years (24 months) per table ---
        for month in months:
            price = vary_price(month)
            for city in ("Lagos", "Abuja", "Port Harcourt"):
                ins("""INSERT INTO bronze.fuel_prices_city (id, month, city, indicative_price, min_price, max_price, avg_price, unit, source_file_id)
                    VALUES (:id, :month, :city, :p, :pmin, :pmax, :p, 'NGN/L', :fid)""",
                    {"id": str(uuid.uuid4()), "month": month, "city": city, "p": price, "pmin": price - 30, "pmax": price + 30, "fid": fid})
            for name, base_val in [("Crude production", 1.2), ("Export volume", 0.8)]:
                val = vary_value(month, base_val)
                ins("""INSERT INTO bronze.performance_highlights (id, month, metric_name, metric_value, unit, source_file_id)
                    VALUES (:id, :month, :name, :val, 'million bbl', :fid)""",
                    {"id": str(uuid.uuid4()), "month": month, "name": name, "val": val, "fid": fid})
            ins("""INSERT INTO bronze.chart_series_values (id, file_id, chart_name, series_name, period_type, period_date, period_month, value, unit, source_page)
                VALUES (:id, :fid, 'Stock days sufficiency', 'PMS', 'monthly', NULL, :month, :val, 'days', 1)""",
                {"id": str(uuid.uuid4()), "fid": fid, "month": month, "val": vary_value(month, 25.5)})
            ins("""INSERT INTO bronze.refinery_status (id, month, refinery_name, refinery_type, capacity_bpsd, utilization_pct, avg_supply_value, avg_supply_unit, source_file_id)
                VALUES (:id, :month, 'Refinery A', 'integrated', 65000, :util, 450, 'kbpd', :fid)""",
                {"id": str(uuid.uuid4()), "month": month, "fid": fid, "util": vary_value(month, 72.5)})
            ins("""INSERT INTO bronze.modular_refinery_output (id, month, refinery_name, capacity_utilization_pct, avg_ago_supply_value, avg_ago_supply_unit, source_file_id)
                VALUES (:id, :month, 'Modular B', :util, 120, 'kbpd', :fid)""",
                {"id": str(uuid.uuid4()), "month": month, "fid": fid, "util": vary_value(month, 68.0)})
            ins("""INSERT INTO bronze.vessel_clearance_schedule (id, report_period, clearance_no, company, vessel_name, processing_days, processing_hours, source_file_id)
                VALUES (:id, :month, :clr, 'Demo Co', 'MV Example', 3, 48, :fid)""",
                {"id": str(uuid.uuid4()), "month": month, "fid": fid, "clr": f"CLR-{month.year % 100:02d}{month.month:02d}"})
            ins("""INSERT INTO bronze.gas_infra (id, month, category, item_name, metric_name, metric_value, unit, source_file_id)
                VALUES (:id, :month, 'LPG', 'Domestic', 'Volume (tonnes)', :val, 'tonnes', :fid)""",
                {"id": str(uuid.uuid4()), "month": month, "fid": fid, "val": vary_value(month, 150.5)})

        # --- Daily: 2 years coverage (one row per month = 24 rows) ---
        for dt in daily_dates:
            ins("""INSERT INTO bronze.stock_days_sufficiency_summary (id, report_date, product, land_stock_litres, marine_stock_litres, total_days_sufficiency, source_file_id)
                VALUES (:id, :dt, 'PMS', 50000000, 30000000, :days, :fid)""",
                {"id": str(uuid.uuid4()), "dt": dt, "fid": fid, "days": vary_value(dt, 28)})
            ins("""INSERT INTO bronze.truckout_by_depot_daily (id, report_date, product, depot_name, truck_count, volume_litres, source_file_id)
                VALUES (:id, :dt, 'PMS', 'Lagos Depot', 120, 4500000, :fid)""",
                {"id": str(uuid.uuid4()), "dt": dt, "fid": fid})

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

    return {
        "ok": True,
        "message": "Library demo seeded: 2 years monthly + 2 years coverage daily. Refresh Prices, Sufficiency, Refineries, Gas, Vessels, Archive.",
        "months": len(months),
        "daily_points": len(daily_dates),
    }
