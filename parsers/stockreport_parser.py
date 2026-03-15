"""Parse Stock & Days Sufficiency PDFs (archived) into bronze stock tables."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import pdfplumber

from parsers.utils import (
    EXTRACTION_METHOD_TABLE,
    PARSER_VERSION,
    safe_decimal,
    parse_date,
    row_meta,
)


def _tables(page: Any) -> List[List[List[str]]]:
    out = []
    for t in page.extract_tables() or []:
        if t and any(cell for row in t for cell in (row or []) if cell):
            out.append(t)
    return out


def parse_stock_days_sufficiency_summary(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_date: date,
) -> List[Dict[str, Any]]:
    """Extract stock_days_sufficiency_summary rows."""
    rows = []
    for page_num, page in pages:
        for table in _tables(page):
            if len(table) < 2:
                continue
            for r in table[1:]:
                if not r or len(r) < 3:
                    continue
                product = str(r[0]).strip() if r[0] else None
                if not product:
                    continue
                r = (r or []) + [None] * 15
                rows.append({
                    "id": str(uuid4()),
                    "report_date": report_date,
                    "product": product,
                    "land_stock_litres": safe_decimal(r[1]),
                    "marine_stock_litres": safe_decimal(r[2]),
                    "total_stock_less_dead_litres": safe_decimal(r[3]),
                    "dead_stock_litres": safe_decimal(r[4]),
                    "total_stock_incl_dead_litres": safe_decimal(r[5]),
                    "land_days_sufficiency": safe_decimal(r[6]),
                    "marine_days_sufficiency": safe_decimal(r[7]),
                    "total_days_sufficiency": safe_decimal(r[8]),
                    "source_file_id": file_id,
                    "source_page": page_num,
                    **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.8),
                })
    return rows


def parse_stock_ledger_by_product(
    pages: List[Tuple[int, Any]],
    file_id: str,
    report_date: date,
) -> List[Dict[str, Any]]:
    """Extract stock_ledger_by_product rows."""
    rows = []
    for page_num, page in pages:
        for table in _tables(page):
            if len(table) < 2:
                continue
            for r in table[1:]:
                if not r or len(r) < 3:
                    continue
                product = str(r[0]).strip() if r[0] else None
                if not product:
                    continue
                r = (r or []) + [None] * 15
                rows.append({
                    "id": str(uuid4()),
                    "report_date": report_date,
                    "product": product,
                    "opening_stock_litres": safe_decimal(r[1]),
                    "receipts_litres": safe_decimal(r[2]),
                    "evacuation_litres": safe_decimal(r[3]),
                    "book_closing_litres": safe_decimal(r[4]),
                    "actual_closing_litres": safe_decimal(r[5]),
                    "dead_stock_litres": safe_decimal(r[6]),
                    "closing_operational_litres": safe_decimal(r[7]),
                    "nat_avg_daily_consumption_litres": safe_decimal(r[8]),
                    "days_sufficiency": safe_decimal(r[9]),
                    "prev_days_sufficiency": safe_decimal(r[10]),
                    "source_file_id": file_id,
                    "source_page": page_num,
                    **row_meta(file_id, page_num, EXTRACTION_METHOD_TABLE, 0.8),
                })
    return rows


def _infer_report_date(pdf_path: Path, pages: List[Tuple[int, Any]]) -> date:
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


def parse_stockreport_pdf(
    pdf_path: Path,
    file_id: str,
    report_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Full parse of one Stock & Days Sufficiency PDF (archived)."""
    pages_list: List[Tuple[int, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, p in enumerate(pdf.pages):
            pages_list.append((i + 1, p))
    report_date = report_date or _infer_report_date(pdf_path, pages_list)
    return {
        "stock_days_sufficiency_summary": parse_stock_days_sufficiency_summary(pages_list, file_id, report_date),
        "stock_ledger_by_product": parse_stock_ledger_by_product(pages_list, file_id, report_date),
        "extraction_method": EXTRACTION_METHOD_TABLE,
        "confidence_score": 0.8,
        "parser_version": PARSER_VERSION,
    }
