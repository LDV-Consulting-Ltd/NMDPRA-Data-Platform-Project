"""Build Gold dimensional model (star schemas) from Silver."""
from __future__ import annotations

from typing import Any, Dict, List
from uuid import uuid4


def silver_to_gold_dim_date(silver_dates: List[dict]) -> List[dict]:
    """Copy silver.dim_date -> gold.dim_date."""
    return [
        {
            "date_key": d["date_key"],
            "year": d["year"],
            "month": d["month"],
            "day": d["day"],
            "week": d.get("week"),
            "quarter": d.get("quarter"),
        }
        for d in silver_dates
    ]


def silver_to_gold_dim_product(silver_products: List[dict]) -> List[dict]:
    """Map silver.dim_product -> gold.dim_product (product_key = product_id)."""
    return [
        {
            "product_key": p["product_id"],
            "product_code": p["product_code"],
            "product_name": p["product_name"],
            "unit_default": p.get("unit_default"),
        }
        for p in silver_products
    ]


def silver_to_gold_dim_location(silver_locations: List[dict]) -> List[dict]:
    """Map silver.dim_location -> gold.dim_location."""
    return [
        {
            "location_key": loc["location_id"],
            "location_name": loc["location_name"],
            "location_type": loc["location_type"],
        }
        for loc in silver_locations
    ]


def silver_to_gold_dim_facility(silver_facilities: List[dict]) -> List[dict]:
    """Map silver.dim_facility -> gold.dim_facility."""
    return [
        {
            "facility_key": f["facility_id"],
            "facility_name": f["facility_name"],
            "facility_type": f["facility_type"],
        }
        for f in silver_facilities
    ]


def silver_to_gold_dim_report(sources: List[dict]) -> List[dict]:
    """Build gold.dim_report (source_name, report_title, status)."""
    seen = set()
    out = []
    for s in sources:
        key = (s.get("source_name"), s.get("report_title") or "", s.get("status") or "active")
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "report_key": str(uuid4()),
            "source_name": key[0],
            "report_title": key[1] or key[0],
            "status": key[2],
        })
    return out


def silver_to_gold_fact_fuel_prices(
    silver_fact_prices: List[dict],
    dim_report_by_source: Dict[str, str],
    month_key_eq_date: bool = True,
) -> List[dict]:
    """Map silver.fact_prices -> gold.fact_fuel_prices with report_key."""
    out = []
    for r in silver_fact_prices:
        month = r.get("date_month")
        report_key = dim_report_by_source.get("oilgasdata")
        out.append({
            "id": str(uuid4()),
            "date_month_key": month,
            "location_key": r.get("city_location_id"),
            "product_key": r.get("product_id"),
            "report_key": report_key,
            "indicative": r.get("indicative"),
            "min_price": r.get("min_price"),
            "max_price": r.get("max_price"),
            "avg_price": r.get("avg_price"),
        })
    return out


def silver_to_gold_fact_stock_sufficiency(
    silver_fact_stock: List[dict],
    dim_report_by_source: Dict[str, str],
) -> List[dict]:
    """Map silver.fact_stock -> gold.fact_stock_sufficiency."""
    report_key = dim_report_by_source.get("stockreport")
    return [
        {
            "id": str(uuid4()),
            "date_key": r.get("date"),
            "product_key": r.get("product_id"),
            "report_key": report_key,
            "land_stock": r.get("land_stock"),
            "marine_stock": r.get("marine_stock"),
            "total_stock": r.get("total_stock"),
            "days_sufficiency": r.get("days_sufficiency"),
        }
        for r in silver_fact_stock
    ]


def silver_to_gold_fact_truckout(
    silver_fact_truckout: List[dict],
    dim_report_by_source: Dict[str, str],
) -> List[dict]:
    """Map silver.fact_truckout -> gold.fact_truckout."""
    report_key = dim_report_by_source.get("dailytruckout")
    return [
        {
            "id": str(uuid4()),
            "date_key": r.get("date"),
            "location_key": r.get("location_id"),
            "product_key": r.get("product_id"),
            "report_key": report_key,
            "trucks": r.get("trucks"),
            "volume_litres": r.get("volume_litres"),
        }
        for r in silver_fact_truckout
    ]


def silver_to_gold_fact_refinery(
    silver_fact_refinery: List[dict],
    dim_report_by_source: Dict[str, str],
) -> List[dict]:
    """Map silver.fact_refinery_output -> gold.fact_refinery."""
    report_key = dim_report_by_source.get("oilgasdata")
    return [
        {
            "id": str(uuid4()),
            "month_key": r.get("month"),
            "facility_key": r.get("facility_id"),
            "report_key": report_key,
            "utilization_pct": r.get("utilization_pct"),
            "output_value": r.get("output_value"),
        }
        for r in silver_fact_refinery
    ]


def silver_to_gold_fact_vessel_clearance(
    silver_fact_vessel: List[dict],
    dim_report_by_source: Dict[str, str],
) -> List[dict]:
    """Map silver.fact_vessel_clearance -> gold.fact_vessel_clearance."""
    report_key = dim_report_by_source.get("vesselschedule")
    return [
        {
            "id": str(uuid4()),
            "month_key": r.get("month"),
            "report_key": report_key,
            "company": r.get("company"),
            "vessel": r.get("vessel"),
            "processing_days": r.get("processing_days"),
            "processing_hours": r.get("processing_hours"),
        }
        for r in silver_fact_vessel
    ]


def silver_to_gold_fact_series(
    silver_fact_chart: List[dict],
    dim_report_by_source: Dict[str, str],
) -> List[dict]:
    """Map silver.fact_chart_series -> gold.fact_series."""
    report_key = dim_report_by_source.get("oilgasdata")
    out = []
    for r in silver_fact_chart:
        out.append({
            "id": str(uuid4()),
            "date_key": r.get("period_date"),
            "month_key": r.get("period_month"),
            "report_key": report_key,
            "series_name": r.get("series_name"),
            "metric_value": r.get("value"),
            "chart_name": r.get("chart_key", "").split("_")[0] if r.get("chart_key") else None,
        })
    return out
