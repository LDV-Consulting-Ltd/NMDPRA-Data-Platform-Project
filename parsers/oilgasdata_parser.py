"""Parse Oil & Gas Data monthly fact sheet PDFs into bronze tables + chart_series_values."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import pdfplumber

from parsers.utils import (
    EXTRACTION_METHOD_TABLE,
    EXTRACTION_METHOD_TEXT,
    EXTRACTION_METHOD_CHART_TABLE,
    PARSER_VERSION,
    safe_decimal,
    safe_int,
    parse_date,
    parse_month_first,
    row_meta,
)


def _text(page: Any) -> str:
    return (page.extract_text() or "").strip()


def _tables(page: Any) -> List[List[List[str]]]:
    out = []
    for t in page.extract_tables() or []:
        if t and any(cell for row in t for cell in (row or []) if cell):
            out.append(t)
    return out


def parse_performance_highlights(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_month: Optional[date],
) -> List[Dict[str, Any]]:
    """Extract performance highlights (metric_name, metric_value) from text/tables."""
    rows = []
    for page_num, page in pages:
        text = _text(page)
        tables = _tables(page)
        month = report_month or parse_month_first(text)
        # Simple pattern: "Metric Name: value unit" or table with metric/value columns
        for table in tables:
            for r in table:
                if len(r) >= 2 and r[0] and r[1]:
                    name = str(r[0]).strip()
                    val = safe_decimal(r[1])
                    if name and (val is not None or (len(r) > 2 and r[2])):
                        rows.append({
                            "id": str(uuid4()),
                            "month": month,
                            "metric_name": name,
                            "metric_value": val,
                            "unit": str(r[2]).strip() if len(r) > 2 and r[2] else None,
                            "source_file_id": file_id,
                            "source_page": page_num,
                            **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.85),
                        })
    return rows


def parse_refinery_status(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_month: Optional[date],
) -> List[Dict[str, Any]]:
    """Extract refinery status table."""
    rows = []
    for page_num, page in pages:
        tables = _tables(page)
        month = report_month
        for table in tables:
            # Assume header row then data; columns may vary
            if len(table) < 2:
                continue
            headers = [str(h).strip().lower() for h in (table[0] or [])]
            for r in table[1:]:
                if not r or not any(r):
                    continue
                r = (r or []) + [None] * (len(headers) - len(r))
                get = lambda i: r[i] if i < len(r) and r[i] is not None else None
                name = get(0)
                if not name:
                    continue
                month = month or parse_month_first(str(get(1)) if get(1) else None)
                rows.append({
                    "id": str(uuid4()),
                    "month": month or report_month,
                    "refinery_name": str(name).strip(),
                    "refinery_type": _norm_refinery_type(str(get(1)) if get(1) else None),
                    "capacity_bpsd": safe_decimal(get(2)),
                    "utilization_pct": safe_decimal(get(3)),
                    "product": str(get(4)).strip() if get(4) else None,
                    "avg_supply_value": safe_decimal(get(5)),
                    "avg_supply_unit": str(get(6)).strip() if get(6) else None,
                    "status": str(get(7)).strip() if get(7) else None,
                    "notes": str(get(8)).strip() if get(8) else None,
                    "source_file_id": file_id,
                    "source_page": page_num,
                    **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.8),
                })
    return rows


def _norm_refinery_type(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.lower()
    if "state" in s or "nnpc" in s:
        return "state_owned"
    if "modular" in s:
        return "modular"
    if "private" in s:
        return "private"
    return "unknown"


def parse_modular_refinery_output(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_month: Optional[date],
) -> List[Dict[str, Any]]:
    """Extract modular refinery output."""
    rows = []
    for page_num, page in pages:
        for table in _tables(page):
            if len(table) < 2:
                continue
            for r in table[1:]:
                if not r or not r[0]:
                    continue
                r = (r or []) + [None] * 8
                rows.append({
                    "id": str(uuid4()),
                    "month": report_month or parse_month_first(str(r[1])),
                    "refinery_name": str(r[0]).strip(),
                    "capacity_utilization_pct": safe_decimal(r[2]),
                    "avg_ago_supply_value": safe_decimal(r[3]),
                    "avg_ago_supply_unit": str(r[4]).strip() if r[4] else None,
                    "status": str(r[5]).strip() if r[5] else None,
                    "source_file_id": file_id,
                    "source_page": page_num,
                    **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.8),
                })
    return rows


def parse_consumption_benchmark(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_month: Optional[date],
) -> List[Dict[str, Any]]:
    """Extract consumption benchmark (product, benchmark_value, unit)."""
    rows = []
    for page_num, page in pages:
        for table in _tables(page):
            for r in table or []:
                if len(r) >= 3 and r[0] and r[1]:
                    rows.append({
                        "id": str(uuid4()),
                        "month": report_month or parse_month_first(str(r[2]) if len(r) > 2 else None),
                        "product": str(r[0]).strip(),
                        "benchmark_value": safe_decimal(r[1]) or Decimal("0"),
                        "unit": str(r[2]).strip() if len(r) > 2 and r[2] else None,
                        "source_file_id": file_id,
                        "source_page": page_num,
                        **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.85),
                    })
    return rows


def parse_actual_consumption_truckout_daily(
    pages: List[Tuple[int, Any]],
    file_id: str,
) -> List[Dict[str, Any]]:
    """Extract actual consumption / truckout daily (date, product, volume)."""
    rows = []
    for page_num, page in pages:
        for table in _tables(page):
            for r in table or []:
                if len(r) >= 3 and r[0] and r[1]:
                    dt = parse_date(r[0])
                    if dt:
                        rows.append({
                            "id": str(uuid4()),
                            "date": dt,
                            "product": str(r[1]).strip(),
                            "volume_value": safe_decimal(r[2]) or Decimal("0"),
                            "unit": str(r[3]).strip() if len(r) > 3 and r[3] else None,
                            "source_file_id": file_id,
                            "source_page": page_num,
                            **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.8),
                        })
    return rows


def parse_fuel_prices_city(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_month: Optional[date],
) -> List[Dict[str, Any]]:
    """Extract fuel prices by city."""
    rows = []
    for page_num, page in pages:
        for table in _tables(page):
            if len(table) < 2:
                continue
            headers = [str(h).strip().lower() for h in (table[0] or [])]
            for r in table[1:]:
                if not r or not r[0]:
                    continue
                r = (r or []) + [None] * 10
                city = str(r[0]).strip()
                if not city or city.lower() in ("city", "location", ""):
                    continue
                rows.append({
                    "id": str(uuid4()),
                    "month": report_month or parse_month_first(str(r[1])),
                    "city": city,
                    "indicative_price": safe_decimal(r[2]),
                    "min_price": safe_decimal(r[3]),
                    "max_price": safe_decimal(r[4]),
                    "avg_price": safe_decimal(r[5]),
                    "unit": "NGN/L",
                    "notes": str(r[7]).strip() if len(r) > 7 and r[7] else None,
                    "source_file_id": file_id,
                    "source_page": page_num,
                    **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.85),
                })
    return rows


def parse_gas_infra(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_month: Optional[date],
) -> List[Dict[str, Any]]:
    """Extract gas infrastructure (category, item_name, metric_name, metric_value)."""
    rows = []
    categories = ("gas_supply_summary", "gas_processing_capacity", "pipeline_progress", "other")
    for page_num, page in pages:
        text = _text(page)
        month = report_month or parse_month_first(text)
        for table in _tables(page):
            for r in table or []:
                if len(r) >= 2 and r[0]:
                    cat = str(r[0]).strip().lower().replace(" ", "_")[:50]
                    if cat not in categories:
                        cat = "other"
                    rows.append({
                        "id": str(uuid4()),
                        "month": month,
                        "category": cat,
                        "item_name": str(r[1]).strip() if len(r) > 1 and r[1] else None,
                        "metric_name": str(r[2]).strip() if len(r) > 2 and r[2] else str(r[0]).strip(),
                        "metric_value": safe_decimal(r[3]) if len(r) > 3 else safe_decimal(r[2]) if len(r) > 2 else None,
                        "unit": str(r[4]).strip() if len(r) > 4 and r[4] else None,
                        "source_file_id": file_id,
                        "source_page": page_num,
                        **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.75),
                    })
    return rows


def parse_chart_series_values(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_month: Optional[date],
) -> List[Dict[str, Any]]:
    """
    Parse table-under-chart values (Inland/Marine/Total by day or month).
    DO NOT digitize chart pixels; only use printed tables under charts.
    """
    rows = []
    for page_num, page in pages:
        for table in _tables(page):
            # Detect series: headers like Inland, Marine, Total; period column
            if len(table) < 2:
                continue
            header = [str(h).strip() for h in (table[0] or [])]
            series_names = [h for h in header[1:] if h and h.lower() in ("inland", "marine", "total", "day", "month")]
            if not series_names:
                series_names = header[1:] if len(header) > 1 else []
            for r in table[1:]:
                if not r:
                    continue
                r = (r or []) + [None] * (len(header) - len(r))
                period_str = str(r[0]).strip() if r[0] else None
                period_date = parse_date(period_str)
                period_month = parse_month_first(period_str) or report_month
                for i, series in enumerate(series_names):
                    if i + 1 >= len(r):
                        break
                    val = safe_decimal(r[i + 1])
                    if val is None:
                        continue
                    rows.append({
                        "id": str(uuid4()),
                        "file_id": file_id,
                        "chart_name": "consumption_trend",
                        "series_name": series,
                        "period_type": "monthly" if period_month and not period_date else "daily",
                        "period_date": period_date,
                        "period_month": period_month,
                        "value": val,
                        "unit": None,
                        "source_page": page_num,
                        **row_meta(file_id, page_num, EXTRACTION_METHOD_CHART_TABLE, 0.9),
                    })
    return rows


def parse_oilgasdata_pdf(
    pdf_path: Path,
    file_id: str,
    report_period: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Full parse of one Oil & Gas fact sheet PDF.
    Returns dict with keys: performance_highlights, refinery_status, modular_refinery_output,
    consumption_benchmark, actual_consumption_truckout_daily, fuel_prices_city, gas_infra,
    chart_series_values, extraction_method, confidence_score, parser_version.
    """
    pages_list: List[Tuple[int, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, p in enumerate(pdf.pages):
            pages_list.append((i + 1, p))

    month = report_period or (parse_month_first(pdf_path.stem) if pdf_path.stem else None)

    result = {
        "performance_highlights": parse_performance_highlights(pages_list, file_id, month),
        "refinery_status": parse_refinery_status(pages_list, file_id, month),
        "modular_refinery_output": parse_modular_refinery_output(pages_list, file_id, month),
        "consumption_benchmark": parse_consumption_benchmark(pages_list, file_id, month),
        "actual_consumption_truckout_daily": parse_actual_consumption_truckout_daily(pages_list, file_id),
        "fuel_prices_city": parse_fuel_prices_city(pages_list, file_id, month),
        "gas_infra": parse_gas_infra(pages_list, file_id, month),
        "chart_series_values": parse_chart_series_values(pages_list, file_id, month),
        "extraction_method": EXTRACTION_METHOD_TABLE,
        "confidence_score": 0.85,
        "parser_version": PARSER_VERSION,
    }
    return result
