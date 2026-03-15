"""Parse Daily Truckout PDFs (archived) into bronze truckout tables."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import pdfplumber

from parsers.utils import (
    EXTRACTION_METHOD_TABLE,
    PARSER_VERSION,
    safe_decimal,
    safe_int,
    parse_date,
    row_meta,
)


def _tables(page: Any) -> List[List[List[str]]]:
    out = []
    for t in page.extract_tables() or []:
        if t and any(cell for row in t for cell in (row or []) if cell):
            out.append(t)
    return out


def parse_truckout_by_depot_daily(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_date: date,
) -> List[Dict[str, Any]]:
    """Extract truckout by depot: report_date, product, depot_name, truck_count, volume_litres."""
    rows = []
    for page_num, page in pages:
        for table in _tables(page):
            for r in table or []:
                if len(r) >= 4 and r[0]:
                    depot = str(r[0]).strip()
                    if not depot or depot.lower() in ("depot", "depot name", ""):
                        continue
                    rows.append({
                        "id": str(uuid4()),
                        "report_date": report_date,
                        "product": str(r[1]).strip() if len(r) > 1 and r[1] else "PMS",
                        "depot_name": depot,
                        "truck_count": safe_int(r[2]) if len(r) > 2 else None,
                        "volume_litres": safe_decimal(r[3]) if len(r) > 3 else None,
                        "source_file_id": file_id,
                        "source_page": page_num,
                        **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.8),
                    })
    return rows


def parse_truckout_by_state_daily(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_date: date,
) -> List[Dict[str, Any]]:
    """Extract truckout by state."""
    rows = []
    for page_num, page in pages:
        for table in _tables(page):
            for r in table or []:
                if len(r) >= 4 and r[0]:
                    state = str(r[0]).strip()
                    if not state or state.lower() in ("state", "state name", ""):
                        continue
                    rows.append({
                        "id": str(uuid4()),
                        "report_date": report_date,
                        "product": str(r[1]).strip() if len(r) > 1 and r[1] else "PMS",
                        "state_name": state,
                        "truck_count": safe_int(r[2]) if len(r) > 2 else None,
                        "volume_litres": safe_decimal(r[3]) if len(r) > 3 else None,
                        "source_file_id": file_id,
                        "source_page": page_num,
                        **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.8),
                    })
    return rows


def parse_truckout_daily_totals(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_date: date,
) -> List[Dict[str, Any]]:
    """Extract daily totals: report_date, product, total_trucks, total_volume_litres."""
    rows = []
    for page_num, page in pages:
        for table in _tables(page):
            for r in table or []:
                if len(r) >= 3 and r[0]:
                    product = str(r[0]).strip() or "PMS"
                    rows.append({
                        "id": str(uuid4()),
                        "report_date": report_date,
                        "product": product,
                        "total_trucks": safe_int(r[1]) if len(r) > 1 else None,
                        "total_volume_litres": safe_decimal(r[2]) if len(r) > 2 else None,
                        "source_file_id": file_id,
                        "source_page": page_num,
                        **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.8),
                    })
    return rows


def _infer_report_date(pdf_path: Path, pages: List[Tuple[int, Any]]) -> date:
    """Infer report date from filename or first page text."""
    from parsers.utils import parse_date
    text = (pdf_path.stem or "").replace("_", " ").replace("-", " ")
    d = parse_date(text)
    if d:
        return d
    if pages:
        try:
            raw = pages[0][1].extract_text() or ""
            d = parse_date(raw[:200])
            if d:
                return d
        except Exception:
            pass
    return date.today()


def parse_dailytruckout_pdf(
    pdf_path: Path,
    file_id: str,
    report_date: date | None = None,
) -> Dict[str, Any]:
    """Full parse of one Daily Truckout PDF (archived)."""
    pages_list: List[Tuple[int, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, p in enumerate(pdf.pages):
            pages_list.append((i + 1, p))
    report_date = report_date or _infer_report_date(pdf_path, pages_list)
    return {
        "truckout_by_depot_daily": parse_truckout_by_depot_daily(pages_list, file_id, report_date),
        "truckout_by_state_daily": parse_truckout_by_state_daily(pages_list, file_id, report_date),
        "truckout_daily_totals": parse_truckout_daily_totals(pages_list, file_id, report_date),
        "extraction_method": EXTRACTION_METHOD_TABLE,
        "confidence_score": 0.8,
        "parser_version": PARSER_VERSION,
    }
