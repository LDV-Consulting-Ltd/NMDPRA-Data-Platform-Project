"""Build Silver normalized model from Bronze (dims + facts)."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List
from uuid import uuid4
import hashlib


def _hash_id(*parts: Any) -> str:
    h = hashlib.sha256(str(parts).encode()).hexdigest()
    return str(uuid4())  # deterministic UUID from hash would require uuid5; use uuid4 for simplicity


def build_dim_date(dates: List[date]) -> List[dict]:
    """Build silver.dim_date from distinct dates."""
    seen = set()
    out = []
    for d in sorted(set(dates)):
        if d in seen:
            continue
        seen.add(d)
        out.append({
            "date_key": d,
            "year": d.year,
            "month": d.month,
            "day": d.day,
            "week": d.isocalendar()[1],
            "quarter": (d.month - 1) // 3 + 1,
        })
    return out


def build_dim_product(products: List[str]) -> List[dict]:
    """Build silver.dim_product from distinct product names."""
    seen = set()
    out = []
    for p in sorted(set(p for p in products if p)):
        if p in seen:
            continue
        seen.add(p)
        out.append({
            "product_id": str(uuid4()),
            "product_code": p[:50],
            "product_name": p,
            "unit_default": "litres" if "stock" in p.lower() or "truckout" in p.lower() else None,
        })
    return out


def build_dim_location(locations: List[tuple]) -> List[dict]:
    """Build silver.dim_location (location_name, location_type, parent). location = (name, type)."""
    seen = set()
    out = []
    for name, loc_type in locations:
        if not name or (name, loc_type) in seen:
            continue
        seen.add((name, loc_type))
        out.append({
            "location_id": str(uuid4()),
            "location_name": name,
            "location_type": loc_type,
            "parent_location_id": None,
        })
    return out


def build_dim_facility(facilities: List[tuple]) -> List[dict]:
    """Build silver.dim_facility (facility_name, facility_type)."""
    seen = set()
    out = []
    for name, ftype in facilities:
        if not name or (name, ftype) in seen:
            continue
        seen.add((name, ftype))
        out.append({
            "facility_id": str(uuid4()),
            "facility_name": name,
            "facility_type": ftype,
        })
    return out


def bronze_to_silver_fact_prices(
    bronze_prices: List[dict],
    dim_location_by_name: Dict[tuple, str],
    dim_product_by_name: Dict[str, str],
) -> List[dict]:
    """Map bronze.fuel_prices_city -> silver.fact_prices."""
    out = []
    for r in bronze_prices:
        city = (r.get("city") or "").strip()
        loc_id = dim_location_by_name.get((city, "city")) if city else None
        prod_id = dim_product_by_name.get((r.get("product") or "PMS").strip())
        out.append({
            "id": str(uuid4()),
            "date_month": r.get("month"),
            "city_location_id": loc_id,
            "product_id": prod_id,
            "indicative": r.get("indicative_price"),
            "min_price": r.get("min_price"),
            "max_price": r.get("max_price"),
            "avg_price": r.get("avg_price"),
        })
    return out


def bronze_to_silver_fact_stock(
    bronze_stock: List[dict],
    dim_product_by_name: Dict[str, str],
) -> List[dict]:
    """Map bronze.stock_days_sufficiency_summary -> silver.fact_stock."""
    out = []
    for r in bronze_stock:
        prod_id = dim_product_by_name.get((r.get("product") or "").strip())
        out.append({
            "id": str(uuid4()),
            "date": r.get("report_date"),
            "product_id": prod_id,
            "land_stock": r.get("land_stock_litres"),
            "marine_stock": r.get("marine_stock_litres"),
            "total_stock": r.get("total_stock_less_dead_litres"),
            "dead_stock": r.get("dead_stock_litres"),
            "days_sufficiency": r.get("total_days_sufficiency"),
        })
    return out


def bronze_to_silver_fact_truckout(
    bronze_depot: List[dict],
    bronze_state: List[dict],
    dim_location_by_name: Dict[tuple, str],
    dim_product_by_name: Dict[str, str],
) -> List[dict]:
    """Map bronze truckout -> silver.fact_truckout (depot + state)."""
    out = []
    for r in bronze_depot:
        depot_name = (r.get("depot_name") or "").strip()
        loc_id = dim_location_by_name.get((depot_name, "depot")) if depot_name else None
        prod_id = dim_product_by_name.get((r.get("product") or "PMS").strip())
        out.append({
            "id": str(uuid4()),
            "date": r.get("report_date"),
            "location_id": loc_id,
            "product_id": prod_id,
            "trucks": r.get("truck_count"),
            "volume_litres": r.get("volume_litres"),
        })
    for r in bronze_state:
        state_name = (r.get("state_name") or "").strip()
        loc_id = dim_location_by_name.get((state_name, "state")) if state_name else None
        prod_id = dim_product_by_name.get((r.get("product") or "PMS").strip())
        out.append({
            "id": str(uuid4()),
            "date": r.get("report_date"),
            "location_id": loc_id,
            "product_id": prod_id,
            "trucks": r.get("truck_count"),
            "volume_litres": r.get("volume_litres"),
        })
    return out


def bronze_to_silver_fact_refinery_output(
    bronze_refinery: List[dict],
    bronze_modular: List[dict],
    dim_facility_by_name: Dict[str, str],
) -> List[dict]:
    """Map bronze refinery + modular -> silver.fact_refinery_output."""
    out = []
    for r in bronze_refinery:
        fid = dim_facility_by_name.get((r.get("refinery_name") or "").strip())
        out.append({
            "id": str(uuid4()),
            "month": r.get("month"),
            "facility_id": fid,
            "utilization_pct": r.get("utilization_pct"),
            "output_value": r.get("avg_supply_value"),
            "output_unit": r.get("avg_supply_unit"),
        })
    for r in bronze_modular:
        fid = dim_facility_by_name.get((r.get("refinery_name") or "").strip())
        out.append({
            "id": str(uuid4()),
            "month": r.get("month"),
            "facility_id": fid,
            "utilization_pct": r.get("capacity_utilization_pct"),
            "output_value": r.get("avg_ago_supply_value"),
            "output_unit": r.get("avg_ago_supply_unit"),
        })
    return out


def bronze_to_silver_fact_vessel_clearance(bronze_vessels: List[dict]) -> List[dict]:
    """Map bronze.vessel_clearance_schedule -> silver.fact_vessel_clearance."""
    return [
        {
            "id": str(uuid4()),
            "month": r.get("report_period"),
            "clearance_no": r.get("clearance_no"),
            "company": r.get("company"),
            "vessel": r.get("vessel_name"),
            "processing_days": r.get("processing_days"),
            "processing_hours": r.get("processing_hours"),
        }
        for r in bronze_vessels
    ]


def bronze_to_silver_fact_chart_series(bronze_chart: List[dict]) -> List[dict]:
    """Map bronze.chart_series_values -> silver.fact_chart_series."""
    return [
        {
            "id": str(uuid4()),
            "chart_key": f"{r.get('chart_name')}_{r.get('series_name')}",
            "period_date": r.get("period_date"),
            "period_month": r.get("period_month"),
            "series_name": r.get("series_name"),
            "value": r.get("value"),
        }
        for r in bronze_chart
    ]
